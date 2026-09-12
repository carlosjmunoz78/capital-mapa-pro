import pytest

from runtime.provider_adapters import (
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


def test_video_adapter_preserves_fail_closed_old_contract():
    result = plan_video_generation(VideoGenerationRequest(scope(), "short", 30, "9:16", "script-1"))
    assert result["status"] == "BLOCKED_PROVIDER_NOT_CONNECTED"
    assert result["difference"] == "VIDEO_GENERATOR_API_NOT_CONNECTED"
    assert result["operation_type"] == "generate_video"
    assert result["external_action_allowed"] is False
    assert result["requires_human"] is True


def test_editing_adapter_preserves_fail_closed_old_contract():
    result = plan_editing(EditingRequest(scope(), "video-1", True, "brand", "vertical"))
    assert result["difference"] == "VIDEO_EDITOR_API_NOT_CONNECTED"
    assert result["subtitles"] is True
    assert result["external_action_allowed"] is False


def test_presenter_adapter_preserves_fail_closed_old_contract():
    result = plan_presenter(PresenterRequest(scope(), "presenter-a", "audio-1", "office"))
    assert result["difference"] == "PRESENTER_API_NOT_CONNECTED"
    assert result["operation_type"] == "generate_presenter_video"


def test_tts_adapter_preserves_fail_closed_old_contract_and_length():
    result = plan_tts(TTSRequest(scope(), "hola mundo", "es-ES", "fenix-default"))
    assert result["difference"] == "TTS_API_NOT_CONNECTED"
    assert result["script_length"] == 10
    assert result["external_action_allowed"] is False


def test_scope_isolation_is_explicit():
    result = plan_tts(TTSRequest(scope("PREPROD"), "hola", "es-ES", "voice"))
    assert result["company_id"] == "fenix"
    assert result["engine_id"] == "FACTORY"
    assert result["environment"] == "PREPROD"
    assert result["version"] == "1.0.0"


def test_invalid_environment_and_invalid_duration_fail_closed():
    with pytest.raises(ValueError):
        plan_tts(TTSRequest(scope("INVALID"), "hola", "es-ES", "voice"))
    with pytest.raises(ValueError):
        plan_video_generation(VideoGenerationRequest(scope(), "short", 0, "9:16", "script-1"))
