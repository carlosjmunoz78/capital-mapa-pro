import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "supabase_security_frontend_caller_evidence.py"
spec = importlib.util.spec_from_file_location("supabase_security_frontend_caller_evidence", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SupabaseSecurityFrontendCallerEvidenceTests(unittest.TestCase):
    def test_target_surface_and_observed_callers_are_conservative(self):
        result = module.assess_frontend_mutator_evidence()
        self.assertEqual(result["target_mutator_count"], 15)
        self.assertEqual(result["current_frontend_direct_caller_count"], 6)
        self.assertEqual(result["remaining_count"], 9)
        self.assertTrue(result["all_observed_direct_callers_keep_and_wrap"])
        self.assertFalse(result["prod_change_allowed"])
        self.assertFalse(result["grant_or_rls_change_allowed"])
        self.assertFalse(result["retirement_allowed"])

    def test_signature_human_gate_is_preserved(self):
        result = module.assess_frontend_mutator_evidence()
        self.assertTrue(result["signature_gate_preserved"])
        self.assertEqual(
            module.CURRENT_FRONTEND_EVIDENCE["fenix_prod_sign_create"]["human_gate"],
            "SIGNATURE_REQUIRED",
        )


if __name__ == "__main__":
    unittest.main()
