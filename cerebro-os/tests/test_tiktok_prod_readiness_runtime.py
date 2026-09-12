import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from tiktok_prod_readiness import TikTokProdReadinessEvidence, assess_tiktok_prod_readiness, inventory


class TikTokProdReadinessTests(unittest.TestCase):
    def test_live_inventory_reports_only_core_preflight(self):
        self.assertEqual(inventory()["core_preflight"], 9535460)
        self.assertEqual(inventory()["prod_executors"], ())

    def test_missing_oauth_and_prod_executor_fail_closed(self):
        out = assess_tiktok_prod_readiness(
            TikTokProdReadinessEvidence(
                core_preflight_present=True,
                core_preflight_parity_green=True,
                official_oauth_connected=False,
                prod_executor_present=False,
                prod_executor_tested=False,
                rollback_proven=False,
            )
        )
        self.assertEqual(out["status"], "BLOCKED")
        self.assertIn("OFFICIAL_OAUTH_NOT_CONNECTED", out["blockers"])
        self.assertIn("PROD_EXECUTOR_MISSING", out["blockers"])
        self.assertFalse(out["external_action_allowed"])
        self.assertEqual(out["human_reason"], "PERMISSION_REQUIRED")

    def test_all_gates_green_still_requires_explicit_execution(self):
        out = assess_tiktok_prod_readiness(
            TikTokProdReadinessEvidence(True, True, True, True, True, True)
        )
        self.assertEqual(out["status"], "READY_FOR_EXPLICIT_EXECUTION")
        self.assertFalse(out["external_action_allowed"])
        self.assertFalse(out["delete_old_allowed"])
        self.assertEqual(out["human_reason"], "SIGNATURE_REQUIRED")

    def test_fixture_matches_live_make_contract(self):
        fixture = ROOT / "runtime" / "fixtures" / "tiktok_core_preflight_live_contract.json"
        data = json.loads(fixture.read_text(encoding="utf-8"))
        self.assertEqual(data["scenario_id"], 9535460)
        self.assertEqual(data["connections"], [])
        self.assertEqual(data["old_contract"]["preflight_status"], "PREFLIGHT_READY_CONNECTION_PENDING")
        self.assertFalse(data["old_contract"]["prod_executor_present"])
        self.assertFalse(data["new_runtime_invariants"]["external_action_allowed"])


if __name__ == "__main__":
    unittest.main()
