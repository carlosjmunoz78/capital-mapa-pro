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


obs = load("competitor_observation", "discovery/competitor_observation.py")
change = load("competitor_change_detection", "discovery/competitor_change_detection.py")
market = load("market_intelligence", "discovery/market_intelligence.py")


def make_change(metric="title", priority="HIGH", confidence=0.9, company="fenix", env="LAB", version="1.0.0"):
    item = change.CompetitorChange(
        company_id=company,
        competitor_id="comp-1",
        engine_id="COMPET-001",
        environment=env,
        version=version,
        source="https://competitor.example/",
        metric_or_fact=metric,
        previous_value="old",
        current_value="new",
        previous_hash="a" * 64,
        current_hash="b" * 64,
        previous_observed_at="2026-09-12T08:00:00+00:00",
        current_observed_at="2026-09-12T09:00:00+00:00",
        evidence_ref="evidence:delta:1",
        confidence=confidence,
        priority=priority,
    )
    item.validate()
    return item


class MarketIntelligenceTests(unittest.TestCase):
    def test_high_confidence_high_priority_becomes_action_candidate(self):
        signal = market.to_market_signal(make_change())
        self.assertEqual("COMPET-001", signal.source_engine_id)
        self.assertEqual("MKT-002", signal.target_engine_id)
        self.assertEqual("ACTION_CANDIDATE", signal.action)
        self.assertEqual("COMPETITOR_WEB_CHANGE", signal.signal_type)

    def test_medium_change_requires_review_not_automatic_action(self):
        signal = market.to_market_signal(make_change(metric="price", priority="MEDIUM"))
        self.assertEqual("REVIEW", signal.action)
        self.assertEqual("COMPETITOR_OFFER_CHANGE", signal.signal_type)

    def test_low_change_is_observe_only(self):
        signal = market.to_market_signal(make_change(metric="minor_fact", priority="LOW"))
        self.assertEqual("OBSERVE", signal.action)

    def test_scope_is_preserved(self):
        signal = market.to_market_signal(make_change(company="fenix-b", env="PROD", version="2.0.0"))
        self.assertEqual("fenix-b", signal.company_id)
        self.assertEqual("PROD", signal.environment)
        self.assertEqual("2.0.0", signal.version)

    def test_signals_are_deduped_and_high_priority_first(self):
        high = make_change()
        low = make_change(metric="minor_fact", priority="LOW")
        result = market.build_market_signals([low, high, high])
        self.assertEqual(2, len(result))
        self.assertEqual("HIGH", result[0].priority)
        self.assertEqual("LOW", result[1].priority)


if __name__ == "__main__":
    unittest.main()
