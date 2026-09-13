import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "supabase_security_mutator_family_parity.py"
spec = importlib.util.spec_from_file_location("supabase_security_mutator_family_parity", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SupabaseSecurityMutatorFamilyParityTests(unittest.TestCase):
    def test_all_15_mutators_are_accounted_for_once(self):
        result = module.assess_mutator_family_parity()
        self.assertEqual(result["family_count"], 6)
        self.assertEqual(result["mutator_count"], 15)
        self.assertEqual(result["duplicate_count"], 0)
        self.assertTrue(result["all_15_accounted_for"])

    def test_security_stays_fail_closed_until_real_parity(self):
        result = module.assess_mutator_family_parity()
        self.assertFalse(result["security_green"])
        self.assertFalse(result["automatic_prod_rpc_execution_allowed"])
        self.assertFalse(result["automatic_grant_or_rls_change_allowed"])
        self.assertFalse(result["automatic_retirement_allowed"])
        self.assertEqual(result["signature_family_human_gate"], "SIGNATURE_REQUIRED")
        self.assertEqual(len(result["pending_families"]), 6)


if __name__ == "__main__":
    unittest.main()
