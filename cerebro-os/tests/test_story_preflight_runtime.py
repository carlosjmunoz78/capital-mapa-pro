import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from story_preflight import StoryRequest, preflight_story


class StoryPreflightRuntimeTests(unittest.TestCase):
    def req(self, **changes):
        data = dict(company_id="fenix-capital", engine_id="SOC-STORY", environment="LAB", version="1.0.0", publication_id="P1", run_id="R1", asset_type="image", asset_url="https://example.invalid/a.jpg", width=1080, height=1920, qa_approved=True)
        data.update(changes)
        return StoryRequest(**data)

    def test_valid_vertical_story_remains_fail_closed_without_provider(self):
        result = preflight_story(self.req())
        self.assertEqual(result["preflight_status"], "READY_FOR_PROVIDER_OR_MANUAL_HANDOFF")
        self.assertEqual(result["status"], "BLOCKED_PROVIDER_NOT_CONNECTED")
        self.assertFalse(result["external_action_allowed"])

    def test_invalid_story_is_blocked(self):
        result = preflight_story(self.req(width=1920, height=1080))
        self.assertEqual(result["status"], "BLOCKED_PREFLIGHT")
        self.assertFalse(result["external_action_allowed"])

    def test_scope_is_enforced(self):
        with self.assertRaises(ValueError):
            preflight_story(self.req(environment="DEV"))


if __name__ == "__main__":
    unittest.main()
