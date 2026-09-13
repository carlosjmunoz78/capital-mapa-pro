import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AppRpcBranchZeroCallersTests(unittest.TestCase):
    def test_branch_is_zero_without_false_live_claim(self):
        mod = runpy.run_path(str(ROOT / "runtime" / "app_rpc_branch_zero_callers_20260913.py"))
        row = mod["assess"]()
        self.assertTrue(row["audit_success"])
        self.assertEqual(row["persisted_direct_rpc_callers"], 0)
        self.assertEqual(row["persisted_unique_direct_rpcs"], 0)
        self.assertTrue(row["gateway_routes_persisted"])
        self.assertTrue(row["communications_prod_gateway_targeted_in_branch"])
        self.assertFalse(row["main_modified"])
        self.assertFalse(row["production_deployed"])
        self.assertFalse(row["live_parity_proven"])


if __name__ == "__main__":
    unittest.main()
