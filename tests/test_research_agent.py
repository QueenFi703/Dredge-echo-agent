import json
import unittest

from bridge.research_agent import ResearchAgent
from bridge.verification import NemotronVerifier, VerificationError


class _FakeSearch:
    def search(self, query, *, max_results=5):
        return {"query": query, "sources": [{"id": "source-1", "url": "https://one.example", "content": "supported fact"}, {"id": "source-2", "url": "https://two.example", "content": "conflicting fact"}]}


class _FakeLLM:
    def __init__(self, response): self.response, self.calls = response, []
    def generate(self, action, source="source", target="target", source_value=None):
        self.calls.append((action, source, target, source_value)); return self.response


def _verification(status="SUPPORTED", correction=None):
    return json.dumps({"claims": [{"claim": "material claim", "status": status, "evidence_ids": ["source-1"], "reason": "checked", "recommended_correction": correction}], "overall_status": status, "conflicts": ["source disagreement"] if status == "CONFLICTED" else [], "missing_evidence": ["primary source"] if status == "UNSUPPORTED" else []})


class ResearchAgentTests(unittest.TestCase):
    def _agent(self, verification=_verification(), arbitration="corrected answer"):
        architect = _FakeLLM("Architect grounded synthesis")
        critic, arbiter = _FakeLLM(verification), _FakeLLM(arbitration)
        agent = ResearchAgent(search=_FakeSearch(), llm=architect, verifier=NemotronVerifier(critic), repairer=architect, arbitrator=arbiter, architect_model="glm-id", arbitrator_model="kimi-id", nemotron_model="nemotron-id")
        return agent, architect, critic, arbiter

    def test_nemotron_receives_kimi_draft_and_tavily_evidence(self):
        agent, kimi, critic, _ = self._agent(); result = agent.research("What changed?"); payload = critic.calls[0][3]
        self.assertEqual(payload["proposed_answer"], "Architect grounded synthesis")
        self.assertEqual(payload["evidence"]["sources"][0]["id"], "source-1")
        self.assertEqual(kimi.calls[0][0], "research_and_reason")
        self.assertEqual(result.trace["synthesis"]["model"], "glm-id")
        self.assertEqual(result.trace["verification"]["model"], "nemotron-id")

    def test_supported_claim_keeps_kimi_answer_and_skips_arbitration(self):
        agent, _, _, arbiter = self._agent(); result = agent.research("Question")
        self.assertEqual(result.answer, result.draft); self.assertEqual(arbiter.calls, [])
        self.assertEqual(result.trace["arbitration"]["claims_revised"], 0)

    def test_unsupported_claim_is_flagged_and_revised(self):
        agent, _, _, arbiter = self._agent(_verification("UNSUPPORTED", "Remove it")); result = agent.research("Question")
        self.assertEqual(result.answer, "corrected answer")
        self.assertEqual(result.verification["claims"][0]["status"], "UNSUPPORTED")
        self.assertEqual(arbiter.calls[0][0], "arbitrate_evidence_critique")
        self.assertEqual(result.trace["arbitration"]["claims_revised"], 1)
        self.assertEqual(result.trace["arbitration"]["route"], "KIMI_ESCALATION")

    def test_partial_claim_uses_low_cost_architect_repair(self):
        agent, architect, _, arbiter = self._agent(_verification("PARTIAL", "Qualify it"), "unused")
        architect.response = "qualified answer"
        result = agent.research("Question")
        self.assertEqual(result.answer, "qualified answer")
        self.assertEqual(len(architect.calls), 2)
        self.assertEqual(arbiter.calls, [])
        self.assertEqual(result.trace["arbitration"]["route"], "ARCHITECT_REPAIR")

    def test_conflicting_evidence_is_surfaced(self):
        agent, _, _, _ = self._agent(_verification("CONFLICTED", "Qualify it")); result = agent.research("Question")
        self.assertEqual(result.verification["conflicts"], ["source disagreement"])
        self.assertEqual(result.trace["verification"]["conflicted"], 1)

    def test_empty_verification_fails(self):
        agent, _, _, _ = self._agent("")
        with self.assertRaises(VerificationError): agent.research("Question")

    def test_no_sources_fails_before_models_are_called(self):
        agent, kimi, _, _ = self._agent(); agent.search = type("EmptySearch", (), {"search": lambda *a, **k: {"sources": []}})()
        with self.assertRaises(RuntimeError): agent.research("Question")
        self.assertEqual(kimi.calls, [])


if __name__ == "__main__": unittest.main()
