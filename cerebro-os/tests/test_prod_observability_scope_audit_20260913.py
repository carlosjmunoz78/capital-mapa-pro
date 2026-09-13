import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "prod_observability_scope_audit_20260913.py"
spec = importlib.util.spec_from_file_location("prod_observability_scope_audit", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class ProdObservabilityScopeAuditTests(unittest.TestCase):
    def test_live_operational_tables_and_counts_are_locked(self):
        result = module.assess()
        self.assertEqual(result["schema"], "fenix_prod")
        self.assertEqual(result["table_count"], 6)
        self.assertEqual(result["total_rows_observed"], 103)
        self.assertTrue(result["live_operational_evidence_present"])

    def test_existing_prod_tables_do_not_fake_per_engine_scope(self):
        result = module.assess()
        self.assertEqual(result["tables_with_full_engine_scope"], ())
        self.assertFalse(result["per_engine_prod_coverage_proven"])
        self.assertTrue(result["shared_177_lab_scope_contract_remains_separate"])
        self.assertFalse(result["schema_mutation_performed"])
        self.assertFalse(result["prod_observability_green"])


if __name__ == "__main__":
    unittest.main()
