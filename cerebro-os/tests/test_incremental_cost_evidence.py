import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "incremental_cost_evidence.py"
spec = importlib.util.spec_from_file_location("incremental_cost_evidence", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class IncrementalCostEvidenceTests(unittest.TestCase):
    def test_incremental_cost_is_zero(self):
        result = module.assess_incremental_cost()
        self.assertTrue(result["incremental_cost_green"])
        self.assertEqual(result["incremental_monthly_cost_eur"], 0.0)
        self.assertFalse(result["additional_paid_ai_required"])
        self.assertFalse(result["new_subscription_required"])

    def test_total_provider_cost_is_not_fabricated(self):
        result = module.assess_incremental_cost()
        self.assertFalse(result["existing_provider_total_cost_measured"])
        self.assertFalse(result["observability_cost_gate_fully_green"])
        self.assertFalse(result["prod_candidate_allowed"])
        self.assertEqual(result["status"], "ZERO_INCREMENTAL_COST_PROVEN_TOTAL_PROVIDER_COST_PENDING")


if __name__ == "__main__":
    unittest.main()
