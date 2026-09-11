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


inventory = load("live_inventory_progress", "registry/live_inventory_lab.py")
live = load("live_status_progress", "registry/live_status.py")


class LiveInventoryProgressTests(unittest.TestCase):
    def test_inventory_keeps_unverified_engines_unknown(self):
        canonical = json.loads((ROOT / "registry/canonical_177.json").read_text(encoding="utf-8"))["engine_ids"]
        records = inventory.verified_lab_records(commit_sha="abc123", ci_run_id="run-1")
        rows = inventory.overlay_live_inventory(canonical, records)
        self.assertEqual(177, len(rows))
        green = [r for r in rows if r["state"] == "LAB_GREEN"]
        unknown = [r for r in rows if r["state"] == "UNKNOWN_REQUIRES_AUDIT"]
        self.assertEqual(len(inventory.VERIFIED_LAB_ENGINES), len(green))
        self.assertEqual(177 - len(green), len(unknown))
        self.assertEqual(set(inventory.VERIFIED_LAB_ENGINES), {r["engine_id"] for r in green})
        for record in green:
            live.validate_live_status(record)
            self.assertTrue(record["evidence_refs"])


if __name__ == "__main__":
    unittest.main()
