import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from cutover_gate import CutoverDecision, CutoverEvidence, assess_cutover, rollback_required


class CutoverGateTests(unittest.TestCase):
    def base(self, **overrides):
        data = dict(
            scenario_id=9530582,
            replacement_runtime="facebook_link_preflight.py",
            caller_map_complete=True,
            replay_parity_green=True,
            rollback_proven=True,
            target_runtime_live=True,
            old_preserved=True,
            external_action_safe=True,
        )
        data.update(overrides)
        return CutoverEvidence(**data)

    def test_all_gates_required_for_ready(self):
        result = assess_cutover(self.base())
        self.assertEqual(result.decision, CutoverDecision.READY)
        self.assertEqual(result.blockers, ())

    def test_each_missing_gate_blocks(self):
        fields = (
            "caller_map_complete",
            "replay_parity_green",
            "rollback_proven",
            "target_runtime_live",
            "old_preserved",
            "external_action_safe",
        )
        for field in fields:
            with self.subTest(field=field):
                result = assess_cutover(self.base(**{field: False}))
                self.assertEqual(result.decision, CutoverDecision.BLOCKED)
                self.assertTrue(result.blockers)

    def test_rollback_triggers_fail_closed(self):
        self.assertTrue(rollback_required(new_health_green=False, parity_green=True, unexpected_external_action=False))
        self.assertTrue(rollback_required(new_health_green=True, parity_green=False, unexpected_external_action=False))
        self.assertTrue(rollback_required(new_health_green=True, parity_green=True, unexpected_external_action=True))
        self.assertFalse(rollback_required(new_health_green=True, parity_green=True, unexpected_external_action=False))


if __name__ == "__main__":
    unittest.main()
