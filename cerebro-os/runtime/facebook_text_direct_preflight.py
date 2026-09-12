from dataclasses import dataclass

_ALLOWED_ENVIRONMENTS = {"LAB", "PREPROD", "PROD", "TEST"}


@dataclass(frozen=True)
class FacebookTextDirectPreflightRequest:
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    platform: str
    format: str
    publication_state: str
    real_publish_authorized: bool
    integration_authorized: bool
    integration_blocked: bool
    copy_reviewed: bool
    integration_state: str
    technical_request: str
    technical_state: str
    production_order_id: str
    production_state: str
    final_approved: bool
    qa_brand_state: str
    qa_legal_state: str
    production_format: str
    copy_blocks: int
    calendar_item_id: str
    calendar_network: str
    calendar_channel: str
    calendar_format: str
    calendar_review_state: str
    calendar_saturation_state: str
    calendar_legal_risk_state: str
    calendar_state: str
    programming_id: str
    programming_state: str
    programming_control: str
    programming_type: str


def audit_facebook_text_direct_preflight(req: FacebookTextDirectPreflightRequest) -> dict:
    required = (
        req.company_id, req.engine_id, req.environment, req.version, req.publication_id,
        req.run_id, req.platform, req.format, req.publication_state, req.integration_state,
        req.technical_request, req.technical_state, req.production_order_id, req.production_state,
        req.qa_brand_state, req.qa_legal_state, req.production_format, req.calendar_item_id,
        req.calendar_network, req.calendar_channel, req.calendar_format, req.calendar_review_state,
        req.calendar_saturation_state, req.calendar_legal_risk_state, req.calendar_state,
        req.programming_id, req.programming_state, req.programming_control, req.programming_type,
    )
    if any(not str(value).strip() for value in required):
        raise ValueError("missing required Facebook direct-text preflight input")
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
        "operation_type": "publication_preflight_direct",
        "platform_state": "FACEBOOK_NOT_CALLED",
        "external_action_allowed": False,
    }

    if req.platform.strip().lower() != "facebook":
        return {**base, "status": "BLOCKED_WRONG_PLATFORM", "requires_human": True}
    if req.real_publish_authorized:
        return {**base, "status": "BLOCKED_REAL_PUBLISH_AUTH_PRESENT", "requires_human": True}
    if not req.integration_authorized or req.integration_blocked:
        return {**base, "status": "BLOCKED_INTEGRATION", "requires_human": True}
    if not req.copy_reviewed or not req.final_approved or req.copy_blocks <= 0:
        return {**base, "status": "BLOCKED_CONTENT_NOT_APPROVED", "requires_human": True}

    return {
        **base,
        "status": "DIRECT_CONTRACT_AUDITED",
        "difference": "ROLLUPS_IGNORED_DIRECT_RECORD_READ",
        "requires_human": False,
        "automatic_action": "USE_DIRECT_EVIDENCE_NO_PUBLISH",
    }
