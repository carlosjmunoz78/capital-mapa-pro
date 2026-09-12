from dataclasses import dataclass

_ALLOWED_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}
_NATIVE_FORMATS = {"texto", "enlace", "imagen", "vídeo"}
_ADAPTER_FORMATS = {"documento", "carrusel"}


@dataclass(frozen=True)
class LinkedInPreflightRequest:
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    format: str
    content_ready: bool
    asset_ready: bool
    url_ready: bool
    qa_passed: bool
    schedule_ready: bool
    duplicate_exists: bool = False


def _validate(req: LinkedInPreflightRequest) -> None:
    required = (
        req.company_id,
        req.engine_id,
        req.environment,
        req.version,
        req.publication_id,
        req.run_id,
        req.format,
    )
    if any(not str(value).strip() for value in required):
        raise ValueError("missing required LinkedIn preflight scope/input")
    if req.environment not in _ALLOWED_ENVIRONMENTS:
        raise ValueError("invalid environment")


def plan_linkedin_preflight(req: LinkedInPreflightRequest) -> dict:
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
        "network": "LinkedIn",
        "external_action_allowed": False,
        "platform_state": "LINKEDIN_NOT_CALLED",
        "requires_human": True,
    }

    if req.duplicate_exists:
        return {**base, "status": "BLOCKED_DUPLICATE", "operation_type": "route_format"}

    if fmt in _ADAPTER_FORMATS:
        return {
            **base,
            "status": "ADAPTER_REQUIRED",
            "operation_type": f"route_{fmt}",
            "adapter_required": True,
        }

    if fmt not in _NATIVE_FORMATS:
        return {**base, "status": "BLOCKED_UNSUPPORTED_FORMAT", "operation_type": "route_format"}

    gates = [req.content_ready, req.qa_passed, req.schedule_ready]
    if fmt == "enlace":
        gates.append(req.url_ready)
    if fmt in {"imagen", "vídeo"}:
        gates.append(req.asset_ready)

    if not all(gates):
        return {**base, "status": "BLOCKED_PREFLIGHT", "operation_type": f"route_{fmt}"}

    return {
        **base,
        "status": "ROUTED_WITH_PUBLISH_ENGINE_DISABLED",
        "preflight_status": "PREFLIGHT_READY",
        "operation_type": f"route_{fmt}",
        "adapter_required": False,
    }
