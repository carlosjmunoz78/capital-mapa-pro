import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "supabase_security_remaining_families_lab_20260913.py"
spec = importlib.util.spec_from_file_location("remaining_families_lab", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class RemainingFamiliesLabTests(unittest.TestCase):
    def test_four_remaining_families_have_structural_lab_contract_coverage(self):
        result = module.assess()
        self.assertEqual(result["family_count"], 4)
        self.assertEqual(result["mutator_count"], 4)
        self.assertTrue(result["structural_lab_contract_coverage_green"])
        self.assertTrue(result["signature_required_preserved"])
        self.assertTrue(result["profile_non_equivalent_server_reuse_blocked"])

    def test_lab_coverage_never_false_promotes_prod(self):
        result = module.assess()
        self.assertFalse(result["real_db_replay_proven"])
        self.assertFalse(result["rollback_proven"])
        self.assertFalse(result["prod_parity_green"])
        self.assertFalse(result["prod_mutation_allowed"])
        self.assertFalse(result["grant_or_rls_change_allowed"])
        self.assertFalse(result["legacy_retirement_allowed"])


if __name__ == "__main__":
    unittest.main()
