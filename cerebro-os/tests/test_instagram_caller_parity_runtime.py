import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from instagram_caller_parity import InstagramCutoverEvidence, assess_instagram_cutover, inventory


class InstagramCallerParityTests(unittest.TestCase):
    def test_inventory_exact(self):
        self.assertEqual(inventory(), {9534139: "image", 9534084: "carousel", 9534087: "reel"})

    def test_all_green_still_requires_explicit_human_and_never_delete(self):
        result = assess_instagram_cutover(InstagramCutoverEvidence(
            9534139, True, True, True, True, True, True
        ))
        self.assertTrue(result["cutover_ready"])
        self.assertTrue(result["deactivate_old_allowed"])
        self.assertFalse(result["delete_old_allowed"])
        self.assertFalse(result["external_action_allowed"])
        self.assertEqual(result["human_reason"], "SIGNATURE_REQUIRED")

    def test_every_missing_gate_blocks_cutover(self):
        fields = ["caller_map_complete", "replay_parity_green", "rollback_proven", "target_runtime_live", "old_preserved", "external_action_safe"]
        for field in fields:
            kwargs = dict(scenario_id=9534084, caller_map_complete=True, replay_parity_green=True,
                          rollback_proven=True, target_runtime_live=True, old_preserved=True,
                          external_action_safe=True)
            kwargs[field] = False
            result = assess_instagram_cutover(InstagramCutoverEvidence(**kwargs))
            self.assertFalse(result["cutover_ready"], field)
            self.assertFalse(result["deactivate_old_allowed"], field)

    def test_unknown_target_rejected(self):
        with self.assertRaises(ValueError):
            assess_instagram_cutover(InstagramCutoverEvidence(1, True, True, True, True, True, True))


if __name__ == "__main__":
    unittest.main()
