import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runtime"))

from facebook_analytics_windows import AnalyticsWindowsRequest, plan_analytics_windows


class AnalyticsWindowsTests(unittest.TestCase):
    def base(self, **overrides):
        data = dict(
            company_id="fenix",
            engine_id="MKT-ANALYTICS",
            environment="PROD",
            version="V1",
            publication_id="pub-1",
            external_id="post-1",
            published_at="2026-09-01T10:00:00Z",
            canonical_receipt_exists=True,
            windows_exist=False,
        )
        data.update(overrides)
        return AnalyticsWindowsRequest(**data)

    def test_existing_windows_block_duplicate(self):
        result = plan_analytics_windows(self.base(windows_exist=True))
        self.assertEqual("BLOCKED_EXISTING_WINDOWS", result["status"])
        self.assertFalse(result["notion_mutation_allowed"])

    def test_missing_receipt_waits_fail_closed(self):
        result = plan_analytics_windows(self.base(canonical_receipt_exists=False))
        self.assertEqual("WAITING_PUBLICATION_RECEIPT", result["status"])
        self.assertEqual("LOW_CONFIDENCE", result["human_reason"])

    def test_ready_dates_match_24h_27h_7d_plus_3h_contract(self):
        result = plan_analytics_windows(self.base())
        self.assertEqual("WINDOWS_READY_TO_CREATE", result["status"])
        self.assertTrue(result["window_24h_at"].startswith("2026-09-02T10:00:00"))
        self.assertTrue(result["window_24h_grace_until"].startswith("2026-09-02T13:00:00"))
        self.assertTrue(result["window_7d_at"].startswith("2026-09-08T10:00:00"))
        self.assertTrue(result["window_7d_grace_until"].startswith("2026-09-08T13:00:00"))
        self.assertFalse(result["external_action_allowed"])


if __name__ == "__main__":
    unittest.main()
