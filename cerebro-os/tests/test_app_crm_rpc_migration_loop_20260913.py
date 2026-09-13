import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AppCrmRpcMigrationLoopTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "app_crm_rpc_migration_loop_20260913.py"))

    def test_pre_high_risk_gate_is_green(self):
        result = self.mod["assess"]()
        self.assertTrue(result["pre_high_risk_gate_green"])
        self.assertTrue(result["high_risk_gate_required"])
        self.assertFalse(result["high_risk_gate_approved"])
        self.assertFalse(result["live_migration_allowed"])
        self.assertFalse(result["prod_green"])

    def test_live_systems_remain_unchanged_by_pre_gate_loop(self):
        state = self.mod["STATE"]
        self.assertTrue(state["app_main_unchanged"])
        self.assertFalse(state["app_preprod_reactivated"])
        self.assertFalse(state["prod_db_changed_by_this_loop"])
        self.assertFalse(state["prod_edge_changed_by_this_loop"])

    def test_counts_are_locked_to_live_and_static_evidence(self):
        evidence = self.mod["STATE"]["evidence"]
        self.assertEqual(evidence["direct_call_count"], 10)
        self.assertEqual(evidence["unique_direct_rpc_count"], 8)
        self.assertEqual(evidence["existing_server_wrappers"], 3)
        self.assertEqual(evidence["missing_server_wrappers"], 5)


if __name__ == "__main__":
    unittest.main()
