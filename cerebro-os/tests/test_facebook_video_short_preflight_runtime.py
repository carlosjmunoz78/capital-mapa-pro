import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from facebook_video_short_preflight import FacebookVideoShortEvidenceRequest, capture_facebook_video_short_evidence


def req(**changes):
    data = dict(
        company_id="fenix-capital", engine_id="SOC-PREFLIGHT", environment="TEST", version="1.0.0",
        publication_id="PUB1", production_order_id="OP1", calendar_item_id="CAL1", programming_id="PRG1",
        asset_id="ASSET1", run_id="TEST-FB-VIDEO-SHORT-CANON-001", asset_url="https://example.com/video.mp4",
        http_status=200, publication_snapshot="{}", production_snapshot="{}", calendar_snapshot="{}",
        programming_snapshot="{}", asset_snapshot="{}",
    )
    data.update(changes)
    return FacebookVideoShortEvidenceRequest(**data)


class FacebookVideoShortPreflightRuntimeTests(unittest.TestCase):
    def test_preserves_old_evidence_capture_contract(self):
        result = capture_facebook_video_short_evidence(req())
        self.assertEqual(result["status"], "DIRECT_EVIDENCE_CAPTURED")
        self.assertEqual(result["difference"], "PENDING_EVIDENCE_EVALUATION")
        self.assertEqual(result["platform_state"], "FACEBOOK_NOT_CALLED")
        self.assertTrue(result["requires_human"])
        self.assertFalse(result["external_action_allowed"])

    def test_unreachable_asset_stays_fail_closed(self):
        result = capture_facebook_video_short_evidence(req(http_status=404))
        self.assertEqual(result["status"], "EVIDENCE_CAPTURED_ASSET_UNREACHABLE")
        self.assertTrue(result["requires_human"])
        self.assertFalse(result["external_action_allowed"])

    def test_invalid_environment_rejected(self):
        with self.assertRaises(ValueError):
            capture_facebook_video_short_evidence(req(environment="DEV"))

    def test_missing_snapshot_rejected(self):
        with self.assertRaises(ValueError):
            capture_facebook_video_short_evidence(req(asset_snapshot=""))


if __name__ == "__main__":
    unittest.main()
