"""
Entity model for Aster.

An entity is anything that *exists* in the program — a dataset, a model,
a queue, a service.  This module tracks which entities have been declared
and provides helpers for checking whether a name is a known entity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Entity:
    """A single declared entity."""
    name: str
    declared_at_line: int = 0

    def __repr__(self) -> str:
        return f"Entity({self.name!r})"


class EntityModel:
    """
    Registry of all entities declared in a program.

    Usage::

        model = EntityModel()
        model.declare("dataset", line=1)
        model.declare("model", line=2)
        assert model.exists("dataset")
    """

    def __init__(self) -> None:
        self._entities: Dict[str, Entity] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def declare(self, name: str, line: int = 0) -> Entity:
        """Register a new entity.  Raises :exc:`ValueError` if already declared."""
        if name in self._entities:
            raise ValueError(f"Entity {name!r} already declared")
        entity = Entity(name=name, declared_at_line=line)
        self._entities[name] = entity
        return entity

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def exists(self, name: str) -> bool:
        """Return *True* if *name* is a declared entity."""
        return name in self._entities

    def get(self, name: str) -> Optional[Entity]:
        """Return the :class:`Entity` for *name*, or *None*."""
        return self._entities.get(name)

    def all(self) -> List[Entity]:
        """Return all declared entities in declaration order."""
        return list(self._entities.values())

    def names(self) -> List[str]:
        """Return all entity names in declaration order."""
        return list(self._entities.keys())

    def __len__(self) -> int:
        return len(self._entities)

    def __repr__(self) -> str:
        return f"EntityModel({list(self._entities.keys())})"
