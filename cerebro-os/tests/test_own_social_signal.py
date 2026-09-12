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
HASH = "a" * 64


class OwnSocialSignalTests(unittest.TestCase):
    def make(self, **overrides):
        data = dict(
            company_id="fenix",
            engine_id="SOCAUD-001",
            environment="LAB",
            version="1.0.0",
            platform="FACEBOOK",
            signal_type="COMMENT",
            observed_at="2026-09-12T10:00:00+00:00",
            external_id="comment-1",
            source_account_id="fenix-facebook-page",
            source_content_id="post-1",
            value="Necesito información",
            content_hash=HASH,
            evidence_ref="make:9597297:comment-1",
            confidence=0.95,
            cost_units=1.0,
        )
        data.update(overrides)
        return social.OwnSocialSignal(**data)

    def test_accepts_exact_scope_and_dedupes(self):
        store = social.OwnSocialSignalStore("fenix", "LAB", "1.0.0")
        item = self.make()
        self.assertTrue(store.add(item))
        self.assertFalse(store.add(item))
        self.assertEqual((item,), store.by_platform("FACEBOOK"))
        self.assertEqual(1.0, store.cost_units())

    def test_rejects_cross_company_environment_and_version(self):
        store = social.OwnSocialSignalStore("fenix", "PROD", "2.0.0")
        with self.assertRaises(ValueError):
            store.add(self.make(company_id="other", environment="PROD", version="2.0.0"))
        with self.assertRaises(ValueError):
            store.add(self.make(environment="LAB", version="2.0.0"))
        with self.assertRaises(ValueError):
            store.add(self.make(environment="PROD", version="1.0.0"))

    def test_requires_known_platform_signal_engine_hash_timezone_and_cost(self):
        invalid = (
            self.make(platform="TIKTOK"),
            self.make(signal_type="UNKNOWN"),
            self.make(engine_id="COMPET-001"),
            self.make(content_hash="bad"),
            self.make(observed_at="2026-09-12T10:00:00"),
            self.make(confidence=1.1),
            self.make(cost_units=-1),
        )
        for item in invalid:
            with self.assertRaises(ValueError):
                item.validate()

    def test_same_external_id_can_emit_new_version_when_content_changes(self):
        store = social.OwnSocialSignalStore("fenix")
        self.assertTrue(store.add(self.make(content_hash="a" * 64)))
        self.assertTrue(store.add(self.make(content_hash="b" * 64, value="Comentario actualizado")))
        self.assertEqual(2, len(store.signals))


if __name__ == "__main__":
    unittest.main()
