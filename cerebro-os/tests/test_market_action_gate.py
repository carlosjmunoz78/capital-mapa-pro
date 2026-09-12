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


change = load("competitor_change_detection", "discovery/competitor_change_detection.py")
market = load("market_intelligence", "discovery/market_intelligence.py")
gate = load("market_action_gate", "discovery/market_action_gate.py")


def signal(confidence=0.9, action_priority="HIGH"):
    c = change.CompetitorChange(
        company_id="fenix",
        competitor_id="comp-1",
        engine_id="COMPET-001",
        environment="LAB",
        version="1.0.0",
        source="https://competitor.example/",
        metric_or_fact="title",
        previous_value="old",
        current_value="new",
        previous_hash="a" * 64,
        current_hash="b" * 64,
        previous_observed_at="2026-09-12T08:00:00+00:00",
        current_observed_at="2026-09-12T09:00:00+00:00",
        evidence_ref="evidence:delta:1",
        confidence=confidence,
        priority=action_priority,
    )
    return market.to_market_signal(c)


class MarketActionGateTests(unittest.TestCase):
    def test_action_candidate_only_becomes_proposal_not_execution(self):
        result = gate.decide_market_action(signal())
        self.assertEqual("PROPOSAL_READY", result.decision)
        self.assertEqual("", result.reason)

    def test_low_confidence_requires_human(self):
        result = gate.decide_market_action(signal(confidence=0.5))
        self.assertEqual("HUMAN_REQUIRED", result.decision)
        self.assertEqual("LOW_CONFIDENCE", result.reason)

    def test_high_risk_requires_human(self):
        result = gate.decide_market_action(signal(), high_risk=True)
        self.assertEqual("HUMAN_REQUIRED", result.decision)
        self.assertEqual("HIGH_RISK", result.reason)

    def test_money_required_uses_only_canonical_reason(self):
        result = gate.decide_market_action(signal(), money_required=True)
        self.assertEqual("HUMAN_REQUIRED", result.decision)
        self.assertEqual("MONEY_LIMIT", result.reason)

    def test_policy_conflict_requires_human(self):
        result = gate.decide_market_action(signal(), policy_conflict=True)
        self.assertEqual("HUMAN_REQUIRED", result.decision)
        self.assertEqual("POLICY_CONFLICT", result.reason)


if __name__ == "__main__":
    unittest.main()
