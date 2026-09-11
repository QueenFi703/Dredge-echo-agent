import unittest

from bridge.control_plane import (
    DredgeControlPlane,
    InvestigationSignals,
    OrchestrationMode,
    ReasoningDepth,
)


class DredgeControlPlaneTests(unittest.TestCase):
    def setUp(self):
        self.control = DredgeControlPlane()

    def test_simple_task_stays_direct(self):
        state = self.control.decide(
            InvestigationSignals(task_complexity=0.1, uncertainty=0.1)
        )
        self.assertEqual(state.mode, OrchestrationMode.DIRECT)
        self.assertEqual(state.reasoning, ReasoningDepth.MEDIUM)
        self.assertEqual(state.agents, ("astra_investigator",))

    def test_low_coverage_expands_investigation(self):
        state = self.control.decide(
            InvestigationSignals(
                task_complexity=0.7,
                evidence_needed=True,
                evidence_coverage=0.3,
            )
        )
        self.assertEqual(state.mode, OrchestrationMode.INVESTIGATIVE)
        self.assertEqual(state.reasoning, ReasoningDepth.HIGH)
        self.assertIn("parallel_scout", state.agents)

    def test_conflict_spawns_adversarial_path(self):
        state = self.control.decide(
            InvestigationSignals(
                evidence_needed=True,
                evidence_coverage=0.7,
                contradiction_score=0.8,
            )
        )
        self.assertEqual(state.mode, OrchestrationMode.ADVERSARIAL)
        self.assertIn("challenger", state.agents)
        self.assertIn("arbiter", state.agents)

    def test_multiple_hypotheses_trigger_deep_deliberation(self):
        state = self.control.decide(
            InvestigationSignals(
                evidence_needed=True,
                competing_hypotheses=3,
                uncertainty=0.6,
            )
        )
        self.assertEqual(state.mode, OrchestrationMode.DELIBERATIVE)
        self.assertEqual(state.reasoning, ReasoningDepth.XHIGH)
        self.assertIn("hypothesis_judge", state.agents)

    def test_high_stakes_unresolved_escalates(self):
        state = self.control.decide(
            InvestigationSignals(
                evidence_needed=True,
                materiality=0.95,
                uncertainty=0.9,
                source_quality=0.4,
            )
        )
        self.assertEqual(state.mode, OrchestrationMode.ESCALATED)
        self.assertEqual(state.reasoning, ReasoningDepth.XHIGH)
        self.assertIn("independent_verifier", state.agents)

    def test_converged_evidence_can_collapse(self):
        state = self.control.decide(
            InvestigationSignals(
                evidence_needed=True,
                evidence_coverage=0.95,
                contradiction_score=0.05,
                uncertainty=0.1,
                source_quality=0.9,
            )
        )
        self.assertTrue(state.may_collapse)
        self.assertIn("EVIDENCE_CONVERGED", state.rationale_codes)


if __name__ == "__main__":
    unittest.main()
