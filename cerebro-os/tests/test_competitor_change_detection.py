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


def make(value, digest, when, *, metric="title", company="fenix", competitor="c1", env="LAB", version="1.0.0"):
    return obs.CompetitorObservation(
        company_id=company,
        competitor_id=competitor,
        engine_id="COMPET-001",
        environment=env,
        version=version,
        source="https://competitor.example/",
        source_type="WEB",
        observed_at=when,
        url_or_external_id="https://competitor.example/",
        metric_or_fact=metric,
        value=value,
        content_hash=digest,
        evidence_ref=f"evidence:{when}",
        confidence=0.9,
        cost_units=0.0,
    )


class CompetitorChangeDetectionTests(unittest.TestCase):
    def test_unchanged_fact_produces_no_change(self):
        a = make("A", "a" * 64, "2026-09-12T08:00:00+00:00")
        b = make("A", "a" * 64, "2026-09-12T09:00:00+00:00")
        self.assertIsNone(change.detect_change(a, b))

    def test_changed_high_signal_fact_is_high_priority(self):
        a = make("A", "a" * 64, "2026-09-12T08:00:00+00:00")
        b = make("B", "b" * 64, "2026-09-12T09:00:00+00:00")
        result = change.detect_change(a, b)
        self.assertIsNotNone(result)
        self.assertEqual("HIGH", result.priority)
        self.assertEqual("A", result.previous_value)
        self.assertEqual("B", result.current_value)

    def test_cross_scope_comparison_is_denied(self):
        a = make("A", "a" * 64, "2026-09-12T08:00:00+00:00")
        b = make("B", "b" * 64, "2026-09-12T09:00:00+00:00", company="other")
        with self.assertRaises(ValueError):
            change.detect_change(a, b)

    def test_reverse_time_is_denied(self):
        a = make("A", "a" * 64, "2026-09-12T10:00:00+00:00")
        b = make("B", "b" * 64, "2026-09-12T09:00:00+00:00")
        with self.assertRaises(ValueError):
            change.detect_change(a, b)

    def test_latest_by_fact_selects_latest_observation(self):
        older = make("A", "a" * 64, "2026-09-12T08:00:00+00:00")
        latest = make("B", "b" * 64, "2026-09-12T10:00:00+00:00")
        middle = make("C", "c" * 64, "2026-09-12T09:00:00+00:00")
        index = change.latest_by_fact([older, latest, middle])
        self.assertEqual("B", index[("c1", "https://competitor.example/", "title")].value)


if __name__ == "__main__":
    unittest.main()
