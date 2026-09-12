import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runtime"))

from facebook_analytics_capture import AnalyticsCaptureRequest, plan_analytics_capture


class AnalyticsCaptureTests(unittest.TestCase):
    def base(self, **overrides):
        data = dict(
            company_id="fenix",
            engine_id="MKT-ANALYTICS",
            environment="TEST",
            version="V1",
            notion_record_id="rec-1",
            window="24h",
            post_id="post-1",
            duplicate_committed=False,
            reactions=10,
            comments=3,
            shares=2,
        )
        data.update(overrides)
        return AnalyticsCaptureRequest(**data)

    def test_duplicate_is_blocked_without_platform_call(self):
        result = plan_analytics_capture(self.base(duplicate_committed=True))
        self.assertEqual("BLOCKED_DUPLICATE", result["status"])
        self.assertEqual("NOT_CALLED", result["platform_state"])
        self.assertFalse(result["external_action_allowed"])

    def test_missing_post_id_fails_closed(self):
        result = plan_analytics_capture(self.base(post_id=""))
        self.assertEqual("BLOCKED_POST_ID_MISSING", result["status"])
        self.assertEqual("LOW_CONFIDENCE", result["human_reason"])

    def test_capture_keeps_learning_blocked(self):
        result = plan_analytics_capture(self.base())
        self.assertEqual("CAPTURED_PARTIAL", result["status"])
        self.assertEqual("PARTIAL_DATA_REVIEW", result["quality_status"])
        self.assertEqual("CONSISTENT_CAPTURED_PARTIAL_HOLD", result["reconciliation_status"])
        self.assertEqual("COMMITTED", result["idempotency_status"])
        self.assertEqual("CLOSED_CAPTURED_PARTIAL", result["window_status"])
        self.assertFalse(result["learning_allowed"])
        self.assertFalse(result["external_action_allowed"])


if __name__ == "__main__":
    unittest.main()
