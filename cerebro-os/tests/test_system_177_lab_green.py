import importlib.util
import json
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


inventory = load("final_live_inventory", "registry/live_inventory_lab.py")
gate = load("final_system_gate", "registry/system_gate.py")
live = load("final_live_status", "registry/live_status.py")


class System177LabGreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canonical = json.loads((ROOT / "registry/canonical_177.json").read_text(encoding="utf-8"))["engine_ids"]

    def test_evidence_catalog_is_exactly_canonical_177(self):
        self.assertEqual(177, len(self.canonical))
        self.assertEqual(177, len(inventory.TEST_EVIDENCE))
        self.assertEqual(set(self.canonical), set(inventory.TEST_EVIDENCE))

    def test_every_engine_has_real_test_file_reference_or_factory_smoke(self):
        for engine_id, evidence in inventory.TEST_EVIDENCE.items():
            self.assertTrue(evidence.startswith("test:"), msg=engine_id)
            if evidence == "test:smoke_scaffold":
                continue
            parts = evidence.split(":")
            self.assertGreaterEqual(len(parts), 3, msg=engine_id)
            test_stem = parts[1]
            self.assertTrue((ROOT / "tests" / f"{test_stem}.py").is_file(), msg=f"{engine_id}:{evidence}")

    def test_final_lab_matrix_validates_and_system_gate_is_177_green(self):
        records = inventory.verified_lab_records(commit_sha="final-head", ci_run_id="final-ci")
        matrix = inventory.overlay_live_inventory(self.canonical, records)
        self.assertEqual(177, len(matrix))
        for row in matrix:
            live.validate_live_status(row)
            self.assertEqual("LAB_GREEN", row["state"], msg=row["engine_id"])
            self.assertTrue(row["evidence_refs"], msg=row["engine_id"])
        result = gate.system_readiness(canonical_ids=self.canonical, matrix=matrix)
        self.assertEqual("GREEN", result["state"])
        self.assertEqual(177, result["green_count"])
        self.assertEqual((), result["missing_rows"])
        self.assertEqual((), result["not_green"])


if __name__ == "__main__":
    unittest.main()
