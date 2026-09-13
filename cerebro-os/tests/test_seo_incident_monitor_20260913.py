import importlib.util
from pathlib import Path
import unittest

P = Path(__file__).parents[1] / "runtime" / "seo_incident_monitor_20260913.py"
spec = importlib.util.spec_from_file_location("seo_incident_monitor", P)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class T(unittest.TestCase):
    def test_incident_classification(self):
        args = dict(scenario_id=9597710, company_id="fenix_capital", engine_id="seo", environment="LAB", version="v1", execution_id="e1")
        self.assertTrue(mod.classify_run(status="error", **args)["incident"])
        self.assertTrue(mod.classify_run(status="warning", **args)["incident"])
        self.assertFalse(mod.classify_run(status="success", **args)["incident"])

    def test_current_state_stays_fail_closed(self):
        a = mod.assess_current_retained_evidence()
        self.assertEqual(a["retained_run_count"], 5)
        self.assertEqual(a["retained_success_count"], 5)
        self.assertTrue(a["incident_classifier_ready"])
        self.assertFalse(a["prod_wiring_enabled"])
        self.assertFalse(a["seo_incident_observability_green"])

    def test_bad_input_rejected(self):
        with self.assertRaises(ValueError):
            mod.classify_run(scenario_id=1, status="success", company_id="fenix_capital", engine_id="seo", environment="LAB", version="v1", execution_id="x")

if __name__ == "__main__":
    unittest.main()
