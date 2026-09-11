import unittest

from bridge.adaptive_agent import AdaptiveResearchAgent


class _FakeSearch:
    def search(self, question, max_results=6):
        return {
            "query": question,
            "sources": [
                {"title": "A", "url": "https://a.example", "content": "evidence a"},
                {"title": "B", "url": "https://b.example", "content": "evidence b"},
                {"title": "C", "url": "https://c.example", "content": "evidence c"},
                {"title": "D", "url": "https://d.example", "content": "evidence d"},
            ],
        }


class _FakeLLM:
    def __init__(self):
        self.calls = []

    def generate(self, action, source="source", target="target", source_value=None, *, reasoning_effort=None):
        self.calls.append({
            "action": action,
            "reasoning_effort": reasoning_effort,
            "source_value": source_value,
        })
        if action == "dredge_arbitrate":
            return "arbitrated answer"
        return "initial grounded draft"


def _conflicted_critic(question, evidence, draft):
    return {
        "claims": [
            {"claim": "one", "status": "SUPPORTED"},
            {"claim": "two", "status": "CONFLICTED"},
            {"claim": "three", "status": "UNSUPPORTED"},
        ]
    }


def _supported_critic(question, evidence, draft):
    return {
        "claims": [
            {"claim": "one", "status": "SUPPORTED"},
            {"claim": "two", "status": "SUPPORTED"},
            {"claim": "three", "status": "SUPPORTED"},
        ]
    }


class AdaptiveResearchAgentTests(unittest.TestCase):
    def test_conflict_expands_into_deeper_orchestration_and_arbitration(self):
        llm = _FakeLLM()
        agent = AdaptiveResearchAgent(
            search=_FakeSearch(),
            llm=llm,
            critic=_conflicted_critic,
            arbitrator=llm,
        )

        result = agent.research(
            "Should this company launch the product given conflicting market evidence?",
            max_results=4,
        )

        self.assertEqual(result.answer, "arbitrated answer")
        self.assertIn(result.intelligence_state["mode"], {"deliberative", "adversarial"})
        self.assertIn(result.intelligence_state["reasoning"], {"high", "xhigh"})
        topology_events = [e for e in result.events if e["event"] == "TOPOLOGY_CHANGED"]
        self.assertTrue(topology_events)
        self.assertTrue(any(e["details"]["spawned_agents"] for e in topology_events))
        self.assertEqual(llm.calls[-1]["action"], "dredge_arbitrate")

    def test_converged_evidence_avoids_unnecessary_arbitration(self):
        llm = _FakeLLM()
        agent = AdaptiveResearchAgent(
            search=_FakeSearch(),
            llm=llm,
            critic=_supported_critic,
            arbitrator=llm,
        )

        result = agent.research("What does the evidence show?", max_results=4)

        self.assertEqual(result.answer, "initial grounded draft")
        self.assertNotEqual(result.intelligence_state["mode"], "adversarial")
        self.assertEqual([c["action"] for c in llm.calls], ["investigate_with_evidence"])

    def test_reasoning_effort_is_selected_per_call(self):
        llm = _FakeLLM()
        agent = AdaptiveResearchAgent(
            search=_FakeSearch(),
            llm=llm,
            critic=_conflicted_critic,
            arbitrator=llm,
        )

        agent.research(
            "Compare multiple strategic paths and determine which is likely to survive scrutiny.",
            max_results=4,
            materiality=0.9,
            risk_tolerance="low",
        )

        efforts = [call["reasoning_effort"] for call in llm.calls]
        self.assertTrue(all(effort in {"medium", "high", "xhigh"} for effort in efforts))
        self.assertIn("xhigh", efforts)


if __name__ == "__main__":
    unittest.main()
