import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from youtube_caller_parity import YouTubeCutoverEvidence, assess_youtube_cutover, inventory


class YouTubeCallerParityTests(unittest.TestCase):
    def test_inventory_has_both_prod_upload_targets(self):
        self.assertEqual(inventory(), {9537699: "short_private", 9537702: "long_private"})

    def test_cutover_blocks_until_all_gates_green(self):
        out = assess_youtube_cutover(
            YouTubeCutoverEvidence(
                scenario_id=9537699,
                caller_map_complete=True,
                replay_parity_green=True,
                rollback_proven=True,
                target_runtime_live=False,
                old_preserved=True,
                external_action_safe=False,
            )
        )
        self.assertFalse(out["cutover_ready"])
        self.assertIn("TARGET_RUNTIME_NOT_LIVE", out["blockers"])
        self.assertIn("EXTERNAL_ACTION_NOT_SAFE", out["blockers"])
        self.assertFalse(out["deactivate_old_allowed"])
        self.assertFalse(out["delete_old_allowed"])

    def test_all_gates_green_still_never_autoexecutes(self):
        out = assess_youtube_cutover(
            YouTubeCutoverEvidence(
                scenario_id=9537702,
                caller_map_complete=True,
                replay_parity_green=True,
                rollback_proven=True,
                target_runtime_live=True,
                old_preserved=True,
                external_action_safe=True,
            )
        )
        self.assertTrue(out["cutover_ready"])
        self.assertTrue(out["deactivate_old_allowed"])
        self.assertFalse(out["delete_old_allowed"])
        self.assertFalse(out["external_action_allowed"])
        self.assertEqual(out["human_reason"], "SIGNATURE_REQUIRED")

    def test_replay_fixture_matches_make_private_upload_contracts(self):
        fixture = ROOT / "runtime" / "fixtures" / "youtube_old_new_replay.json"
        data = json.loads(fixture.read_text(encoding="utf-8"))
        self.assertEqual(len(data["scenarios"]), 2)
        by_id = {row["scenario_id"]: row for row in data["scenarios"]}
        self.assertEqual(by_id[9537699]["old_contract"]["privacy_status"], "private")
        self.assertEqual(by_id[9537699]["old_contract"]["duration_max_seconds"], 180)
        self.assertEqual(by_id[9537702]["old_contract"]["duration_min_seconds"], 181)
        self.assertEqual(by_id[9537702]["old_contract"]["notion_state"], "Incidencia")
        self.assertFalse(data["new_runtime_invariants"]["external_action_allowed"])
        self.assertFalse(data["new_runtime_invariants"]["retry_upload_allowed"])


if __name__ == "__main__":
    unittest.main()
