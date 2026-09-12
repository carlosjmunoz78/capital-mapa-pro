import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from facebook_v4_target_registry import (
    MUTATING_TARGET_IDS,
    NON_MUTATING_TARGET_IDS,
    TARGETS,
    evaluate_target_cutover,
    get_target,
)


class FacebookV4TargetRegistryTests(unittest.TestCase):
    def test_exact_v4_target_inventory(self):
        self.assertEqual(
            set(TARGETS),
            {9533715, 9533724, 9533532, 9533564, 9533967, 9533972, 9533976},
        )
        self.assertEqual(
            MUTATING_TARGET_IDS,
            frozenset({9533715, 9533724, 9533532, 9533564, 9533967, 9533972}),
        )
        self.assertEqual(NON_MUTATING_TARGET_IDS, frozenset({9533976}))

    def test_video_targets_preserve_finalizers(self):
        self.assertEqual(get_target(9533564).finalizer_scenario_id, 9533584)
        self.assertEqual(get_target(9533972).finalizer_scenario_id, 9533974)

    def test_unknown_target_fails_closed(self):
        with self.assertRaises(ValueError):
            get_target(9999999)

    def test_missing_any_cutover_gate_blocks_deactivation(self):
        gate_names = (
            "caller_map_complete",
            "replay_parity_green",
            "rollback_proven",
            "runtime_live",
            "old_preserved",
            "external_action_safety_green",
        )
        for missing in gate_names:
            kwargs = {name: True for name in gate_names}
            kwargs[missing] = False
            out = evaluate_target_cutover(scenario_id=9533715, **kwargs)
            self.assertFalse(out["cutover_ready"], missing)
            self.assertFalse(out["deactivate_old_allowed"], missing)
            self.assertFalse(out["delete_old_allowed"], missing)
            self.assertFalse(out["external_action_allowed"], missing)

    def test_all_gates_still_require_explicit_human_for_mutator(self):
        out = evaluate_target_cutover(
            scenario_id=9533532,
            caller_map_complete=True,
            replay_parity_green=True,
            rollback_proven=True,
            runtime_live=True,
            old_preserved=True,
            external_action_safety_green=True,
        )
        self.assertTrue(out["cutover_ready"])
        self.assertTrue(out["deactivate_old_allowed"])
        self.assertFalse(out["delete_old_allowed"])
        self.assertFalse(out["external_action_allowed"])
        self.assertTrue(out["requires_human"])
        self.assertEqual(out["human_reason"], "SIGNATURE_REQUIRED")

    def test_story_is_non_mutating_but_old_delete_remains_forbidden(self):
        out = evaluate_target_cutover(
            scenario_id=9533976,
            caller_map_complete=True,
            replay_parity_green=True,
            rollback_proven=True,
            runtime_live=True,
            old_preserved=True,
            external_action_safety_green=True,
        )
        self.assertTrue(out["cutover_ready"])
        self.assertFalse(out["mutates_facebook"])
        self.assertFalse(out["requires_human"])
        self.assertFalse(out["delete_old_allowed"])


if __name__ == "__main__":
    unittest.main()
