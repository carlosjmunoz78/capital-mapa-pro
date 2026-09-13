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

    def test_live_wrappers_are_hardened_and_rpc_parity_is_proven_without_false_http_e2e(self):
        rpc = self.mod["BLOCKERS"]["rpc_live_migration"]
        self.assertEqual(rpc["remaining_server_wrappers"], 0)
        self.assertTrue(rpc["server_wrappers_live"])
        self.assertTrue(rpc["server_wrappers_security_definer"])
        self.assertTrue(rpc["server_wrappers_service_role_only"])
        self.assertTrue(rpc["unknown_actor_fail_closed_all_five"])
        self.assertTrue(rpc["exp_create_null_actor_guard"])
        self.assertTrue(rpc["sign_create_null_actor_guard"])
        self.assertEqual(rpc["app_gateway_live_version"], 17)
        self.assertTrue(rpc["app_gateway_required_routes_live"])
        self.assertEqual(rpc["runner_direct_callers_before"], 10)
        self.assertEqual(rpc["runner_direct_callers_after"], 0)
        self.assertTrue(rpc["persisted_branch_direct_callers_zero"])
        self.assertFalse(rpc["live_direct_callers_zero_proven"])
        self.assertTrue(rpc["live_rpc_old_new_parity_proven"])
        self.assertTrue(rpc["live_rpc_old_new_parity_transaction_rolled_back"])
        self.assertEqual(len(rpc["live_rpc_old_new_parity_cases"]), 5)
        self.assertFalse(rpc["live_gateway_http_e2e_proven"])
        self.assertFalse(rpc["authenticated_execute_revoke_allowed"])

    def test_persisted_branch_migrations_are_recorded_without_premature_privilege_retirement(self):
        rpc = self.mod["BLOCKERS"]["rpc_live_migration"]
        persisted = rpc["branch_persisted_migrations"]
        self.assertTrue(persisted["notifications_list"])
        self.assertTrue(persisted["notification_mark"])
        self.assertTrue(persisted["signature_create"])
        self.assertTrue(persisted["contact_create"])
        self.assertTrue(persisted["expediente_create"])
        self.assertTrue(persisted["audit_ci_success"])
        self.assertFalse(persisted["main_modified"])
        self.assertFalse(persisted["legacy_authenticated_execute_revoked"])

    def test_communications_contract_is_aligned_but_assistant_dependency_is_open(self):
        communications = self.mod["BLOCKERS"]["communications"]
        self.assertTrue(communications["prod_gateway_exists"])
        self.assertTrue(communications["app_shell_targets_prod_gateway"])
        self.assertTrue(communications["prepare_send_contract_aligned"])
        self.assertFalse(communications["assistant_present_in_current_prod_edge_inventory"])
        self.assertTrue(communications["assistant_failure_is_fail_soft"])
        self.assertFalse(communications["real_send_claimed"])

    def test_cerebro_route_and_branch_launcher_exist_but_deployed_url_remains_fail_closed(self):
        console = self.mod["BLOCKERS"]["cerebro_console"]
        self.assertTrue(console["app_profile_surface_found"])
        self.assertTrue(console["internal_console_route_present"])
        self.assertEqual(console["internal_console_route"], "/cerebro")
        self.assertTrue(console["branch_profile_launcher_present"])
        self.assertTrue(console["web_shell_fail_closed_without_gateway_url"])
        self.assertFalse(console["deployed_authenticated_console_url_proven"])
        self.assertFalse(console["deployed_profile_launcher_proven"])
        self.assertFalse(console["dead_link_allowed"])

    def test_credential_registry_remains_metadata_only(self):
        registry = self.mod["BLOCKERS"]["credential_registry"]
        self.assertTrue(registry["metadata_only_registry_present"])
        self.assertTrue(registry["raw_secret_fields_forbidden_by_validator"])
        self.assertTrue(registry["opaque_provider_managed_credentials_supported"])
        self.assertTrue(registry["vault_refs_supported"])
        self.assertFalse(registry["raw_values_in_registry_allowed"])


if __name__ == "__main__":
    unittest.main()
