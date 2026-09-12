import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "family_evidence_matrix.py"
spec = importlib.util.spec_from_file_location("family_evidence_matrix", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FamilyEvidenceMatrixTests(unittest.TestCase):
    def test_known_families_are_structural_green(self):
        self.assertTrue(module.all_structural_green())
        self.assertEqual(set(module.FAMILIES), {"core_specific_replay", "factory_legacy", "recovery", "observability_cost"})

    def test_recovery_external_proofs_remain_pending(self):
        item = module.get_family("recovery")
        self.assertIn("PROVIDER_RESTORE_PROOF", item["external_gaps"])
        self.assertIn("PROD_ROLLBACK_REHEARSAL_PROOF", item["external_gaps"])
        self.assertFalse(item["prod_candidate"])

    def test_observability_never_invents_cost_or_telemetry(self):
        item = module.get_family("observability_cost")
        self.assertIn("ENGINE_COST_MEASUREMENT", item["external_gaps"])
        self.assertFalse(item["prod_candidate"])

    def test_external_queue_is_fail_closed(self):
        queue = module.external_evidence_queue()
        self.assertTrue(queue)
        for gap in queue:
            self.assertEqual(gap["status"], "EXTERNAL_PROOF_PENDING")
            self.assertTrue(gap["blocks_prod_candidate"])
            self.assertFalse(gap["automatic_external_action_allowed"])

    def test_global_prod_green_cannot_be_derived_from_structural_ci(self):
        self.assertFalse(module.global_prod_green())

    def test_unknown_family_fails_closed(self):
        with self.assertRaises(ValueError):
            module.get_family("unknown")


if __name__ == "__main__":
    unittest.main()
