import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AppRpcProdWrapperProgressTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "app_rpc_prod_wrapper_progress_20260913.py"))

    def test_first_wrapper_is_live_and_service_role_only(self):
        row = self.mod["EVIDENCE"]["prod_wrappers"]["fenix_prod_notifications_list_server"]
        self.assertTrue(row["exists"])
        self.assertTrue(row["security_definer"])
        self.assertEqual(row["execute_roles"], ("service_role",))
        self.assertTrue(row["read_only"])

    def test_revoke_remains_fail_closed(self):
        result = self.mod["assess"]()
        self.assertEqual(result["wrapper_count_live"], 1)
        self.assertEqual(result["wrapper_count_target"], 5)
        self.assertFalse(result["authenticated_execute_revoke_allowed"])
        self.assertIn("fenix_prod_notification_mark_server", result["pending_wrappers"])


if __name__ == "__main__":
    unittest.main()
