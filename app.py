"""Dual-architecture entry point for Dredge Echo Astra.

The Product Hunt path defaults to Dredge's adaptive GPT-6 Astra control plane.
The original Kimi + Nemotron pipeline remains available as an explicit opt-in;
it is never invoked merely because its credentials are present.
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional, Union
from urllib.parse import urlparse

import gradio as gr

from bridge.adaptive_agent import AdaptiveResearchAgent, AdaptiveResearchResult
from bridge.architecture import (
    ARCHITECTURE_CHOICES,
    DEFAULT_ARCHITECTURE,
    Architecture,
    build_selected_architecture,
    resolve_architecture,
)
from bridge.astra_verifier import AstraEvidenceCritic
from bridge.demo import present_result
from bridge.llm_adapter import LLMAdapter
from bridge.research_agent import ResearchAgent
from bridge.search_adapter import TavilySearchAdapter
from bridge.verification import NemotronVerifier

try:
    import spaces
except ImportError:  # Local and non-Space deployments do not need ZeroGPU.
    spaces = None


if spaces is not None:
    @spaces.GPU(duration=1)
    def _zero_gpu_capability_marker():
        """Declare free-tier compatibility; Dredge Echo never calls this function."""


def build_astra_agent() -> AdaptiveResearchAgent:
    """Build the default Dredge control plane using GPT-6 Astra for every LLM role."""

    model = (os.environ.get("OPENAI_MODEL") or "gpt-6-astra").strip()
    astra = LLMAdapter(backend="openai", model=model)
    return AdaptiveResearchAgent(
        search=TavilySearchAdapter(),
        llm=astra,
        critic=AstraEvidenceCritic(astra),
        arbitrator=astra,
        model=model,
    )


def build_nebius_agent() -> ResearchAgent:
    """Build the original Nebius route only after a user explicitly selects it."""

    kimi_model = os.environ["NEBIUS_MODEL"]
    nemotron_model = os.environ["NVIDIA_MODEL"]
    kimi = LLMAdapter(backend="nebius", model=kimi_model)
    nemotron = LLMAdapter(backend="nebius", model=nemotron_model)
    return ResearchAgent(
        search=TavilySearchAdapter(),
        llm=kimi,
        verifier=NemotronVerifier(nemotron),
        arbitrator=kimi,
        kimi_model=kimi_model,
        nemotron_model=nemotron_model,
    )


def build_agent(
    architecture: Optional[Union[str, Architecture]] = None
):
    """Build exactly the architecture selected by the user."""

    return build_selected_architecture(
        architecture,
        astra_builder=build_astra_agent,
        nebius_builder=build_nebius_agent,
    )


def _sources_markdown(evidence: dict[str, Any]) -> str:
    lines = []
    for index, source in enumerate(evidence.get("sources") or [], start=1):
        title = str(source.get("title") or f"Source {index}").replace("[", "").replace("]", "")
        url = str(source.get("url") or "")
        if urlparse(url).scheme in {"http", "https"}:
            lines.append(f"{index}. [{title}]({url})")
    return "\n".join(lines) or "Insufficient evidence: no usable source URLs were returned."


def _present_astra(result: AdaptiveResearchResult):
    verification = result.verification or {}
    overall_status = verification.get("overall_status") or "UNRESOLVED"
    public_trace = {
        "architecture": Architecture.ASTRA.value,
        "model": result.trace.get("model"),
        "intelligence_state": result.intelligence_state,
        "control_events": result.events,
        "timing": result.trace,
    }
    return (
        result.answer,
        _sources_markdown(result.evidence),
        f"Evidence status: **{overall_status}** · Dredge mode: **{result.intelligence_state['mode'].upper()}**",
        json.dumps(verification, indent=2),
        json.dumps(public_trace, indent=2),
    )


def run_research(
    question: str,
    architecture: Optional[Union[str, Architecture]] = None,
):
    question = (question or "").strip()
    if not question:
        return "Ask a research question to begin.", "", "Waiting for a question.", "{}", "{}"
    if len(question) > 500:
        return "Please shorten the question to 500 characters or fewer.", "", "Input rejected.", "{}", "{}"

    try:
        route = resolve_architecture(architecture)
        result = build_agent(route).research(question)
        if route is Architecture.ASTRA:
            return _present_astra(result)
        output = present_result(result)
        return (
            output.answer,
            output.sources_markdown,
            output.evidence_status,
            output.verification_json,
            output.trace_json,
        )
    except KeyError:
        return "The selected architecture is not configured on this deployment.", "", "Unavailable.", "{}", "{}"
    except RuntimeError as exc:
        if "no sources" in str(exc).lower():
            return "Insufficient evidence", "No sources were retrieved.", "Evidence confidence: **LOW**", "{}", "{}"
        return "The selected research path is temporarily unavailable.", "", "Unavailable.", "{}", "{}"
    # The public boundary must not expose provider exception text or credentials.
    except Exception:  # noqa: BLE001
        return "The selected research path is temporarily unavailable.", "", "Unavailable.", "{}", "{}"


with gr.Blocks(title="Dredge Echo Astra") as demo:
    gr.Markdown(
        "# Dredge Echo Astra\n"
        "One Dredge control plane, two selectable intelligence architectures. "
        "Astra Adaptive is the default Product Hunt experience; Nebius Verified "
        "remains available when you explicitly choose it."
    )
    architecture = gr.Radio(
        choices=ARCHITECTURE_CHOICES,
        value=DEFAULT_ARCHITECTURE.value,
        label="Intelligence architecture",
    )
    question = gr.Textbox(
        label="Research question",
        placeholder="Should Missouri pilot this policy before a national launch, given conflicting evidence?",
        lines=3,
        max_lines=6,
    )
    submit = gr.Button("Dredge the evidence", variant="primary")
    answer = gr.Markdown(label="Grounded answer")
    evidence_status = gr.Markdown(label="Evidence and control status")
    sources = gr.Markdown(label="Sources")
    with gr.Accordion("Evidence challenge", open=False):
        verification = gr.Code(language="json", label="Claim-level verification")
    with gr.Accordion("Dredge execution trace", open=False):
        trace = gr.Code(language="json", label="Architecture and topology trace")
    outputs = [answer, sources, evidence_status, verification, trace]
    inputs = [question, architecture]
    submit.click(run_research, inputs=inputs, outputs=outputs, concurrency_limit=2)
    question.submit(run_research, inputs=inputs, outputs=outputs, concurrency_limit=2)


if __name__ == "__main__":
    demo.launch()
