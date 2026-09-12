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


obs = load("competitor_observation_contract", "discovery/competitor_observation.py")
HASH = "a" * 64


class CompetitorObservationContractTests(unittest.TestCase):
    def make(self, **overrides):
        data = dict(
            company_id="fenix",
            competitor_id="competitor-1",
            engine_id="COMPET-001",
            environment="LAB",
            version="1.0.0",
            source="https://example.com/sitemap.xml",
            source_type="WEB",
            observed_at="2026-09-12T08:00:00+00:00",
            url_or_external_id="https://example.com/landing",
            metric_or_fact="title",
            value="Hipotecas competitivas",
            content_hash=HASH,
            evidence_ref="evidence:web:competitor-1:1",
            confidence=0.95,
            cost_units=0.2,
        )
        data.update(overrides)
        return obs.CompetitorObservation(**data)

    def test_accepts_exact_scope_and_dedupes_identical_evidence(self):
        store = obs.CompetitorObservationStore("fenix", "LAB", "1.0.0")
        item = self.make()
        self.assertTrue(store.add(item))
        self.assertFalse(store.add(item))
        self.assertEqual((item,), store.by_competitor("competitor-1"))
        self.assertAlmostEqual(0.2, store.cost_units())

    def test_rejects_cross_company_environment_and_version(self):
        store = obs.CompetitorObservationStore("fenix", "PROD", "2.0.0")
        with self.assertRaises(ValueError):
            store.add(self.make(company_id="other", environment="PROD", version="2.0.0"))
        with self.assertRaises(ValueError):
            store.add(self.make(environment="LAB", version="2.0.0"))
        with self.assertRaises(ValueError):
            store.add(self.make(environment="PROD", version="1.0.0"))

    def test_requires_sha256_timezone_valid_confidence_and_nonnegative_cost(self):
        for item in (
            self.make(content_hash="bad"),
            self.make(observed_at="2026-09-12T08:00:00"),
            self.make(confidence=1.1),
            self.make(cost_units=-1),
        ):
            with self.assertRaises(ValueError):
                item.validate()

    def test_allows_same_fact_when_content_hash_changes(self):
        store = obs.CompetitorObservationStore("fenix")
        self.assertTrue(store.add(self.make(content_hash="a" * 64)))
        self.assertTrue(store.add(self.make(content_hash="b" * 64, value="Nuevo title")))
        self.assertEqual(2, len(store.observations))


if __name__ == "__main__":
    unittest.main()
