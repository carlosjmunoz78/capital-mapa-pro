import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class AppRpcProdWrapperProgressTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "app_rpc_prod_wrapper_progress_20260913.py"))

    def test_all_wrappers_are_live_service_role_only(self):
        rows = self.mod["EVIDENCE"]["prod_wrappers"]
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(row["exists"] for row in rows.values()))
        self.assertTrue(all(row["security_definer"] for row in rows.values()))
        self.assertTrue(all(row["execute_roles"] == ("service_role",) for row in rows.values()))

    def test_next_gate_stays_closed(self):
        result = self.mod["assess"]()
        self.assertEqual(result["wrapper_count_live"], 5)
        self.assertEqual(result["pending_wrappers"], ())
        self.assertFalse(result["live_parity_proven"])
        self.assertFalse(result["authenticated_execute_revoke_allowed"])

if __name__ == "__main__":
    unittest.main()
