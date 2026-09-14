import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "closure_objective_groups.py"
spec = importlib.util.spec_from_file_location("closure_objective_groups", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ClosureObjectiveGroupsTests(unittest.TestCase):
    def test_execution_order_and_fail_closed_status(self):
        result = module.assess_objective_groups()
        self.assertEqual(
            result["execution_order"],
            ("SECURITY", "RECOVERY", "OBSERVABILITY", "FINOPS", "PROMOTION"),
        )
        self.assertFalse(result["all_green"])
        self.assertFalse(result["prod_candidate_allowed"])
        self.assertFalse(result["automatic_prod_promotion_allowed"])
        self.assertEqual(result["status"], "GREEN_LOOP_IN_PROGRESS")
        self.assertIn(("SECURITY", "HIGH_RISK"), result["human_required"])
        self.assertIn(("RECOVERY", "MONEY_LIMIT"), result["human_required"])
        self.assertIn(("OBSERVABILITY", "HIGH_RISK"), result["human_required"])

    def test_all_groups_have_remaining_evidence_until_proven(self):
        result = module.assess_objective_groups()
        self.assertEqual(set(result["pending_groups"]), set(result["execution_order"]))
        for name in result["execution_order"]:
            row = result["groups"][name]
            self.assertFalse(row["green"])
            self.assertTrue(row["remaining"])

    def test_security_tracks_promoted_app_http_boundary_and_remaining_high_risk_gates(self):
        security = module.OBJECTIVE_GROUPS["SECURITY"]
        completed = security["completed"]
        remaining = security["remaining"]
        self.assertEqual(security["human_required"], ("HIGH_RISK",))
        self.assertIn("44_of_44_fenix_prod_tables_rls_enabled_live", completed)
        self.assertIn("five_target_server_wrappers_live_security_definer_service_role_only", completed)
        self.assertIn("five_target_server_wrappers_unknown_actor_fail_closed", completed)
        self.assertIn("exp_create_and_sign_create_null_actor_guard_hardened_live", completed)
        self.assertIn("five_target_old_new_rpc_parity_green_in_rolled_back_prod_transaction", completed)
        self.assertIn("app_gateway_v17_required_target_routes_live", completed)
        self.assertIn("reviewed_rpc_migration_pr_376_human_authorized_and_merged", completed)
        self.assertIn("app_main_merge_sha_dd09153a6d025d9cc75eb2c14e776a9e5bd8e16c", completed)
        self.assertIn("prod_live_deploy_run_34790008072_success", completed)
        self.assertIn("prod_runtime_smoke_run_34790008059_success", completed)
        self.assertIn("gh_pages_prod_snapshot_c8a4bc720ce91eb46ed811c506623c265d043594", completed)
        self.assertIn("prod_source_sha_matches_main_merge_dd09153a6d025d9cc75eb2c14e776a9e5bd8e16c", completed)
        self.assertIn("live_deployed_source_direct_prod_rpc_search_zero_after_promotion", completed)
        self.assertIn("live_gateway_http_health_200_contract_v3", completed)
        self.assertIn("live_gateway_target_route_without_identity_fails_closed_401", completed)
        self.assertIn("eight_legacy_rpc_retirement_sql_and_rollback_prepared_not_applied", completed)
        self.assertIn("cloudflare_pages_parallel_check_failure_recorded_fail_closed", completed)
        self.assertIn("24_authenticated_security_definer_execute_warnings_captured", completed)
        self.assertIn("24_security_definer_warnings_partitioned_8_legacy_7_read_session_9_mutators", completed)
        self.assertIn("pg_net_function_namespace_net_confirmed_read_only", completed)
        self.assertIn("leaked_password_protection_disabled_warning_captured", completed)
        self.assertIn("leaked_password_protection_supported_remediation_path_documented", completed)
        self.assertIn("safe_prod_authenticated_test_identity_absence_proven", completed)
        self.assertIn("blind_bulk_security_changes_rejected", completed)
        self.assertIn("authenticated_http_gateway_e2e_for_target_routes_with_safe_identity", remaining)
        self.assertIn("rollback_or_non_durable_cleanup_evidence_for_full_http_write_path", remaining)
        self.assertIn("selective_retirement_of_only_migrated_legacy_authenticated_execute_after_http_gate", remaining)
        self.assertIn("post_retirement_gateway_e2e_and_advisor_recheck", remaining)
        self.assertIn("caller_and_contract_disposition_of_7_read_session_and_9_mutating_security_definer_surfaces", remaining)
        self.assertIn("cloudflare_pages_parallel_routing_role_and_failure_disposition", remaining)
        self.assertIn("pg_net_extension_namespace_dependency_backup_and_rebuild_review_before_any_move", remaining)
        self.assertIn("leaked_password_protection_enablement_when_auth_config_write_channel_is_available", remaining)

    def test_recovery_records_real_app_source_rollback_and_money_limit_provider_gate(self):
        recovery = module.OBJECTIVE_GROUPS["RECOVERY"]
        completed = recovery["completed"]
        remaining = recovery["remaining"]
        self.assertEqual(recovery["human_required"], ("MONEY_LIMIT",))
        self.assertIn("app_previous_prod_source_rollback_rehearsal_run_34808719859_green", completed)
        self.assertIn("real_release_or_provider_rollback_target_proven", completed)
        self.assertIn("supabase_restore_to_new_project_paid_and_additional_monthly_expense_documented", completed)
        self.assertIn("no_existing_zero_incremental_cost_isolated_provider_target_proven", completed)
        self.assertNotIn("real_release_or_provider_rollback_target_proven", remaining)
        self.assertIn("money_limit_authorization_or_zero_incremental_cost_isolated_provider_target", remaining)
        self.assertIn("completed_provider_restore", remaining)

    def test_observability_tracks_linkedin_and_latest_youtube_failure_without_false_green(self):
        observability = module.OBJECTIVE_GROUPS["OBSERVABILITY"]
        completed = observability["completed"]
        remaining = observability["remaining"]
        self.assertEqual(observability["human_required"], ("HIGH_RISK",))
        self.assertIn("linkedin_retained_health_execution_green", completed)
        self.assertIn("make_datastore_171764_shared_core_health_and_dedupe_inventory_captured", completed)
        self.assertIn("make_scope_probe_scenario_creation_refused_precreated_datastore_required_no_record_written", completed)
        self.assertIn("youtube_health_activation_attempt_20260914_failed_closed_connection_verify_400_zero_operations_zero_credits", completed)
        self.assertNotIn("youtube_health_reauthorization_green", completed)
        self.assertNotIn("youtube_health_connection_rewired_green", completed)
        self.assertIn("youtube_secure_oauth_reauthorization_and_retained_health_execution_green", remaining)
        self.assertIn("youtube_retained_metric_execution_or_explicit_approved_absence_policy", remaining)

    def test_finops_keeps_reference_separate_from_current_unknown_invoice(self):
        finops = module.OBJECTIVE_GROUPS["FINOPS"]
        self.assertEqual(finops["human_required"], ())
        self.assertIn("notion_authoritative_historical_trial_price_2025_04_04_eur_11_50_per_member_three_members_eur_34_50_month", finops["completed"])
        self.assertIn("notion_historical_price_not_misclassified_as_current_2026_cost", finops["completed"])
        self.assertIn("notion_cost_matrix_2026_08_26_business_reference_20_usd_per_member_month_found", finops["completed"])
        self.assertIn("notion_business_reference_not_misclassified_as_exact_current_invoice", finops["completed"])
        self.assertIn("google_cloud_recent_billing_email_search_found_no_exact_amount", finops["completed"])
        self.assertIn("notion_current_2026_exact_monthly_amount_from_authoritative_billing_source", finops["remaining"])
        self.assertIn("google_cloud_exact_monthly_amount_or_zero_cost_proof_from_authoritative_billing_source", finops["remaining"])


if __name__ == "__main__":
    unittest.main()
