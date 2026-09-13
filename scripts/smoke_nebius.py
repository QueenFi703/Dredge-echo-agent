"""Make one safe live call to the configured Nebius Token Factory model."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from bridge.llm_adapter import LLMAdapter


def main() -> None:
    model = os.environ["ARBITRATION_MODEL"]
    started_at = datetime.now(timezone.utc).isoformat()
    # Kimi is a reasoning model; a tiny cap can be consumed before visible output.
    # This manual-only smoke test therefore allows a complete short response.
    adapter = LLMAdapter(backend="nebius", model=model, max_tokens=2048)
    response = adapter.generate(
        "health_check",
        source="dredge_echo_agent",
        target="connection_confirmation",
        source_value={
            "instruction": (
                "Confirm the connection in one short sentence and include the words "
                "Dredge Echo online."
            )
        },
    )

    if not response.strip():
        raise RuntimeError("Token Factory returned an empty response")

    print(f"Token Factory call started: {started_at}")
    print(f"Model: {model}")
    print(f"Kimi response: {response.strip()[:1000]}")


if __name__ == "__main__":
    main()
