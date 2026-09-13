import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RecoveryBranchInventoryTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "recovery_branch_inventory_20260913_1549.py"))

    def test_no_isolated_restore_target_is_not_green(self):
        result = self.mod["assess_recovery_branch_inventory"]()
        self.assertEqual(result["prod_branches"], ("main",))
        self.assertEqual(result["legacy_branches"], ())
        self.assertFalse(result["isolated_restore_target_available"])
        self.assertFalse(result["restore_attempted"])
        self.assertFalse(result["existing_projects_modified"])
        self.assertFalse(result["recovery_restore_green"])
        self.assertEqual(result["status"], "NO_ISOLATED_RESTORE_TARGET")


if __name__ == "__main__":
    unittest.main()
