import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "recovery_zero_cost_strategy.py"
spec = importlib.util.spec_from_file_location("recovery_zero_cost_strategy", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RecoveryZeroCostStrategyTests(unittest.TestCase):
    def test_zero_cost_is_default_and_no_paid_branch_is_created(self):
        result = module.assess_zero_cost_recovery_strategy()
        self.assertFalse(result["new_paid_branch_required"])
        self.assertFalse(result["paid_branch_created"])
        self.assertEqual(result["incremental_monthly_cost_eur"], 0.0)

    def test_provider_restore_remains_fail_closed(self):
        result = module.assess_zero_cost_recovery_strategy()
        self.assertFalse(result["provider_restore_proven"])
        self.assertFalse(result["prod_database_restore_allowed"])
        self.assertFalse(result["prod_destructive_test_allowed"])

    def test_paid_fallback_requires_money_limit_gate(self):
        result = module.assess_zero_cost_recovery_strategy()
        self.assertEqual(result["fallback_paid_branch"], "MONEY_LIMIT_HUMAN_CONFIRMATION_REQUIRED")
        self.assertEqual(result["human_reason_if_paid_resource_needed"], "MONEY_LIMIT")


if __name__ == "__main__":
    unittest.main()
