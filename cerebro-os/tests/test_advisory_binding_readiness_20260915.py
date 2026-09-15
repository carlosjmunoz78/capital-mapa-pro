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
    def test_all_12_domains_are_fully_bindable(self):
        rows = all_binding_readiness()
        self.assertEqual(len(rows), 12)
        self.assertEqual(
            capability_binding_summary(),
            {"domains": 12, "fully_bindable": 12, "partially_bindable": 0, "unbound": 0},
        )
        self.assertTrue(all(row.status == "FULLY_BINDABLE" for row in rows))
        self.assertTrue(all(not row.missing_engine_ids for row in rows))

    def test_fiscal_is_bound_to_tax_001(self):
        row = binding_readiness("FISCAL")
        self.assertEqual(row.status, "FULLY_BINDABLE")
        self.assertEqual(row.executable_engine_ids, ("TAX-001",))

    def test_financial_includes_finops(self):
        row = binding_readiness("FINANCIERA")
        self.assertEqual(row.status, "FULLY_BINDABLE")
        self.assertIn("FINOPS-001", row.executable_engine_ids)

    def test_real_estate_dependencies_are_bound(self):
        row = binding_readiness("INMOBILIARIA")
        self.assertEqual(row.status, "FULLY_BINDABLE")
        self.assertEqual(
            row.executable_engine_ids,
            ("PROP-001", "REGP-001", "CAT-001", "NOT-001"),
        )

    def test_mortgage_dependencies_are_bound(self):
        row = binding_readiness("HIPOTECARIA")
        self.assertEqual(row.status, "FULLY_BINDABLE")
        self.assertIn("VIA-001", row.executable_engine_ids)
        self.assertIn("OFR-001", row.executable_engine_ids)
        self.assertIn("REC-001", row.executable_engine_ids)
        self.assertEqual(len(row.executable_engine_ids), 9)


if __name__ == "__main__":
    unittest.main()
