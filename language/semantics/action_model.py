"""
Action model for Aster.

An action is anything that *happens* — a transformation from one entity
to another.  This module tracks declared actions and their directed
relations (source → target).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class Action:
    """A single declared action with a directed relation."""
    name: str
    source: str
    target: str
    declared_at_line: int = 0

    def relation_tuple(self) -> Tuple[str, str]:
        """Return ``(source, target)`` as a convenience tuple."""
        return (self.source, self.target)

    def __repr__(self) -> str:
        return f"Action({self.name!r}: {self.source!r} -> {self.target!r})"


class ActionModel:
    """
    Registry of all actions declared in a program.

    Usage::

        model = ActionModel()
        model.declare("learn", source="dataset", target="model", line=3)
        assert model.exists("learn")
        assert model.get("learn").target == "model"
    """

    def __init__(self) -> None:
        self._actions: Dict[str, Action] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def declare(self, name: str, source: str, target: str, line: int = 0) -> Action:
        """Register a new action.  Raises :exc:`ValueError` if already declared."""
        if name in self._actions:
            raise ValueError(f"Action {name!r} already declared")
        action = Action(name=name, source=source, target=target, declared_at_line=line)
        self._actions[name] = action
        return action

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def exists(self, name: str) -> bool:
        """Return *True* if *name* is a declared action."""
        return name in self._actions

    def get(self, name: str) -> Optional[Action]:
        """Return the :class:`Action` for *name*, or *None*."""
        return self._actions.get(name)

    def all(self) -> List[Action]:
        """Return all declared actions in declaration order."""
        return list(self._actions.values())

    def names(self) -> List[str]:
        """Return all action names in declaration order."""
        return list(self._actions.keys())

    def __len__(self) -> int:
        return len(self._actions)

    def __repr__(self) -> str:
        return f"ActionModel({list(self._actions.keys())})"
