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


social = load("own_social_signal", "discovery/own_social_signal.py")
adapter = load("make_radar_adapter", "discovery/make_radar_adapter.py")


class MakeRadarAdapterTests(unittest.TestCase):
    def payload(self, **overrides):
        data = {
            "observed_at": "2026-09-12T10:00:00+00:00",
            "external_id": "comment-1",
            "source_account_id": "fenix-social-account",
            "source_content_id": "post-1",
            "value": "Necesito información",
            "evidence_ref": "make:9597297:execution:abc:comment-1",
        }
        data.update(overrides)
        return data

    def test_maps_all_five_verified_radar_scenarios(self):
        expected = {
            9597297: ("FACEBOOK", "COMMENT", "OPP-001"),
            9595955: ("INSTAGRAM", "COMMENT", "OPP-001"),
            9597307: ("LINKEDIN", "COMMENT", "OPP-001"),
            9597372: ("LINKEDIN", "ENGAGEMENT", "MKT-002"),
            9597332: ("YOUTUBE", "COMMENT", "OPP-001"),
        }
        for scenario_id, triple in expected.items():
            signal = adapter.adapt_make_radar_signal(
                scenario_id=scenario_id,
                company_id="fenix",
                environment="LAB",
                version="1.0.0",
                payload=self.payload(external_id=f"id-{scenario_id}"),
                cost_units=1,
            )
            self.assertEqual(triple, (signal.platform, signal.signal_type, signal.engine_id))
            signal.validate()

    def test_hash_is_deterministic_and_payload_change_changes_hash(self):
        a = adapter.adapt_make_radar_signal(
            scenario_id=9597297,
            company_id="fenix",
            environment="LAB",
            version="1.0.0",
            payload=self.payload(),
        )
        b = adapter.adapt_make_radar_signal(
            scenario_id=9597297,
            company_id="fenix",
            environment="LAB",
            version="1.0.0",
            payload=self.payload(),
        )
        c = adapter.adapt_make_radar_signal(
            scenario_id=9597297,
            company_id="fenix",
            environment="LAB",
            version="1.0.0",
            payload=self.payload(value="Texto distinto"),
        )
        self.assertEqual(a.content_hash, b.content_hash)
        self.assertNotEqual(a.content_hash, c.content_hash)

    def test_store_dedupes_adapter_output(self):
        store = social.OwnSocialSignalStore("fenix", "LAB", "1.0.0")
        signal = adapter.adapt_make_radar_signal(
            scenario_id=9595955,
            company_id="fenix",
            environment="LAB",
            version="1.0.0",
            payload=self.payload(external_id="ig-comment"),
        )
        self.assertTrue(store.add(signal))
        self.assertFalse(store.add(signal))

    def test_rejects_unknown_scenario_and_missing_fields(self):
        with self.assertRaises(ValueError):
            adapter.adapt_make_radar_signal(
                scenario_id=1,
                company_id="fenix",
                environment="LAB",
                version="1.0.0",
                payload=self.payload(),
            )
        bad = self.payload()
        bad.pop("external_id")
        with self.assertRaises(ValueError):
            adapter.adapt_make_radar_signal(
                scenario_id=9597297,
                company_id="fenix",
                environment="LAB",
                version="1.0.0",
                payload=bad,
            )

    def test_preserves_scope_and_rejects_invalid_contract_values(self):
        signal = adapter.adapt_make_radar_signal(
            scenario_id=9597332,
            company_id="company-b",
            environment="PROD",
            version="2.0.0",
            payload=self.payload(external_id="yt-comment"),
            confidence=0.9,
            cost_units=0.25,
        )
        self.assertEqual(("company-b", "PROD", "2.0.0"), (signal.company_id, signal.environment, signal.version))
        self.assertAlmostEqual(0.25, signal.cost_units)
        with self.assertRaises(ValueError):
            adapter.adapt_make_radar_signal(
                scenario_id=9597332,
                company_id="company-b",
                environment="UNKNOWN",
                version="2.0.0",
                payload=self.payload(),
            )


if __name__ == "__main__":
    unittest.main()
