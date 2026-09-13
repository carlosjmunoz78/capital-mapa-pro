import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SecurityFrontendNegativeRevalidationTest(unittest.TestCase):
    def test_nine_zero_matches_are_fail_closed(self):
        mod = runpy.run_path(str(ROOT / "runtime" / "supabase_security_frontend_negative_revalidation_20260913.py"))
        row = mod["assess"]()
        self.assertEqual(row["mutator_count"], 9)
        self.assertEqual(row["zero_indexed_match_count"], 9)
        self.assertTrue(row["all_zero_indexed_matches"])
        self.assertFalse(row["global_absence_proven"])
        self.assertFalse(row["safe_retirement_proven"])
        self.assertFalse(row["prod_privilege_change_allowed"])


if __name__ == "__main__":
    unittest.main()
