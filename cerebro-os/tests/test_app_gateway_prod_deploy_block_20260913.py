import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AppGatewayProdDeployBlockTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "app_gateway_prod_deploy_block_20260913.py"))

    def test_gateway_deploy_remains_fail_closed(self):
        evidence = self.mod["EVIDENCE"]
        self.assertTrue(evidence["five_server_wrappers_live"])
        self.assertTrue(evidence["branch_direct_callers_zero"])
        self.assertTrue(evidence["prod_deploy_attempted"])
        self.assertFalse(evidence["prod_deploy_executed"])
        self.assertTrue(evidence["blocked_by_execution_controls"])
        self.assertFalse(evidence["partial_change_observed"])

    def test_no_revoke_without_live_parity(self):
        result = self.mod["assess"]()
        self.assertFalse(result["gateway_live_new_routes"])
        self.assertFalse(result["live_parity_proven"])
        self.assertFalse(result["authenticated_execute_revoke_allowed"])


if __name__ == "__main__":
    unittest.main()
