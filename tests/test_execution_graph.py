import unittest

from bridge.control_plane import IntelligenceState, OrchestrationMode, ReasoningDepth
from bridge.execution_graph import ExecutionGraph, NodeStatus


class ExecutionGraphTests(unittest.TestCase):
    def test_materialize_spawns_requested_roles(self):
        graph = ExecutionGraph()
        state = IntelligenceState(
            mode=OrchestrationMode.GROUNDED,
            reasoning=ReasoningDepth.MEDIUM,
            agents=("evidence_scout", "astra_investigator"),
            rationale_codes=("EXTERNAL_EVIDENCE_REQUIRED",),
            may_collapse=False,
        )

        mutation = graph.materialize(state)

        self.assertEqual(len(mutation.spawned), 2)
        snapshot = graph.snapshot()
        self.assertEqual(snapshot["active_nodes"], 2)
        self.assertEqual({n["role"] for n in snapshot["nodes"]}, {"evidence_scout", "astra_investigator"})

    def test_materialize_expands_without_recreating_existing_nodes(self):
        graph = ExecutionGraph()
        grounded = IntelligenceState(
            mode=OrchestrationMode.GROUNDED,
            reasoning=ReasoningDepth.MEDIUM,
            agents=("evidence_scout", "astra_investigator"),
            rationale_codes=(),
            may_collapse=False,
        )
        adversarial = IntelligenceState(
            mode=OrchestrationMode.ADVERSARIAL,
            reasoning=ReasoningDepth.HIGH,
            agents=("evidence_scout", "astra_investigator", "challenger", "arbiter"),
            rationale_codes=("EVIDENCE_CONFLICT",),
            may_collapse=False,
        )
        graph.materialize(grounded)
        mutation = graph.materialize(adversarial)

        self.assertEqual(len(mutation.spawned), 2)
        self.assertEqual(graph.snapshot()["total_nodes"], 4)

    def test_steer_preserves_and_retires_targeted_work(self):
        graph = ExecutionGraph()
        state = IntelligenceState(
            mode=OrchestrationMode.INVESTIGATIVE,
            reasoning=ReasoningDepth.HIGH,
            agents=("evidence_scout", "parallel_scout", "claim_mapper"),
            rationale_codes=(),
            may_collapse=False,
        )
        graph.materialize(state)

        mutation = graph.steer(
            preserve_roles=("claim_mapper",),
            retire_roles=("parallel_scout",),
            new_roles=("local_regulation_scout",),
            reasoning_effort="high",
            instruction="Refocus on St. Louis regulation",
        )

        self.assertEqual(len(mutation.preserved), 1)
        self.assertEqual(len(mutation.retired), 1)
        self.assertEqual(len(mutation.spawned), 1)
        statuses = {n["role"]: n["status"] for n in graph.snapshot()["nodes"]}
        self.assertEqual(statuses["claim_mapper"], NodeStatus.PRESERVED.value)
        self.assertEqual(statuses["parallel_scout"], NodeStatus.RETIRED.value)
        self.assertEqual(statuses["local_regulation_scout"], NodeStatus.PENDING.value)


if __name__ == "__main__":
    unittest.main()
