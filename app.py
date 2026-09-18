"""Hugging Face Space entry point for the Dredge Echo research demo."""

from __future__ import annotations

import os

import gradio as gr

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


def build_agent() -> ResearchAgent:
    architect_model = os.environ["NEBIUS_MODEL"]
    arbitration_model = os.environ.get("ARBITRATION_MODEL", "moonshotai/Kimi-K3")
    nemotron_model = os.environ["NVIDIA_MODEL"]
    architect = LLMAdapter(backend="nebius", model=architect_model, max_tokens=2048)
    nemotron = LLMAdapter(backend="nebius", model=nemotron_model, max_tokens=2048)
    kimi = LLMAdapter(backend="nebius", model=arbitration_model, max_tokens=2048)
    return ResearchAgent(
        search=TavilySearchAdapter(),
        llm=architect,
        verifier=NemotronVerifier(nemotron),
        repairer=architect,
        arbitrator=kimi,
        architect_model=architect_model,
        arbitrator_model=arbitration_model,
        nemotron_model=nemotron_model,
    )


def run_research(question: str):
    question = (question or "").strip()
    if not question:
        return "Ask a research question to begin.", "", "Waiting for a question.", "{}", "{}"
    if len(question) > 500:
        return "Please shorten the question to 500 characters or fewer.", "", "Input rejected.", "{}", "{}"

    try:
        result = build_agent().research(question)
        output = present_result(result)
        return (
            output.answer,
            output.sources_markdown,
            output.evidence_status,
            output.verification_json,
            output.trace_json,
        )
    except KeyError:
        return "Demo configuration is incomplete.", "", "Unavailable.", "{}", "{}"
    except RuntimeError as exc:
        if "no sources" in str(exc).lower():
            return "Insufficient evidence", "No sources were retrieved.", "Evidence confidence: **LOW**", "{}", "{}"
        return "The research pipeline is temporarily unavailable.", "", "Unavailable.", "{}", "{}"
    # The public boundary must not expose provider exception text or credentials.
    except Exception:  # noqa: BLE001
        return "The research pipeline is temporarily unavailable.", "", "Unavailable.", "{}", "{}"


with gr.Blocks(title="Dredge Echo") as demo:
    gr.Markdown(
        "# Dredge Echo\n"
        "Current, verifiable research through Tavily retrieval, a fast GLM Architect, "
        "NVIDIA Nemotron citation checking, and Kimi escalation for disputed claims."
    )
    question = gr.Textbox(
        label="Research question",
        placeholder="Which current model is best suited to citation verification, and why?",
        lines=3,
        max_lines=6,
    )
    submit = gr.Button("Research", variant="primary")
    answer = gr.Markdown(label="Grounded answer")
    evidence_status = gr.Markdown(label="Evidence status")
    sources = gr.Markdown(label="Sources")
    with gr.Accordion("Citation-integrity assessment", open=False):
        verification = gr.Code(language="json", label="Nemotron verification")
    with gr.Accordion("Observability trace", open=False):
        trace = gr.Code(language="json", label="Pipeline trace")
    outputs = [answer, sources, evidence_status, verification, trace]
    submit.click(run_research, inputs=question, outputs=outputs, concurrency_limit=2)
    question.submit(run_research, inputs=question, outputs=outputs, concurrency_limit=2)


if __name__ == "__main__":
    demo.launch()
