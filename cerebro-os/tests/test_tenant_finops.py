import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "governance"))
sys.path.insert(0, str(ROOT / "finops"))

from tenant import assert_tenant_access
from budget import check_additional_cost


class TenantFinOpsTests(unittest.TestCase):
    def test_same_company_allowed(self):
        assert_tenant_access("A", "A")

    def test_cross_company_denied(self):
        with self.assertRaises(PermissionError):
            assert_tenant_access("A", "B")

    def test_missing_company_denied(self):
        with self.assertRaises(PermissionError):
            assert_tenant_access(None, "A")

    def test_zero_cost_allowed_by_default(self):
        self.assertTrue(check_additional_cost(0).allowed)

    def test_unapproved_cost_blocked(self):
        decision = check_additional_cost(0.01)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "MONEY_LIMIT")


if __name__ == "__main__":
    unittest.main()
