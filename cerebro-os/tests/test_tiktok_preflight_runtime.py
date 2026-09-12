import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from tiktok_preflight import TikTokPreflightRequest, plan_tiktok_preflight


class TikTokPreflightRuntimeTests(unittest.TestCase):
    def req(self, **changes):
        data = dict(
            company_id="fenix",
            engine_id="SOCIAL",
            environment="LAB",
            version="1.0.0",
            publication_id="pub-1",
            run_id="run-1",
            format="video",
            route_type="ORGANIC",
            content_ready=True,
            asset_ready=True,
            qa_passed=True,
            schedule_ready=True,
            duplicate_exists=False,
        )
        data.update(changes)
        return TikTokPreflightRequest(**data)

    def test_old_organic_contract_routes_but_never_executes(self):
        result = plan_tiktok_preflight(self.req())
        self.assertEqual(result["status"], "ROUTED_ORGANIC_WITH_ENGINE_DISABLED")
        self.assertEqual(result["preflight_status"], "PREFLIGHT_READY_CONNECTION_PENDING")
        self.assertFalse(result["external_action_allowed"])
        self.assertFalse(result["ads_conversion_allowed"])
        self.assertTrue(result["oauth_required"])

    def test_non_organic_route_fails_closed(self):
        result = plan_tiktok_preflight(self.req(route_type="ADS"))
        self.assertEqual(result["status"], "BLOCKED_NON_ORGANIC_ROUTE")
        self.assertFalse(result["external_action_allowed"])

    def test_duplicate_and_missing_gate_block(self):
        self.assertEqual(plan_tiktok_preflight(self.req(duplicate_exists=True))["status"], "BLOCKED_DUPLICATE")
        self.assertEqual(plan_tiktok_preflight(self.req(qa_passed=False))["status"], "BLOCKED_PREFLIGHT")

    def test_scope_is_explicit(self):
        result = plan_tiktok_preflight(self.req(environment="PREPROD"))
        self.assertEqual(result["company_id"], "fenix")
        self.assertEqual(result["environment"], "PREPROD")
        self.assertEqual(result["version"], "1.0.0")

    def test_invalid_environment_rejected(self):
        with self.assertRaises(ValueError):
            plan_tiktok_preflight(self.req(environment="DEV"))


if __name__ == "__main__":
    unittest.main()
