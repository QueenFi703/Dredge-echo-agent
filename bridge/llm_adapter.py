"""
LLM bridge adapter for Aster.

Translates .co ``action`` declarations into prompts that are sent to a
large language model.  The adapter provides a lightweight, model-agnostic
interface so the same .co program can drive any LLM backend.

Usage::

    from bridge.llm_adapter import LLMAdapter

    adapter = LLMAdapter(backend="openai")  # or "anthropic", "local", etc.

    # Dry-run (no real API call — returns the prompt that would be sent)
    prompt = adapter.build_prompt("infer", question="What is gravity?", knowledge=None)
    print(prompt)

    # Real call (requires a configured backend)
    result = adapter.infer(question="What is gravity?", knowledge=None)
"""

from __future__ import annotations

import json
import os
from time import monotonic, sleep
from typing import Any, Callable, Dict, Optional


# Nebius limits are shared by all completion-budget attempts in one generate().
# SDK timeouts bound each I/O phase, not a hard wall-clock cancellation. The
# scheduling budget prevents new attempts or acceptance of late responses.
NEBIUS_REQUEST_TIMEOUT_SECONDS = 90.0
NEBIUS_TOTAL_BUDGET_SECONDS = 180.0
NEBIUS_MAX_RETRIES = 1
NEBIUS_RETRY_DELAY_SECONDS = 1.0


class LLMBackendError(Exception):
    """Raised when the configured LLM backend is unavailable."""


class LLMCompletionError(LLMBackendError):
    """Raised when a provider returns no complete, usable model response."""


def nebius_completion_budgets(model: str, configured: Optional[int]):
    """Return bounded output budgets that let reasoning models emit final content."""
    if configured is None:
        return (None,)
    if model in {"zai-org/GLM-5.3", "zai-org/GLM-5.3-Flash", "moonshotai/Kimi-K3"}:
        return (max(configured, 4096), max(configured * 2, 8192))
    if model.startswith("nvidia/NVIDIA-Nemotron-3-Nano"):
        return (max(configured, 2048), max(configured * 2, 4096))
    return (configured, min(configured * 2, 8192))


