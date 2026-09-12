import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from make_support_folder_inventory import total_expected, validate_folder


class MakeSupportFolderInventoryTests(unittest.TestCase):
    def setUp(self):
        fixture = ROOT / "runtime" / "fixtures" / "make_support_folders_live_inventory_2026-09-12.json"
        self.data = json.loads(fixture.read_text(encoding="utf-8"))

    def test_total_support_scenarios_is_19(self):
        self.assertEqual(total_expected(), 19)
        self.assertEqual(self.data["global_invariants"]["total_scenarios"], 19)

    def test_each_folder_inventory_is_green(self):
        for folder in self.data["folders"]:
            out = validate_folder(folder["folder_id"], set(folder["ids"]))
            self.assertTrue(out["inventory_green"])
            self.assertFalse(out["auto_activate_allowed"])
            self.assertFalse(out["delete_allowed"])

    def test_legacy_errors_are_preserved_not_retried(self):
        legacy = next(row for row in self.data["folders"] if row["folder_id"] == 520861)
        self.assertEqual(set(legacy["error_ids"]), {9527814, 5565247, 5566037, 9531064})
        self.assertEqual(legacy["policy"], "PRESERVE_FOR_EVIDENCE_NEVER_AUTOACTIVATE")

    def test_no_support_scenario_is_active(self):
        for folder in self.data["folders"]:
            self.assertEqual(folder["active_ids"], [])
        self.assertTrue(self.data["global_invariants"]["all_incomplete_executions_zero"])


if __name__ == "__main__":
    unittest.main()
