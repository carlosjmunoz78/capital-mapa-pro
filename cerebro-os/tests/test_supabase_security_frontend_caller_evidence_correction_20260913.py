import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "supabase_security_frontend_caller_evidence_correction_20260913.py"
spec = importlib.util.spec_from_file_location("supabase_security_frontend_caller_evidence_correction_20260913", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SupabaseSecurityFrontendCallerEvidenceCorrectionTests(unittest.TestCase):
    def test_correction_is_pinned_to_current_app_head_and_all_six_sources(self):
        result = module.assess_correction()
        self.assertEqual(result["app_repository"], "carlosjmunoz78/fenix-capital-inmo-map")
        self.assertEqual(result["app_branch"], "main")
        self.assertEqual(result["app_head_sha"], "95106d8e792257f809033486b7025d81665ea83b")
        self.assertEqual(result["corrected_source_count"], 2)
        self.assertEqual(result["verified_source_count"], 6)
        self.assertTrue(result["all_six_current_frontend_callers_have_verified_blob_sha"])
        self.assertFalse(result["prod_mutation_performed"])
        self.assertFalse(result["app_mutation_performed"])
        self.assertEqual(result["status"], "FRONTEND_CALLER_EVIDENCE_TRANSCRIPTION_CORRECTED")

    def test_corrected_blob_shas_are_exact(self):
        self.assertEqual(
            module.CORRECTED_CALLER_BLOB_SHAS["src/ContactCreateShell.tsx"],
            "830a1b950ba573ae769cca402252d98e4fccbe81",
        )
        self.assertEqual(
            module.CORRECTED_CALLER_BLOB_SHAS["src/ExpedienteCreateShell.tsx"],
            "cf810a3ad89eb63bcb48a2d703d6d62ed9db792c",
        )


if __name__ == "__main__":
    unittest.main()
