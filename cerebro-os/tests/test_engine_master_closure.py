import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "engine_master_closure.py"
spec = importlib.util.spec_from_file_location("engine_master_closure", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class EngineMasterClosureTests(unittest.TestCase):
    def test_structural_block_is_green(self):
        result = module.assess_master_closure()
        self.assertTrue(result["structural_green"])

    def test_remaining_blockers_are_external_and_explicit(self):
        result = module.assess_master_closure()
        self.assertEqual(
            set(result["next_groups"]),
            {"SECURITY", "RECOVERY", "OBSERVABILITY"},
        )
        self.assertFalse(result["perfect"])
        self.assertFalse(result["prod_candidate"])
        self.assertFalse(result["prod_green"])

    def test_no_automatic_prod_mutation_or_promotion(self):
        result = module.assess_master_closure()
        self.assertFalse(result["automatic_prod_promotion_allowed"])
        self.assertFalse(result["prod_mutation_allowed"])
        self.assertEqual(result["non_blocking"]["tiktok"], "PARKED_ACCOUNT_NOT_AVAILABLE")


if __name__ == "__main__":
    unittest.main()
