import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "social_retained_execution_revalidation_20260913.py"
spec = importlib.util.spec_from_file_location("social_retained_execution_revalidation", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class SocialRetainedExecutionRevalidationTests(unittest.TestCase):
    def test_external_absence_is_explicit_not_invented_metrics(self):
        result = module.assess()
        self.assertEqual(result["scenario_count"], 2)
        self.assertEqual(result["platforms_without_retained_execution"], ("linkedin", "youtube"))
        self.assertTrue(result["explicit_external_absence_proven"])
        self.assertFalse(result["linkedin_metric_execution_proven"])
        self.assertFalse(result["youtube_metric_execution_proven"])

    def test_read_only_audit_does_not_activate_or_run_scenarios(self):
        result = module.assess()
        self.assertFalse(result["scenario_activation_performed"])
        self.assertFalse(result["scenario_run_performed"])
        self.assertFalse(result["external_mutation_performed"])
        self.assertFalse(result["social_observability_green"])


if __name__ == "__main__":
    unittest.main()
