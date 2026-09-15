import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from advisory.global_autonomy_readiness import (  # noqa: E402
    GLOBAL_PROMOTION_GATES,
    evaluate_global_autonomy_readiness,
)


class AdvisoryGlobalAutonomyReadinessTests(unittest.TestCase):
    def test_missing_evidence_fails_closed_and_never_promotes(self):
        verdict = evaluate_global_autonomy_readiness({})
        self.assertEqual(verdict.verdict, "BLOCKED")
        self.assertEqual(verdict.blockers, GLOBAL_PROMOTION_GATES)
        self.assertFalse(verdict.capability_green_global)
        self.assertFalse(verdict.autonomy_green)
        self.assertFalse(verdict.prod_enabled)

    def test_partial_evidence_cannot_false_green(self):
        evidence = {gate: True for gate in GLOBAL_PROMOTION_GATES}
        evidence["security_gate_green"] = False
        verdict = evaluate_global_autonomy_readiness(evidence)
        self.assertEqual(verdict.verdict, "BLOCKED")
        self.assertEqual(verdict.blockers, ("security_gate_green",))
        self.assertFalse(verdict.prod_enabled)

    def test_all_evidence_only_opens_explicit_promotion_gate(self):
        verdict = evaluate_global_autonomy_readiness(
            {gate: True for gate in GLOBAL_PROMOTION_GATES}
        )
        self.assertEqual(verdict.verdict, "READY_FOR_EXPLICIT_PROD_PROMOTION")
        self.assertEqual(verdict.blockers, ())
        self.assertFalse(verdict.capability_green_global)
        self.assertFalse(verdict.autonomy_green)
        self.assertFalse(verdict.prod_enabled)

    def test_gate_inventory_is_exact_and_stable(self):
        self.assertEqual(len(GLOBAL_PROMOTION_GATES), 9)
        self.assertEqual(len(set(GLOBAL_PROMOTION_GATES)), 9)
        self.assertIn("prod_promotion_explicitly_authorized", GLOBAL_PROMOTION_GATES)
        self.assertIn("legal_signature_policy_green", GLOBAL_PROMOTION_GATES)


if __name__ == "__main__":
    unittest.main()
