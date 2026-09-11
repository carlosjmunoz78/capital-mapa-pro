import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

recovery = load("cerebro_recovery_verify", "resilience/verification.py")
versioning = load("cerebro_versioning", "versioning/compatibility.py")
data = load("cerebro_data_contracts", "data/contracts.py")
onboarding = load("cerebro_onboarding", "onboarding/plan.py")

class ResilienceVersioningDataOnboardingTests(unittest.TestCase):
    def test_recovery_needs_all_three_verified_and_canonical_scope(self):
        with self.assertRaises(ValueError):
            recovery.RecoveryEvidence("b", "r", "rb", True, True, True).validate()
        ev = recovery.RecoveryEvidence("b", "r", "rb", True, True, False, "fenix", "FACT-001", "LAB", "1.0.0")
        self.assertFalse(ev.green)
        self.assertTrue(recovery.RecoveryEvidence("b", "r", "rb", True, True, True, "fenix", "FACT-001", "LAB", "1.0.0").green)
        with self.assertRaises(ValueError):
            recovery.RecoveryEvidence("b", "r", "rb", True, True, True, "fenix", "FACT-001", "INVALID", "1.0.0").validate()

    def test_version_contract_is_tenant_scoped_and_same_major_only(self):
        with self.assertRaises(ValueError):
            versioning.VersionContract("FACT-001", "1.2.0", "1.0.0", "LAB").validate()
        contract = versioning.VersionContract("FACT-001", "1.2.0", "1.0.0", "LAB", "fenix")
        self.assertTrue(contract.compatible_with("1.1.0"))
        self.assertFalse(contract.compatible_with("0.9.9"))
        self.assertFalse(contract.compatible_with("2.0.0"))
        with self.assertRaises(ValueError):
            versioning.VersionContract("FACT-001", "1.2.0", "2.0.0", "LAB", "fenix").validate()
        with self.assertRaises(ValueError):
            versioning.VersionContract("FACT-001", "1.2.0", "1.3.0", "LAB", "fenix").validate()

    def test_data_contract_requires_consumer_and_company_scope(self):
        unsafe = data.DataContract("DATA-001", "engine-event", "1.0.0", True, "schemas/event.json", "EVT-001", ("AUD-001",))
        unsafe.validate()
        self.assertFalse(unsafe.safe_for_multicompany())
        contract = data.DataContract(
            "DATA-001", "engine-event", "1.0.0", True, "schemas/event.json", "EVT-001", ("AUD-001",),
            ("company_id", "engine_id", "environment", "version"),
        )
        contract.validate()
        self.assertTrue(contract.safe_for_multicompany())

    def test_onboarding_order_completion_and_scope(self):
        plan = onboarding.CompanyOnboardingPlan("fenix-capital", environment="PROD", version="2.0.0")
        self.assertEqual(plan.next_phase(()), "company_registry")
        self.assertIsNone(plan.next_phase(plan.phases))
        with self.assertRaises(ValueError):
            onboarding.CompanyOnboardingPlan("fenix-capital", environment="INVALID").validate()
        with self.assertRaises(ValueError):
            onboarding.CompanyOnboardingPlan("fenix-capital", version="").validate()
        with self.assertRaises(ValueError):
            plan.next_phase(("unknown_phase",))

if __name__ == "__main__":
    unittest.main()
