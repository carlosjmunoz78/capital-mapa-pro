import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PreAppCrmClosureCutTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "pre_app_crm_closure_cut_20260913.py"))

    def test_current_cut_is_fail_closed(self):
        result = self.mod["assess"]()
        self.assertFalse(result["global_prod_green"])
        self.assertFalse(result["automatic_prod_promotion_allowed"])
        self.assertTrue(result["ready_to_enter_app_crm_without_claiming_global_prod_green"])
        self.assertEqual(
            set(result["pending_groups"]),
            {"security", "recovery", "observability", "finops", "promotion"},
        )

    def test_rls_is_green_but_security_is_not_globally_green(self):
        security = self.mod["CUT"]["security"]
        self.assertTrue(security["four_table_rls_prod_green"])
        self.assertTrue(security["remaining"])

    def test_recovery_does_not_count_schema_only_branch_as_restore(self):
        recovery = self.mod["CUT"]["recovery"]
        self.assertTrue(recovery["temporary_branch_create_delete_proven"])
        self.assertTrue(recovery["schema_only_branch_not_provider_restore"])
        self.assertFalse(recovery["new_monthly_spend_authorized"])
        self.assertIn("true_provider_restore_or_clone_with_data", recovery["remaining"])

    def test_observability_prod_wiring_is_authorized_but_execution_blocked(self):
        obs = self.mod["CUT"]["observability"]
        self.assertEqual(obs["prod_wiring_human_gate"], "APPROVED")
        self.assertTrue(obs["prod_wiring_attempted"])
        self.assertFalse(obs["prod_wiring_executed"])
        self.assertTrue(obs["prod_wiring_blocked_by_execution_controls"])
        self.assertFalse(obs["partial_prod_change_observed"])
        self.assertTrue(obs["remaining"])


if __name__ == "__main__":
    unittest.main()
