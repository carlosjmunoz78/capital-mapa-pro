from dataclasses import dataclass

_ALLOWED_FORMATS = {"short", "long_video", "community"}
_EXPECTED_CHANNEL_ID = "UC0XL5bW9A6vXfNc5EDIN0Ig"


@dataclass(frozen=True)
class YouTubePreflightRequest:
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    format: str
    channel_id: str
    privacy_status: str
    content_ready: bool
    asset_ready: bool
    qa_passed: bool
    schedule_ready: bool
    duplicate_exists: bool = False


def _validate(req: YouTubePreflightRequest) -> None:
    required = (
        req.company_id,
        req.engine_id,
        req.environment,
        req.version,
        req.publication_id,
        req.run_id,
        req.format,
        req.channel_id,
        req.privacy_status,
    )
    if any(not str(value).strip() for value in required):
        raise ValueError("missing required YouTube preflight scope/input")
    if req.environment not in {"LAB", "PREPROD", "PROD"}:
        raise ValueError("invalid environment")


def plan_youtube_preflight(req: YouTubePreflightRequest) -> dict:
    _validate(req)
    fmt = req.format.strip().lower()

    base = {
        "company_id": req.company_id,
        "engine_id": req.engine_id,
        "environment": req.environment,
        "version": req.version,
        "publication_id": req.publication_id,
        "run_id": req.run_id,
        "format": fmt,
        "channel_id": req.channel_id,
        "privacy_status": req.privacy_status,
        "network": "YouTube",
        "external_action_allowed": False,
        "platform_state": "YOUTUBE_NOT_CALLED",
        "requires_human": True,
    }

    if req.channel_id != _EXPECTED_CHANNEL_ID:
        return {**base, "status": "BLOCKED_WRONG_CHANNEL", "operation_type": "route_format"}
    if req.duplicate_exists:
        return {**base, "status": "BLOCKED_DUPLICATE", "operation_type": f"route_{fmt}"}
    if fmt not in _ALLOWED_FORMATS:
        return {**base, "status": "BLOCKED_UNSUPPORTED_FORMAT", "operation_type": "route_format"}
    if not all((req.content_ready, req.asset_ready, req.qa_passed, req.schedule_ready)):
        return {**base, "status": "BLOCKED_PREFLIGHT", "operation_type": f"route_{fmt}"}

    if fmt == "community":
        return {
            **base,
            "status": "QUEUED_MANUAL_COMMUNITY",
            "preflight_status": "PREFLIGHT_READY_PUBLISH_BLOCKED",
            "operation_type": "route_community",
        }

    return {
        **base,
        "status": "ROUTED_WITH_ENGINE_DISABLED",
        "preflight_status": "PREFLIGHT_READY_PUBLISH_BLOCKED",
        "operation_type": f"route_{fmt}",
        "post_video_id_steps": ["thumbnail", "playlist", "captions", "processing"],
    }
