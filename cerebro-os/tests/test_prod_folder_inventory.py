import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from prod_folder_inventory import classify, expected_ids, validate_inventory


class ProdFolderInventoryTests(unittest.TestCase):
    def test_expected_inventory_has_exactly_25_scenarios(self):
        self.assertEqual(len(expected_ids()), 25)

    def test_live_fixture_matches_expected_inventory(self):
        fixture = ROOT / "runtime" / "fixtures" / "make_prod_folder_live_inventory_2026-09-12.json"
        data = json.loads(fixture.read_text(encoding="utf-8"))
        live = set(data["active_ids"]) | set(data["inactive_ids"])
        out = validate_inventory(live)
        self.assertTrue(out["green"])
        self.assertEqual(data["scenario_count"], 25)
        self.assertEqual(len(data["active_ids"]), 2)
        self.assertEqual(len(data["inactive_ids"]), 23)
        self.assertEqual(data["family_counts"]["facebook"], 10)
        self.assertEqual(data["family_counts"]["instagram"], 4)
        self.assertEqual(data["family_counts"]["linkedin"], 4)
        self.assertEqual(data["family_counts"]["youtube"], 4)
        self.assertEqual(data["family_counts"]["seo"], 2)
        self.assertEqual(data["family_counts"]["wordpress_test_anomaly"], 1)

    def test_active_seo_edges_are_preserved(self):
        for scenario_id in (9597710, 9550706):
            out = classify(scenario_id)
            self.assertEqual(out["target"], "PRESERVE_ACTIVE_EDGE")
            self.assertFalse(out["delete_allowed"])
            self.assertFalse(out["auto_activate_allowed"])

    def test_one_shots_and_folder_anomaly_are_never_autoactivated(self):
        for scenario_id in (9721473, 9721479, 9550846):
            out = classify(scenario_id)
            self.assertFalse(out["delete_allowed"])
            self.assertFalse(out["auto_activate_allowed"])


if __name__ == "__main__":
    unittest.main()
