import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "supabase_security_blockers.py"
spec = importlib.util.spec_from_file_location("supabase_security_blockers", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SupabaseSecurityBlockersTests(unittest.TestCase):
    def test_exact_live_finding_counts_are_locked(self):
        result = module.assess_security_blockers()
        self.assertEqual(result["finding_counts"]["rls_enabled_no_policy"], 70)
        self.assertEqual(result["finding_counts"]["authenticated_security_definer_function_executable"], 24)
        self.assertEqual(result["finding_counts"]["extension_in_public"], 1)
        self.assertEqual(result["finding_counts"]["leaked_password_protection_disabled"], 2)
        self.assertEqual(result["finding_total"], 97)

    def test_prod_security_remediation_is_human_gated(self):
        result = module.assess_security_blockers()
        self.assertTrue(result["prod_security_blocking"])
        self.assertEqual(result["human_required_reason"], "HIGH_RISK")
        self.assertFalse(result["automatic_prod_ddl_allowed"])
        self.assertFalse(result["automatic_auth_policy_change_allowed"])
        self.assertFalse(result["automatic_extension_move_allowed"])
        self.assertFalse(result["automatic_function_privilege_change_allowed"])

    def test_preservation_order_is_explicit(self):
        self.assertEqual(module.REMEDIATION_ORDER[0], "INVENTORY_AFFECTED_OBJECTS")
        self.assertIn("PROVE_ROLLBACK", module.REMEDIATION_ORDER)
        self.assertEqual(module.REMEDIATION_ORDER[-1], "HUMAN_GATED_PROD_CHANGE")
        self.assertFalse(module.assess_security_blockers()["prod_mutation_performed"])


if __name__ == "__main__":
    unittest.main()
