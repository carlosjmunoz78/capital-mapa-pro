from __future__ import annotations

from dataclasses import dataclass

YOUTUBE_AUX_TARGETS = {
    9537710: "thumbnail",
    9537718: "playlist",
}


@dataclass(frozen=True)
class YouTubeAuxRequest:
    scenario_id: int
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    video_id: str
    engine_enabled: bool
    override_authorized_once: bool
    override_record_matches: bool
    idempotency_clear: bool
    qa_passed: bool
    authorized: bool
    thumbnail_data_present: bool = False
    playlist_id: str = ""


def validate_youtube_aux(req: YouTubeAuxRequest) -> dict:
    if req.scenario_id not in YOUTUBE_AUX_TARGETS:
        raise ValueError("unknown YouTube auxiliary PROD target")
    required = (req.company_id, req.engine_id, req.environment, req.version, req.publication_id, req.run_id, req.video_id)
    if any(not str(v).strip() for v in required):
        raise ValueError("missing required YouTube auxiliary scope/input")
    if req.environment != "PROD":
        raise ValueError("YouTube auxiliary PROD target requires PROD environment")

    operation = YOUTUBE_AUX_TARGETS[req.scenario_id]
    blockers = []
    if not req.engine_enabled:
        blockers.append("ENGINE_DISABLED")
    if not req.override_authorized_once:
        blockers.append("OVERRIDE_NOT_AUTHORIZED_ONCE")
    if not req.override_record_matches:
        blockers.append("OVERRIDE_RECORD_MISMATCH")
    if not req.idempotency_clear:
        blockers.append("DUPLICATE")
    if not req.qa_passed:
        blockers.append("QA_NOT_PASSED")
    if not req.authorized:
        blockers.append("SIGNATURE_REQUIRED")
    if operation == "thumbnail" and not req.thumbnail_data_present:
        blockers.append("THUMBNAIL_DATA_REQUIRED")
    if operation == "playlist" and not req.playlist_id.strip():
        blockers.append("PLAYLIST_ID_REQUIRED")

    return {
        "scenario_id": req.scenario_id,
        "operation": operation,
        "status": "READY_FOR_EXPLICIT_EXECUTION" if not blockers else "BLOCKED",
        "blockers": tuple(blockers),
        "external_action_allowed": False,
        "youtube_called_by_runtime": False,
        "retry_external_action_allowed": False,
        "requires_human": not blockers,
        "human_reason": "SIGNATURE_REQUIRED" if not blockers else None,
        "old_preserved": True,
    }


@dataclass(frozen=True)
class YouTubeAuxReceipt:
    scenario_id: int
    publication_id: str
    run_id: str
    video_id: str
    platform_success: bool


def normalize_youtube_aux_receipt(receipt: YouTubeAuxReceipt) -> dict:
    if receipt.scenario_id not in YOUTUBE_AUX_TARGETS:
        raise ValueError("unknown YouTube auxiliary PROD target")
    operation = YOUTUBE_AUX_TARGETS[receipt.scenario_id]
    if not receipt.platform_success:
        return {
            "status": "PLATFORM_NOT_CONFIRMED",
            "operation": operation,
            "idempotency_state": "OPEN",
            "retry_external_action_allowed": False,
            "external_action_allowed": False,
        }
    return {
        "status": "THUMBNAIL_SET" if operation == "thumbnail" else "PLAYLIST_ASSIGNED",
        "operation": operation,
        "idempotency_state": "COMPLETED",
        "retry_external_action_allowed": False,
        "external_action_allowed": False,
    }


def inventory() -> dict[int, str]:
    return dict(YOUTUBE_AUX_TARGETS)
