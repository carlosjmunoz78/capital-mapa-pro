from dataclasses import dataclass

_ALLOWED_ENVIRONMENTS = {"LAB", "PREPROD", "PROD", "TEST"}
_ALLOWED_IMAGE_MIME = {"image/jpeg", "image/png", "jpeg", "jpg", "png"}


@dataclass(frozen=True)
class FacebookImagePreflightRequest:
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    format: str
    real_publish_authorized: bool
    integration_authorized: bool
    integration_blocked: bool
    copy_reviewed: bool
    production_order_id: str
    production_state: str
    final_approved: bool
    qa_brand_state: str
    qa_legal_state: str
    calendar_item_id: str
    calendar_network: str
    calendar_channel: str
    calendar_format: str
    calendar_review_state: str
    calendar_saturation_state: str
    calendar_legal_risk_state: str
    asset_id: str
    asset_state: str
    asset_type: str
    asset_main: bool
    asset_url: str
    asset_size: int
    asset_width: int
    asset_height: int
    asset_mime: str
    asset_qa_brand: str
    asset_qa_legal: str
    asset_rights: str
    http_status: int
    programming_id: str
    programming_order_id: str
    programming_run_id: str
    programming_state: str
    programming_type: str
    programming_control: str
    programming_incident: bool
    programming_date: str
    programming_draft_url: str


def plan_facebook_image_preflight(req: FacebookImagePreflightRequest) -> dict:
    required = (
        req.company_id, req.engine_id, req.environment, req.version, req.publication_id,
        req.run_id, req.format, req.production_order_id, req.calendar_item_id, req.asset_id,
        req.asset_url, req.asset_mime, req.programming_id, req.programming_order_id,
        req.programming_run_id, req.programming_state, req.programming_type,
        req.programming_control, req.programming_date,
    )
    if any(not str(value).strip() for value in required):
        raise ValueError("missing required Facebook image preflight input")
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
        "platform_state": "FACEBOOK_NOT_CALLED",
        "external_action_allowed": False,
        "operation_type": "direct_image_asset_programming_contract_validation",
    }

    if req.real_publish_authorized:
        return {**base, "status": "BLOCKED_REAL_PUBLISH_AUTH_PRESENT", "requires_human": True}
    if not req.integration_authorized or req.integration_blocked:
        return {**base, "status": "BLOCKED_INTEGRATION", "requires_human": True}
    if not req.copy_reviewed or not req.final_approved:
        return {**base, "status": "BLOCKED_CONTENT_NOT_APPROVED", "requires_human": True}
    if not req.asset_main:
        return {**base, "status": "BLOCKED_ASSET_NOT_MAIN", "requires_human": True}
    if req.asset_mime.strip().lower() not in _ALLOWED_IMAGE_MIME:
        return {**base, "status": "BLOCKED_UNSUPPORTED_IMAGE_FORMAT", "requires_human": True}
    if req.asset_size <= 0 or req.asset_width <= 0 or req.asset_height <= 0:
        return {**base, "status": "BLOCKED_INVALID_ASSET_METADATA", "requires_human": True}
    if not (200 <= req.http_status < 400):
        return {**base, "status": "BLOCKED_ASSET_UNREACHABLE", "requires_human": True}
    if req.programming_incident:
        return {**base, "status": "BLOCKED_PROGRAMMING_INCIDENT", "requires_human": True}
    if req.programming_order_id != req.production_order_id:
        return {**base, "status": "BLOCKED_ORDER_RELATION_MISMATCH", "requires_human": True}
    if req.programming_run_id != req.run_id:
        return {**base, "status": "BLOCKED_RUN_ID_MISMATCH", "requires_human": True}

    return {
        **base,
        "status": "DIRECT_CONTRACT_VALIDATED",
        "requires_human": False,
        "result_fingerprint": "|".join((
            req.publication_id,
            req.production_order_id,
            req.calendar_item_id,
            req.asset_id,
            req.programming_id,
            f"HTTP_{req.http_status}",
        )),
    }
