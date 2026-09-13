import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AppRpcPreprodGuardAndGatewayBlockTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "app_rpc_preprod_guard_and_gateway_block_20260913.py"))

    def test_branch_and_preprod_guards_are_green(self):
        result = self.mod["assess"]()
        self.assertTrue(result["preprod_auto_trigger_guard_green"])
        self.assertTrue(result["branch_rpc_migration_green"])
        self.assertTrue(result["safe_live_parity_green"])

    def test_gateway_and_global_cutover_remain_fail_closed(self):
        result = self.mod["assess"]()
        self.assertFalse(result["gateway_prod_green"])
        self.assertFalse(result["global_rpc_cutover_green"])
        self.assertFalse(self.mod["CUT"]["security"]["authenticated_execute_revoke_allowed"])
        self.assertFalse(self.mod["CUT"]["security"]["final_prod_promotion_allowed"])


if __name__ == "__main__":
    unittest.main()
