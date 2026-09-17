import json
import unittest
from bridge.demo import present_result
from bridge.verification import NemotronVerifier, VerificationError
from tests import test_research_agent as fixtures

class SequenceCritic:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.answers = []
    def generate(self, action, source, target, source_value):
        self.answers.append(source_value["proposed_answer"])
        return next(self.responses)

class FinalVerificationTests(unittest.TestCase):
    def agent(self, final, initial="UNSUPPORTED"):
        agent, _, _, arbiter = fixtures.ResearchAgentTests()._agent()
        critic = SequenceCritic(fixtures._verification(initial, "Correct it"), final)
        agent.verifier = NemotronVerifier(critic)
        return agent, critic, arbiter

    def test_revised_answer_is_verified_and_presented(self):
        agent, critic, _ = self.agent(fixtures._verification())
        result = agent.research("Question")
        self.assertEqual(critic.answers, [result.draft, result.answer])
        self.assertEqual(result.verification["overall_status"], "SUPPORTED")
        self.assertEqual(result.draft_verification["overall_status"], "UNSUPPORTED")
        self.assertEqual(result.trace["final_verification"]["status"], "COMPLETE")
        self.assertEqual(result.trace["arbitration"]["evidence_confidence"], "HIGH")
        self.assertEqual(json.loads(present_result(result).verification_json)["overall_status"], "SUPPORTED")

    def test_unresolved_revision_remains_visible(self):
        agent, critic, _ = self.agent(fixtures._verification("UNSUPPORTED", "Still unsupported"))
        result = agent.research("Question")
        self.assertEqual(len(critic.answers), 2)
        self.assertEqual(result.trace["final_verification"]["evidence_confidence"], "LOW")
        self.assertIn("unresolved", present_result(result).evidence_status.lower())

    def test_invalid_final_verification_fails_closed(self):
        agent, _, _ = self.agent("not json")
        with self.assertRaises(VerificationError):
            agent.research("Question")

    def test_supported_answer_reuses_check(self):
        agent, _, critic, _ = fixtures.ResearchAgentTests()._agent()
        result = agent.research("Question")
        self.assertEqual(len(critic.calls), 1)
        self.assertEqual(result.trace["final_verification"]["status"], "REUSED_DRAFT_CHECK")

    def test_partial_repair_also_gets_final_check(self):
        agent, critic, arbiter = self.agent(fixtures._verification(), "PARTIAL")
        result = agent.research("Question")
        self.assertEqual(len(critic.answers), 2)
        self.assertEqual(arbiter.calls, [])
        self.assertEqual(result.verification["overall_status"], "SUPPORTED")

if __name__ == "__main__":
    unittest.main()
