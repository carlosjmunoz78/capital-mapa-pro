import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FinopsNotionConnectedEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "finops_notion_connected_evidence_20260913.py"))

    def test_connected_sources_do_not_fake_exact_billing(self):
        row = self.mod["assess"]()
        self.assertTrue(row["notion_workspace_connected"])
        self.assertTrue(row["notion_cost_matrix_record_found"])
        self.assertEqual(row["notion_reference_price_usd_per_member_month"], 20.0)
        self.assertFalse(row["notion_reference_price_is_actual_invoice"])
        self.assertTrue(row["notion_record_explicitly_requires_real_invoice_eur"])
        self.assertFalse(row["notion_exact_monthly_amount_proven"])
        self.assertTrue(row["gcp_billing_account_notice_found"])
        self.assertTrue(row["gcp_pending_charge_notice_found"])
        self.assertFalse(row["gcp_exact_amount_proven"])
        self.assertFalse(row["estimated_amounts_used"])
        self.assertFalse(row["finops_green"])


if __name__ == "__main__":
    unittest.main()