class LLMAdapter:
    """
    Model-agnostic LLM bridge for .co action declarations.

    The adapter maps .co actions to prompt templates and dispatches them
    to the configured backend.  It ships with a *dry-run* mode that
    returns the prompt string without making any network call — useful for
    testing and development.

    Parameters
    ----------
    backend:
        Name of the LLM backend to use.  Supported values: ``"dry_run"``
        (default), ``"nebius"``, ``"openai"``, ``"anthropic"``, ``"local"``.
    model:
        Optional model name forwarded to the backend (e.g. ``"gpt-4o"``).
    prompt_template:
        Optional custom prompt template.  Use ``{action}``, ``{source}``,
        and ``{target}`` as placeholders.
    """

    DEFAULT_TEMPLATE = (
        "You are a semantic reasoning engine.\n"
        "Action: {action}\n"
        "Input ({source}): {source_value}\n"
        "Produce output for: {target}\n"
    )

    def __init__(
        self,
        backend: str = "dry_run",
        model: Optional[str] = None,
        prompt_template: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> None:
        if max_tokens is not None and max_tokens < 1:
            raise ValueError("max_tokens must be positive")
        self._backend = backend
        self._model = model
        self._max_tokens = max_tokens
        self._template = prompt_template or self.DEFAULT_TEMPLATE
        self._call_fn: Callable = self._resolve_backend(backend)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def build_prompt(
        self,
        action: str,
        source: str = "source",
        target: str = "target",
        source_value: Any = None,
    ) -> str:
        """Return the prompt string that would be sent to the LLM."""
        return self._template.format(
            action=action,
            source=source,
            target=target,
            source_value=json.dumps(source_value) if source_value is not None else "(none)",
        )

    def generate(
        self,
        action: str,
        source: str = "source",
        target: str = "target",
        source_value: Any = None,
    ) -> str:
        """
        Send the prompt to the configured backend and return the response.

        In ``dry_run`` mode the prompt itself is returned.
        """
        prompt = self.build_prompt(action, source, target, source_value)
        return self._call_fn(prompt)

    # ------------------------------------------------------------------
    # Backend resolution
    # ------------------------------------------------------------------

    def _resolve_backend(self, name: str) -> Callable[[str], str]:
        if name == "dry_run":
            return self._dry_run
        if name == "nebius":
            return self._nebius_call
        if name == "openai":
            return self._openai_call
        if name == "anthropic":
            return self._anthropic_call
        if name == "local":
            return self._local_call
        raise LLMBackendError(f"Unknown LLM backend: {name!r}")

    # ------------------------------------------------------------------
    # Backend implementations
    # ------------------------------------------------------------------

    @staticmethod
    def _dry_run(prompt: str) -> str:
        """Return the prompt unchanged (no API call)."""
        return f"[DRY RUN]\n{prompt}"

    def _openai_call(self, prompt: str) -> str:
        try:
            import openai  # type: ignore
            client = openai.OpenAI()
            request = {
                "model": self._model or "gpt-4o",
                "messages": [{"role": "user", "content": prompt}],
            }
            if self._max_tokens is not None:
                request["max_tokens"] = self._max_tokens
            response = client.chat.completions.create(
                **request,
            )
            return response.choices[0].message.content or ""
        except ImportError:
            raise LLMBackendError(
                "openai package is not installed. Run: pip install openai"
            )

    def _nebius_call(self, prompt: str) -> str:
        """Call a Nebius Token Factory model through its OpenAI-compatible API."""
        api_key = (os.environ.get("NEBIUS_API_KEY") or "").strip()
        model = (self._model or os.environ.get("NEBIUS_MODEL") or "").strip()
        base_url = (
            os.environ.get(
                "NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1"
            )
            .strip()
            .rstrip("/")
        )

        if not api_key:
            raise LLMBackendError("NEBIUS_API_KEY is not configured")
        if not model:
            raise LLMBackendError(
                "A Nebius model is required; pass model=... or set NEBIUS_MODEL"
            )

        try:
            import openai  # type: ignore
        except ImportError as exc:
            raise LLMBackendError(
                "openai package is not installed. Run: pip install 'aster-lang[nebius]'"
            ) from exc

        deadline = monotonic() + NEBIUS_TOTAL_BUDGET_SECONDS
        try:
            client = openai.OpenAI(
                api_key=api_key, base_url=base_url,
                timeout=NEBIUS_REQUEST_TIMEOUT_SECONDS, max_retries=0,
            )
        except Exception:
            # Never expose provider URLs, response bodies, prompts, or credentials.
            raise LLMBackendError("Nebius client could not be initialized") from None
        try:
            request = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            }
            retries_left = NEBIUS_MAX_RETRIES
            for max_tokens in nebius_completion_budgets(model, self._max_tokens):
                attempt = dict(request)
                if max_tokens is not None:
                    attempt["max_tokens"] = max_tokens
                while True:
                    remaining = deadline - monotonic()
                    if remaining <= 0:
                        raise LLMBackendError("Nebius exceeded its time budget")
                    attempt["timeout"] = min(NEBIUS_REQUEST_TIMEOUT_SECONDS, remaining)
                    try:
                        response = client.chat.completions.create(**attempt)
                    except Exception as exc:
                        status = getattr(exc, "status_code", None)
                        retryable = (
                            isinstance(exc, (TimeoutError, ConnectionError))
                            or isinstance(exc, getattr(openai, "APIConnectionError", ()))
                            or (isinstance(exc, getattr(openai, "APIStatusError", ()))
                                and isinstance(status, int)
                                and (status in {408, 409, 429} or 500 <= status < 600))
                        )
                        if not retryable or retries_left <= 0:
                            raise LLMBackendError("Nebius request failed within the bounded retry policy") from None
                        if deadline - monotonic() <= NEBIUS_RETRY_DELAY_SECONDS:
                            raise LLMBackendError("Nebius exceeded its time budget") from None
                        retries_left -= 1
                        sleep(NEBIUS_RETRY_DELAY_SECONDS)
                        continue
                    if monotonic() >= deadline:
                        raise LLMBackendError("Nebius exceeded its time budget")
                    break
                try:
                    choice = response.choices[0]
                    content = choice.message.content or ""
                    finish_reason = getattr(choice, "finish_reason", None)
                    if not isinstance(content, str):
                        raise TypeError
                except (AttributeError, IndexError, TypeError):
                    raise LLMCompletionError("Nebius returned an invalid completion") from None
                if content.strip() and finish_reason != "length":
                    return content

            raise LLMCompletionError(
                "Nebius returned no complete response within the bounded output budget"
            )
        finally:
            try:
                client.close()
            except Exception:
                # Cleanup must not leak provider details or mask the primary error.
                pass

    @staticmethod
    def _anthropic_call(prompt: str) -> str:
        try:
            import anthropic  # type: ignore
            client = anthropic.Anthropic()
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except ImportError:
            raise LLMBackendError(
                "anthropic package is not installed. Run: pip install anthropic"
            )

    @staticmethod
    def _local_call(prompt: str) -> str:
        """
        Stub for a locally-hosted model (e.g. via Ollama or llama.cpp).
        Override this method or use :meth:`register_backend` to provide
        a real implementation.
        """
        return f"[LOCAL MODEL STUB]\n{prompt}"

    def register_backend(self, name: str, fn: Callable[[str], str]) -> None:
        """Register a custom backend callable."""
        self._backend = name
        self._call_fn = fn

    def __repr__(self) -> str:
        return f"LLMAdapter(backend={self._backend!r}, model={self._model!r})"
