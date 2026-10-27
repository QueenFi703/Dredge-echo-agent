"""Offline regression coverage for untrusted verifier citation IDs."""

import copy
import json
import unittest

from bridge.demo import present_result
from bridge.verification import NemotronVerifier, VerificationError, parse_verification
from tests import test_research_agent as fixtures
from tests.test_final_verification import SequenceCritic


class EvidenceIdTests(unittest.TestCase):
    def setUp(self):
        self.evidence = fixtures._FakeSearch().search("Question")
        self.valid = json.loads(fixtures._verification())

    def verify(self, verification, evidence=None):
        critic = fixtures._FakeLLM(json.dumps(verification))
        return NemotronVerifier(critic).verify(
            question="Question", evidence=self.evidence if evidence is None else evidence,
            proposed_answer="A material claim with a citation.",
        )

    def test_valid_ids_are_preserved_without_normalization(self):
        self.valid["claims"][0]["evidence_ids"] = ["source-2", "source-1"]
        self.assertEqual(self.verify(self.valid), self.valid)

    def test_rejects_unknown_mixed_non_string_and_blank_ids(self):
        for ids in (["source-404"], ["source-1", "source-404"], [42, {}],
                    [None], [True], [["source-1"]], [""], [" "], [" source-1"]):
            with self.subTest(ids=ids):
                self.valid["claims"][0]["evidence_ids"] = ids
                with self.assertRaises(VerificationError):
                    self.verify(self.valid)

    def test_evidence_ids_field_must_be_present_and_a_list(self):
        for ids in (None, "source-1", {}, 1):
            with self.subTest(ids=ids):
                self.valid["claims"][0]["evidence_ids"] = ids
                with self.assertRaises(VerificationError):
                    self.verify(self.valid)
        del self.valid["claims"][0]["evidence_ids"]
        with self.assertRaises(VerificationError):
            self.verify(self.valid)

    def test_only_unsupported_claims_may_have_empty_evidence_ids(self):
        self.valid["claims"][0]["evidence_ids"] = []
        for status in ("SUPPORTED", "PARTIAL", "CONFLICTED"):
            with self.subTest(status=status):
                self.valid["claims"][0]["status"] = status
                self.valid["overall_status"] = status
                with self.assertRaises(VerificationError):
                    self.verify(self.valid)
        self.valid["claims"][0]["status"] = "UNSUPPORTED"
        self.valid["overall_status"] = "UNSUPPORTED"
        self.valid["missing_evidence"] = ["No primary evidence"]
        self.assertEqual(self.verify(self.valid), self.valid)

    def test_unsupported_claims_still_cannot_invent_source_ids(self):
        self.valid["claims"][0].update(status="UNSUPPORTED", evidence_ids=["source-404"])
        self.valid["overall_status"] = "UNSUPPORTED"
        with self.assertRaises(VerificationError):
            self.verify(self.valid)

    def test_malformed_evidence_packets_fail_before_verifier_call(self):
        packets = [None, [], {}, {"sources": None}, {"sources": {}}, {"sources": []},
                   {"sources": [None]}, {"sources": [{}]}]
        for value in (None, "", " ", 42, {}, [], " source-1"):
            source = dict(self.evidence["sources"][0], id=value)
            packets.append({"sources": [source]})
        source = self.evidence["sources"][0]
        packets.append({"sources": [source, dict(source)]})
        for value in (None, "", " ", 42, {}):
            packets.append({"sources": [dict(source, content=value)]})
        for evidence in packets:
            with self.subTest(evidence=evidence):
                critic = fixtures._FakeLLM(json.dumps(self.valid))
                with self.assertRaises(VerificationError):
                    NemotronVerifier(critic).verify(question="Question", evidence=evidence,
                                                    proposed_answer="Claim")
                self.assertEqual(critic.calls, [])

    def test_parser_cannot_accept_verification_without_evidence_context(self):
        with self.assertRaises(VerificationError):
            parse_verification(json.dumps(self.valid))

    def test_supported_summary_cannot_hide_missing_or_disputed_evidence(self):
        for field in ("conflicts", "missing_evidence"):
            with self.subTest(field=field):
                data = copy.deepcopy(self.valid)
                data[field] = ["Unresolved limitation"]
                with self.assertRaises(VerificationError):
                    self.verify(data)
        self.valid["claims"][0]["status"] = "UNSUPPORTED"
        with self.assertRaises(VerificationError):
            self.verify(self.valid)

    def test_malformed_status_or_claim_text_fails_as_verification_error(self):
        for field, value in (("status", []), ("status", {}), ("claim", 42), ("claim", {})):
            with self.subTest(field=field, value=value):
                data = copy.deepcopy(self.valid)
                data["claims"][0][field] = value
                with self.assertRaises(VerificationError):
                    self.verify(data)
        self.valid["overall_status"] = []
        with self.assertRaises(VerificationError):
            self.verify(self.valid)

    def test_initial_unknown_id_never_returns_high_confidence_success(self):
        self.valid["claims"][0]["evidence_ids"] = ["source-404"]
        agent, architect, _, arbiter = fixtures.ResearchAgentTests()._agent(json.dumps(self.valid))
        with self.assertRaises(VerificationError):
            agent.research("Question")
        self.assertEqual(len(architect.calls), 1)
        self.assertEqual(arbiter.calls, [])

    def test_final_unknown_id_fails_for_both_repair_routes(self):
        self.valid["claims"][0]["evidence_ids"] = ["source-404"]
        for status in ("PARTIAL", "UNSUPPORTED"):
            with self.subTest(status=status):
                agent, _, _, _ = fixtures.ResearchAgentTests()._agent()
                critic = SequenceCritic(fixtures._verification(status), json.dumps(self.valid))
                agent.verifier = NemotronVerifier(critic)
                with self.assertRaises(VerificationError):
                    agent.research("Question")
                self.assertEqual(len(critic.answers), 2)

    def test_valid_result_preserves_citation_and_high_confidence(self):
        agent, architect, _, _ = fixtures.ResearchAgentTests()._agent()
        architect.response = "A supported fact: https://one.example"
        result = agent.research("Question")
        self.assertEqual(result.answer, architect.response)
        self.assertEqual(result.verification["claims"][0]["evidence_ids"], ["source-1"])
        self.assertEqual(result.trace["arbitration"]["route"], "SKIPPED")
        self.assertIn("**HIGH**", present_result(result).evidence_status)
        self.assertIn("https://one.example", present_result(result).sources_markdown)

    def test_explicit_missing_evidence_escalates_and_stays_low_confidence(self):
        self.valid["claims"][0].update(status="UNSUPPORTED", evidence_ids=[])
        self.valid["overall_status"] = "UNSUPPORTED"
        self.valid["missing_evidence"] = ["No source supports the claim"]
        agent, _, _, _ = fixtures.ResearchAgentTests()._agent(json.dumps(self.valid))
        result = agent.research("Question")
        self.assertEqual(result.trace["arbitration"]["route"], "KIMI_ESCALATION")
        self.assertEqual(result.trace["final_verification"]["evidence_confidence"], "LOW")
        self.assertIn("unresolved", present_result(result).evidence_status.lower())


if __name__ == "__main__":
    unittest.main()
