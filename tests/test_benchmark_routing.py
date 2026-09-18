import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import benchmark_routing as benchmark

class FakeModel:
    def __init__(self, model):
        self._model, self.calls = model, []
    def generate(self, action, **kwargs):
        self.calls.append({"model": self._model, "latency_ms": 0,
                           "input_tokens": 10, "output_tokens": 5})
        value = kwargs["source_value"]
        if action == "research_and_reason":
            return "draft"
        if action == "verify_material_claims":
            status = {"Q0": "SUPPORTED", "Q1": "PARTIAL", "Q2": "UNSUPPORTED"}[value["question"]] if value["proposed_answer"] == "draft" else "SUPPORTED"
            return json.dumps({"claims": [{"claim": "claim", "status": status,
                "recommended_correction": None if status == "SUPPORTED" else "correct"}],
                "overall_status": status, "conflicts": [], "missing_evidence": []})
        return "revised"

class FakeSearch:
    def search(self, *args, **kwargs):
        return {"sources": [{"id": "source-1", "url": "https://example.com", "content": "fact"}]}

class TimeoutModel(FakeModel):
    def generate(self, action, **kwargs):
        if action == "research_and_reason":
            raise TimeoutError("provider timed out")
        return super().generate(action, **kwargs)

class EmptyModel(FakeModel):
    def generate(self, action, **kwargs):
        if action == "research_and_reason":
            self.calls.append({"model": self._model, "latency_ms": 1,
                               "input_tokens": 12, "output_tokens": 7,
                               "empty_completion": True})
            return ""
        return super().generate(action, **kwargs)

class BenchmarkTests(unittest.TestCase):
    def test_glm_reasoning_budget_is_larger_but_bounded(self):
        self.assertEqual(benchmark.completion_budgets("zai-org/GLM-5.3"), (4096, 8192))
        self.assertEqual(benchmark.completion_budgets("moonshotai/Kimi-K3"), (4096, 8192))
        self.assertEqual(benchmark.completion_budgets(
            "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"), (2048, 4096))

    def test_length_truncated_completion_is_not_accepted(self):
        self.assertFalse(benchmark.completion_is_usable("partial answer", "length"))
        self.assertFalse(benchmark.completion_is_usable("", "stop"))
        self.assertTrue(benchmark.completion_is_usable("complete answer", "stop"))

    def test_paired_report_counts_each_route_and_shared_prefix_once(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/"report.json"
            with patch.object(benchmark, "MeteredLLM", FakeModel), patch.object(benchmark, "TavilySearchAdapter", FakeSearch), patch.object(benchmark, "QUESTIONS", ["Q0", "Q1", "Q2"]), patch.object(benchmark.sys, "argv", ["benchmark", str(output)]), patch.dict(os.environ, {"NEBIUS_MODEL": "glm", "NVIDIA_MODEL": "critic", "ARBITRATION_MODEL": "kimi"}), contextlib.redirect_stdout(io.StringIO()):
                benchmark.main()
            report = json.loads(output.read_text())
        self.assertEqual(report["complete_pairs"], 3)
        self.assertEqual([c["dynamic"]["route"] for c in report["cases"]],
                         ["SKIPPED", "ARCHITECT_REPAIR", "KIMI_ESCALATION"])
        self.assertEqual([c["dynamic"]["model_calls"] for c in report["cases"]], [2, 4, 4])
        self.assertEqual([c["always_kimi"]["model_calls"] for c in report["cases"]], [4, 4, 4])
        self.assertEqual([c["dynamic"]["input_tokens"] for c in report["cases"]], [20, 40, 40])
        self.assertTrue(all(c["dynamic"]["final_overall_status"] == "SUPPORTED" for c in report["cases"]))
        self.assertEqual(report["comparison_status"], "COMPLETE")

    def test_provider_timeout_is_reported_without_failing_ci(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/"report.json"
            with patch.object(benchmark, "MeteredLLM", TimeoutModel), patch.object(benchmark, "TavilySearchAdapter", FakeSearch), patch.object(benchmark, "QUESTIONS", ["Q0"]), patch.object(benchmark.sys, "argv", ["benchmark", str(output)]), patch.dict(os.environ, {"NEBIUS_MODEL": "glm", "NVIDIA_MODEL": "critic", "ARBITRATION_MODEL": "kimi"}), contextlib.redirect_stdout(io.StringIO()):
                benchmark.main()
            report = json.loads(output.read_text())
        self.assertEqual(report["comparison_status"], "INCOMPLETE")
        self.assertEqual(report["complete_pairs"], 0)
        self.assertEqual(report["cases"][0]["stage"], "synthesis")
        self.assertEqual(report["cases"][0]["error_type"], "TimeoutError")
        self.assertEqual(report["attempted_usage"]["model_calls"], 0)

    def test_empty_completion_preserves_billable_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/"report.json"
            with patch.object(benchmark, "MeteredLLM", EmptyModel), patch.object(benchmark, "TavilySearchAdapter", FakeSearch), patch.object(benchmark, "QUESTIONS", ["Q0"]), patch.object(benchmark.sys, "argv", ["benchmark", str(output)]), patch.dict(os.environ, {"NEBIUS_MODEL": "glm", "NVIDIA_MODEL": "critic", "ARBITRATION_MODEL": "kimi"}), contextlib.redirect_stdout(io.StringIO()):
                benchmark.main()
            report = json.loads(output.read_text())
        self.assertEqual(report["comparison_status"], "INCOMPLETE")
        self.assertEqual(report["attempted_usage"], {
            "model_calls": 1, "input_tokens": 12, "output_tokens": 7
        })
        self.assertTrue(report["cases"][0]["attempted_calls"][0]["empty_completion"])

if __name__ == "__main__":
    unittest.main()
