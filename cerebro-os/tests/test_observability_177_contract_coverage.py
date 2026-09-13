import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "observability_177_contract_coverage.py"
spec = importlib.util.spec_from_file_location("observability_177_contract_coverage", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class Observability177ContractCoverageTests(unittest.TestCase):
    def test_exact_177_unique_engines_inherit_shared_contract(self):
        result = module.assess_observability_contract_coverage()
        self.assertEqual(result["engine_count"], 177)
        self.assertEqual(result["unique_engine_count"], 177)
        self.assertTrue(result["all_engines_inherit_shared_runtime_contract"])
        self.assertTrue(result["structural_logs_contract_177_green"])
        self.assertTrue(result["structural_cost_field_177_green"])

    def test_live_evidence_is_not_faked(self):
        result = module.assess_observability_contract_coverage()
        self.assertFalse(result["live_metrics_complete"])
        self.assertFalse(result["live_incident_coverage_complete"])
        self.assertFalse(result["monthly_provider_cost_measured"])
        self.assertFalse(result["prod_candidate_allowed"])

    def test_multicompany_scope_is_mandatory(self):
        self.assertEqual(
            module.REQUIRED_SCOPE_FIELDS,
            ("company_id", "engine_id", "environment", "version"),
        )


if __name__ == "__main__":
    unittest.main()
