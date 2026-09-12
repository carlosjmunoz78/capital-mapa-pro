from dataclasses import dataclass

_ALLOWED_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class TikTokPreflightRequest:
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    format: str
    route_type: str
    content_ready: bool
    asset_ready: bool
    qa_passed: bool
    schedule_ready: bool
    duplicate_exists: bool = False


def _validate(req: TikTokPreflightRequest) -> None:
    required = (
        req.company_id,
        req.engine_id,
        req.environment,
        req.version,
        req.publication_id,
        req.run_id,
        req.format,
        req.route_type,
    )
    if any(not str(value).strip() for value in required):
        raise ValueError("missing required TikTok preflight scope/input")
    if req.environment not in _ALLOWED_ENVIRONMENTS:
        raise ValueError("invalid environment")


def plan_tiktok_preflight(req: TikTokPreflightRequest) -> dict:
    _validate(req)
    route_type = req.route_type.strip().upper()
    fmt = req.format.strip().lower()

    base = {
        "company_id": req.company_id,
        "engine_id": req.engine_id,
        "environment": req.environment,
        "version": req.version,
        "publication_id": req.publication_id,
        "run_id": req.run_id,
        "format": fmt,
        "route_type": route_type,
        "network": "TikTok",
        "external_action_allowed": False,
        "platform_state": "TIKTOK_NOT_CALLED",
        "requires_human": True,
    }

    if route_type != "ORGANIC":
        return {**base, "status": "BLOCKED_NON_ORGANIC_ROUTE", "operation_type": "route_format"}

    if req.duplicate_exists:
        return {**base, "status": "BLOCKED_DUPLICATE", "operation_type": f"route_{fmt}"}

    if not all((req.content_ready, req.asset_ready, req.qa_passed, req.schedule_ready)):
        return {**base, "status": "BLOCKED_PREFLIGHT", "operation_type": f"route_{fmt}"}

    return {
        **base,
        "status": "ROUTED_ORGANIC_WITH_ENGINE_DISABLED",
        "preflight_status": "PREFLIGHT_READY_CONNECTION_PENDING",
        "operation_type": f"route_{fmt}",
        "oauth_required": True,
        "ads_conversion_allowed": False,
    }
