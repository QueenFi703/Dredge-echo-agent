"""
Python bridge adapter for Aster.

Translates a .co program into callable Python objects so that action
definitions can be wired directly to Python functions at runtime.

Usage::

    from bridge.python_adapter import PythonAdapter
    from language.runtime import Interpreter

    adapter = PythonAdapter()

    @adapter.bind("learn")
    def learn(source, target):
        # Real Python implementation
        model.fit(dataset)

    interpreter = Interpreter()
    adapter.attach(interpreter)
    result = interpreter.run(source_code)
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from language.runtime.interpreter import Interpreter


class PythonAdapter:
    """
    Bridges .co action declarations to Python callables.

    Bindings are registered with :meth:`bind` and then pushed into an
    :class:`~language.runtime.interpreter.Interpreter` via :meth:`attach`.
    """

    def __init__(self) -> None:
        self._bindings: Dict[str, Callable] = {}

    def bind(self, action_name: str) -> Callable:
        """
        Decorator that registers a Python function as the implementation
        of the named action.

        Example::

            @adapter.bind("learn")
            def learn(source, target):
                ...
        """
        def decorator(fn: Callable) -> Callable:
            self._bindings[action_name] = fn
            return fn
        return decorator

    def register(self, action_name: str, fn: Callable) -> None:
        """Register *fn* as the implementation of *action_name* (non-decorator form)."""
        self._bindings[action_name] = fn

    def attach(self, interpreter: Interpreter) -> None:
        """Push all registered bindings into *interpreter*."""
        for name, fn in self._bindings.items():
            interpreter.register(name, fn)

    def call(self, action_name: str, source: Any, target: Any) -> Optional[Any]:
        """
        Directly invoke the bound implementation of *action_name*.

        Returns *None* if no binding is registered.
        """
        fn = self._bindings.get(action_name)
        if fn:
            return fn(source, target)
        return None

    def __repr__(self) -> str:
        return f"PythonAdapter(bindings={list(self._bindings.keys())})"
