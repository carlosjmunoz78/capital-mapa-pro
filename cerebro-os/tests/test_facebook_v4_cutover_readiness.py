import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from facebook_v4_cutover_readiness import ComponentEvidence, V4_COMPONENTS, assess_component_cutover, summarize_v4_readiness


def evidence(scenario_id, **kwargs):
    base = dict(
        scenario_id=scenario_id,
        caller_map_green=True,
        input_contract_green=True,
        replay_parity_green=True,
        rollback_ci_green=True,
        runtime_code_ci_green=True,
        target_runtime_live=False,
        old_preserved=True,
        external_action_safety_green=True,
    )
    base.update(kwargs)
    return ComponentEvidence(**base)


class FacebookV4CutoverReadinessTest(unittest.TestCase):
    def test_lab_ci_ready_but_live_pending(self):
        out = assess_component_cutover(evidence(9533715))
        self.assertTrue(out["lab_ci_ready"])
        self.assertFalse(out["cutover_ready"])
        self.assertEqual(out["status"], "LAB_CI_READY_RUNTIME_LIVE_PENDING")
        self.assertIn("target_runtime_live", out["blockers"])
        self.assertFalse(out["deactivate_old_allowed"])
        self.assertFalse(out["delete_old_allowed"])

    def test_mutator_live_ready_still_human_gated(self):
        out = assess_component_cutover(evidence(9533715, target_runtime_live=True))
        self.assertTrue(out["cutover_ready"])
        self.assertEqual(out["status"], "CUTOVER_READY_HUMAN_GATE")
        self.assertEqual(out["human_reason"], "SIGNATURE_REQUIRED")
        self.assertFalse(out["external_action_allowed"])
        self.assertFalse(out["deactivate_old_allowed"])

    def test_non_mutating_story_can_be_cutover_ready(self):
        out = assess_component_cutover(evidence(9533976, target_runtime_live=True))
        self.assertEqual(out["status"], "CUTOVER_READY")
        self.assertTrue(out["deactivate_old_allowed"])
        self.assertFalse(out["delete_old_allowed"])

    def test_missing_replay_breaks_lab_ci_readiness(self):
        out = assess_component_cutover(evidence(9533974, replay_parity_green=False))
        self.assertFalse(out["lab_ci_ready"])
        self.assertEqual(out["status"], "NOT_CUTOVER_READY")

    def test_summary_requires_complete_inventory(self):
        with self.assertRaises(ValueError):
            summarize_v4_readiness([evidence(9533715)])

    def test_complete_inventory_all_lab_ci_ready_and_live_pending(self):
        items = [evidence(sid) for sid in V4_COMPONENTS]
        out = summarize_v4_readiness(items)
        self.assertEqual(out["total"], 9)
        self.assertEqual(out["lab_ci_ready"], 9)
        self.assertEqual(out["runtime_live_pending"], 9)
        self.assertEqual(out["cutover_ready"], 0)
        self.assertFalse(out["delete_old_allowed"])


if __name__ == "__main__":
    unittest.main()
