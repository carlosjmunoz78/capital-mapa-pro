import importlib.util
import sqlite3
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


obs_mod = load("competitor_observation", "discovery/competitor_observation.py")
store_mod = load("competitor_store_sqlite", "discovery/competitor_store_sqlite.py")


def observation(company="fenix", env="LAB", version="1.0.0", value="A", hash_char="a", observed_at="2026-09-12T09:00:00+00:00"):
    return obs_mod.CompetitorObservation(
        company_id=company,
        competitor_id="comp-1",
        engine_id="COMPET-001",
        environment=env,
        version=version,
        source="https://example.com",
        source_type="WEB",
        observed_at=observed_at,
        url_or_external_id="https://example.com",
        metric_or_fact="title",
        value=value,
        content_hash=hash_char * 64,
        evidence_ref="evidence:test",
        confidence=0.95,
        cost_units=0.0,
    )


class CompetitorSqliteStoreTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.store = store_mod.CompetitorSqliteStore(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_dedupes_identical_observation(self):
        item = observation()
        self.assertTrue(self.store.add(item))
        self.assertFalse(self.store.add(item))
        self.assertEqual(1, self.store.count_scope(company_id="fenix", environment="LAB", version="1.0.0"))

    def test_latest_is_exact_scope_and_uses_newest_timestamp(self):
        older = observation(value="Old", hash_char="a", observed_at="2026-09-12T09:00:00+00:00")
        newer = observation(value="New", hash_char="b", observed_at="2026-09-12T10:00:00+00:00")
        other_env = observation(env="PROD", value="Prod", hash_char="c", observed_at="2026-09-12T11:00:00+00:00")
        self.assertEqual(3, self.store.add_many([older, newer, other_env]))
        latest = self.store.latest(
            company_id="fenix",
            competitor_id="comp-1",
            engine_id="COMPET-001",
            environment="LAB",
            version="1.0.0",
            source="https://example.com",
            url_or_external_id="https://example.com",
            metric_or_fact="title",
        )
        self.assertIsNotNone(latest)
        self.assertEqual("New", latest.value)
        self.assertEqual(2, self.store.count_scope(company_id="fenix", environment="LAB", version="1.0.0"))
        self.assertEqual(1, self.store.count_scope(company_id="fenix", environment="PROD", version="1.0.0"))

    def test_scope_is_required(self):
        with self.assertRaises(ValueError):
            self.store.latest(
                company_id="",
                competitor_id="comp-1",
                engine_id="COMPET-001",
                environment="LAB",
                version="1.0.0",
                source="https://example.com",
                url_or_external_id="https://example.com",
                metric_or_fact="title",
            )


if __name__ == "__main__":
    unittest.main()
