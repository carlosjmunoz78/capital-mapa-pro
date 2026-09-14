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

    def test_security_authenticated_e2e_is_high_risk_not_auto_executable(self):
        row = module.BLOCKERS["SECURITY_AUTHENTICATED_HTTP_E2E"]
        self.assertEqual(row["human_required"], "HIGH_RISK")
        self.assertIn("no_dedicated_safe_prod_test_identity_proven", row["facts"])
        self.assertIn("raw_auth_users_insertion_forbidden", row["facts"])

    def test_provider_restore_is_money_limit_not_false_green(self):
        row = module.BLOCKERS["RECOVERY_PROVIDER_RESTORE"]
        self.assertEqual(row["human_required"], "MONEY_LIMIT")
        self.assertIn("restore_to_new_project_creates_new_project_with_additional_monthly_expense", row["facts"])
        self.assertIn("restoring_over_prod_is_rejected", row["facts"])

    def test_auth_configuration_remediation_requires_supported_channel(self):
        row = module.BLOCKERS["SECURITY_LEAKED_PASSWORD_PROTECTION"]
        self.assertEqual(row["human_required"], "HIGH_RISK")
        self.assertIn("current_supabase_connector_has_no_auth_config_write_action", row["facts"])

    def test_make_store_discovery_does_not_get_misclassified_as_prod_sink(self):
        row = module.BLOCKERS["OBSERVABILITY_PERSISTENT_PROD_SINK"]
        self.assertIsNone(row["human_required"])
        self.assertIn("make_datastore_171764_is_live_shared_core_health_and_dedupe_store", row["facts"])
        self.assertIn("make_datastore_172319_is_temp_test_schema_audit_store", row["facts"])
        self.assertIn("reusing_shared_core_store_without_schema_contract_rejected", row["facts"])
        self.assertIn("inactive_scope_probe_scenario_creation_refused_because_make_requires_precreated_datastore", row["facts"])
        self.assertIn("scope_probe_created_no_scenario_and_wrote_no_records", row["facts"])

    def test_youtube_health_does_not_stay_green_after_connection_verify_failure(self):
        row = module.BLOCKERS["OBSERVABILITY_YOUTUBE_HEALTH"]
        self.assertEqual(row["human_required"], "HIGH_RISK")
        self.assertEqual(row["status"], "BLOCKED_CONNECTION_VERIFICATION_400")
        self.assertIn("execution_a96383dd40b54b3c91688fe1039a84f4_failed_before_operations", row["facts"])
        self.assertIn("execution_consumed_zero_operations_and_zero_credits", row["facts"])

    def test_finops_does_not_estimate_unknown_current_amounts(self):
        row = module.BLOCKERS["FINOPS_EXACT_CURRENT_INVOICES"]
        self.assertIsNone(row["human_required"])
        self.assertIn("estimation_for_green_forbidden", row["facts"])


if __name__ == "__main__":
    unittest.main()
