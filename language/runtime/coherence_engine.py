"""
Coherence engine for Aster.

The coherence engine evaluates whether a program is semantically *coherent*:

  1. **Entity coherence** – every entity referenced in an action or cycle is
     declared.
  2. **Action coherence** – every action called inside a cycle is declared.
  3. **Graph coherence** – the relation graph has no completely isolated nodes
     (every declared entity participates in at least one relation).
  4. **Cycle coherence** – cycles contain at least one step.

Instead of executing code line by line, this engine first checks that the
whole system *makes sense* before any work is done.  This is the unique
feature of the language: **meaning is validated before execution**.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ..semantics.action_model import ActionModel
from ..semantics.entity_model import EntityModel
from ..semantics.relation_graph import RelationGraph
from ..parser.ast_builder import (
    ActionCall,
    ActionDecl,
    CycleDecl,
    EntityDecl,
    Program,
)


@dataclass
class CoherenceIssue:
    """A single coherence problem found during analysis."""
    level: str        # "error" | "warning"
    message: str
    line: int = 0

    def __str__(self) -> str:
        return f"[{self.level.upper()}] line {self.line}: {self.message}"


@dataclass
class CoherenceReport:
    """Aggregated result of coherence analysis."""
    issues: List[CoherenceIssue] = field(default_factory=list)

    @property
    def is_coherent(self) -> bool:
        """*True* when no error-level issues were found."""
        return not any(i.level == "error" for i in self.issues)

    def errors(self) -> List[CoherenceIssue]:
        return [i for i in self.issues if i.level == "error"]

    def warnings(self) -> List[CoherenceIssue]:
        return [i for i in self.issues if i.level == "warning"]

    def __str__(self) -> str:
        if not self.issues:
            return "Coherence check passed — no issues found."
        lines = [str(issue) for issue in self.issues]
        lines.append(
            f"\n{'COHERENT' if self.is_coherent else 'NOT COHERENT'} "
            f"({len(self.errors())} error(s), {len(self.warnings())} warning(s))"
        )
        return "\n".join(lines)


class CoherenceEngine:
    """
    Analyses a parsed program for semantic coherence.

    Usage::

        engine = CoherenceEngine()
        report = engine.check(program, entity_model, action_model, graph)
        if not report.is_coherent:
            for issue in report.errors():
                print(issue)
    """

    def check(
        self,
        program: Program,
        entity_model: EntityModel,
        action_model: ActionModel,
        graph: RelationGraph,
    ) -> CoherenceReport:
        """Run all coherence checks and return a :class:`CoherenceReport`."""
        report = CoherenceReport()

        self._check_action_relations(program, entity_model, report)
        self._check_cycle_bodies(program, action_model, report)
        self._check_graph_isolation(entity_model, graph, report)
        self._check_empty_cycles(program, report)

        return report

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_action_relations(
        self,
        program: Program,
        entity_model: EntityModel,
        report: CoherenceReport,
    ) -> None:
        """Every entity referenced in an action relation must be declared."""
        for stmt in program.statements:
            if isinstance(stmt, ActionDecl) and stmt.relation:
                for ref in (stmt.relation.source, stmt.relation.target):
                    if not entity_model.exists(ref):
                        report.issues.append(
                            CoherenceIssue(
                                level="error",
                                message=(
                                    f"Action {stmt.name!r} references undeclared entity {ref!r}"
                                ),
                                line=stmt.line,
                            )
                        )

    def _check_cycle_bodies(
        self,
        program: Program,
        action_model: ActionModel,
        report: CoherenceReport,
    ) -> None:
        """Every action called inside a cycle must be declared."""
        for stmt in program.statements:
            if isinstance(stmt, CycleDecl):
                for step in stmt.body:
                    if isinstance(step, ActionCall):
                        if not action_model.exists(step.name):
                            report.issues.append(
                                CoherenceIssue(
                                    level="error",
                                    message=(
                                        f"Cycle {stmt.name!r} calls undeclared action {step.name!r}"
                                    ),
                                    line=step.line,
                                )
                            )

    def _check_graph_isolation(
        self,
        entity_model: EntityModel,
        graph: RelationGraph,
        report: CoherenceReport,
    ) -> None:
        """Warn about entities that do not participate in any relation."""
        graph_nodes = set(graph.nodes())
        for entity in entity_model.all():
            if entity.name not in graph_nodes:
                report.issues.append(
                    CoherenceIssue(
                        level="warning",
                        message=(
                            f"Entity {entity.name!r} is declared but not connected "
                            "to any action — it is isolated in the relation graph"
                        ),
                        line=entity.declared_at_line,
                    )
                )

    def _check_empty_cycles(
        self,
        program: Program,
        report: CoherenceReport,
    ) -> None:
        """Warn about cycles with empty bodies."""
        for stmt in program.statements:
            if isinstance(stmt, CycleDecl) and not stmt.body:
                report.issues.append(
                    CoherenceIssue(
                        level="warning",
                        message=f"Cycle {stmt.name!r} has an empty body",
                        line=stmt.line,
                    )
                )
