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


class Tax001BackupRebuildRehearsalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rehearsal = load_module("tax001_rehearsal", ROOT / "engines" / "TAX-001" / "ops" / "rehearsal.py")

    def test_rehearsal_is_non_destructive_and_exact(self):
        result = self.rehearsal.rehearse()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["scope"], "ENGINE_CODE_CONFIG_ONLY")
        self.assertFalse(result["corpus_artifacts_included"])
        self.assertFalse(result["prod_touched"])
        self.assertGreater(result["files_verified"], 0)

    def test_rollback_restores_exact_known_good_package(self):
        result = self.rehearsal.rehearse_rollback()
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["rollback_exact"])
        self.assertFalse(result["corpus_artifacts_mutated"])
        self.assertFalse(result["prod_touched"])


if __name__ == "__main__":
    unittest.main()
