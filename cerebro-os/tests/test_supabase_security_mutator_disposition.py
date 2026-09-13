import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "supabase_security_mutator_disposition.py"
spec = importlib.util.spec_from_file_location("supabase_security_mutator_disposition", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SupabaseSecurityMutatorDispositionTests(unittest.TestCase):
    def test_mutator_surface_is_exactly_15_and_non_destructive(self):
        result = module.assess_mutator_disposition()
        self.assertEqual(result["mutator_count"], 15)
        self.assertTrue(result["all_unique"])
        self.assertFalse(result["automatic_prod_change_allowed"])
        self.assertFalse(result["automatic_grant_revoke_allowed"])
        self.assertFalse(result["automatic_retire_allowed"])

    def test_all_mutators_require_wrap_review_until_parity_is_proven(self):
        self.assertEqual(set(module.MUTATOR_DISPOSITION.values()), {"WRAP_REVIEW"})
        self.assertEqual(len(module.PARITY_REQUIREMENTS), 8)
        self.assertIn("rollback_path_proven", module.PARITY_REQUIREMENTS)
        self.assertIn("authz_scope_equivalence", module.PARITY_REQUIREMENTS)


if __name__ == "__main__":
    unittest.main()
