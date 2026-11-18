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


    def test_failed_late_hook_leaves_no_partial_engine_or_lock(self):
        # A failing docs/ops write after staging media must not publish.
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {
            "CEREBRO_FACT_ENROLL_EVENT_KEY": "x" * 64,
            "CEREBRO_CLOUDFLARE_API_TOKEN": "fake-placeholder-never-transmit",
            "CEREBRO_CLOUDFLARE_ACCOUNT_ID": "a" * 32,
            "CEREBRO_FACT_ENROLL_QUEUE_ID": "b" * 32,
        }, clear=True):
            root = Path(tmp)
            original = Path.write_text

            def fail_rebuild(self, content, *args, **kwargs):
                if self.name == "rebuild.md":
                    raise OSError("INTENTIONAL_LAB_WRITE_FAULT")
                return original(self, content, *args, **kwargs)

            with patch.object(Path, "write_text", new=fail_rebuild), \
                    patch("urllib.request.urlopen") as network:
                with self.assertRaisesRegex(OSError, "INTENTIONAL_LAB_WRITE_FAULT"):
                    factory.scaffold(root, "FACT-ATOMIC-001", "Fault injection", company_id="fenix")
                network.assert_not_called()
            parent = root / "engines"
            self.assertFalse((parent / "FACT-ATOMIC-001").exists())
            self.assertFalse((parent / ".FACT-ATOMIC-001.factory.lock").exists())
            self.assertEqual(list(parent.glob(".FACT-ATOMIC-001.build-*")), [])

    def test_lock_prevents_concurrent_writers_without_touching_lock(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            parent = Path(tmp) / "engines"
            parent.mkdir()
            lock = parent / ".FACT-LOCK-001.factory.lock"
            lock.write_text("OTHER_WRITER")
            with self.assertRaises(FileExistsError):
                factory.scaffold(Path(tmp), "FACT-LOCK-001", "Concurrent", company_id="fenix")
            self.assertEqual(lock.read_text(), "OTHER_WRITER")
            self.assertFalse((parent / "FACT-LOCK-001").exists())

    def test_signed_transport_only_after_complete_scaffold_commit(self):
        class FakeResponse:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return b'{"success":true,"result":{}}'

        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {
            "CEREBRO_FACT_ENROLL_EVENT_KEY": "k" * 64,
            "CEREBRO_CLOUDFLARE_API_TOKEN": "fake-lab-token",
            "CEREBRO_CLOUDFLARE_ACCOUNT_ID": "a" * 32,
            "CEREBRO_FACT_ENROLL_QUEUE_ID": "b" * 32,
        }, clear=True):
            path = Path(tmp) / "engines" / "FACT-POSTCOMMIT-001"
            requests = []

            def check_post_commit(req, timeout=8):
                self.assertTrue(path.is_dir(), "no network until manifest committed")
                self.assertTrue((path / "manifest.json").is_file())
                self.assertTrue((path / "ops" / "rebuild.md").is_file())
                self.assertTrue((path / "events" / "FACT001_ENGINE_CREATED.outbox.json").is_file())
                self.assertEqual(timeout, 8)
                requests.append(req)
                return FakeResponse()

            with patch("urllib.request.urlopen", new=check_post_commit):
                result = factory.scaffold(
                    Path(tmp), "FACT-POSTCOMMIT-001", "One queue", company_id="fenix"
                )
            self.assertEqual(result, path)
            self.assertEqual(len(requests), 1)
            receipt = json.loads((path / "events" / "UMS001_FACTORY_ENROLLMENT_STATUS.json").read_text())
            self.assertEqual(receipt["status"], "QUEUED_SIGNED_ENROLLMENT_PENDING_GATEWAY_ACK")
            self.assertFalse(receipt["media_dispatch_enabled"])
            self.assertFalse((path.parent / ".FACT-POSTCOMMIT-001.factory.lock").exists())

    def test_partial_iam_configuration_cannot_send_or_publish(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {
            "CEREBRO_FACT_ENROLL_EVENT_KEY": "k" * 64,
            "CEREBRO_CLOUDFLARE_API_TOKEN": "fake-lab-token",
            # Missing account and queue on purpose.
        }, clear=True), patch("urllib.request.urlopen") as network:
            path = factory.scaffold(
                Path(tmp), "FACT-PARTIAL-IAM-001", "No transport", company_id="fenix"
            )
            network.assert_not_called()
            receipt = json.loads((path / "events" / "UMS001_FACTORY_ENROLLMENT_STATUS.json").read_text())
            self.assertEqual(receipt["status"], "PENDING_FACTORY_IAM_TRANSPORT")
            self.assertFalse(receipt["media_dispatch_enabled"])


    def test_concurrent_factory_calls_publish_only_one_complete_engine(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            barrier = Barrier(2)
            def attempt():
                barrier.wait(timeout=5)
                try:
                    return factory.scaffold(Path(tmp), "FACT-CONCURRENT-001", "Same ID", company_id="fenix")
                except FileExistsError:
                    return None
            with ThreadPoolExecutor(max_workers=2) as workers:
                values = list(workers.map(lambda _: attempt(), range(2)))
            self.assertEqual(sum(x is not None for x in values), 1)
            target = Path(tmp) / "engines" / "FACT-CONCURRENT-001"
            self.assertTrue((target / "manifest.json").is_file())
            self.assertTrue((target / "ops" / "rebuild.md").is_file())
            self.assertEqual(list(target.parent.glob(".FACT-CONCURRENT-001.build-*")), [])
            self.assertFalse((target.parent / ".FACT-CONCURRENT-001.factory.lock").exists())

    def test_transient_transport_failure_keeps_committed_scaffold_in_hold(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {
            "CEREBRO_FACT_ENROLL_EVENT_KEY": "q" * 64,
            "CEREBRO_CLOUDFLARE_API_TOKEN": "fake-lab-token",
            "CEREBRO_CLOUDFLARE_ACCOUNT_ID": "a" * 32,
            "CEREBRO_FACT_ENROLL_QUEUE_ID": "b" * 32,
        }, clear=True):
            def reject_network(request, timeout=8):
                raise OSError("INTENTIONAL_LAB_QUEUE_UNAVAILABLE")
            with patch("urllib.request.urlopen", new=reject_network):
                target = factory.scaffold(
                    Path(tmp), "FACT-TRANSPORT-FAIL-001", "Transport hold", company_id="fenix"
                )
            self.assertTrue((target / "manifest.json").exists())
            self.assertTrue((target / "events" / "FACT001_ENGINE_CREATED.outbox.json").is_file())
            receipt = json.loads((target / "events" / "UMS001_FACTORY_ENROLLMENT_STATUS.json").read_text())
            self.assertEqual(receipt["status"], "HOLD_ENROLLMENT_TRANSPORT")
            self.assertFalse(receipt["media_dispatch_enabled"])
            self.assertFalse((target.parent / ".FACT-TRANSPORT-FAIL-001.factory.lock").exists())


if __name__ == "__main__":
    unittest.main()
