import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "runtime" / "observability_lab_177_evidence_20260913.py"
spec = importlib.util.spec_from_file_location("observability_lab_177_evidence_20260913", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ObservabilityLab177EvidenceTests(unittest.TestCase):
    def test_lab_is_green_without_false_prod_green(self):
        result = module.assess_lab_observability_177()
        self.assertTrue(result["lab_runtime_observability_177_green"])
        self.assertEqual(result["engine_count"], 177)
        self.assertEqual(result["log_coverage_count"], 177)
        self.assertEqual(result["metric_coverage_count"], 177)
        self.assertEqual(result["incident_coverage_count"], 177)
        self.assertFalse(result["additional_subscription_required"])
        self.assertFalse(result["prod_live_observability_green"])
        self.assertFalse(result["prod_candidate_allowed"])


if __name__ == "__main__":
    unittest.main()
