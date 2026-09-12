from dataclasses import dataclass


YOUTUBE_PROD_TARGETS = {9537699: "SHORT", 9537702: "LONG_VIDEO"}


@dataclass(frozen=True)
class YouTubeUploadRequest:
    scenario_id: int
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    engine_enabled: bool
    override_authorized_once: bool
    override_record_matches: bool
    idempotency_clear: bool
    authorized: bool
    format: str
    title: str
    description: str
    file_name: str
    video_data_present: bool
    duration_seconds: float
    qa_passed: bool
    vertical_validated: bool = False
    horizontal_validated: bool = False


def validate_youtube_upload(req: YouTubeUploadRequest) -> dict:
    if req.scenario_id not in YOUTUBE_PROD_TARGETS:
        raise ValueError("unknown YouTube PROD target")
    blockers = []
    for name in ("company_id", "engine_id", "version", "publication_id", "run_id", "title", "description", "file_name"):
        if not str(getattr(req, name)).strip(): blockers.append(f"MISSING_{name.upper()}")
    if req.environment != "PROD": blockers.append("ENVIRONMENT_NOT_PROD")
    if not req.video_data_present: blockers.append("MISSING_VIDEO_BINARY")
    if not req.engine_enabled: blockers.append("ENGINE_DISABLED")
    if not req.override_authorized_once: blockers.append("OVERRIDE_NOT_AUTHORIZED_ONCE")
    if not req.override_record_matches: blockers.append("OVERRIDE_RECORD_MISMATCH")
    if not req.idempotency_clear: blockers.append("DUPLICATE_OR_LOCK_PRESENT")
    if not req.authorized: blockers.append("SIGNATURE_REQUIRED")
    if not req.qa_passed: blockers.append("QA_NOT_PASSED")
    expected = YOUTUBE_PROD_TARGETS[req.scenario_id]
    if req.format != expected: blockers.append("FORMAT_MISMATCH")
    if expected == "SHORT":
        if req.duration_seconds > 180: blockers.append("SHORT_TOO_LONG")
        if not req.vertical_validated: blockers.append("SHORT_NOT_VERTICAL_VALIDATED")
    else:
        if req.duration_seconds < 181: blockers.append("LONG_VIDEO_TOO_SHORT")
        if not req.horizontal_validated: blockers.append("LONG_VIDEO_NOT_HORIZONTAL_VALIDATED")
    return {
        "scenario_id": req.scenario_id,
        "format": expected,
        "status": "READY_FOR_EXPLICIT_EXECUTION" if not blockers else "BLOCKED",
        "privacy_status": "private",
        "blockers": tuple(blockers),
        "external_action_allowed": False,
        "retry_upload_allowed": False,
        "requires_human": True if not blockers or "SIGNATURE_REQUIRED" in blockers else False,
        "human_reason": "SIGNATURE_REQUIRED" if not blockers or "SIGNATURE_REQUIRED" in blockers else None,
    }
