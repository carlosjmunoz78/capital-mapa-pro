import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "billing_email_evidence_audit_20260913.py"
spec = importlib.util.spec_from_file_location("billing_email_evidence", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class BillingEmailEvidenceAuditTests(unittest.TestCase):
    def test_fail_closed_until_exact_provider_balances_exist(self):
        result = module.assess()
        self.assertEqual(result["provider_count"], 2)
        self.assertEqual(result["unresolved_provider_count"], 2)
        self.assertFalse(result["google_cloud_over_free_tier_proven"])
        self.assertFalse(result["exact_total_due_known"])
        self.assertFalse(result["estimated_amounts_used"])
        self.assertFalse(result["billing_mutation_allowed"])
        self.assertFalse(result["finops_green"])
        self.assertFalse(module.PROVIDERS["google_cloud"]["exact_amount_present_in_available_billing_emails"])
        self.assertFalse(module.PROVIDERS["notion"]["exact_amount_present_in_available_billing_emails"])


if __name__ == "__main__":
    unittest.main()
