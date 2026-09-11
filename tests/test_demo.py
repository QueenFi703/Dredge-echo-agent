import json
import unittest

from bridge.demo import present_result
from bridge.research_agent import ResearchResult


class DemoPresentationTests(unittest.TestCase):
    def test_presents_answer_sources_verification_and_trace(self):
        result = ResearchResult(
            question="What changed?",
            evidence={"sources": [{"title": "Release notes", "url": "https://example.com/release"}]},
            answer="A grounded answer [1].",
            draft="A grounded answer [1].",
            verification={"overall_status": "SUPPORTED", "claims": [], "conflicts": [], "missing_evidence": []},
            trace={"arbitration": {"evidence_confidence": "HIGH"}},
        )
        output = present_result(result)
        self.assertEqual(output.answer, "A grounded answer [1].")
        self.assertIn("https://example.com/release", output.sources_markdown)
        self.assertIn("HIGH", output.evidence_status)
        self.assertEqual(json.loads(output.verification_json)["overall_status"], "SUPPORTED")

    def test_rejects_non_http_source_urls(self):
        result = ResearchResult("q", {"sources": [{"url": "javascript:alert(1)"}]}, "a", "a", {}, {})
        output = present_result(result)
        self.assertIn("no usable source URLs", output.sources_markdown)


if __name__ == "__main__":
    unittest.main()
