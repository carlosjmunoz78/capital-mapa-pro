import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ObservabilityProdWiringAttemptTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "observability_prod_wiring_attempt_20260913.py"))

    def test_approved_attempt_remains_fail_closed_after_execution_block(self):
        result = self.mod["assess"]()
        self.assertEqual(result["human_gate"], "APPROVED")
        self.assertTrue(result["prod_wiring_attempted"])
        self.assertFalse(result["prod_wiring_executed"])
        self.assertTrue(result["blocked_by_execution_controls"])
        self.assertFalse(result["partial_prod_change_observed"])
        self.assertFalse(result["observability_prod_green"])
        self.assertFalse(result["automatic_prod_promotion_allowed"])


if __name__ == "__main__":
    unittest.main()
