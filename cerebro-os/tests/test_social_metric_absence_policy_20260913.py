import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "social_metric_absence_policy_20260913.py"
spec = importlib.util.spec_from_file_location("social_metric_absence_policy_20260913", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SocialMetricAbsencePolicyTests(unittest.TestCase):
    def test_current_policy_is_defined_but_not_self_approved(self):
        result = module.assess_current()
        self.assertTrue(result["policy_defined"])
        self.assertFalse(result["all_approved"])
        self.assertTrue(result["human_approval_required"])
        self.assertFalse(result["make_mutation_performed"])
        self.assertEqual(set(result["targets"]), {"linkedin", "youtube"})

    def test_explicit_approval_can_close_only_intentionally_inactive_target(self):
        row = module.evaluate_absence_policy(
            network="linkedin",
            reason="INTENTIONALLY_INACTIVE",
            explicitly_approved=True,
        )
        self.assertTrue(row["approved_absence_green"])
        self.assertFalse(row["scenario_activation_performed"])
        self.assertFalse(row["automatic_activation_allowed"])

    def test_without_explicit_approval_fail_closed(self):
        row = module.evaluate_absence_policy(
            network="youtube",
            reason="INTENTIONALLY_INACTIVE",
            explicitly_approved=False,
        )
        self.assertFalse(row["approved_absence_green"])
        self.assertEqual(row["status"], "ABSENCE_POLICY_PENDING_APPROVAL")


if __name__ == "__main__":
    unittest.main()
