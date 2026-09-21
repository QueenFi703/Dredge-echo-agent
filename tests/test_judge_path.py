import unittest

from bridge.demo import present_result
from bridge.research_agent import ResearchResult


class JudgePathPresentationTests(unittest.TestCase):
    def _result(self, route):
        return ResearchResult(
            question="What changed?",
            evidence={"sources": [{"title": "Release notes", "url": "https://example.com/release"}]},
            answer="Grounded answer.",
            draft="Grounded answer.",
            verification={
                "overall_status": "SUPPORTED",
                "claims": [],
                "conflicts": [],
                "missing_evidence": [],
            },
            trace={
                "arbitration": {"route": route, "evidence_confidence": "HIGH"},
                "total_latency_ms": 1250,
            },
        )

    def test_supported_path_is_visible_without_opening_trace(self):
        output = present_result(self._result("SKIPPED"))
        self.assertIn("Tavily", output.route_summary)
        self.assertIn("GLM Architect", output.route_summary)
        self.assertIn("NVIDIA Nemotron", output.route_summary)
        self.assertIn("No escalation needed", output.route_summary)
        self.assertIn("1.2s total", output.route_summary)

    def test_kimi_escalation_is_visible_without_opening_trace(self):
        output = present_result(self._result("KIMI_ESCALATION"))
        self.assertIn("Kimi escalation", output.route_summary)


if __name__ == "__main__":
    unittest.main()
