import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SecurityLabExecutionBoundaryTest(unittest.TestCase):
    def test_fail_closed_boundary(self):
        mod = runpy.run_path(str(ROOT / "runtime" / "security_lab_execution_boundary_20260913.py"))
        row = mod["assess"]()
        self.assertTrue(row["rls_enabled"])
        self.assertEqual(row["policy_count"], 0)
        self.assertEqual(row["row_count_before_attempt"], 0)
        self.assertTrue(row["transactional_write_replay_attempted"])
        self.assertFalse(row["transactional_write_replay_executed"])
        self.assertTrue(row["blocked_by_execution_controls"])
        self.assertFalse(row["legacy_tables_modified"])
        self.assertFalse(row["app_modified"])
        self.assertFalse(row["crm_modified"])
        self.assertFalse(row["prod_modified"])
        self.assertFalse(row["real_business_replay_proven"])
        self.assertFalse(row["rollback_write_path_proven"])
        self.assertFalse(row["automatic_prod_change_allowed"])


if __name__ == "__main__":
    unittest.main()
