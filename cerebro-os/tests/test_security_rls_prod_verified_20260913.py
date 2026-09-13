import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SecurityRlsProdVerifiedTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "security_rls_prod_verified_20260913.py"))

    def test_four_target_tables_are_verified_rls_enabled(self):
        result = self.mod["assess"]()
        self.assertTrue(result["four_table_rls_green"])
        self.assertEqual(len(result["verified_rls_enabled"]), 4)
        self.assertTrue(all(result["verified_rls_enabled"].values()))

    def test_security_remains_fail_closed_for_other_findings(self):
        result = self.mod["assess"]()
        self.assertFalse(result["security_global_green"])
        self.assertFalse(result["automatic_privilege_change_allowed"])
        self.assertEqual(result["status"], "FOUR_TABLE_RLS_GREEN_SECURITY_REVIEW_CONTINUES")


if __name__ == "__main__":
    unittest.main()
