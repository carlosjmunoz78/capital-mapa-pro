import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "supabase_live_dependency_evidence.py"
spec = importlib.util.spec_from_file_location("supabase_live_dependency_evidence", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SupabaseLiveDependencyEvidenceTests(unittest.TestCase):
    def test_projects_are_exact_and_live_verified(self):
        self.assertEqual(set(module.PROJECTS), {"legacy_core", "prod"})
        result = module.assess_live_supabase_dependency()
        self.assertTrue(result["live_read_only_verified"])
        self.assertTrue(result["projects_healthy"])
        self.assertTrue(result["edge_functions_live_verified"])

    def test_security_findings_block_promotion(self):
        result = module.assess_live_supabase_dependency()
        self.assertGreater(result["security_findings_total"], 0)
        self.assertTrue(result["security_review_required"])
        self.assertFalse(result["promotion_allowed"])
        self.assertEqual(result["status"], "LIVE_DEPENDENCY_VERIFIED_SECURITY_REVIEW_PENDING")

    def test_no_prod_or_schema_mutation_is_claimed(self):
        result = module.assess_live_supabase_dependency()
        self.assertFalse(result["prod_mutation_performed"])
        self.assertFalse(result["schema_mutation_performed"])


if __name__ == "__main__":
    unittest.main()
