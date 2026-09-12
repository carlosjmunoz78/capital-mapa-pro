import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "prod_observability_live_evidence.py"
spec = importlib.util.spec_from_file_location("prod_observability_live_evidence", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ProdObservabilityLiveEvidenceTests(unittest.TestCase):
    def test_live_read_only_observability_tables_are_present(self):
        result = module.assess_prod_observability()
        self.assertTrue(result["read_only_live_verified"])
        self.assertTrue(result["logs_evidence_present"])
        self.assertTrue(result["metrics_reporting_evidence_present"])
        self.assertTrue(result["engine_run_evidence_present"])
        self.assertTrue(result["incident_state_evidence_present"])

    def test_partial_evidence_never_becomes_full_green(self):
        result = module.assess_prod_observability()
        self.assertIsNone(result["monthly_cost_eur"])
        self.assertFalse(result["cost_measured_green"])
        self.assertFalse(result["per_engine_coverage_proven"])
        self.assertFalse(result["observability_green"])
        self.assertFalse(result["prod_candidate_allowed"])
        self.assertFalse(result["prod_mutation_performed"])

    def test_exact_snapshot_is_locked(self):
        self.assertEqual(module.PROD_TABLE_EVIDENCE["activity_log"]["estimated_rows"], 24)
        self.assertEqual(module.PROD_TABLE_EVIDENCE["document_intelligence_runs"]["estimated_rows"], 66)
        self.assertEqual(module.PROD_TABLE_EVIDENCE["daily_report_snapshots"]["estimated_rows"], 2)


if __name__ == "__main__":
    unittest.main()
