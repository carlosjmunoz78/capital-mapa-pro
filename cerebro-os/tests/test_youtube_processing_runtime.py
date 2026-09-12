import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from youtube_processing import YouTubeProcessingObservation, classify_processing


class YouTubeProcessingRuntimeTests(unittest.TestCase):
    def obs(self, **changes):
        data = dict(
            company_id="fenix-capital",
            engine_id="SOCIAL-PUBLISH",
            environment="PROD",
            version="1.0.0",
            run_id="run-1",
            publication_id="pub-1",
            video_id="yt-1",
            http_status=200,
            upload_status="uploaded",
            qa_approved=False,
        )
        data.update(changes)
        return YouTubeProcessingObservation(**data)

    def test_old_contract_processing_read_is_preserved(self):
        result = classify_processing(self.obs())
        self.assertEqual(result["status"], "PROCESSING_READ")
        self.assertEqual(result["network"], "YouTube")
        self.assertEqual(result["operation_type"], "verify_video_processing")
        self.assertEqual(result["platform_state"], "uploaded")
        self.assertTrue(result["requires_human"])
        self.assertFalse(result["external_action_allowed"])

    def test_ready_and_qa_only_opens_next_gate_not_external_execution(self):
        result = classify_processing(self.obs(upload_status="processed", qa_approved=True))
        self.assertTrue(result["ready_for_next_gate"])
        self.assertFalse(result["requires_human"])
        self.assertFalse(result["external_action_allowed"])
        self.assertFalse(result["connector_action_required"])

    def test_bad_http_or_missing_qa_stays_fail_closed(self):
        bad_http = classify_processing(self.obs(http_status=503, upload_status="processed", qa_approved=True))
        no_qa = classify_processing(self.obs(upload_status="processed", qa_approved=False))
        self.assertFalse(bad_http["ready_for_next_gate"])
        self.assertTrue(bad_http["requires_human"])
        self.assertFalse(no_qa["ready_for_next_gate"])
        self.assertTrue(no_qa["requires_human"])

    def test_scope_is_explicit_and_invalid_environment_fails(self):
        result = classify_processing(self.obs(environment="LAB"))
        self.assertEqual(result["company_id"], "fenix-capital")
        self.assertEqual(result["environment"], "LAB")
        self.assertEqual(result["version"], "1.0.0")
        with self.assertRaises(ValueError):
            classify_processing(self.obs(environment="DEV"))


if __name__ == "__main__":
    unittest.main()
