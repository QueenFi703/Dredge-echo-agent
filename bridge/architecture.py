"""Public architecture choices for the Dredge Echo Astra demo.

Selection is explicit: Astra remains the default Product Hunt path, while the
original Nebius pipeline is available only when a user chooses it. Keeping the
route names here makes the UI and runtime dispatch share one contract.
"""

from __future__ import annotations

from enum import Enum
from typing import Callable, Optional, TypeVar, Union


T = TypeVar("T")


class Architecture(str, Enum):
    ASTRA = "Astra Adaptive — Dredge + GPT-6 Astra"
    NEBIUS = "Nebius Verified — Kimi + NVIDIA Nemotron"


DEFAULT_ARCHITECTURE = Architecture.ASTRA
ARCHITECTURE_CHOICES = [architecture.value for architecture in Architecture]


def resolve_architecture(
    selection: Optional[Union[str, Architecture]]
) -> Architecture:
    """Return a validated architecture without silently falling back."""

    if selection is None or not str(selection).strip():
        return DEFAULT_ARCHITECTURE
    if isinstance(selection, Architecture):
        return selection
    try:
        return Architecture(selection)
    except ValueError as exc:
        raise ValueError(f"Unknown Dredge architecture: {selection!r}") from exc


def build_selected_architecture(
    selection: Optional[Union[str, Architecture]],
    *,
    astra_builder: Callable[[], T],
    nebius_builder: Callable[[], T],
) -> T:
    """Invoke only the builder for the explicitly resolved route."""

    route = resolve_architecture(selection)
    if route is Architecture.ASTRA:
        return astra_builder()
    return nebius_builder()
