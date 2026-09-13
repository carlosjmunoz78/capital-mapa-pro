import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class GreenLoopCut1800Tests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "green_loop_cut_20260913_1800.py"))

    def test_youtube_is_real_green_but_prod_promotion_remains_fail_closed(self):
        result = self.mod["assess"]()
        self.assertTrue(result["youtube_green"])
        self.assertFalse(result["automatic_prod_promotion_allowed"])

    def test_security_recovery_and_finops_remain_fail_closed(self):
        result = self.mod["assess"]()
        self.assertFalse(result["security_prod_rls_green"])
        self.assertFalse(result["recovery_green"])
        self.assertFalse(result["finops_green"])
        self.assertEqual(result["status"], "GREEN_LOOP_IN_PROGRESS")


if __name__ == "__main__":
    unittest.main()
