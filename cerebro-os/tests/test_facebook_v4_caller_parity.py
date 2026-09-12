import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from facebook_v4_caller_parity import (  # noqa: E402
    LIVE_V4_TARGETS,
    evaluate_v4_target_cutover,
    safety_replay_fixture,
)


class FacebookV4CallerParityTests(unittest.TestCase):
    def test_inventory_is_exact(self):
        self.assertEqual(
            set(LIVE_V4_TARGETS),
            {9533715, 9533724, 9533532, 9533564, 9533967, 9533972, 9533976},
        )
        self.assertEqual(LIVE_V4_TARGETS[9533564].finalizer_scenario_id, 9533584)
        self.assertEqual(LIVE_V4_TARGETS[9533972].finalizer_scenario_id, 9533974)
        self.assertFalse(LIVE_V4_TARGETS[9533976].mutates_facebook)

    def test_old_cannot_deactivate_if_any_gate_missing(self):
        names = [
            "caller_map_complete",
            "replay_parity_green",
            "rollback_proven",
            "runtime_live",
            "old_preserved",
            "external_action_safe",
        ]
        for missing in names:
            args = {name: True for name in names}
            args[missing] = False
            out = evaluate_v4_target_cutover(scenario_id=9533715, **args)
            self.assertFalse(out["cutover_ready"], missing)
            self.assertFalse(out["deactivate_old_allowed"], missing)
            self.assertFalse(out["delete_old_allowed"], missing)

    def test_mutator_ready_still_requires_signature_and_never_autoexecutes(self):
        out = evaluate_v4_target_cutover(
            scenario_id=9533715,
            caller_map_complete=True,
            replay_parity_green=True,
            rollback_proven=True,
            runtime_live=True,
            old_preserved=True,
            external_action_safe=True,
        )
        self.assertTrue(out["cutover_ready"])
        self.assertTrue(out["requires_human"])
        self.assertEqual(out["human_reason"], "SIGNATURE_REQUIRED")
        self.assertFalse(out["external_action_allowed"])
        self.assertFalse(out["delete_old_allowed"])

    def test_story_ready_does_not_require_signature(self):
        out = evaluate_v4_target_cutover(
            scenario_id=9533976,
            caller_map_complete=True,
            replay_parity_green=True,
            rollback_proven=True,
            runtime_live=True,
            old_preserved=True,
            external_action_safe=True,
        )
        self.assertTrue(out["cutover_ready"])
        self.assertFalse(out["requires_human"])
        self.assertIsNone(out["human_reason"])

    def test_processing_cannot_commit_or_open_analytics(self):
        bad_commit = safety_replay_fixture(
            scenario_id=9533564,
            platform_state="UPLOAD_ACCEPTED",
            idempotency_state="COMMITTED",
            analytics_windows_ready=False,
            retry_publish_allowed=False,
        )
        self.assertFalse(bad_commit["parity_green"])

        bad_analytics = safety_replay_fixture(
            scenario_id=9533972,
            platform_state="UPLOAD_ACCEPTED",
            idempotency_state="PENDING_PLATFORM_CONFIRMATION",
            analytics_windows_ready=True,
            retry_publish_allowed=False,
        )
        self.assertFalse(bad_analytics["parity_green"])

    def test_safe_published_fixture_is_green(self):
        out = safety_replay_fixture(
            scenario_id=9533532,
            platform_state="PUBLISHED",
            idempotency_state="COMMITTED",
            analytics_windows_ready=True,
            retry_publish_allowed=False,
        )
        self.assertTrue(out["parity_green"])
        self.assertFalse(out["external_action_allowed"])

    def test_retry_publish_is_always_red(self):
        out = safety_replay_fixture(
            scenario_id=9533564,
            platform_state="UPLOAD_ACCEPTED",
            idempotency_state="PENDING_PLATFORM_CONFIRMATION",
            analytics_windows_ready=False,
            retry_publish_allowed=True,
        )
        self.assertFalse(out["parity_green"])


if __name__ == "__main__":
    unittest.main()
