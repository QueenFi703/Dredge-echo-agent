"""
LLM bridge adapter for Aster.

Translates .co ``action`` declarations into prompts that are sent to a
large language model. The adapter provides a lightweight, model-agnostic
interface so the same .co program can drive any LLM backend.
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Optional


class LLMBackendError(Exception):
    """Raised when the configured LLM backend is unavailable."""


class LLMAdapter:
    """Model-agnostic LLM bridge for .co action declarations."""

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
    ) -> None:
        self._backend = backend
        self._model = model
        self._template = prompt_template or self.DEFAULT_TEMPLATE
        self._call_fn: Callable[[str], str] = self._resolve_backend(backend)

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
        *,
        reasoning_effort: Optional[str] = None,
    ) -> str:
        """Send the prompt to the configured backend and return the response.

        ``reasoning_effort`` is intentionally a per-call control.  OpenAI/Astra
        consumes it directly, which lets Dredge deepen or collapse reasoning
        during one investigation without mutating global process state. Other
        backends ignore the argument and retain their existing behavior.
        """
        prompt = self.build_prompt(action, source, target, source_value)
        if self._backend == "openai":
            return self._openai_call(prompt, reasoning_effort=reasoning_effort)
        return self._call_fn(prompt)

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

    @staticmethod
    def _dry_run(prompt: str) -> str:
        return f"[DRY RUN]\n{prompt}"

    def _openai_call(self, prompt: str, *, reasoning_effort: Optional[str] = None) -> str:
        """Call GPT-6 Astra through OpenAI's Responses API.

        Environment variables:
            OPENAI_API_KEY: required API credential.
            OPENAI_MODEL: optional model override; defaults to gpt-6-astra.
            OPENAI_REASONING_EFFORT: fallback effort when a call does not
                explicitly provide one.
        """
        api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
        model = (self._model or os.environ.get("OPENAI_MODEL") or "gpt-6-astra").strip()
        effort = (
            reasoning_effort
            or os.environ.get("OPENAI_REASONING_EFFORT")
            or "low"
        ).strip().lower()

        if not api_key:
            raise LLMBackendError("OPENAI_API_KEY is not configured")
        if effort not in {"low", "medium", "high", "xhigh", "max"}:
            raise LLMBackendError(
                "reasoning effort must be one of: low, medium, high, xhigh, max"
            )

        try:
            import openai  # type: ignore
        except ImportError as exc:
            raise LLMBackendError(
                "openai package is not installed. Run: pip install openai"
            ) from exc

        client = openai.OpenAI(api_key=api_key)
        response = client.responses.create(
            model=model,
            input=prompt,
            reasoning={"effort": effort},
        )
        return response.output_text or ""

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

        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""

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
        return f"[LOCAL MODEL STUB]\n{prompt}"

    def register_backend(self, name: str, fn: Callable[[str], str]) -> None:
        self._backend = name
        self._call_fn = fn

    def __repr__(self) -> str:
        return f"LLMAdapter(backend={self._backend!r}, model={self._model!r})"
