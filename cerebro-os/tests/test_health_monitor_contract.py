import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from health_monitor_contract import assess_external_health, assess_internal_health, inventory


class HealthMonitorContractTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / "runtime" / "fixtures" / "health_monitor_live_contract_2026-09-12.json"
        self.data = json.loads(path.read_text(encoding="utf-8"))

    def test_inventory_has_all_eight_targets(self):
        self.assertEqual(len(inventory()), 8)
        self.assertEqual(inventory(), {row["scenario_id"] for row in self.data["scenarios"]})

    def test_external_health_edges_are_green_read_only(self):
        for row in self.data["scenarios"]:
            if row.get("mode") != "READ_ONLY":
                continue
            out = assess_external_health(row["scenario_id"], connection_ok=row["connection_status"] == "ok", incomplete_executions=row["incomplete_executions"])
            self.assertEqual(out["status"], "HEALTH_EDGE_GREEN")
            self.assertFalse(out["external_mutation_allowed"])
            self.assertFalse(out["publication_allowed"])
            self.assertFalse(out["auto_activate_allowed"])

    def test_internal_monitors_are_green_and_non_mutating(self):
        for row in self.data["scenarios"]:
            if row.get("external_connector") is not False:
                continue
            out = assess_internal_health(row["scenario_id"], incomplete_executions=row["incomplete_executions"])
            self.assertEqual(out["status"], "INTERNAL_MONITOR_GREEN")
            self.assertFalse(out["external_mutation_allowed"])
            self.assertFalse(out["publication_allowed"])

    def test_fixture_safety_invariants(self):
        inv = self.data["invariants"]
        self.assertTrue(inv["all_incomplete_executions_zero"])
        self.assertTrue(inv["external_health_connections_ok"])
        self.assertFalse(inv["publication_allowed"])
        self.assertFalse(inv["external_mutation_allowed"])
        self.assertFalse(inv["auto_activate_allowed"])


if __name__ == "__main__":
    unittest.main()
