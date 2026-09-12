import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from provider_adapters import (
    EditingRequest,
    PresenterRequest,
    ProviderScope,
    TTSRequest,
    VideoGenerationRequest,
    plan_editing,
    plan_presenter,
    plan_tts,
    plan_video_generation,
)


def scope(environment="LAB"):
    return ProviderScope(
        company_id="fenix",
        engine_id="FACTORY",
        environment=environment,
        version="1.0.0",
        run_id="run-1",
        production_order_id="po-1",
    )


class ProviderAdapterRuntimeTests(unittest.TestCase):
    def test_video_adapter_preserves_fail_closed_old_contract(self):
        result = plan_video_generation(VideoGenerationRequest(scope(), "short", 30, "9:16", "script-1"))
        self.assertEqual(result["status"], "BLOCKED_PROVIDER_NOT_CONNECTED")
        self.assertEqual(result["difference"], "VIDEO_GENERATOR_API_NOT_CONNECTED")
        self.assertEqual(result["operation_type"], "generate_video")
        self.assertFalse(result["external_action_allowed"])
        self.assertTrue(result["requires_human"])

    def test_editing_adapter_preserves_fail_closed_old_contract(self):
        result = plan_editing(EditingRequest(scope(), "video-1", True, "brand", "vertical"))
        self.assertEqual(result["difference"], "VIDEO_EDITOR_API_NOT_CONNECTED")
        self.assertTrue(result["subtitles"])
        self.assertFalse(result["external_action_allowed"])

    def test_presenter_adapter_preserves_fail_closed_old_contract(self):
        result = plan_presenter(PresenterRequest(scope(), "presenter-a", "audio-1", "office"))
        self.assertEqual(result["difference"], "PRESENTER_API_NOT_CONNECTED")
        self.assertEqual(result["operation_type"], "generate_presenter_video")

    def test_tts_adapter_preserves_fail_closed_old_contract_and_length(self):
        result = plan_tts(TTSRequest(scope(), "hola mundo", "es-ES", "fenix-default"))
        self.assertEqual(result["difference"], "TTS_API_NOT_CONNECTED")
        self.assertEqual(result["script_length"], 10)
        self.assertFalse(result["external_action_allowed"])

    def test_scope_isolation_is_explicit(self):
        result = plan_tts(TTSRequest(scope("PREPROD"), "hola", "es-ES", "voice"))
        self.assertEqual(result["company_id"], "fenix")
        self.assertEqual(result["engine_id"], "FACTORY")
        self.assertEqual(result["environment"], "PREPROD")
        self.assertEqual(result["version"], "1.0.0")

    def test_invalid_environment_and_invalid_duration_fail_closed(self):
        with self.assertRaises(ValueError):
            plan_tts(TTSRequest(scope("INVALID"), "hola", "es-ES", "voice"))
        with self.assertRaises(ValueError):
            plan_video_generation(VideoGenerationRequest(scope(), "short", 0, "9:16", "script-1"))


if __name__ == "__main__":
    unittest.main()
