import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "supabase_security_object_inventory.py"
spec = importlib.util.spec_from_file_location("supabase_security_object_inventory", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SupabaseSecurityObjectInventoryTests(unittest.TestCase):
    def test_exact_live_counts_are_locked(self):
        result = module.assess_security_inventory()
        self.assertEqual(result["prod_rls_no_policy_count"], 40)
        self.assertEqual(result["prod_security_definer_count"], 24)
        self.assertEqual(result["legacy_rls_no_policy_count"], 30)
        self.assertEqual(result["extension_in_public_count"], 1)
        self.assertEqual(result["leaked_password_protection_disabled_count"], 2)
        self.assertEqual(result["total_findings"], 97)

    def test_object_inventory_is_unique(self):
        self.assertEqual(len(module.PROD_RLS_NO_POLICY_TABLES), len(set(module.PROD_RLS_NO_POLICY_TABLES)))
        self.assertEqual(len(module.PROD_AUTHENTICATED_SECURITY_DEFINER_FUNCTIONS), len(set(module.PROD_AUTHENTICATED_SECURITY_DEFINER_FUNCTIONS)))

    def test_inventory_never_authorizes_prod_remediation(self):
        result = module.assess_security_inventory()
        self.assertTrue(result["live_read_only_audit"])
        self.assertFalse(result["prod_mutation_performed"])
        self.assertFalse(result["automatic_remediation_allowed"])
        self.assertFalse(result["security_green"])
        self.assertEqual(result["human_reason"], "HIGH_RISK")


if __name__ == "__main__":
    unittest.main()
