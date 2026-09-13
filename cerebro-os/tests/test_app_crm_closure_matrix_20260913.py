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
        self.assertIn("APP_007_communications", result["green_objectives"])
        self.assertIn("APP_008_reports", result["green_objectives"])
        self.assertIn("APP_002_auth_rpc_security", result["pending_objectives"])
        self.assertIn("APP_009_carlos_cerebro_access", result["pending_objectives"])
        self.assertIn("APP_010_cerebro_gateway", result["pending_objectives"])
        self.assertIn("APP_011_old_new_rollback_promotion", result["pending_objectives"])
        self.assertTrue(result["app_main_mutation_claimed"])
        self.assertFalse(result["app_preprod_reactivated"])
        self.assertFalse(result["global_prod_green"])
        self.assertFalse(result["automatic_prod_promotion_allowed"])

    def test_live_wrappers_source_promotion_and_http_boundary_are_proven_without_false_auth_e2e(self):
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
        self.assertTrue(rpc["persisted_branch_direct_callers_zero"])
        self.assertEqual(rpc["live_deploy_channel"], "GITHUB_PAGES_GH_PAGES")
        self.assertEqual(rpc["live_deployed_source_sha"], "dd09153a6d025d9cc75eb2c14e776a9e5bd8e16c")
        self.assertEqual(rpc["live_deployed_snapshot_sha"], "c8a4bc720ce91eb46ed811c506623c265d043594")
        self.assertEqual(rpc["live_deploy_run"], 34790008072)
        self.assertTrue(rpc["live_deploy_success"])
        self.assertFalse(rpc["live_deployed_app_is_pre_rpc_migration_branch"])
        self.assertTrue(rpc["live_direct_callers_zero_proven"])
        self.assertTrue(rpc["live_rpc_old_new_parity_proven"])
        self.assertTrue(rpc["live_rpc_old_new_parity_transaction_rolled_back"])
        self.assertEqual(len(rpc["live_rpc_old_new_parity_cases"]), 5)
        self.assertTrue(rpc["live_gateway_http_health_proven"])
        self.assertEqual(rpc["live_gateway_http_health_status"], 200)
        self.assertTrue(rpc["live_gateway_unauthenticated_target_fail_closed"])
        self.assertEqual(rpc["live_gateway_unauthenticated_target_status"], 401)
        self.assertFalse(rpc["live_gateway_http_e2e_proven"])
        self.assertFalse(rpc["http_write_path_rollback_proven"])
        self.assertFalse(rpc["safe_test_identity_available"])
        self.assertFalse(rpc["authenticated_execute_revoke_allowed"])
        self.assertTrue(rpc["legacy_retirement_sql_prepared"])
        self.assertFalse(rpc["legacy_retirement_applied"])

    def test_pr_376_is_merged_with_human_gate_satisfied(self):
        pr = self.mod["BLOCKERS"]["rpc_live_migration"]["pull_request"]
        self.assertEqual(pr["number"], 376)
        self.assertEqual(pr["state"], "MERGED")
        self.assertTrue(pr["mergeable_before_merge"])
        self.assertEqual(pr["head_sha"], "b1b6fb5404a4704c5d637fc770fc90e9f2eb8312")
        self.assertEqual(pr["merge_sha"], "dd09153a6d025d9cc75eb2c14e776a9e5bd8e16c")
        self.assertTrue(pr["promotion_human_gate_satisfied"])

    def test_persisted_branch_migrations_are_promoted_without_premature_privilege_retirement(self):
        persisted = self.mod["BLOCKERS"]["rpc_live_migration"]["branch_persisted_migrations"]
        self.assertTrue(persisted["notifications_list"])
        self.assertTrue(persisted["notification_mark"])
        self.assertTrue(persisted["signature_create"])
        self.assertTrue(persisted["contact_create"])
        self.assertTrue(persisted["expediente_create"])
        self.assertTrue(persisted["audit_ci_success"])
        self.assertTrue(persisted["main_modified"])
        self.assertEqual(persisted["main_merge_sha"], "dd09153a6d025d9cc75eb2c14e776a9e5bd8e16c")
        self.assertFalse(persisted["legacy_authenticated_execute_revoked"])

    def test_parallel_cloudflare_topology_is_preserved_until_routing_is_proven(self):
        hosting = self.mod["BLOCKERS"]["rpc_live_migration"]["parallel_hosting"]
        self.assertTrue(hosting["cloudflare_workers_builds_success"])
        self.assertFalse(hosting["cloudflare_pages_check_success"])
        self.assertFalse(hosting["cloudflare_pages_routing_role_proven"])
        self.assertEqual(hosting["safe_disposition"], "PRESERVE_AND_AUDIT_ROUTING_BEFORE_CHANGE")

    def test_communications_core_is_green_and_optional_assistant_failure_is_fail_soft(self):
        communications = self.mod["BLOCKERS"]["communications"]
        self.assertTrue(communications["prod_gateway_exists"])
        self.assertTrue(communications["app_shell_targets_prod_gateway"])
        self.assertTrue(communications["prepare_send_contract_aligned"])
        self.assertTrue(communications["real_send_path_owned_by_gateway"])
        self.assertEqual(set(communications["real_send_providers"]), {"brevo", "whatsapp"})
        self.assertFalse(communications["assistant_present_in_current_prod_edge_inventory"])
        self.assertTrue(communications["assistant_is_optional_draft_enrichment_only"])
        self.assertTrue(communications["assistant_failure_is_fail_soft"])
        self.assertTrue(communications["communications_core_operational_without_assistant"])
        self.assertTrue(communications["prod_ana_api_present"])
        self.assertEqual(communications["prod_ana_api_scope"], "capabilities_and_corrections_not_expediente_advice")
        self.assertTrue(communications["prod_ana_canonical_present"])
        self.assertFalse(communications["real_send_claimed"])

    def test_supabase_security_advisor_findings_stay_fail_closed_not_bulk_fixed(self):
        sec = self.mod["BLOCKERS"]["supabase_security_advisor"]
        self.assertEqual(sec["rls_enabled_no_policy_count"], 44)
        self.assertTrue(sec["rls_tables_are_currently_fail_closed_for_direct_table_access"])
        self.assertEqual(sec["security_definer_authenticated_executable_count"], 24)
        self.assertFalse(sec["bulk_revoke_allowed"])
        self.assertTrue(sec["live_app_caller_zero_now_proven"])
        self.assertTrue(sec["legacy_rpc_retirement_also_requires_authenticated_http_e2e"])
        self.assertEqual(sec["pg_net_extension_schema"], "public")
        self.assertEqual(sec["pg_net_functions_namespace"], "net")
        self.assertFalse(sec["pg_net_move_without_dependency_backup_review_allowed"])
        self.assertFalse(sec["leaked_password_protection_enabled"])
        self.assertFalse(sec["auth_config_write_channel_available"])

    def test_cerebro_route_is_promoted_but_external_gateway_url_remains_fail_closed(self):
        console = self.mod["BLOCKERS"]["cerebro_console"]
        self.assertTrue(console["app_profile_surface_found"])
        self.assertTrue(console["internal_console_route_present"])
        self.assertEqual(console["internal_console_route"], "/cerebro")
        self.assertTrue(console["promoted_internal_console_route"])
        self.assertTrue(console["profile_launcher_present"])
        self.assertTrue(console["web_shell_fail_closed_without_gateway_url"])
        self.assertFalse(console["deployed_authenticated_console_url_proven"])
        self.assertFalse(console["deployed_profile_launcher_to_external_gateway_proven"])
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
