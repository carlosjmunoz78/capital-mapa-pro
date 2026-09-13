import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "supabase_security_remaining_frontend_search_evidence_20260913.py"
spec = importlib.util.spec_from_file_location("supabase_security_remaining_frontend_search_evidence_20260913", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SupabaseSecurityRemainingFrontendSearchEvidenceTests(unittest.TestCase):
    def test_all_nine_searches_are_recorded_without_false_retirement(self):
        result = module.assess_remaining_frontend_search_evidence()
        self.assertEqual(result["searched_mutator_count"], 9)
        self.assertEqual(result["zero_indexed_match_count"], 9)
        self.assertTrue(result["all_nine_zero_indexed_matches"])
        self.assertTrue(result["frontend_negative_search_evidence_complete"])
        self.assertFalse(result["global_caller_absence_proven"])
        self.assertFalse(result["rpc_unused_proven"])
        self.assertFalse(result["retirement_allowed"])
        self.assertFalse(result["grant_or_rls_change_allowed"])
        self.assertFalse(result["prod_change_allowed"])


if __name__ == "__main__":
    unittest.main()
