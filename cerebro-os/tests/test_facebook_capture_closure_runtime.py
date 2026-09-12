import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runtime"))

from facebook_capture_closure import FacebookCaptureClosureRequest, close_facebook_capture_24h


class FacebookCaptureClosureTests(unittest.TestCase):
    def base(self, **overrides):
        data = dict(
            company_id="fenix-capital",
            engine_id="SOC-FB-CAPTURE-CLOSURE",
            environment="TEST",
            version="1.0",
            capture_key="CAPTURE_POST_24h",
            quality_key="QUALITY_GATE_FACEBOOK_24H",
            capture_status="CAPTURED_PARTIAL",
            quality_status="PARTIAL_DATA_REVIEW",
            capture_result_hash="capture-hash",
            quality_result_hash="quality-hash",
            source_hash="source-hash",
            platform_state="FACEBOOK_READ_ONLY",
            notion_record_id="notion-1",
            external_id="post-1",
            page_id="page-1",
        )
        data.update(overrides)
        return FacebookCaptureClosureRequest(**data)

    def test_closes_window_and_commits_idempotency(self):
        result = close_facebook_capture_24h(self.base())
        self.assertEqual(result["closure"]["status"], "TECHNICALLY_VALIDATED_PARTIAL_HOLD")
        self.assertEqual(result["closure"]["difference"], "LEARNING_BLOCKED_PARTIAL_DATA")
        self.assertTrue(result["closure"]["requires_human"])
        self.assertEqual(result["closure"]["human_reason"], "LOW_CONFIDENCE")
        self.assertEqual(result["window"]["status"], "CLOSED_CAPTURED_PARTIAL")
        self.assertFalse(result["window"]["recapture_allowed"])
        self.assertEqual(result["idempotency"]["status"], "COMMITTED")
        self.assertFalse(result["idempotency"]["duplicate_allowed"])
        self.assertFalse(result["external_action_allowed"])
        self.assertFalse(result["notion_mutation_allowed"])

    def test_scope_is_part_of_idempotency_key(self):
        a = close_facebook_capture_24h(self.base(company_id="a"))
        b = close_facebook_capture_24h(self.base(company_id="b"))
        self.assertNotEqual(a["idempotency"]["idempotency_key"], b["idempotency"]["idempotency_key"])

    def test_invalid_environment_fails_closed(self):
        with self.assertRaises(ValueError):
            close_facebook_capture_24h(self.base(environment="UNKNOWN"))


if __name__ == "__main__":
    unittest.main()
