import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "supabase_preprod_recovery_target_evidence.py"
spec = importlib.util.spec_from_file_location("supabase_preprod_recovery_target_evidence", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SupabasePreprodRecoveryTargetEvidenceTests(unittest.TestCase):
    def test_metadata_supports_preprod_candidate_classification(self):
        result = module.assess_recovery_target()
        self.assertTrue(result["metadata_supports_preprod_classification"])
        self.assertEqual(result["role"], "EXISTING_NON_PROD_PREPROD_TEST_SURFACE")
        self.assertTrue(result["preprod_or_test_named_functions_present"])

    def test_restore_is_not_falsely_claimed(self):
        result = module.assess_recovery_target()
        self.assertFalse(result["restore_executed"])
        self.assertFalse(result["safe_restore_target_proven"])
        self.assertFalse(result["provider_restore_green"])
        self.assertFalse(result["destructive_action_allowed"])
        self.assertFalse(result["prod_mutation_allowed"])
        self.assertEqual(len(result["next_required_evidence"]), 4)


if __name__ == "__main__":
    unittest.main()
