import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, rel):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


commercial = load("commercial_loop22", "commercial/pipeline.py")
mortgage = load("mortgage_loop23", "mortgage/pipeline.py")
enterprise = load("enterprise_loop24", "enterprise/ops.py")


class Loop22CommercialTests(unittest.TestCase):
    def test_order_evidence_confidence_and_tenant(self):
        pipe = commercial.CommercialPipeline("fenix")
        self.assertEqual("LEAD-001", pipe.next_engine())
        with self.assertRaises(ValueError):
            pipe.update(commercial.CommercialStep("fenix", "SALE-001", "GREEN", "e:sale"))
        pipe.update(commercial.CommercialStep("fenix", "LEAD-001", "GREEN", "e:lead", 0.95))
        pipe.update(commercial.CommercialStep("fenix", "SALE-001", "GREEN", "e:sale", 0.60))
        self.assertEqual("HUMAN_REQUIRED", pipe.status())
        self.assertEqual("SALE-001", pipe.next_engine())
        pipe.update(commercial.CommercialStep("fenix", "SALE-001", "GREEN", "e:sale2", 0.90))
        with self.assertRaises(ValueError):
            pipe.update(commercial.CommercialStep("other", "COM-001", "GREEN", "e:com"))

    def test_full_commercial_sequence_green(self):
        pipe = commercial.CommercialPipeline("fenix")
        for engine_id in commercial.COMMERCIAL_SEQUENCE:
            pipe.update(commercial.CommercialStep("fenix", engine_id, "GREEN", f"e:{engine_id}", 0.99))
        self.assertEqual("GREEN", pipe.status())
        self.assertIsNone(pipe.next_engine())

    def test_commercial_rejects_cross_environment_or_version(self):
        pipe = commercial.CommercialPipeline("fenix", environment="PROD", version="2.0.0")
        with self.assertRaises(ValueError):
            pipe.update(commercial.CommercialStep("fenix", "LEAD-001", "GREEN", "e", .99, "LAB", "2.0.0"))
        with self.assertRaises(ValueError):
            pipe.update(commercial.CommercialStep("fenix", "LEAD-001", "GREEN", "e", .99, "PROD", "1.0.0"))
        pipe.update(commercial.CommercialStep("fenix", "LEAD-001", "GREEN", "e:prod", .99, "PROD", "2.0.0"))
        self.assertEqual("SALE-001", pipe.next_engine())


class Loop23MortgageTests(unittest.TestCase):
    def test_human_exception_is_canonical_and_blocks_progress(self):
        pipe = mortgage.MortgagePipeline("fenix")
        pipe.update(mortgage.MortgageStep("fenix", "DOC-001", "HUMAN_REQUIRED", "e:doc", "SIGNATURE_REQUIRED"))
        self.assertEqual("HUMAN_REQUIRED", pipe.status())
        self.assertEqual("DOC-001", pipe.next_engine())
        with self.assertRaises(ValueError):
            pipe.update(mortgage.MortgageStep("fenix", "DOC-001", "HUMAN_REQUIRED", "e:doc", "OTHER"))

    def test_full_mortgage_sequence_green(self):
        pipe = mortgage.MortgagePipeline("fenix")
        for engine_id in mortgage.MORTGAGE_SEQUENCE:
            pipe.update(mortgage.MortgageStep("fenix", engine_id, "GREEN", f"e:{engine_id}"))
        self.assertEqual("GREEN", pipe.status())

    def test_mortgage_rejects_cross_environment_or_version(self):
        pipe = mortgage.MortgagePipeline("fenix", "PROD", "2.0.0")
        with self.assertRaises(ValueError):
            pipe.update(mortgage.MortgageStep("fenix", "DOC-001", "GREEN", "e", environment="LAB", version="2.0.0"))
        with self.assertRaises(ValueError):
            pipe.update(mortgage.MortgageStep("fenix", "DOC-001", "GREEN", "e", environment="PROD", version="1.0.0"))
        pipe.update(mortgage.MortgageStep("fenix", "DOC-001", "GREEN", "e:prod", environment="PROD", version="2.0.0"))
        self.assertEqual("DOC-002", pipe.next_engine())


class Loop24EnterpriseTests(unittest.TestCase):
    def test_money_limit_converts_green_to_human_required(self):
        pipe = enterprise.EnterpriseOps("fenix")
        step = enterprise.EnterpriseStep("fenix", "HR-001", "GREEN", "e:hr", None, 10.0, 0.0)
        pipe.update(step)
        self.assertEqual("HUMAN_REQUIRED", pipe.status())
        self.assertEqual("HR-001", pipe.next_engine())

    def test_full_enterprise_sequence_green_at_zero_cost(self):
        pipe = enterprise.EnterpriseOps("fenix", "LAB", "1.0.0")
        for engine_id in enterprise.ENTERPRISE_SEQUENCE:
            pipe.update(enterprise.EnterpriseStep("fenix", engine_id, "GREEN", f"e:{engine_id}"))
        self.assertEqual("GREEN", pipe.status())
        self.assertIsNone(pipe.next_engine())

    def test_enterprise_rejects_cross_environment_or_version(self):
        pipe = enterprise.EnterpriseOps("fenix", "PROD", "2.0.0")
        with self.assertRaises(ValueError):
            pipe.update(enterprise.EnterpriseStep("fenix", "HR-001", "GREEN", "e", environment="LAB", version="2.0.0"))
        with self.assertRaises(ValueError):
            pipe.update(enterprise.EnterpriseStep("fenix", "HR-001", "GREEN", "e", environment="PROD", version="1.0.0"))
        pipe.update(enterprise.EnterpriseStep("fenix", "HR-001", "GREEN", "e:prod", environment="PROD", version="2.0.0"))
        self.assertEqual("HR-002", pipe.next_engine())


if __name__ == "__main__":
    unittest.main()
