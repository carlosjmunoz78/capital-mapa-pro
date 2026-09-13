import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "observability_prod_parallel_wiring_gate_20260913.py"
spec = importlib.util.spec_from_file_location("observability_prod_parallel_wiring_gate_20260913", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ObservabilityProdParallelWiringGateTests(unittest.TestCase):
    def test_current_evidence_is_ready_but_prod_stays_disabled(self):
        result = module.assess_wiring_gate(module.current_evidence_snapshot())
        self.assertTrue(result["ready_for_controlled_prod_wiring"])
        self.assertEqual(result["missing"], ())
        self.assertFalse(result["prod_mirroring_enabled"])
        self.assertFalse(result["automatic_prod_activation_allowed"])
        self.assertFalse(result["legacy_tables_modified"])
        self.assertEqual(result["rollback_action"], "disable_parallel_mirror_only")

    def test_missing_evidence_fails_closed(self):
        evidence = module.current_evidence_snapshot()
        evidence["incident_fixture_nonprod_green"] = False
        result = module.assess_wiring_gate(evidence)
        self.assertFalse(result["ready_for_controlled_prod_wiring"])
        self.assertIn("incident_fixture_nonprod_green", result["missing"])
        self.assertEqual(result["status"], "PROD_WIRING_EVIDENCE_PENDING")


if __name__ == "__main__":
    unittest.main()
