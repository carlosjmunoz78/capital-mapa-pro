import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from advisory.preprod_readiness import DEFAULT_READINESS, REQUIRED_GATES, preprod_readiness_report


class AdvisoryPreprodReadinessTests(unittest.TestCase):
    def test_all_required_gates_are_accounted_for(self):
        self.assertEqual(tuple(DEFAULT_READINESS.gates.keys()), REQUIRED_GATES)
        self.assertEqual(DEFAULT_READINESS.missing, ())
        self.assertTrue(DEFAULT_READINESS.ready_for_preprod_candidate)

    def test_candidate_does_not_enable_preprod_or_prod(self):
        report = preprod_readiness_report()
        self.assertTrue(report["ready_for_preprod_candidate"])
        self.assertFalse(report["preprod_enabled"])
        self.assertFalse(report["autonomy_green"])
        self.assertFalse(report["prod_enabled"])
        self.assertFalse(report["app_crm_prod_touched"])

    def test_zero_additional_cost_policy_is_preserved(self):
        self.assertEqual(preprod_readiness_report()["cost_policy"], "0 EUR additional by default")

    def test_missing_gate_fails_closed(self):
        gates = dict(DEFAULT_READINESS.gates)
        gates["backup_rebuild_contract"] = False
        from advisory.preprod_readiness import PreprodReadiness
        candidate = PreprodReadiness(gates=gates)
        self.assertFalse(candidate.ready_for_preprod_candidate)
        self.assertEqual(candidate.missing, ("backup_rebuild_contract",))


if __name__ == "__main__":
    unittest.main()
