import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))

from learning.continuous_improvement import (
    DailyImprovementCycle,
    ImprovementCandidate,
    ImprovementObjective,
    decide,
)
from multicompany.bootstrap_orchestrator import CANONICAL_PHASES


def candidate(profile="AUTONOMOUS_VENTURE", value=11.0, risk="LOW", cost=0.0, reversible=True, environment="LAB"):
    objective = ImprovementObjective(
        company_id="company-1",
        engine_id="SEO-001",
        domain="seo",
        metric="qualified_leads",
        baseline=10.0,
        direction="MAXIMIZE",
        autonomy_profile=profile,
        environment=environment,
    )
    evidence = tuple((key, f"evidence://{key}") for key in (
        "baseline", "candidate", "tests", "evaluation", "tribunal",
        "rollback", "backup", "observability", "cost", "policy",
    ))
    return ImprovementCandidate(objective, "1.1.0", value, evidence, risk, cost, reversible)


class ContinuousImprovementTests(unittest.TestCase):
    def test_new_company_bootstrap_contains_continuous_improvement(self):
        self.assertIn("continuous_improvement", CANONICAL_PHASES)
        self.assertLess(CANONICAL_PHASES.index("supervisor"), CANONICAL_PHASES.index("continuous_improvement"))

    def test_autonomous_venture_improvement_can_advance_without_human(self):
        decision = decide(candidate())
        self.assertEqual(decision.decision, "PROMOTE_CANDIDATE")
        self.assertEqual(decision.next_stage, "PREPROD")

    def test_fenix_digital_is_automatic_by_default(self):
        self.assertTrue(DailyImprovementCycle("fenix-capital", "FENIX_DIGITAL").automatic_by_default)

    def test_fenix_sensitive_requires_human_for_promotion(self):
        self.assertEqual(decide(candidate(profile="FENIX_SENSITIVE")).decision, "HUMAN_REQUIRED")

    def test_regression_is_rejected(self):
        self.assertEqual(decide(candidate(value=9.0)).decision, "REJECT")

    def test_paid_change_requires_human(self):
        decision = decide(candidate(cost=1.0))
        self.assertEqual(decision.decision, "HUMAN_REQUIRED")
        self.assertIn("MONEY_LIMIT", decision.reasons)

    def test_high_risk_requires_human(self):
        self.assertEqual(decide(candidate(risk="HIGH")).decision, "HUMAN_REQUIRED")

    def test_irreversible_change_requires_human(self):
        self.assertEqual(decide(candidate(reversible=False)).decision, "HUMAN_REQUIRED")

    def test_prod_candidate_goes_to_canary(self):
        self.assertEqual(decide(candidate(environment="PROD")).next_stage, "CANARY")

    def test_daily_cycle_is_closed_loop(self):
        stages = DailyImprovementCycle("aion", "AUTONOMOUS_VENTURE").stages()
        self.assertEqual(stages[0], "OBSERVE")
        self.assertEqual(stages[-1], "LEARN")
        self.assertIn("OLD_VS_NEW", stages)
        self.assertIn("PROMOTE_OR_ROLLBACK", stages)


if __name__ == "__main__":
    unittest.main()
