import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AppCrmRpcProdAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "app_crm_rpc_prod_authorization_20260913.py"))

    def test_authorization_is_green_but_execution_stays_fail_closed(self):
        result = self.mod["assess"]()
        self.assertTrue(result["authorization_green"])
        self.assertFalse(result["prod_execution_green"])
        self.assertTrue(result["permission_retirement_blocked"])
        self.assertEqual(result["status"], "AUTHORIZED_EXECUTION_BLOCKED_FAIL_CLOSED")

    def test_no_prod_change_is_claimed(self):
        execution = self.mod["EVIDENCE"]["execution"]
        self.assertFalse(execution["supabase_wrapper_migration_applied"])
        self.assertFalse(execution["github_caller_persist_applied"])
        self.assertFalse(execution["prod_permissions_changed"])
        self.assertFalse(execution["prod_gateway_changed"])


if __name__ == "__main__":
    unittest.main()
