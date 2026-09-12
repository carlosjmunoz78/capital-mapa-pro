import json
import os
import sys
import unittest

HERE = os.path.dirname(__file__)
RUNTIME = os.path.abspath(os.path.join(HERE, "..", "runtime"))
if RUNTIME not in sys.path:
    sys.path.insert(0, RUNTIME)

from core_active_edge_parity import CORE_ACTIVE_EDGES, assess_core_active_edge

FIXTURE = os.path.join(RUNTIME, "fixtures", "core_active_edges_live_contract_2026-09-12.json")


class CoreActiveEdgeParityTests(unittest.TestCase):
    def test_eight_live_edges_are_registered(self):
        self.assertEqual(len(CORE_ACTIVE_EDGES), 8)
        self.assertEqual(set(CORE_ACTIVE_EDGES), {9534096, 9534088, 9523007, 9405249, 9768402, 9527242, 9705138, 9533690})

    def test_all_known_edges_preserve_existing_and_fail_closed_for_publish(self):
        for scenario_id in CORE_ACTIVE_EDGES:
            out = assess_core_active_edge(scenario_id)
            self.assertEqual(out["state"], "PRESERVE_AND_WRAP")
            self.assertFalse(out["auto_disable_old"])
            self.assertFalse(out["auto_activate_replacement"])
            self.assertFalse(out["delete_allowed"])
            self.assertFalse(out["platform_publish_allowed"])
            self.assertFalse(out["external_action_allowed"])

    def test_unknown_edge_requires_human(self):
        out = assess_core_active_edge(99999999)
        self.assertEqual(out["state"], "UNKNOWN_EDGE")
        self.assertTrue(out["human_required"])
        self.assertEqual(out["human_reason"], "LOW_CONFIDENCE")

    def test_fixture_matches_runtime_registry(self):
        with open(FIXTURE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["active_count"], 8)
        self.assertEqual({row["scenario_id"] for row in data["edges"]}, set(CORE_ACTIVE_EDGES))
        self.assertTrue(all(row["status"] == "active" for row in data["edges"]))
        self.assertTrue(all(row["incomplete_executions"] == 0 for row in data["edges"]))
        self.assertTrue(all(row["platform_publish"] is False for row in data["edges"]))


if __name__ == "__main__":
    unittest.main()
