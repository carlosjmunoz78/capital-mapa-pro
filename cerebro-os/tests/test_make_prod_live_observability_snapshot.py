import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "make_prod_live_observability_snapshot.py"
spec = importlib.util.spec_from_file_location("make_prod_live_observability_snapshot", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MakeProdLiveObservabilitySnapshotTests(unittest.TestCase):
    def test_two_active_prod_scenarios_are_locked(self):
        result = module.assess_make_prod_observability()
        self.assertEqual(result["active_scenario_count"], 2)
        self.assertEqual(result["successful_run_count"], 5)
        self.assertEqual(result["operations_observed"], 507)
        self.assertEqual(result["credits_observed"], 507)
        self.assertEqual(result["data_transfer_observed"], 2965036)
        self.assertTrue(result["live_execution_evidence_green"])

    def test_monthly_invoice_cost_is_not_invented(self):
        result = module.assess_make_prod_observability()
        self.assertFalse(result["monthly_invoice_cost_measured"])
        self.assertFalse(result["prod_candidate_allowed"])
        self.assertEqual(result["status"], "LIVE_EXECUTION_EVIDENCE_GREEN_MONTHLY_COST_PENDING")


if __name__ == "__main__":
    unittest.main()
