import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AppCrmClosureMatrixTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "app_crm_closure_matrix_20260913.py"))

    def test_green_modules_and_fail_closed_pending_modules_are_explicit(self):
        result = self.mod["assess"]()
        self.assertIn("APP_001_inventory", result["green_objectives"])
        self.assertIn("APP_005_documents", result["green_objectives"])
        self.assertIn("APP_008_reports", result["green_objectives"])
        self.assertIn("APP_002_auth_rpc_security", result["pending_objectives"])
        self.assertIn("APP_007_communications", result["pending_objectives"])
        self.assertIn("APP_009_carlos_cerebro_access", result["pending_objectives"])
        self.assertIn("APP_010_cerebro_gateway", result["pending_objectives"])
        self.assertIn("APP_011_old_new_rollback_promotion", result["pending_objectives"])
        self.assertFalse(result["global_prod_green"])
        self.assertFalse(result["automatic_prod_promotion_allowed"])

    def test_rpc_retirement_cannot_be_promoted_from_runner_only_evidence(self):
        rpc = self.mod["BLOCKERS"]["rpc_live_migration"]
        self.assertEqual(rpc["runner_direct_callers_before"], 10)
        self.assertEqual(rpc["runner_direct_callers_after"], 0)
        self.assertFalse(rpc["live_direct_callers_zero_proven"])
        self.assertFalse(rpc["live_parity_proven"])
        self.assertFalse(rpc["authenticated_execute_revoke_allowed"])

    def test_no_dead_cerebro_profile_link_is_claimed(self):
        console = self.mod["BLOCKERS"]["cerebro_console"]
        self.assertTrue(console["app_profile_surface_found"])
        self.assertFalse(console["deployable_console_route_proven"])
        self.assertFalse(console["carlos_profile_link_present"])
        self.assertFalse(console["dead_link_allowed"])


if __name__ == "__main__":
    unittest.main()
