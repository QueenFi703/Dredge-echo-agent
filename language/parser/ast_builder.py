"""
AST node definitions for Aster.

The AST is a tree of :class:`Node` objects produced by the parser and
consumed by the semantic analysis and compilation layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

@dataclass
class Node:
    """Base class for all AST nodes."""
    line: int = field(default=0, compare=False, repr=False)
    column: int = field(default=0, compare=False, repr=False)


# ---------------------------------------------------------------------------
# Leaf nodes
# ---------------------------------------------------------------------------

@dataclass
class Identifier(Node):
    """A bare name used as an entity reference or action call target."""
    name: str = ""

    def __repr__(self) -> str:
        return f"Identifier({self.name!r})"


@dataclass
class Relation(Node):
    """A directed connection between two identifiers: source -> target."""
    source: str = ""
    target: str = ""

    def __repr__(self) -> str:
        return f"Relation({self.source!r} -> {self.target!r})"


# ---------------------------------------------------------------------------
# Declaration nodes
# ---------------------------------------------------------------------------

@dataclass
class EntityDecl(Node):
    """Declaration of a named entity: ``entity <name>``."""
    name: str = ""

    def __repr__(self) -> str:
        return f"EntityDecl({self.name!r})"


@dataclass
class ActionDecl(Node):
    """
    Declaration of a named action with a directed relation.

    Example: ``action learn(dataset -> model)``
    """
    name: str = ""
    relation: Optional[Relation] = None

    def __repr__(self) -> str:
        return f"ActionDecl({self.name!r}, {self.relation})"


@dataclass
class ActionCall(Node):
    """
    An invocation of a previously declared action inside a cycle body.

    Example: ``learn``
    """
    name: str = ""

    def __repr__(self) -> str:
        return f"ActionCall({self.name!r})"


@dataclass
class CycleDecl(Node):
    """
    A named repeating process containing a sequence of statements.

    Example::

        cycle training {
            learn
            evaluate
        }
    """
    name: str = ""
    body: List[Node] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"CycleDecl({self.name!r}, body={self.body})"


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------

@dataclass
class Program(Node):
    """The root node of a parsed .co program."""
    statements: List[Node] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"Program(statements={self.statements})"
