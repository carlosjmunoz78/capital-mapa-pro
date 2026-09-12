import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "provider_restore_drill_contract.py"
spec = importlib.util.spec_from_file_location("provider_restore_drill_contract", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ProviderRestoreDrillContractTests(unittest.TestCase):
    def test_missing_evidence_fails_closed(self):
        result = module.assess_provider_restore_drill({"target_type": "ISOLATED_RESTORE"})
        self.assertFalse(result["restore_green"])
        self.assertFalse(result["provider_restore_ref_eligible"])
        self.assertTrue(result["missing"])
        self.assertFalse(result["prod_mutation_allowed"])

    def test_complete_isolated_restore_can_be_green(self):
        evidence = {"target_type": "ISOLATED_RESTORE"}
        for name in module.REQUIRED_EVIDENCE:
            evidence[name] = f"evidence:{name}"
        result = module.assess_provider_restore_drill(evidence)
        self.assertTrue(result["restore_green"])
        self.assertTrue(result["provider_restore_ref_eligible"])
        self.assertFalse(result["destructive_prod_restore_allowed"])

    def test_prod_restore_is_never_automatic(self):
        evidence = {"target_type": "PROD"}
        for name in module.REQUIRED_EVIDENCE:
            evidence[name] = f"evidence:{name}"
        result = module.assess_provider_restore_drill(evidence)
        self.assertFalse(result["restore_green"])
        self.assertEqual(result["human_reason"], "HIGH_RISK")
        self.assertFalse(result["prod_mutation_allowed"])


if __name__ == "__main__":
    unittest.main()
