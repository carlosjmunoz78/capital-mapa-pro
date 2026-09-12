import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from test_folder_active_edges import assess_active_edge, inventory


class TestFolderActiveEdgesTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / "runtime" / "fixtures" / "test_folder_active_edges_2026-09-12.json"
        self.data = json.loads(path.read_text(encoding="utf-8"))

    def test_inventory_has_exactly_two_active_edges(self):
        self.assertEqual(inventory(), {9538231, 9555725})
        self.assertEqual(self.data["invariants"]["active_count"], 2)

    def test_live_active_edges_are_preserved_not_duplicated(self):
        for row in self.data["active_scenarios"]:
            out = assess_active_edge(row["scenario_id"], connection_ok=row["connection_status"] == "ok", incomplete_executions=row["incomplete_executions"])
            self.assertEqual(out["status"], "PRESERVE_ACTIVE_EDGE_GREEN")
            self.assertTrue(out["preserve_active"])
            self.assertFalse(out["runtime_duplicate_execution_allowed"])
            self.assertFalse(out["automatic_relocation_allowed"])
            self.assertFalse(out["delete_allowed"])

    def test_ga4_is_read_only_and_signal_pipeline_is_test_protected(self):
        rows = {row["scenario_id"]: row for row in self.data["active_scenarios"]}
        self.assertEqual(rows[9538231]["kind"], "PROD_SEO_GA4_READ_ONLY")
        self.assertTrue(rows[9555725]["writes_only_test_protected_chain"])
        self.assertEqual(rows[9555725]["idempotency_prefix"], "CEREBRO_SIGNAL_")


if __name__ == "__main__":
    unittest.main()
