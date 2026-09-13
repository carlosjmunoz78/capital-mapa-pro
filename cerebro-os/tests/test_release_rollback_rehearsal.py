import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "release_rollback_rehearsal.py"
MODULE_NAME = "release_rollback_rehearsal"
spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[MODULE_NAME] = module
spec.loader.exec_module(module)


class ReleaseRollbackRehearsalTests(unittest.TestCase):
    def test_green_requires_pinned_refs_and_all_validations(self):
        evidence = module.RehearsalEvidence(
            current_ref="current",
            target_ref="known-good",
            build_valid=True,
            contract_valid=True,
            smoke_valid=True,
        )
        result = module.assess_release_rollback_rehearsal(evidence)
        self.assertTrue(result["rollback_rehearsal_green"])
        self.assertFalse(result["external_mutation_allowed"])
        self.assertFalse(result["automatic_promotion_allowed"])

    def test_external_mutation_keeps_gate_red(self):
        evidence = module.RehearsalEvidence(
            current_ref="current",
            target_ref="known-good",
            build_valid=True,
            contract_valid=True,
            smoke_valid=True,
            external_mutation=True,
        )
        result = module.assess_release_rollback_rehearsal(evidence)
        self.assertFalse(result["rollback_rehearsal_green"])
        self.assertEqual(result["human_reason"], "HIGH_RISK")

    def test_missing_ref_is_rejected(self):
        with self.assertRaises(ValueError):
            module.assess_release_rollback_rehearsal(module.RehearsalEvidence("", "target"))


if __name__ == "__main__":
    unittest.main()
