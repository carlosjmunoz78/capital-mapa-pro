from dataclasses import dataclass

_ALLOWED_ENVIRONMENTS = {"LAB", "PREPROD", "PROD", "TEST"}
_ALLOWED_FORMATS = {"texto", "enlace", "text", "link"}


@dataclass(frozen=True)
class FacebookLinkPreflightRequest:
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    format: str
    real_publish_authorized: bool
    integration_authorized: bool
    copy_reviewed: bool
    utm_required: bool
    domain_allowed: bool
    production_order_id: str
    production_state: str
    final_approved: bool
    qa_brand_state: str
    qa_legal_state: str
    final_url: str
    calendar_item_id: str
    calendar_network: str
    calendar_channel: str
    calendar_format: str
    calendar_review_state: str
    calendar_saturation_state: str
    calendar_legal_risk_state: str
    programming_id: str
    programming_order_id: str
    programming_run_id: str
    programming_state: str
    programming_type: str
    programming_control: str
    programming_incident: bool
    programming_date: str
    programming_draft_url: str


def _required_text(req: FacebookLinkPreflightRequest):
    return (
        req.company_id,
        req.engine_id,
        req.environment,
        req.version,
        req.publication_id,
        req.run_id,
        req.format,
        req.production_order_id,
        req.production_state,
        req.qa_brand_state,
        req.qa_legal_state,
        req.calendar_item_id,
        req.calendar_network,
        req.calendar_channel,
        req.calendar_format,
        req.calendar_review_state,
        req.calendar_saturation_state,
        req.calendar_legal_risk_state,
        req.programming_id,
        req.programming_order_id,
        req.programming_run_id,
        req.programming_state,
        req.programming_type,
        req.programming_control,
        req.programming_date,
    )


def plan_facebook_link_preflight(req: FacebookLinkPreflightRequest) -> dict:
    if any(not str(value).strip() for value in _required_text(req)):
        raise ValueError("missing required Facebook link preflight input")
    if req.environment not in _ALLOWED_ENVIRONMENTS:
        raise ValueError("invalid environment")

    fmt = req.format.strip().lower()
    base = {
        "company_id": req.company_id,
        "engine_id": req.engine_id,
        "environment": req.environment,
        "version": req.version,
        "publication_id": req.publication_id,
        "run_id": req.run_id,
        "network": "Facebook",
        "format": fmt,
        "platform_state": "FACEBOOK_NOT_CALLED",
        "external_action_allowed": False,
        "operation_type": "direct_url_contract_validation",
    }

    if fmt not in _ALLOWED_FORMATS:
        return {**base, "status": "BLOCKED_UNSUPPORTED_FORMAT", "requires_human": True}
    if req.real_publish_authorized:
        return {**base, "status": "BLOCKED_REAL_PUBLISH_AUTH_PRESENT", "requires_human": True}
    if not req.integration_authorized:
        return {**base, "status": "BLOCKED_INTEGRATION_NOT_AUTHORIZED", "requires_human": True}
    if not req.copy_reviewed or not req.final_approved:
        return {**base, "status": "BLOCKED_CONTENT_NOT_APPROVED", "requires_human": True}
    if not req.domain_allowed:
        return {**base, "status": "BLOCKED_DOMAIN_NOT_ALLOWED", "requires_human": True}
    if fmt in {"enlace", "link"} and not req.final_url.strip():
        return {**base, "status": "BLOCKED_MISSING_FINAL_URL", "requires_human": True}
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
        "utm_required": req.utm_required,
        "result_fingerprint": "|".join((
            req.publication_id,
            req.production_order_id,
            req.calendar_item_id,
            req.programming_id,
            req.final_url,
        )),
    }
