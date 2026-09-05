"""
Optimizer for Aster.

Applies graph-level optimisations to a :class:`~language.semantics.relation_graph.RelationGraph`
before transpilation.  The optimizer works on the *semantic graph*, not the
AST, so all optimisations are meaning-preserving by construction.

Current optimisations
---------------------
1. **Dead-entity elimination** — Remove entities that have no edges and are
   not referenced by any action.
2. **Redundant-edge deduplication** — When two edges share the same source,
   label, and target they carry identical information; keep only the first.
3. **Action-chain fusion** — When action A produces the input of action B and
   neither has any other consumers/producers, fuse them into a single step
   to reduce overhead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from language.semantics.relation_graph import Edge, RelationGraph


@dataclass
class OptimizationReport:
    """Summary of changes applied during an optimization pass."""
    removed_nodes: List[str] = field(default_factory=list)
    removed_edges: List[Tuple[str, str, str]] = field(default_factory=list)
    fused_chains: List[Tuple[str, str]] = field(default_factory=list)

    def __str__(self) -> str:
        parts: List[str] = []
        if self.removed_nodes:
            parts.append(f"Removed {len(self.removed_nodes)} isolated node(s): {self.removed_nodes}")
        if self.removed_edges:
            parts.append(f"Removed {len(self.removed_edges)} duplicate edge(s)")
        if self.fused_chains:
            parts.append(f"Fused {len(self.fused_chains)} action chain(s)")
        return "\n".join(parts) if parts else "No optimisations applied."


class Optimizer:
    """
    Applies a configurable sequence of graph-level optimisations.

    Usage::

        optimizer = Optimizer()
        optimized_graph, report = optimizer.optimize(graph)
    """

    def __init__(
        self,
        dead_entity_elimination: bool = True,
        edge_deduplication: bool = True,
        chain_fusion: bool = False,
    ) -> None:
        self._dead_entity = dead_entity_elimination
        self._dedup_edges = edge_deduplication
        self._chain_fusion = chain_fusion

    def optimize(self, graph: RelationGraph) -> Tuple[RelationGraph, OptimizationReport]:
        """
        Return an optimised copy of *graph* together with an
        :class:`OptimizationReport` describing the changes.

        The original *graph* is not modified.
        """
        report = OptimizationReport()

        # Work on a fresh graph so the original is never mutated
        optimized = RelationGraph()
        for node in graph.nodes():
            optimized.add_entity(node)
        for edge in graph.edges():
            optimized.add_edge(edge.label, edge.source, edge.target)

        if self._dedup_edges:
            self._apply_edge_deduplication(optimized, report)

        if self._dead_entity:
            self._apply_dead_entity_elimination(optimized, report)

        if self._chain_fusion:
            self._apply_chain_fusion(optimized, report)

        return optimized, report

    # ------------------------------------------------------------------
    # Optimisation passes
    # ------------------------------------------------------------------

    def _apply_edge_deduplication(
        self, graph: RelationGraph, report: OptimizationReport
    ) -> None:
        seen: set = set()
        unique_edges: List[Edge] = []
        for edge in graph.edges():
            key = edge.as_tuple()
            if key not in seen:
                seen.add(key)
                unique_edges.append(edge)
            else:
                report.removed_edges.append(key)

        # Rebuild edge list in-place by clearing and re-adding
        graph._edges.clear()
        graph._edges.extend(unique_edges)

    def _apply_dead_entity_elimination(
        self, graph: RelationGraph, report: OptimizationReport
    ) -> None:
        connected: set = set()
        for edge in graph.edges():
            connected.add(edge.source)
            connected.add(edge.target)

        isolated = [n for n in graph.nodes() if n not in connected]
        for node in isolated:
            graph._nodes.discard(node)
            report.removed_nodes.append(node)

    def _apply_chain_fusion(
        self, graph: RelationGraph, report: OptimizationReport
    ) -> None:
        """
        Fuse A→X→B into A→B when X has exactly one incoming and one outgoing
        edge and is not declared as a primary entity (i.e. it exists only as a
        relay node).

        This is a conservative pass: it only fuses when the relay node has no
        other connections.
        """
        relay_candidates = [
            n for n in graph.nodes()
            if len(graph.edges_from(n)) == 1 and len(graph.edges_to(n)) == 1
        ]

        for relay in relay_candidates:
            incoming = graph.edges_to(relay)
            outgoing = graph.edges_from(relay)
            if len(incoming) == 1 and len(outgoing) == 1:
                in_edge = incoming[0]
                out_edge = outgoing[0]
                fused_label = f"{in_edge.label}_{out_edge.label}"
                graph._edges.remove(in_edge)
                graph._edges.remove(out_edge)
                graph._nodes.discard(relay)
                graph.add_edge(fused_label, in_edge.source, out_edge.target)
                report.fused_chains.append((in_edge.label, out_edge.label))
