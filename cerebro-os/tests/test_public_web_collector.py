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


observation = load("competitor_observation", "discovery/competitor_observation.py")
collector = load("public_web_collector", "discovery/public_web_collector.py")


class PublicWebCollectorTests(unittest.TestCase):
    def test_extracts_high_signal_fields_and_builds_scoped_observations(self):
        html = b'''<!doctype html><html><head>
        <title>Competidor Hipotecas Cordoba</title>
        <link rel="canonical" href="/hipotecas/">
        <script type="application/ld+json">{"@type":"FinancialService","name":"Competidor"}</script>
        </head><body><h1>Hipotecas a medida</h1></body></html>'''
        snap = collector.parse_public_html("https://competidor.example/landing", html)
        self.assertEqual("Competidor Hipotecas Cordoba", snap.title)
        self.assertEqual("Hipotecas a medida", snap.h1)
        self.assertEqual("https://competidor.example/hipotecas/", snap.canonical)
        self.assertEqual(("FinancialService",), snap.schema_types)
        self.assertEqual(64, len(snap.content_hash))

        items = collector.snapshot_observations(
            snap,
            company_id="fenix",
            competitor_id="comp-1",
            environment="LAB",
            version="1.0.0",
            evidence_ref="evidence:web:comp-1:1",
            observed_at="2026-09-12T08:00:00+00:00",
            cost_units=0.25,
        )
        metrics = {item.metric_or_fact for item in items}
        self.assertEqual({"page_fingerprint", "title", "h1", "canonical", "schema_types"}, metrics)
        self.assertTrue(all(item.company_id == "fenix" for item in items))
        self.assertTrue(all(item.competitor_id == "comp-1" for item in items))
        self.assertTrue(all(item.source_type == "WEB" for item in items))
        self.assertEqual(0.25, sum(item.cost_units for item in items))

    def test_rejects_private_local_and_credential_urls(self):
        for url in (
            "http://127.0.0.1/a",
            "http://10.0.0.1/a",
            "http://169.254.1.2/a",
            "http://localhost/a",
            "ftp://example.com/a",
            "https://user:pass@example.com/a",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    collector.validate_public_url(url)

    def test_enforces_response_size_and_non_empty_body(self):
        with self.assertRaises(ValueError):
            collector.parse_public_html("https://example.com", b"")
        with self.assertRaises(ValueError):
            collector.parse_public_html("https://example.com", b"x" * (collector.MAX_HTML_BYTES + 1))

    def test_store_dedupes_repeated_snapshot_facts(self):
        snap = collector.parse_public_html("https://competidor.example/", "<title>A</title><h1>B</h1>")
        items = collector.snapshot_observations(
            snap,
            company_id="fenix",
            competitor_id="comp-1",
            evidence_ref="evidence:1",
            observed_at="2026-09-12T08:00:00+00:00",
        )
        store = observation.CompetitorObservationStore("fenix")
        for item in items:
            self.assertTrue(store.add(item))
            self.assertFalse(store.add(item))
        self.assertEqual(len(items), len(store.observations))


if __name__ == "__main__":
    unittest.main()
