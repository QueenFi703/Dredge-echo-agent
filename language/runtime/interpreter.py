"""
Interpreter for Aster.

The interpreter ties together:
  1. Parsing (tokenizer → parser → AST)
  2. Semantic analysis (entity model, action model, relation graph)
  3. Coherence checking (coherence engine)
  4. Execution (walking the AST and dispatching actions)

Typical usage::

    interpreter = Interpreter()
    result = interpreter.run(source_code)
    print(result.graph.to_dict())
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from ..parser.ast_builder import (
    ActionCall,
    ActionDecl,
    CycleDecl,
    EntityDecl,
    Program,
)
from ..parser.parser import Parser
from ..parser.tokenizer import Tokenizer
from ..semantics.action_model import ActionModel
from ..semantics.entity_model import EntityModel
from ..semantics.relation_graph import RelationGraph
from .coherence_engine import CoherenceEngine, CoherenceReport


@dataclass
class ExecutionResult:
    """Result returned after running a program."""
    program: Program
    entity_model: EntityModel
    action_model: ActionModel
    graph: RelationGraph
    coherence_report: CoherenceReport
    execution_log: List[str] = field(default_factory=list)

    @property
    def is_coherent(self) -> bool:
        return self.coherence_report.is_coherent


class InterpreterError(Exception):
    """Raised when the interpreter encounters a runtime error."""


class Interpreter:
    """
    End-to-end interpreter for .co programs.

    You can optionally register *action handlers* — Python callables that
    are invoked when a named action is executed inside a cycle::

        interpreter = Interpreter()

        @interpreter.on_action("learn")
        def do_learn(source, target):
            print(f"Learning from {source} into {target}")

        result = interpreter.run(source_code)
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable[[str, str], None]] = {}

    # ------------------------------------------------------------------
    # Handler registration
    # ------------------------------------------------------------------

    def on_action(self, name: str) -> Callable:
        """Decorator to register a Python handler for a named action."""
        def decorator(fn: Callable) -> Callable:
            self._handlers[name] = fn
            return fn
        return decorator

    def register(self, name: str, handler: Callable[[str, str], None]) -> None:
        """Register *handler* for the action *name* (non-decorator form)."""
        self._handlers[name] = handler

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run(self, source: str, strict: bool = False) -> ExecutionResult:
        """
        Parse, analyse, and execute *source*.

        Parameters
        ----------
        source:
            The .co program text.
        strict:
            If *True*, raise :exc:`InterpreterError` when the program is
            not coherent.  If *False*, log warnings and continue.
        """
        # 1. Parse
        tokens = Tokenizer(source).tokenize()
        program = Parser(tokens).parse()

        # 2. Build semantic models
        entity_model = EntityModel()
        action_model = ActionModel()
        graph = RelationGraph()

        for stmt in program.statements:
            if isinstance(stmt, EntityDecl):
                entity_model.declare(stmt.name, line=stmt.line)
                graph.add_entity(stmt.name)

            elif isinstance(stmt, ActionDecl):
                action_model.declare(
                    stmt.name,
                    source=stmt.relation.source,
                    target=stmt.relation.target,
                    line=stmt.line,
                )
                graph.add_edge(
                    label=stmt.name,
                    source=stmt.relation.source,
                    target=stmt.relation.target,
                )

        # 3. Coherence check
        engine = CoherenceEngine()
        report = engine.check(program, entity_model, action_model, graph)

        if strict and not report.is_coherent:
            raise InterpreterError(
                f"Program is not coherent:\n{report}"
            )

        # 4. Execute
        log: List[str] = []
        for stmt in program.statements:
            if isinstance(stmt, CycleDecl):
                self._execute_cycle(stmt, action_model, log)

        return ExecutionResult(
            program=program,
            entity_model=entity_model,
            action_model=action_model,
            graph=graph,
            coherence_report=report,
            execution_log=log,
        )

    # ------------------------------------------------------------------
    # Internal execution helpers
    # ------------------------------------------------------------------

    def _execute_cycle(
        self,
        cycle: CycleDecl,
        action_model: ActionModel,
        log: List[str],
    ) -> None:
        log.append(f"[cycle:{cycle.name}] begin")
        for step in cycle.body:
            if isinstance(step, ActionCall):
                action = action_model.get(step.name)
                if action:
                    log.append(
                        f"[cycle:{cycle.name}] execute {action.name}"
                        f"({action.source} -> {action.target})"
                    )
                    handler = self._handlers.get(action.name)
                    if handler:
                        handler(action.source, action.target)
                else:
                    log.append(
                        f"[cycle:{cycle.name}] WARNING: action {step.name!r} not found"
                    )
        log.append(f"[cycle:{cycle.name}] end")


def main() -> None:
    """Entry-point for the ``aster`` CLI command."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="aster",
        description="Run an Aster (.co) program.",
    )
    parser.add_argument("file", nargs="?", help="Path to a .co source file")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Raise an error on coherence violations",
    )
    args = parser.parse_args()

    if args.file is None:
        # No file given: print a brief banner and exit cleanly.
        print("Aster language runtime ready. Pass a .co file to execute.")
        return

    try:
        with open(args.file, encoding="utf-8") as fh:
            source = fh.read()
    except OSError as exc:
        print(f"aster: error: cannot open '{args.file}': {exc}", file=sys.stderr)
        sys.exit(1)

    interpreter = Interpreter()
    result = interpreter.run(source, strict=args.strict)

    for entry in result.execution_log:
        print(entry)

    if not result.is_coherent:
        print("WARNING: program is not fully coherent", file=sys.stderr)
        sys.exit(1)
