"""FACT-001 LAB identity compatibility: no PROD or Cloudflare changes, no paid AI.
Run: python -m unittest discover -s tests -p test_fact001_identity_compat_lab.py
"""
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
FACTORY_DIR = ROOT / "cerebro-os" / "factory"
CANONICAL = ROOT / "cerebro-os" / "registry" / "canonical_177.json"
SEED = ROOT / "cerebro-os" / "registry" / "engine_registry.seed.json"


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


factory = module(FACTORY_DIR / "factory.py", "fact001_identity_factory")
enroll = module(FACTORY_DIR / "universal_media_enrollment.py", "fact001_identity_enroll")


class FactoryIdentityCompatibilityLab(unittest.TestCase):
    def test_all_canonical_and_seed_ids_preserved(self):
        ids = json.loads(CANONICAL.read_text(encoding="utf-8"))["engine_ids"]
        seeded = [r["engine_id"] for r in json.loads(SEED.read_text(encoding="utf-8"))]
        self.assertEqual(len(ids), 177)
        for engine_id in ids + seeded:
            with self.subTest(engine_id=engine_id):
                self.assertEqual(factory.validate_engine_id(engine_id), engine_id)
                self.assertIsNotNone(enroll.ENGINE_RE.fullmatch(engine_id))

    def test_original_canonical_3rd_001_enrolls_only_to_pending(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            target = factory.scaffold(Path(tmp), "3RD-001", "Legacy canonical test", company_id="fenix")
            event = json.loads((target / "events" / "FACT001_ENGINE_CREATED.outbox.json").read_text())
            receipt = json.loads((target / "events" / "UMS001_FACTORY_ENROLLMENT_STATUS.json").read_text())
            self.assertEqual(event["engine_id"], "3RD-001")
            self.assertEqual(receipt["status"], "PENDING_FACTORY_IAM_TRANSPORT")
            self.assertFalse(receipt["media_dispatch_enabled"])

    def test_invalid_ids_rejected_consistently(self):
        invalid = ("---", "999", "A--", "-FACT", "FACT-", "A", "AB", "A__B", "../FACT-001")
        for engine_id in invalid:
            with self.subTest(engine_id=engine_id):
                with self.assertRaises(ValueError):
                    factory.validate_engine_id(engine_id)
                manifest = factory.build_manifest("FACT-001", "Test")
                manifest["engine_id"] = engine_id
                with self.assertRaises(ValueError):
                    enroll.build_enrollment_event(manifest, "fenix")

    def test_mass_canary_177_isolated_no_network(self):
        ids = json.loads(CANONICAL.read_text(encoding="utf-8"))["engine_ids"]
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            for engine_id in ids:
                target = factory.scaffold(Path(tmp), engine_id, "Canonical LAB", company_id="fenix")
                manifest = json.loads((target / "manifest.json").read_text())
                receipt = json.loads((target / "events" / "UMS001_FACTORY_ENROLLMENT_STATUS.json").read_text())
                self.assertEqual(manifest["status"], "DEFINED_NOT_BUILT")
                self.assertEqual(receipt["status"], "PENDING_FACTORY_IAM_TRANSPORT")
                self.assertFalse(receipt["media_dispatch_enabled"])
                self.assertFalse(manifest["media_gateway"]["paid_execution_enabled"])
            self.assertEqual(len(list((Path(tmp) / "engines").iterdir())), 177)

    def test_cross_company_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            target = factory.scaffold(Path(tmp), "3RD-001", "Canonical LAB", company_id="other")
            receipt = json.loads((target / "events" / "UMS001_FACTORY_ENROLLMENT_STATUS.json").read_text())
            self.assertEqual(receipt["status"], "HOLD_INVALID_FACTORY_SCOPE")
            self.assertFalse((target / "events" / "FACT001_ENGINE_CREATED.outbox.json").exists())

    def test_duplicate_does_not_replace_existing_engine(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            target = factory.scaffold(Path(tmp), "3RD-001", "Canonical LAB", company_id="fenix")
            original = (target / "manifest.json").read_bytes()
            with self.assertRaises(FileExistsError):
                factory.scaffold(Path(tmp), "3RD-001", "Duplicate", company_id="fenix")
            self.assertEqual((target / "manifest.json").read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
