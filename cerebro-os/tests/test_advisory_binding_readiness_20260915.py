import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from advisory.binding_readiness import (
    all_binding_readiness,
    binding_readiness,
    capability_binding_summary,
)


class AdvisoryBindingReadinessTests(unittest.TestCase):
    def test_all_12_domains_are_classified(self):
        rows = all_binding_readiness()
        self.assertEqual(len(rows), 12)
        self.assertEqual(
            capability_binding_summary(),
            {"domains": 12, "fully_bindable": 7, "partially_bindable": 3, "unbound": 2},
        )

    def test_fiscal_is_fully_bindable_to_tax_001(self):
        row = binding_readiness("FISCAL")
        self.assertEqual(row.status, "FULLY_BINDABLE")
        self.assertEqual(row.executable_engine_ids, ("TAX-001",))
        self.assertEqual(row.missing_engine_ids, ())

    def test_financial_is_partial_until_finops_exists(self):
        row = binding_readiness("FINANCIERA")
        self.assertEqual(row.status, "PARTIALLY_BINDABLE")
        self.assertEqual(row.missing_engine_ids, ("FINOPS-001",))

    def test_real_estate_is_unbound_fail_closed(self):
        row = binding_readiness("INMOBILIARIA")
        self.assertEqual(row.status, "UNBOUND")
        self.assertEqual(
            row.missing_engine_ids,
            ("PROP-001", "REGP-001", "CAT-001", "NOT-001"),
        )

    def test_mortgage_is_unbound_fail_closed(self):
        row = binding_readiness("HIPOTECARIA")
        self.assertEqual(row.status, "UNBOUND")
        self.assertTrue(row.missing_engine_ids)


if __name__ == "__main__":
    unittest.main()
