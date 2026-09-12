import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from facebook_v4_caller_parity import LIVE_V4_TARGETS, safety_replay_fixture  # noqa: E402


class FacebookV4ReplayFixturesTests(unittest.TestCase):
    def test_every_live_v4_target_has_fixture_and_replay_is_safe(self):
        fixture_path = ROOT / "runtime" / "fixtures" / "facebook_v4_old_new_replay.json"
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        rows = payload["fixtures"]
        self.assertEqual({row["scenario_id"] for row in rows}, set(LIVE_V4_TARGETS))

        for row in rows:
            out = safety_replay_fixture(
                scenario_id=row["scenario_id"],
                platform_state=row["platform_state"],
                idempotency_state=row["idempotency_state"],
                analytics_windows_ready=row["analytics_windows_ready"],
                retry_publish_allowed=row["retry_publish_allowed"],
            )
            self.assertTrue(out["parity_green"], row)
            self.assertFalse(out["external_action_allowed"], row)
            self.assertFalse(out["delete_old_allowed"], row)

    def test_processing_formats_have_finalizers_and_never_retry_upload(self):
        fixture_path = ROOT / "runtime" / "fixtures" / "facebook_v4_old_new_replay.json"
        rows = json.loads(fixture_path.read_text(encoding="utf-8"))["fixtures"]
        processing = [row for row in rows if row["platform_state"] == "UPLOAD_ACCEPTED"]
        self.assertEqual({row["scenario_id"] for row in processing}, {9533564, 9533972})
        for row in processing:
            self.assertIn("finalizer_scenario_id", row)
            self.assertFalse(row["retry_publish_allowed"])
            self.assertFalse(row["analytics_windows_ready"])
            self.assertEqual(row["idempotency_state"], "PENDING_PLATFORM_CONFIRMATION")


if __name__ == "__main__":
    unittest.main()
