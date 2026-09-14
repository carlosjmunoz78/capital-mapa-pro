from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class Tax001CapabilityTribunalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module("tax001_capability_tribunal", ROOT / "engines" / "TAX-001" / "evaluation" / "capability_tribunal.py")

    def test_current_state_fails_closed(self):
        result = self.mod.evaluate_current()
        self.assertEqual(result["status"], "FAIL_CLOSED")
        self.assertFalse(result["capability_green"])
        self.assertFalse(result["autonomy_green"])
        self.assertIn("CORPUS_LOCK_NOT_BOUND", result["blockers"])
        self.assertIn("CORPUS_ARTIFACTS_NOT_BOUND", result["blockers"])
        self.assertNotIn("AUDIT_PERSISTENCE_NOT_VERIFIED", result["blockers"])
        self.assertIn("BACKUP_NOT_VERIFIED", result["blockers"])
        self.assertIn("ROLLBACK_NOT_VERIFIED", result["blockers"])
        self.assertIn("REBUILD_NOT_VERIFIED", result["blockers"])

    def test_synthetic_fully_verified_state_passes_capability_only(self):
        manifest = {
            "engine_id": "TAX-001",
            "environment": "LAB",
            "knowledge_status": "KNOWLEDGE_GREEN",
            "corpus_lock_status": "BOUND",
            "audit_persistence_status": "VERIFIED_LAB",
            "backup": {"verified": True},
            "rollback": {"verified": True},
            "rebuild": {"verified": True},
            "prod_enabled": False,
            "autonomy_status": "DISABLED",
        }
        result = self.mod.evaluate_capability(manifest, {"status": "BOUND"}, aud001_available=True)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["capability_green"])
        self.assertFalse(result["autonomy_green"])
        self.assertFalse(result["prod_enabled"])


if __name__ == "__main__":
    unittest.main()
