import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FinopsBillingDeepSearchTest(unittest.TestCase):
    def test_deep_email_search_remains_fail_closed(self):
        mod = runpy.run_path(str(ROOT / "runtime" / "finops_billing_deep_search_20260913.py"))
        row = mod["assess"]()
        self.assertEqual(row["provider_count"], 2)
        self.assertEqual(row["unresolved_provider_count"], 2)
        self.assertTrue(row["email_search_space_deepened"])
        self.assertFalse(row["estimated_amounts_used"])
        self.assertTrue(row["provider_console_still_required"])
        self.assertFalse(row["finops_green"])


if __name__ == "__main__":
    unittest.main()
