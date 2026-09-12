import importlib.util
import sqlite3
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, rel):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


obs_mod = load("competitor_observation", "discovery/competitor_observation.py")
change_mod = load("competitor_change_detection", "discovery/competitor_change_detection.py")
store_mod = load("competitor_store_sqlite", "discovery/competitor_store_sqlite.py")
monitor_mod = load("competitor_monitor", "discovery/competitor_monitor.py")


def obs(value, hash_char, ts):
    return obs_mod.CompetitorObservation(
        company_id="fenix",
        competitor_id="comp-1",
        engine_id="COMPET-001",
        environment="LAB",
        version="1.0.0",
        source="https://example.com",
        source_type="WEB",
        observed_at=ts,
        url_or_external_id="https://example.com",
        metric_or_fact="title",
        value=value,
        content_hash=hash_char * 64,
        evidence_ref="evidence:test",
        confidence=0.95,
        cost_units=0.0,
    )


class CompetitorMonitorTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.store = store_mod.CompetitorSqliteStore(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_first_ingest_has_no_change_duplicate_is_silent(self):
        first = obs("A", "a", "2026-09-12T09:00:00+00:00")
        result = monitor_mod.ingest_delta_only(self.store, [first])
        self.assertEqual(1, result.inserted)
        self.assertEqual(0, len(result.changes))
        duplicate = monitor_mod.ingest_delta_only(self.store, [first])
        self.assertEqual(0, duplicate.inserted)
        self.assertEqual(1, duplicate.unchanged_or_duplicate)
        self.assertEqual(0, len(duplicate.changes))

    def test_changed_fact_emits_delta(self):
        first = obs("A", "a", "2026-09-12T09:00:00+00:00")
        second = obs("B", "b", "2026-09-12T10:00:00+00:00")
        monitor_mod.ingest_delta_only(self.store, [first])
        result = monitor_mod.ingest_delta_only(self.store, [second])
        self.assertEqual(1, result.inserted)
        self.assertEqual(1, len(result.changes))
        self.assertEqual("HIGH", result.changes[0].priority)
        self.assertEqual("A", result.changes[0].previous_value)
        self.assertEqual("B", result.changes[0].current_value)

    def test_scheduler_is_scope_keyed_and_enforces_minimum_interval(self):
        with self.assertRaises(ValueError):
            monitor_mod.MonitorTarget("fenix", "c", "https://example.com", interval_seconds=60).validate()
        target = monitor_mod.MonitorTarget("fenix", "c", "https://example.com", interval_seconds=300)
        state = monitor_mod.MonitorScheduleState()
        now = datetime(2026, 9, 12, 9, 0, tzinfo=timezone.utc)
        self.assertTrue(state.due(target, now))
        state.mark_run(target, now)
        self.assertFalse(state.due(target, datetime(2026, 9, 12, 9, 4, tzinfo=timezone.utc)))
        self.assertTrue(state.due(target, datetime(2026, 9, 12, 9, 5, tzinfo=timezone.utc)))


if __name__ == "__main__":
    unittest.main()
