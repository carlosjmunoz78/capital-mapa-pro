import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "runtime" / "supabase_security_current_edge_revalidation_20260913.py"
spec = importlib.util.spec_from_file_location("supabase_security_current_edge_revalidation_20260913", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SupabaseSecurityCurrentEdgeRevalidationTests(unittest.TestCase):
    def test_three_current_surfaces_are_pinned_and_fail_closed(self):
        result = module.assess_current_edge_revalidation()
        self.assertEqual(result["surface_count"], 3)
        self.assertEqual(result["tracked_target_mutator_count"], 15)
        self.assertTrue(result["all_current_versions_pinned"])
        self.assertEqual(result["direct_target_reference_count"], 0)
        self.assertTrue(result["all_three_clear_of_direct_target_names"])
        self.assertFalse(result["prod_mutation_performed"])
        self.assertFalse(result["retirement_allowed"])
        self.assertFalse(result["security_green"])


if __name__ == "__main__":
    unittest.main()
