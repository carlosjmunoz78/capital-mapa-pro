import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RecoveryRestoreTargetRevalidationTest(unittest.TestCase):
    def test_restore_remains_fail_closed_without_isolated_target(self):
        mod = runpy.run_path(str(ROOT / "runtime" / "recovery_restore_target_revalidation_20260913.py"))
        row = mod["assess"]()
        self.assertTrue(row["prod_active_healthy"])
        self.assertTrue(row["legacy_active_healthy"])
        self.assertEqual(row["prod_default_branch_count"], 1)
        self.assertEqual(row["prod_isolated_nondefault_branch_count"], 0)
        self.assertEqual(row["legacy_branch_count"], 0)
        self.assertFalse(row["isolated_restore_target_available"])
        self.assertFalse(row["legacy_destructive_restore_allowed"])
        self.assertFalse(row["prod_destructive_restore_allowed"])
        self.assertFalse(row["provider_restore_safe_now"])
        self.assertFalse(row["restore_project_tool_may_be_invoked_now"])
        self.assertFalse(row["recovery_green"])


if __name__ == "__main__":
    unittest.main()
