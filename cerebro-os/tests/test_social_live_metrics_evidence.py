import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "social_live_metrics_evidence.py"
spec = importlib.util.spec_from_file_location("social_live_metrics_evidence", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SocialLiveMetricsEvidenceTests(unittest.TestCase):
    def test_facebook_retained_live_metrics_are_accounted_for(self):
        result = module.assess_social_live_metrics()
        self.assertTrue(result["facebook_live_metrics_proven"])
        self.assertEqual(result["facebook_successful_runs"], 2)
        self.assertEqual(result["facebook_operations_observed"], 6)
        self.assertEqual(result["facebook_credits_observed"], 6)
        self.assertEqual(result["facebook_data_transfer_observed"], 1208)

    def test_social_family_is_not_falsely_marked_complete(self):
        result = module.assess_social_live_metrics()
        self.assertFalse(result["linkedin_live_metrics_proven"])
        self.assertFalse(result["youtube_live_metrics_proven"])
        self.assertFalse(result["cross_network_metrics_complete"])
        self.assertFalse(result["social_metrics_green"])
        self.assertFalse(result["scenario_activation_performed"])
        self.assertFalse(result["external_mutation_performed"])
        self.assertIsNone(result["monthly_cost_eur"])
        self.assertFalse(result["cost_measured_green"])
        self.assertFalse(result["prod_candidate_allowed"])


if __name__ == "__main__":
    unittest.main()
