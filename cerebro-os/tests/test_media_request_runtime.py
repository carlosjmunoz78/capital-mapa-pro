import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from media_request import MediaRequest, plan_media_request


class MediaRequestRuntimeTests(unittest.TestCase):
    def req(self, **changes):
        data = dict(company_id="fenix-capital", engine_id="FACT-MEDIA", environment="LAB", version="1.0.0", run_id="R1", production_order_id="PO1", network="Instagram", format="REEL", image_count=1, needs_voice=True, needs_presenter=False, needs_video=True, needs_editing=True, priority="normal")
        data.update(changes)
        return MediaRequest(**data)

    def test_paid_provider_absent_blocks_cost_consumption(self):
        result = plan_media_request(self.req(), paid_provider_connected=False)
        self.assertEqual(result["status"], "BLOCKED_BY_COST")
        self.assertEqual(result["provider_status"], "QUEUED_PROVIDERS_NOT_CONNECTED")
        self.assertFalse(result["external_action_allowed"])

    def test_no_provider_need_is_runtime_ready_but_non_executing(self):
        result = plan_media_request(self.req(image_count=0, needs_voice=False, needs_video=False, needs_editing=False), paid_provider_connected=False)
        self.assertEqual(result["status"], "READY_FOR_RUNTIME")
        self.assertFalse(result["external_action_allowed"])

    def test_invalid_scope_fails(self):
        with self.assertRaises(ValueError):
            plan_media_request(self.req(environment="DEV"))


if __name__ == "__main__":
    unittest.main()
