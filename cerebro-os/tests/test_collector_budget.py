import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, rel):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


budget = load("collector_budget", "discovery/collector_budget.py")


class CollectorBudgetTests(unittest.TestCase):
    def test_prefers_runtime_for_public_web_when_supported(self):
        mode = budget.choose_execution_mode(
            requires_saas_connector=False,
            runtime_supported=True,
            make_supported=True,
            estimated_make_cost_units=500,
            expected_signal_score=0.9,
        )
        self.assertEqual("RUNTIME", mode)

    def test_uses_make_when_saas_connector_is_required_and_supported(self):
        mode = budget.choose_execution_mode(
            requires_saas_connector=True,
            runtime_supported=False,
            make_supported=True,
            estimated_make_cost_units=300,
            expected_signal_score=0.8,
        )
        self.assertEqual("MAKE", mode)

    def test_reserve_is_never_allocated(self):
        monthly = budget.MonthlyCollectorBudget(make_credit_limit=10_000, make_reserve=1_000, make_spent=8_800)
        first = budget.CollectorCandidate("social-a", "SOCIAL", "MAKE", 150, 0.8, True)
        second = budget.CollectorCandidate("social-b", "SOCIAL", "MAKE", 100, 0.8, True)
        self.assertEqual("MAKE", monthly.allocate(first))
        self.assertEqual(8_950, monthly.make_spent)
        self.assertEqual("BUDGET_BLOCKED", monthly.allocate(second))
        self.assertEqual(8_950, monthly.make_spent)

    def test_runtime_allocation_consumes_no_make_budget(self):
        monthly = budget.MonthlyCollectorBudget()
        candidate = budget.CollectorCandidate("web", "WEB", "RUNTIME", 0, 0.9)
        self.assertEqual("RUNTIME", monthly.allocate(candidate))
        self.assertEqual(0, monthly.make_spent)

    def test_bad_efficiency_falls_back_to_runtime_when_possible(self):
        mode = budget.choose_execution_mode(
            requires_saas_connector=True,
            runtime_supported=True,
            make_supported=True,
            estimated_make_cost_units=500,
            expected_signal_score=0.2,
            minimum_signal_per_cost=0.001,
        )
        self.assertEqual("RUNTIME", mode)


if __name__ == "__main__":
    unittest.main()
