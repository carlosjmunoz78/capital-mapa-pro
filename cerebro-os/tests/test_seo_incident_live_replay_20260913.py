import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
sys.path.insert(0, str(RUNTIME))

spec = importlib.util.spec_from_file_location("seo_incident_live_replay_20260913", RUNTIME / "seo_incident_live_replay_20260913.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
assert spec.loader is not None
spec.loader.exec_module(module)


class SeoIncidentLiveReplayTests(unittest.TestCase):
    def test_retained_prod_runs_are_replayed_read_only(self):
        result = module.assess()
        self.assertEqual(result["retained_run_count"], 5)
        self.assertEqual(result["retained_success_count"], 5)
        self.assertEqual(result["retained_incident_count"], 0)
        self.assertTrue(result["live_replay_green"])
        self.assertFalse(result["prod_mutation_performed"])
        self.assertFalse(result["make_scenario_mutation_performed"])
        self.assertFalse(result["prod_wiring_enabled"])

    def test_nonprod_error_fixture_proves_incident_capture(self):
        incident = module.replay_nonprod_incident_fixture()
        self.assertEqual(incident["environment"], "TEST")
        self.assertTrue(incident["incident"])
        self.assertEqual(incident["severity"], "HIGH")
        self.assertFalse(incident["external_mutation_performed"])
        self.assertFalse(incident["make_scenario_mutation_allowed"])


if __name__ == "__main__":
    unittest.main()
