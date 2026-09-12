from __future__ import annotations

from dataclasses import dataclass

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


def _required(*values: str) -> None:
    if any(not str(value).strip() for value in values):
        raise ValueError("provider adapter missing required fields")


@dataclass(frozen=True)
class ProviderScope:
    company_id: str
    engine_id: str
    environment: str
    version: str
    run_id: str
    production_order_id: str

    def validate(self) -> None:
        _required(self.company_id, self.engine_id, self.environment, self.version, self.run_id, self.production_order_id)
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")


@dataclass(frozen=True)
class VideoGenerationRequest:
    scope: ProviderScope
    video_class: str
    target_duration_seconds: float
    aspect_ratio: str
    script_asset_id: str


@dataclass(frozen=True)
class EditingRequest:
    scope: ProviderScope
    video_asset_id: str
    subtitles: bool
    music_profile: str
    template_profile: str


@dataclass(frozen=True)
class PresenterRequest:
    scope: ProviderScope
    presenter_profile: str
    audio_asset_id: str
    background_profile: str


@dataclass(frozen=True)
class TTSRequest:
    scope: ProviderScope
    script: str
    language: str
    voice_profile: str


def _blocked(scope: ProviderScope, *, operation_type: str, difference: str, details: dict) -> dict:
    scope.validate()
    return {
        "company_id": scope.company_id,
        "engine_id": scope.engine_id,
        "environment": scope.environment,
        "version": scope.version,
        "run_id": scope.run_id,
        "production_order_id": scope.production_order_id,
        "phase": "provider_adapter",
        "status": "BLOCKED_PROVIDER_NOT_CONNECTED",
        "difference": difference,
        "operation_type": operation_type,
        "requires_human": True,
        "external_action_allowed": False,
        **details,
    }


def plan_video_generation(req: VideoGenerationRequest) -> dict:
    _required(req.video_class, req.aspect_ratio, req.script_asset_id)
    if req.target_duration_seconds <= 0:
        raise ValueError("target_duration_seconds must be positive")
    return _blocked(req.scope, operation_type="generate_video", difference="VIDEO_GENERATOR_API_NOT_CONNECTED", details={
        "video_class": req.video_class,
        "target_duration_seconds": req.target_duration_seconds,
        "aspect_ratio": req.aspect_ratio,
        "script_asset_id": req.script_asset_id,
    })


def plan_editing(req: EditingRequest) -> dict:
    _required(req.video_asset_id, req.music_profile, req.template_profile)
    return _blocked(req.scope, operation_type="edit_video", difference="VIDEO_EDITOR_API_NOT_CONNECTED", details={
        "video_asset_id": req.video_asset_id,
        "subtitles": req.subtitles,
        "music_profile": req.music_profile,
        "template_profile": req.template_profile,
    })


def plan_presenter(req: PresenterRequest) -> dict:
    _required(req.presenter_profile, req.audio_asset_id, req.background_profile)
    return _blocked(req.scope, operation_type="generate_presenter_video", difference="PRESENTER_API_NOT_CONNECTED", details={
        "presenter_profile": req.presenter_profile,
        "audio_asset_id": req.audio_asset_id,
        "background_profile": req.background_profile,
    })


def plan_tts(req: TTSRequest) -> dict:
    _required(req.script, req.language, req.voice_profile)
    return _blocked(req.scope, operation_type="generate_voice", difference="TTS_API_NOT_CONNECTED", details={
        "script_length": len(req.script),
        "language": req.language,
        "voice_profile": req.voice_profile,
    })
