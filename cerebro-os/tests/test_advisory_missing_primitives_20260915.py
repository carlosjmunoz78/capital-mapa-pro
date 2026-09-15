import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from advisory.missing_primitives import (
    AMLAssessment,
    BankAssessment,
    CadastreAssessment,
    FinancialOpsAssessment,
    KYCAssessment,
    NotarialAssessment,
    OfferAssessment,
    PropertyAssessment,
    RecommendationAssessment,
    RegistryAssessment,
    ViabilityAssessment,
)


class AdvisoryMissingPrimitivesTests(unittest.TestCase):
    def test_finops_fails_closed_without_evidence(self):
        self.assertEqual(FinancialOpsAssessment(True, True, ()).decision(), "BLOCKED")

    def test_property_requires_verified_ownership_and_encumbrances(self):
        row = PropertyAssessment("PROP-X", True, True, ("registry:1",))
        self.assertEqual(row.decision(), "GREEN")

    def test_registry_and_cadastre_are_not_false_green(self):
        self.assertEqual(RegistryAssessment("R", False, ("e",)).decision(), "AMBER")
        self.assertEqual(CadastreAssessment("C", False, ("e",)).decision(), "AMBER")

    def test_notarial_signature_uses_canonical_exception(self):
        self.assertEqual(
            NotarialAssessment("deed", True, ("notary:1",)).decision(),
            ("HUMAN_REQUIRED", "SIGNATURE_REQUIRED"),
        )

    def test_viability_requires_income_and_evidence(self):
        row = ViabilityAssessment(Decimal("3000"), Decimal("500"), Decimal("700"), ("bank:1",))
        self.assertEqual(row.ratio(), Decimal("0.4"))
        with self.assertRaises(ValueError):
            ViabilityAssessment(Decimal("0"), Decimal("0"), Decimal("0"), ()).ratio()

    def test_bank_family_is_bounded_to_canonical_ids(self):
        self.assertEqual(BankAssessment("BNK-001", True, ("bank:1",)).decision(), "GREEN")
        with self.assertRaises(ValueError):
            BankAssessment("BNK-999", True, ("bank:1",)).decision()

    def test_offer_recommendation_aml_kyc(self):
        OfferAssessment("O1", Decimal("3.2"), Decimal("10000"), ("offer:1",)).validate()
        self.assertEqual(RecommendationAssessment("R1", 2, ("cmp:1",)).decision(), "GREEN")
        self.assertEqual(
            AMLAssessment(True, True, True, ("aml:1",)).decision(),
            ("HUMAN_REQUIRED", "HIGH_RISK"),
        )
        self.assertEqual(KYCAssessment(True, True, ("kyc:1",)).decision(), "GREEN")


if __name__ == "__main__":
    unittest.main()
