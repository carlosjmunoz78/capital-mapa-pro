import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "make_alerts_observability_evidence.py"
spec = importlib.util.spec_from_file_location("make_alerts_observability_evidence", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MakeAlertsObservabilityEvidenceTests(unittest.TestCase):
    def test_exact_folder_inventory_is_locked(self):
        expected = {9527636, 9527843, 9527663, 9527908, 9522860, 9527602, 9527718, 9537666}
        self.assertEqual(set(module.SCENARIOS), expected)
        self.assertEqual(module.inventory()["scenario_count"], 8)

    def test_all_are_inactive_and_fail_closed(self):
        inv = module.inventory()
        self.assertTrue(inv["all_inactive"])
        self.assertTrue(inv["all_no_incomplete"])
        self.assertFalse(inv["external_mutation_allowed"])
        self.assertFalse(inv["publication_allowed"])
        self.assertFalse(inv["auto_activate_allowed"])

    def test_snapshot_does_not_become_monthly_cost_evidence(self):
        result = module.assess_observability_evidence()
        self.assertEqual(result["credits_snapshot_total"], 6)
        self.assertEqual(result["data_transfer_snapshot_total"], 1208)
        self.assertIsNone(result["monthly_cost_eur"])
        self.assertEqual(result["cost_evidence"], "SNAPSHOT_ONLY_NOT_MONTHLY_COST")
        self.assertFalse(result["cost_measured_green"])

    def test_no_false_prod_candidate(self):
        result = module.assess_observability_evidence()
        self.assertFalse(result["observability_green"])
        self.assertFalse(result["prod_candidate_allowed"])
        self.assertTrue(result["external_proof_pending"])


if __name__ == "__main__":
    unittest.main()
