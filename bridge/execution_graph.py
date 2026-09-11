"""Runtime execution graph for Dredge Echo Astra.

The graph materializes control-plane topology into auditable work nodes.
Nodes can be spawned, retired, preserved across steering events, or marked
complete as evidence arrives.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Set

from bridge.control_plane import IntelligenceState


class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    RETIRED = "retired"
    PRESERVED = "preserved"
    FAILED = "failed"


@dataclass
class ExecutionNode:
    id: str
    role: str
    status: NodeStatus = NodeStatus.PENDING
    reasoning_effort: str = "medium"
    depends_on: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass
class GraphMutation:
    event: str
    spawned: List[str] = field(default_factory=list)
    retired: List[str] = field(default_factory=list)
    preserved: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ExecutionGraph:
    """Mutable work graph driven by IntelligenceState transitions."""

    def __init__(self) -> None:
        self.nodes: Dict[str, ExecutionNode] = {}
        self.mutations: List[GraphMutation] = []
        self._counter = 0

    def materialize(self, state: IntelligenceState) -> GraphMutation:
        requested = set(state.agents)
        active_by_role = {
            node.role: node
            for node in self.nodes.values()
            if node.status not in {NodeStatus.RETIRED, NodeStatus.FAILED}
        }

        spawned: List[str] = []
        for role in state.agents:
            if role in active_by_role:
                active_by_role[role].reasoning_effort = state.reasoning.value
                continue
            node = self._spawn(role, reasoning_effort=state.reasoning.value)
            spawned.append(node.id)

        retired: List[str] = []
        for role, node in active_by_role.items():
            if role not in requested and node.status not in {NodeStatus.COMPLETE, NodeStatus.PRESERVED}:
                node.status = NodeStatus.RETIRED
                retired.append(node.id)

        mutation = GraphMutation(
            event="GRAPH_MATERIALIZED",
            spawned=spawned,
            retired=retired,
            details={"mode": state.mode.value, "reasoning": state.reasoning.value},
        )
        self.mutations.append(mutation)
        return mutation

    def mark_running(self, role: str) -> None:
        node = self._active_for_role(role)
        if node:
            node.status = NodeStatus.RUNNING

    def mark_complete(self, role: str, **metadata: Any) -> None:
        node = self._active_for_role(role)
        if node:
            node.status = NodeStatus.COMPLETE
            node.metadata.update(metadata)

    def steer(
        self,
        *,
        preserve_roles: Iterable[str] = (),
        retire_roles: Iterable[str] = (),
        new_roles: Iterable[str] = (),
        reasoning_effort: str = "high",
        instruction: Optional[str] = None,
    ) -> GraphMutation:
        preserve: Set[str] = set(preserve_roles)
        retire: Set[str] = set(retire_roles)
        spawned: List[str] = []
        preserved: List[str] = []
        retired: List[str] = []

        for node in self.nodes.values():
            if node.role in preserve and node.status != NodeStatus.RETIRED:
                node.status = NodeStatus.PRESERVED
                preserved.append(node.id)
            elif node.role in retire and node.status not in {NodeStatus.COMPLETE, NodeStatus.RETIRED}:
                node.status = NodeStatus.RETIRED
                retired.append(node.id)

        existing_roles = {
            node.role for node in self.nodes.values() if node.status != NodeStatus.RETIRED
        }
        for role in new_roles:
            if role not in existing_roles:
                spawned.append(self._spawn(role, reasoning_effort=reasoning_effort).id)

        mutation = GraphMutation(
            event="GRAPH_STEERED",
            spawned=spawned,
            retired=retired,
            preserved=preserved,
            details={"instruction": instruction or "", "reasoning": reasoning_effort},
        )
        self.mutations.append(mutation)
        return mutation

    def snapshot(self) -> Dict[str, Any]:
        active = [node for node in self.nodes.values() if node.status != NodeStatus.RETIRED]
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "active_nodes": len(active),
            "total_nodes": len(self.nodes),
            "mutations": [mutation.to_dict() for mutation in self.mutations],
        }

    def _spawn(self, role: str, *, reasoning_effort: str) -> ExecutionNode:
        self._counter += 1
        node = ExecutionNode(
            id=f"n{self._counter:03d}",
            role=role,
            reasoning_effort=reasoning_effort,
        )
        self.nodes[node.id] = node
        return node

    def _active_for_role(self, role: str) -> Optional[ExecutionNode]:
        matches = [
            node for node in self.nodes.values()
            if node.role == role and node.status != NodeStatus.RETIRED
        ]
        return matches[-1] if matches else None
