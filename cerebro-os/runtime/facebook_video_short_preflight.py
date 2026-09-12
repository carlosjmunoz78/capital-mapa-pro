from dataclasses import dataclass

_ALLOWED_ENVIRONMENTS = {"LAB", "PREPROD", "PROD", "TEST"}


@dataclass(frozen=True)
class FacebookVideoShortEvidenceRequest:
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    production_order_id: str
    calendar_item_id: str
    programming_id: str
    asset_id: str
    run_id: str
    asset_url: str
    http_status: int
    publication_snapshot: str
    production_snapshot: str
    calendar_snapshot: str
    programming_snapshot: str
    asset_snapshot: str


def capture_facebook_video_short_evidence(req: FacebookVideoShortEvidenceRequest) -> dict:
    required = (
        req.company_id, req.engine_id, req.environment, req.version, req.publication_id,
        req.production_order_id, req.calendar_item_id, req.programming_id, req.asset_id,
        req.run_id, req.asset_url, req.publication_snapshot, req.production_snapshot,
        req.calendar_snapshot, req.programming_snapshot, req.asset_snapshot,
    )
    if any(not str(value).strip() for value in required):
        raise ValueError("missing required Facebook short-video evidence input")
    if req.environment not in _ALLOWED_ENVIRONMENTS:
        raise ValueError("invalid environment")

    base = {
        "company_id": req.company_id,
        "engine_id": req.engine_id,
        "environment": req.environment,
        "version": req.version,
        "publication_id": req.publication_id,
        "run_id": req.run_id,
        "network": "Facebook",
        "operation_type": "direct_video_short_contract_evidence_capture",
        "platform_state": "FACEBOOK_NOT_CALLED",
        "external_action_allowed": False,
        "requires_human": True,
    }

    if not (200 <= req.http_status < 400):
        return {
            **base,
            "status": "EVIDENCE_CAPTURED_ASSET_UNREACHABLE",
            "difference": "PENDING_EVIDENCE_EVALUATION",
        }

    return {
        **base,
        "status": "DIRECT_EVIDENCE_CAPTURED",
        "difference": "PENDING_EVIDENCE_EVALUATION",
        "result_fingerprint": "|".join((
            req.publication_id,
            req.production_order_id,
            req.calendar_item_id,
            req.programming_id,
            req.asset_id,
            f"HTTP_{req.http_status}",
        )),
        "automatic_action": "EVALUATE_EVIDENCE_ONLY_NO_PUBLISH",
    }
