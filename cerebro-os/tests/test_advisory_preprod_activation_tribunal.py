import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from advisory.preprod_activation_tribunal import (
    REQUIRED_GATES,
    canonical_preprod_activation_gates,
    evaluate_preprod_activation,
)


class AdvisoryPreprodActivationTribunalTests(unittest.TestCase):
    def test_all_gates_yield_ready_but_do_not_activate(self):
        verdict = evaluate_preprod_activation(canonical_preprod_activation_gates())
        self.assertEqual(verdict.verdict, "READY_FOR_PREPROD_ACTIVATION")
        self.assertEqual(verdict.missing_gates, ())
        self.assertFalse(verdict.preprod_enabled)
        self.assertFalse(verdict.capability_green_global)
        self.assertFalse(verdict.autonomy_green)
        self.assertFalse(verdict.prod_enabled)

    def test_each_missing_gate_blocks(self):
        for missing_gate in REQUIRED_GATES:
            gates = canonical_preprod_activation_gates()
            gates[missing_gate] = False
            verdict = evaluate_preprod_activation(gates)
            self.assertEqual(verdict.verdict, "BLOCKED")
            self.assertIn(missing_gate, verdict.missing_gates)
            self.assertFalse(verdict.preprod_enabled)
            self.assertFalse(verdict.prod_enabled)

    def test_unknown_or_absent_gate_cannot_false_green(self):
        verdict = evaluate_preprod_activation({})
        self.assertEqual(verdict.verdict, "BLOCKED")
        self.assertEqual(set(verdict.missing_gates), set(REQUIRED_GATES))


if __name__ == "__main__":
    unittest.main()
