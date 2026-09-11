import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "governance"))

from registry import load_registry, validate_registry
from policy import PolicyRequest, evaluate


class GovernanceTests(unittest.TestCase):
    def test_registry_seed_is_valid(self):
        registry = load_registry(ROOT / "registry" / "engine_registry.seed.json")
        self.assertGreaterEqual(len(registry), 10)

    def test_registry_rejects_duplicate(self):
        item = {"engine_id":"X-001","name":"X","status":"DEFINED_NOT_BUILT","version":"0.1.0","environment":"LAB","company_scope":"GLOBAL_OR_SCOPED"}
        with self.assertRaises(ValueError):
            validate_registry([item, dict(item)])

    def test_cross_company_is_denied(self):
        result = evaluate(PolicyRequest(company_id="A", target_company_id="B", environment="LAB", action="read"))
        self.assertEqual(result["decision"], "DENY")

    def test_safe_zero_cost_action_is_allowed(self):
        result = evaluate(PolicyRequest(company_id="A", target_company_id="A", environment="LAB", action="scaffold", cost_eur=0, money_limit_eur=0, risk="LOW", confidence=1.0))
        self.assertEqual(result["decision"], "ALLOW")

    def test_high_risk_prod_action_requires_human(self):
        result = evaluate(PolicyRequest(company_id="A", target_company_id="A", environment="PROD", action="delete", irreversible=True, touches_prod=True, risk="HIGH"))
        self.assertEqual(result["decision"], "HUMAN_REQUIRED")
        self.assertIn("HIGH_RISK", result["reasons"])

    def test_money_limit_requires_human(self):
        result = evaluate(PolicyRequest(company_id="A", target_company_id="A", environment="LAB", action="buy", cost_eur=10, money_limit_eur=0))
        self.assertEqual(result["decision"], "HUMAN_REQUIRED")
        self.assertIn("MONEY_LIMIT", result["reasons"])


if __name__ == "__main__":
    unittest.main()
