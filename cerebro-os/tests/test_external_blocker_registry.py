import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "external_blocker_registry.py"
spec = importlib.util.spec_from_file_location("external_blocker_registry", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ExternalBlockerRegistryTests(unittest.TestCase):
    def test_only_canonical_human_required_codes_are_used(self):
        result = module.validate()
        self.assertTrue(result["valid"])
        self.assertEqual(result["invalid_codes"], ())

    def test_security_authenticated_e2e_tracks_dedicated_identity_and_keeps_write_gate(self):
        row = module.BLOCKERS["SECURITY_AUTHENTICATED_HTTP_E2E"]
        self.assertEqual(row["human_required"], "HIGH_RISK")
        self.assertIn("dedicated_identity_authenticated_in_live_app", row["facts"])
        self.assertIn("notifications_read_path_user_verified_green_in_live_app", row["facts"])
        self.assertIn("four_write_target_http_cleanup_routes_not_proven", row["facts"])
        self.assertIn("raw_auth_users_insertion_forbidden", row["facts"])

    def test_cloudflare_secret_exposure_is_security_incident_and_value_is_not_persisted(self):
        row = module.BLOCKERS["SECURITY_CLOUDFLARE_SECRET_EXPOSURE"]
        self.assertEqual(row["human_required"], "SECURITY_INCIDENT")
        self.assertEqual(row["status"], "SECURITY_INCIDENT_RAW_SECRET_RETURNED_BY_READ_ONLY_INVENTORY")
        self.assertIn("secret_value_not_persisted_into_cerebro_docs_or_tests", row["facts"])
        self.assertIn("user_elected_to_preserve_current_cloudflare_configuration_for_now", row["facts"])
        self.assertIn("automatic_rotation_rejected_until_dependency_inventory_and_rollback_are_complete", row["facts"])

    def test_provider_restore_is_money_limit_not_false_green(self):
        row = module.BLOCKERS["RECOVERY_PROVIDER_RESTORE"]
        self.assertEqual(row["human_required"], "MONEY_LIMIT")
        self.assertIn("restore_to_new_project_creates_new_project_with_additional_monthly_expense", row["facts"])
        self.assertIn("restoring_over_prod_is_rejected", row["facts"])

    def test_auth_configuration_remediation_requires_supported_channel(self):
        row = module.BLOCKERS["SECURITY_LEAKED_PASSWORD_PROTECTION"]
        self.assertEqual(row["human_required"], "HIGH_RISK")
        self.assertIn("current_supabase_connector_has_no_auth_config_write_action", row["facts"])

    def test_persistent_sink_is_lab_green_but_prod_parallel_wiring_remains_open(self):
        row = module.BLOCKERS["OBSERVABILITY_PERSISTENT_PROD_SINK"]
        self.assertIsNone(row["human_required"])
        self.assertEqual(row["status"], "PARTIAL_ZERO_COST_PERSISTENT_SINK_LAB_GREEN_PARALLEL_PROD_WIRING_OPEN")
        self.assertIn("dedicated_google_sheets_sink_created_without_new_subscription", row["facts"])
        self.assertIn("final_synthetic_lab_execution_4c9be20f08e54126b4a8a3ab9bb9fd09_success", row["facts"])
        self.assertIn("independent_google_sheets_readback_confirmed_all_ten_fields_persisted", row["facts"])
        self.assertIn("existing_prod_observability_paths_untouched", row["facts"])

    def test_youtube_health_is_green_after_supported_reauthorization_and_controlled_run(self):
        row = module.BLOCKERS["OBSERVABILITY_YOUTUBE_HEALTH"]
        self.assertIsNone(row["human_required"])
        self.assertEqual(row["status"], "GREEN_CONTROLLED_READ_ONLY_HEALTH_EXECUTION")
        self.assertIn("connection_14591497_status_ok", row["facts"])
        self.assertIn("manual_execution_bcdc124704c147daafc12363cee431a5_success", row["facts"])

    def test_finops_does_not_estimate_unknown_gcp_monthly_total(self):
        row = module.BLOCKERS["FINOPS_EXACT_CURRENT_INVOICES"]
        self.assertIsNone(row["human_required"])
        self.assertIn("notion_current_billing_ui_amount_user_reported_eur_68_97_for_two_users", row["facts"])
        self.assertIn("google_cloud_monthly_period_total_not_yet_proven", row["facts"])
        self.assertIn("estimation_for_green_forbidden", row["facts"])


if __name__ == "__main__":
    unittest.main()
