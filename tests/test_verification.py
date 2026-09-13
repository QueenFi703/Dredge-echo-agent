import unittest
from bridge.verification import EVIDENCE_CRITIC_INSTRUCTIONS, VerificationError, parse_verification

class VerificationContractTests(unittest.TestCase):
    def test_critic_contract_limits_response_size(self):
        self.assertIn("at most 6 material", EVIDENCE_CRITIC_INSTRUCTIONS)
        self.assertIn("under 120 characters", EVIDENCE_CRITIC_INSTRUCTIONS)

    def test_rejects_empty_claims(self):
        with self.assertRaises(VerificationError):
            parse_verification('{"claims":[],"overall_status":"SUPPORTED","conflicts":[],"missing_evidence":[]}')
    def test_rejects_unknown_status(self):
        with self.assertRaises(VerificationError):
            parse_verification('{"claims":[{"claim":"x","status":"MAYBE","evidence_ids":[]}],"overall_status":"PARTIAL","conflicts":[],"missing_evidence":[]}')
