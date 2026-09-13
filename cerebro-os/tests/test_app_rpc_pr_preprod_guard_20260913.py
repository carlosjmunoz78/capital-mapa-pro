import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AppRpcPrPreprodGuardTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "app_rpc_pr_preprod_guard_20260913.py"))

    def test_pr_is_closed_without_merge(self):
        e = self.mod["EVIDENCE"]
        self.assertTrue(e["draft_pr_closed"])
        self.assertFalse(e["draft_pr_merged"])
        self.assertTrue(e["app_preprod_cancelled_policy"])
        self.assertTrue(e["legacy_preprod_workflow_triggered_by_pr"])
        self.assertFalse(e["legacy_preprod_workflow_was_intentional_reactivation"])

    def test_prod_and_revoke_remain_fail_closed(self):
        result = self.mod["assess"]()
        self.assertTrue(result["pr_fail_closed"])
        self.assertFalse(result["app_preprod_reactivated"])
        self.assertFalse(result["prod_gateway_updated"])
        self.assertFalse(result["authenticated_execute_revoke_allowed"])


if __name__ == "__main__":
    unittest.main()
