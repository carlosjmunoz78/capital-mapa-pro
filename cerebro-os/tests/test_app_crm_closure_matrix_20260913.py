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

    def test_rpc_retirement_cannot_be_promoted_from_non_live_evidence(self):
        rpc = self.mod["BLOCKERS"]["rpc_live_migration"]
        self.assertEqual(rpc["runner_direct_callers_before"], 10)
        self.assertEqual(rpc["runner_direct_callers_after"], 0)
        self.assertTrue(rpc["persisted_branch_direct_callers_zero"])
        self.assertFalse(rpc["live_direct_callers_zero_proven"])
        self.assertFalse(rpc["live_parity_proven"])
        self.assertFalse(rpc["authenticated_execute_revoke_allowed"])

    def test_persisted_branch_migrations_are_recorded_without_false_live_green(self):
        rpc = self.mod["BLOCKERS"]["rpc_live_migration"]
        persisted = rpc["branch_persisted_migrations"]
        self.assertTrue(persisted["notifications_list"])
        self.assertTrue(persisted["notification_mark"])
        self.assertTrue(persisted["signature_create"])
        self.assertTrue(persisted["audit_ci_success"])
        self.assertFalse(persisted["main_modified"])
        self.assertFalse(persisted["prod_rpc_permissions_modified"])
        self.assertFalse(rpc["live_parity_proven"])

    def test_cerebro_route_exists_but_profile_link_remains_fail_closed(self):
        console = self.mod["BLOCKERS"]["cerebro_console"]
        self.assertTrue(console["app_profile_surface_found"])
        self.assertTrue(console["internal_console_route_present"])
        self.assertEqual(console["internal_console_route"], "/cerebro")
        self.assertTrue(console["web_shell_fail_closed_without_gateway_url"])
        self.assertFalse(console["deployed_authenticated_console_url_proven"])
        self.assertFalse(console["carlos_profile_link_present"])
        self.assertFalse(console["dead_link_allowed"])


if __name__ == "__main__":
    unittest.main()
