from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class Tax001ArtifactIngestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module("tax001_artifact_ingest", ROOT / "engines" / "TAX-001" / "ops" / "artifact_ingest.py")

    def _write_fixture(self, root: Path, name: str, payload):
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_valid_aw_av_bh_bind(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aw = self._write_fixture(root, "aw.json", [{"case_id": f"FISC-G{i:03d}", "theme": "x"} for i in range(1, 78)])
            av = self._write_fixture(root, "av.json", {"audit": "provenance", "result": "placeholder corpus retracted"})
            bh = self._write_fixture(root, "bh.json", [{"case_id": f"FISC-G{i:03d}", "status": "PENDING"} for i in range(1, 22)])
            lock = self.mod.build_bound_lock({"AW": aw, "AV": av, "BH": bh})
            self.assertEqual(lock["status"], "BOUND")
            self.assertEqual(lock["integrity"]["aw_case_count"], 77)
            self.assertEqual(lock["integrity"]["bh_pending_count"], 21)
            self.assertTrue(lock["integrity"]["bh_subset_of_aw"])
            for artifact in ("AW", "AV", "BH"):
                self.assertEqual(len(lock["artifacts"][artifact]["sha256"]), 64)

    def test_aw_with_missing_ids_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aw = self._write_fixture(root, "aw.json", [{"case_id": f"FISC-G{i:03d}"} for i in range(1, 77)])
            av = self._write_fixture(root, "av.json", {"provenance": "placeholder"})
            bh = self._write_fixture(root, "bh.json", [{"case_id": f"FISC-G{i:03d}"} for i in range(1, 22)])
            with self.assertRaises(ValueError):
                self.mod.build_bound_lock({"AW": aw, "AV": av, "BH": bh})

    def test_bh_not_21_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aw = self._write_fixture(root, "aw.json", [{"case_id": f"FISC-G{i:03d}"} for i in range(1, 78)])
            av = self._write_fixture(root, "av.json", {"provenance": "placeholder"})
            bh = self._write_fixture(root, "bh.json", [{"case_id": f"FISC-G{i:03d}"} for i in range(1, 21)])
            with self.assertRaises(ValueError):
                self.mod.build_bound_lock({"AW": aw, "AV": av, "BH": bh})

    def test_av_without_provenance_signals_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aw = self._write_fixture(root, "aw.json", [{"case_id": f"FISC-G{i:03d}"} for i in range(1, 78)])
            av = self._write_fixture(root, "av.json", {"note": "unrelated"})
            bh = self._write_fixture(root, "bh.json", [{"case_id": f"FISC-G{i:03d}"} for i in range(1, 22)])
            with self.assertRaises(ValueError):
                self.mod.build_bound_lock({"AW": aw, "AV": av, "BH": bh})


if __name__ == "__main__":
    unittest.main()
