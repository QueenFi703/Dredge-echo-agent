"""Paired live benchmark; shared evidence/draft, dynamic routing vs always Kimi.

The baseline always calls Kimi and then Nemotron, even for supported drafts.
Token counts are provider-reported; latency is measured, not an invoice estimate.
"""
from __future__ import annotations
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bridge.llm_adapter import LLMAdapter
from bridge.research_agent import ResearchAgent
from bridge.search_adapter import TavilySearchAdapter
from bridge.verification import NemotronVerifier, verification_counts

QUESTIONS = [
    "What does Python's official documentation say a virtual environment isolates, and what does it not isolate?",
    "How do NVIDIA's official materials describe the purpose of the Nemotron 3 Nano model?",
    "What are the documented benefits and limitations of retrieval augmented generation for factual answers?",
]

class MeteredLLM(LLMAdapter):
    def __init__(self, model):
        # Keep live measurement bounded. The earlier 2,048-token request timed out
        # before a single pair completed, so benchmark answers use a compact budget.
        super().__init__(backend="nebius", model=model, max_tokens=512)
        self.calls = []
    def _nebius_call(self, prompt):
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["NEBIUS_API_KEY"],
                        base_url=os.environ.get("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1"),
                        timeout=60, max_retries=0)
        # Some reasoning models can spend a compact completion budget entirely
        # on reasoning and return no answer text. Allow one bounded recovery
        # attempt with a slightly larger budget; transport failures are not retried.
        for attempt, max_tokens in enumerate((512, 768), start=1):
            started = perf_counter()
            print(json.dumps({"event": "model_start", "model": self._model,
                              "attempt": attempt, "max_tokens": max_tokens}), flush=True)
            try:
                response = client.chat.completions.create(
                    model=self._model, messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens)
            except Exception as exc:
                print(json.dumps({"event": "model_error", "model": self._model,
                                  "attempt": attempt, "error_type": type(exc).__name__,
                                  "cause_type": type(exc.__cause__).__name__,
                                  "latency_ms": round((perf_counter()-started)*1000)}), flush=True)
                raise
            usage = response.usage
            content = response.choices[0].message.content or ""
            self.calls.append({
                "model": self._model, "attempt": attempt,
                "latency_ms": round((perf_counter()-started)*1000),
                "input_tokens": usage.prompt_tokens if usage else None,
                "output_tokens": usage.completion_tokens if usage else None,
                "empty_completion": not bool(content.strip()),
            })
            if content.strip():
                return content
        return ""

class ReplaySearch:
    def __init__(self, evidence): self.evidence = evidence
    def search(self, *args, **kwargs): return self.evidence

class ReplayArchitect:
    def __init__(self, draft, real): self.draft, self.real = draft, real
    def generate(self, action, **kwargs):
        if action == "research_and_reason": return self.draft
        return self.real.generate(action, **kwargs)

class ReplayVerifier:
    def __init__(self, verification, real):
        self.initial, self.real = verification, real
        self.first = True
    def verify(self, **kwargs):
        if self.first:
            self.first = False
            return self.initial
        return self.real.verify(**kwargs)

def totals(calls):
    return {
        "model_calls": len(calls),
        "input_tokens": sum(c["input_tokens"] for c in calls) if all(c["input_tokens"] is not None for c in calls) else None,
        "output_tokens": sum(c["output_tokens"] for c in calls) if all(c["output_tokens"] is not None for c in calls) else None,
    }

