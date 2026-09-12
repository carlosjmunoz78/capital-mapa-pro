from dataclasses import dataclass

_ALLOWED_ENVIRONMENTS = {"LAB", "PREPROD", "PROD", "TEST"}


@dataclass(frozen=True)
class FacebookCaptureClosureRequest:
    company_id: str
    engine_id: str
    environment: str
    version: str
    capture_key: str
    quality_key: str
    capture_status: str
    quality_status: str
    capture_result_hash: str
    quality_result_hash: str
    source_hash: str
    platform_state: str
    notion_record_id: str
    external_id: str
    page_id: str


def close_facebook_capture_24h(req: FacebookCaptureClosureRequest) -> dict:
    required = (
        req.company_id,
        req.engine_id,
        req.environment,
        req.version,
        req.capture_key,
        req.quality_key,
        req.capture_status,
        req.quality_status,
        req.capture_result_hash,
        req.quality_result_hash,
        req.source_hash,
        req.platform_state,
        req.notion_record_id,
        req.external_id,
        req.page_id,
    )
    if any(not str(value).strip() for value in required):
        raise ValueError("missing required Facebook capture closure input")
    if req.environment not in _ALLOWED_ENVIRONMENTS:
        raise ValueError("invalid environment")

    combined_hash = f"{req.capture_result_hash}|{req.quality_result_hash}"
    idem_key = f"{req.company_id}:{req.engine_id}:{req.environment}:{req.version}:{req.external_id}:24h"

    return {
        "company_id": req.company_id,
        "engine_id": req.engine_id,
        "environment": req.environment,
        "version": req.version,
        "network": "Facebook",
        "phase": "24h",
        "closure": {
            "status": "TECHNICALLY_VALIDATED_PARTIAL_HOLD",
            "difference": "LEARNING_BLOCKED_PARTIAL_DATA",
            "make_state": "CLOSED_PARTIAL_HOLD",
            "requires_human": True,
            "human_reason": "LOW_CONFIDENCE",
            "automatic_action": "CLOSE_WINDOW_KEEP_LEARNING_BLOCKED",
            "result_hash": combined_hash,
        },
        "window": {
            "status": "CLOSED_CAPTURED_PARTIAL",
            "make_state": "WINDOW_CLOSED",
            "requires_human": False,
            "recapture_allowed": False,
        },
        "idempotency": {
            "status": "COMMITTED",
            "make_state": "IDEMPOTENCY_COMMITTED",
            "idempotency_key": idem_key,
            "duplicate_allowed": False,
        },
        "platform_state": req.platform_state,
        "external_action_allowed": False,
        "notion_mutation_allowed": False,
    }
