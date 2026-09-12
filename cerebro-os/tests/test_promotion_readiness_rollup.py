import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "promotion_readiness_rollup.py"
spec = importlib.util.spec_from_file_location("promotion_readiness_rollup", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PromotionReadinessRollupTests(unittest.TestCase):
    def test_current_known_gaps_block_prod_candidate(self):
        result = module.assess_rollup(
            dependency_live_green=False,
            recovery_external_green=False,
            observability_green=False,
        )
        self.assertEqual(
            set(result["blocking_evidence"]),
            {"dependency_live_verification", "recovery_external_proof", "observability_per_engine"},
        )
        self.assertFalse(result["prod_candidate"])
        self.assertFalse(result["prod_green"])
        self.assertFalse(result["automatic_prod_promotion_allowed"])
        self.assertFalse(result["external_mutation_allowed"])

    def test_tiktok_is_parked_not_blocking(self):
        result = module.assess_rollup(
            dependency_live_green=True,
            recovery_external_green=True,
            observability_green=True,
        )
        self.assertEqual(result["non_blocking_parked"]["tiktok"], "ACCOUNT_NOT_AVAILABLE")
        self.assertTrue(result["prod_candidate"])
        self.assertFalse(result["prod_green"])
        self.assertEqual(result["next_action"], "GRADUAL_HUMAN_GATED_PROMOTION")


if __name__ == "__main__":
    unittest.main()
