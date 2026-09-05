"""
Relation graph for Aster.

Instead of compiling source code directly to instructions, the runtime
first converts the program into a directed graph of semantic relationships.
This graph is the canonical representation consumed by:

  - the coherence engine (validation)
  - the transpiler (code generation)
  - the bridge adapters (cross-language output)

Graph structure
---------------
  Nodes  → entities
  Edges  → actions (labelled with the action name)

Example for::

    entity dataset
    entity model
    action learn(dataset -> model)

Produces::

    dataset ──learn──► model
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class Edge:
    """A directed, labelled edge between two entity nodes."""
    label: str       # action name
    source: str      # source entity name
    target: str      # target entity name

    def __repr__(self) -> str:
        return f"{self.source!r} --{self.label}--> {self.target!r}"

    def as_tuple(self) -> Tuple[str, str, str]:
        return (self.source, self.label, self.target)


class RelationGraph:
    """
    Directed graph of entity relationships for a compiled program.

    Usage::

        graph = RelationGraph()
        graph.add_entity("dataset")
        graph.add_entity("model")
        graph.add_edge("learn", source="dataset", target="model")

        # Inspect
        print(graph.edges_from("dataset"))   # [Edge(dataset --learn--> model)]
        print(graph.is_connected())           # True
    """

    def __init__(self) -> None:
        self._nodes: Set[str] = set()
        self._edges: List[Edge] = []

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def add_entity(self, name: str) -> None:
        """Add an entity node (idempotent)."""
        self._nodes.add(name)

    def add_edge(self, label: str, source: str, target: str) -> Edge:
        """
        Add a directed labelled edge.

        Both *source* and *target* are added as nodes automatically if
        they are not already present.
        """
        self._nodes.add(source)
        self._nodes.add(target)
        edge = Edge(label=label, source=source, target=target)
        self._edges.append(edge)
        return edge

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def nodes(self) -> List[str]:
        """Return all entity names (unsorted)."""
        return list(self._nodes)

    def edges(self) -> List[Edge]:
        """Return all edges in insertion order."""
        return list(self._edges)

    def edges_from(self, source: str) -> List[Edge]:
        """Return all edges originating at *source*."""
        return [e for e in self._edges if e.source == source]

    def edges_to(self, target: str) -> List[Edge]:
        """Return all edges pointing at *target*."""
        return [e for e in self._edges if e.target == target]

    def reachable_from(self, start: str) -> Set[str]:
        """
        Return the set of nodes reachable from *start* via BFS.

        The start node itself is included.
        """
        visited: Set[str] = set()
        queue = [start]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            for edge in self.edges_from(current):
                if edge.target not in visited:
                    queue.append(edge.target)
        return visited

    def is_connected(self) -> bool:
        """
        Return *True* if every entity can be reached from at least one
        other entity (i.e., no isolated nodes exist when edges are present).

        An empty graph or a graph with a single node is considered connected.
        """
        if not self._nodes or len(self._nodes) == 1:
            return True
        if not self._edges:
            return len(self._nodes) <= 1

        # Find a starting node that has at least one edge
        for node in self._nodes:
            if self.edges_from(node):
                reachable = self.reachable_from(node)
                # Check that all nodes that are part of some edge are reachable
                connected_nodes: Set[str] = set()
                for edge in self._edges:
                    connected_nodes.add(edge.source)
                    connected_nodes.add(edge.target)
                return connected_nodes.issubset(reachable)
        return False

    def to_dict(self) -> Dict:
        """Serialise the graph to a plain dict (useful for JSON export)."""
        return {
            "nodes": sorted(self._nodes),
            "edges": [
                {"source": e.source, "label": e.label, "target": e.target}
                for e in self._edges
            ],
        }

    def __repr__(self) -> str:
        return f"RelationGraph(nodes={sorted(self._nodes)}, edges={self._edges})"
