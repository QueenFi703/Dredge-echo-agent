import json
import unittest

from bridge.astra_verifier import AstraEvidenceCritic


class _FakeAstra:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def generate(self, action, source="source", target="target", source_value=None, *, reasoning_effort=None):
        self.calls.append({
            "action": action,
            "source": source,
            "source_value": source_value,
            "reasoning_effort": reasoning_effort,
        })
        return self.response


class AstraEvidenceCriticTests(unittest.TestCase):
    def test_runs_as_independent_high_effort_astra_role(self):
        response = json.dumps({
            "claims": [{
                "claim": "material claim",
                "status": "CONFLICTED",
                "evidence_ids": ["source-1"],
                "reason": "sources disagree",
                "recommended_correction": "qualify the claim",
            }],
            "overall_status": "CONFLICTED",
            "conflicts": ["sources disagree"],
            "missing_evidence": [],
        })
        llm = _FakeAstra(response)

        result = AstraEvidenceCritic(llm)(
            "question", {"sources": [{"id": "source-1"}]}, "draft"
        )

        self.assertEqual(result["overall_status"], "CONFLICTED")
        self.assertEqual(llm.calls[0]["action"], "challenge_material_claims")
        self.assertEqual(llm.calls[0]["reasoning_effort"], "high")
        self.assertEqual(llm.calls[0]["source_value"]["proposed_answer"], "draft")


if __name__ == "__main__":
    unittest.main()
