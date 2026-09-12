import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from linkedin_caller_parity import LinkedInCutoverEvidence, assess_linkedin_cutover, inventory


class LinkedInCallerParityTests(unittest.TestCase):
    def test_inventory_has_all_four_prod_targets(self):
        self.assertEqual(
            inventory(),
            {
                5554207: "text",
                9528327: "link",
                9522428: "image",
                9410589: "video",
            },
        )

    def test_cutover_blocks_until_all_gates_green(self):
        out = assess_linkedin_cutover(
            LinkedInCutoverEvidence(
                scenario_id=9528327,
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
        out = assess_linkedin_cutover(
            LinkedInCutoverEvidence(
                scenario_id=9410589,
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

    def test_replay_fixture_matches_old_post_publish_contracts(self):
        fixture = ROOT / "runtime" / "fixtures" / "linkedin_old_new_replay.json"
        data = json.loads(fixture.read_text(encoding="utf-8"))
        self.assertEqual(len(data["scenarios"]), 4)
        by_id = {row["scenario_id"]: row for row in data["scenarios"]}
        self.assertEqual(by_id[9528327]["old_contract"]["receipt_status"], "LINKEDIN_ACCEPTED")
        self.assertEqual(by_id[9522428]["old_contract"]["idempotency_status"], "COMMITTED")
        self.assertEqual(by_id[9410589]["old_contract"]["override_status"], "CONSUMED")
        self.assertFalse(data["new_runtime_invariants"]["external_action_allowed"])
        self.assertFalse(data["new_runtime_invariants"]["retry_publish_allowed"])


if __name__ == "__main__":
    unittest.main()