def main():
    output = Path(sys.argv[1] if len(sys.argv) > 1 else "routing-benchmark.json")
    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "commit": os.environ.get("GITHUB_SHA"),
        "method": "Three paired questions; same live Tavily packet, GLM draft and initial Nemotron check per pair; baseline always runs Kimi then final Nemotron; alternating route execution order; transport failures are not retried; one bounded recovery attempt is allowed only for an empty completion; small sample, not a general performance guarantee.",
        "comparison_status": "INCOMPLETE",
        "cases": [],
    }
    architect = MeteredLLM(os.environ["NEBIUS_MODEL"])
    critic = MeteredLLM(os.environ["NVIDIA_MODEL"])
    kimi = MeteredLLM(os.environ["ARBITRATION_MODEL"])
    verifier = NemotronVerifier(critic)
    try:
        for index, question in enumerate(QUESTIONS):
            case = {"question": question}
            report["cases"].append(case)
            case_offsets = [len(m.calls) for m in (architect, critic, kimi)]
            try:
                started = perf_counter()
                case["stage"] = "retrieval"
                evidence = TavilySearchAdapter().search(question, max_results=3)
                if not evidence.get("sources"): raise RuntimeError("No evidence")
                case["retrieval_credits"] = (evidence.get("usage") or {}).get("credits")
                case["stage"] = "synthesis"
                draft = architect.generate("research_and_reason", source="tavily_web_evidence",
                    target="grounded_answer", source_value={"question": question,
                    "instructions": "Answer using the supplied evidence. Distinguish evidence from inference, do not invent sources, and include source URLs for material claims.",
                    "evidence": evidence})
                if not draft.strip(): raise RuntimeError("Empty draft")
                case["stage"] = "initial_verification"
                initial = verifier.verify(question=question, evidence=evidence, proposed_answer=draft)
                shared_ms = round((perf_counter()-started)*1000)
                # Capture shared calls by each model's current list; no previous-case records.
                shared = [architect.calls[-1], critic.calls[-1]]
                case["shared"] = {"latency_ms": shared_ms, "calls": shared,
                                  "initial_counts": verification_counts(initial)}
                case["source_urls"] = [s["url"] for s in evidence["sources"]]
                for mode in (["dynamic", "always_kimi"] if index % 2 == 0 else ["always_kimi", "dynamic"]):
                    case["stage"] = mode
                    offsets = [len(m.calls) for m in (architect, critic, kimi)]
                    started = perf_counter()
                    if mode == "dynamic":
                        agent = ResearchAgent(search=ReplaySearch(evidence),
                            llm=ReplayArchitect(draft, architect), repairer=architect,
                            verifier=ReplayVerifier(initial, verifier), arbitrator=kimi,
                            architect_model=architect._model, arbitrator_model=kimi._model,
                            nemotron_model=critic._model)
                        result = agent.research(question)
                        route, final = result.trace["arbitration"]["route"], result.verification
                    else:
                        answer = kimi.generate("arbitrate_evidence_critique",
                            source="architect_draft_and_nemotron_verification", target="final_grounded_answer",
                            source_value={"question": question, "evidence": evidence, "draft": draft,
                                "verification": initial,
                                "instructions": "Apply only evidence-supported corrections. Preserve supported claims, citations, and useful wording. Evidence outranks model consensus."})
                        if not answer.strip(): raise RuntimeError("Empty baseline answer")
                        final = verifier.verify(question=question, evidence=evidence, proposed_answer=answer)
                        route = "ALWAYS_KIMI"
                    post_ms = round((perf_counter()-started)*1000)
                    post_calls = [c for m, offset in zip((architect, critic, kimi), offsets) for c in m.calls[offset:]]
                    case[mode] = {"route": route, "post_draft_latency_ms": post_ms,
                        "total_latency_ms": shared_ms+post_ms,
                        "calls": shared+post_calls, **totals(shared+post_calls),
                        "final_overall_status": final["overall_status"],
                        "final_counts": verification_counts(final)}
                case["stage"] = "complete"
                case["latency_saved_ms"] = case["always_kimi"]["total_latency_ms"] - case["dynamic"]["total_latency_ms"]
                print(json.dumps(case), flush=True)
            except Exception as exc:
                # Avoid exposing provider exception messages or credentials in public artifacts.
                case["error_type"] = type(exc).__name__
                attempted_calls = [
                    call
                    for model, offset in zip((architect, critic, kimi), case_offsets)
                    for call in model.calls[offset:]
                ]
                case["attempted_calls"] = attempted_calls
                case["attempted_usage"] = totals(attempted_calls)
                print(json.dumps({"question": question, "stage": case["stage"], "error_type": type(exc).__name__}), flush=True)
                if "shared" not in case:
                    break  # Do not repeat a failed shared-stage provider call across every question.
    finally:
        report["completed_at"] = datetime.now(timezone.utc).isoformat()
        report["complete_pairs"] = sum("dynamic" in c and "always_kimi" in c for c in report["cases"])
        report["comparison_status"] = (
            "COMPLETE" if report["complete_pairs"] == len(QUESTIONS) else "INCOMPLETE"
        )
        all_calls = architect.calls + critic.calls + kimi.calls
        report["attempted_usage"] = totals(all_calls)
        credits = [case.get("retrieval_credits") for case in report["cases"]]
        report["tavily_credits"] = (
            sum(credits) if credits and all(value is not None for value in credits) else None
        )
        output.write_text(json.dumps(report, indent=2)+"\n")
    # Provider availability is benchmark data, not a code-test verdict. The
    # deterministic suite remains the gating correctness check in CI.
    print(json.dumps({"comparison_status": report["comparison_status"],
                      "complete_pairs": report["complete_pairs"],
                      "requested_pairs": len(QUESTIONS)}), flush=True)

if __name__ == "__main__":
    main()
