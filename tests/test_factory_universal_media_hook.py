"""New factory motors inherit one universal media contract, never a new Worker."""
import importlib.util
import tempfile
import unittest
from pathlib import Path


class UniversalMediaFactoryTest(unittest.TestCase):
    def test_factory_manifest_and_scaffold_contract(self):
        root = Path(__file__).resolve().parents[1]
        path = root / "cerebro-os" / "factory" / "factory.py"
        spec = importlib.util.spec_from_file_location("cerebro_factory", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        manifest = module.build_manifest("SOC-037", "Social Test")
        self.assertEqual(manifest["media_gateway"]["provider_engine_id"], "UMS-001")
        self.assertFalse(manifest["media_gateway"]["uses_per_engine_worker"])
        with tempfile.TemporaryDirectory() as td:
            target = module.scaffold(Path(td), "SOC-037", "Social Test")
            self.assertTrue((target / "config" / "ums001_universal_media.json").is_file())
            self.assertTrue((target / "events" / "MEDIA_JOB_REQUESTED.contract.json").is_file())

    def test_all_engines_have_shared_provider_and_deny_by_default(self):
        root = Path(__file__).resolve().parents[1]
        path = root / "cerebro-os" / "factory" / "universal_media_hook.py"
        spec = importlib.util.spec_from_file_location("universal_media_hook", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for engine_id in ("SEO-002", "SOC-037", "MOTOR-0500"):
            c = module.media_manifest({"engine_id": engine_id, "environment": "LAB", "version": "0.1.0"})
            self.assertEqual(c["capability_provider"], "UMS-001")
            self.assertTrue(c["security"]["signed_identity_required"])
            self.assertFalse(c["transport"]["uses_per_engine_worker"])
            self.assertEqual(c["enrollment_status"], "PENDING_FACTORY_IAM")
            with tempfile.TemporaryDirectory() as td:
                target = Path(td)
                (target / "config").mkdir()
                (target / "events").mkdir()
                module.write_universal_media_scaffold(target, {"engine_id": engine_id, "environment": "LAB", "version": "0.1.0"})
                self.assertTrue((target / "config" / "ums001_universal_media.json").exists())


if __name__ == "__main__":
    unittest.main()
