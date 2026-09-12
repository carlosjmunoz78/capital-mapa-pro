from dataclasses import dataclass

_ALLOWED_ENVIRONMENTS = {"LAB", "PREPROD", "PROD", "TEST"}


@dataclass(frozen=True)
class FacebookMissingOpRequest:
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    format_name: str
    publication_state: str
    production_order_id: str | None


def detect_missing_production_order(req: FacebookMissingOpRequest) -> dict:
    required = (
        req.company_id,
        req.engine_id,
        req.environment,
        req.version,
        req.publication_id,
        req.format_name,
        req.publication_state,
    )
    if any(not str(value).strip() for value in required):
        raise ValueError("missing required Facebook missing-OP detector input")
    if req.environment not in _ALLOWED_ENVIRONMENTS:
        raise ValueError("invalid environment")

    base = {
        "company_id": req.company_id,
        "engine_id": req.engine_id,
        "environment": req.environment,
        "version": req.version,
        "publication_id": req.publication_id,
        "network": "Facebook",
        "platform_state": "NOT_CALLED",
        "external_action_allowed": False,
        "operation_type": "publication_relation_validation",
    }

    is_target = (
        req.format_name == "Texto orgánico simple"
        and req.publication_state == "Pendiente de publicar"
    )
    if not is_target:
        return {
            **base,
            "status": "NOT_APPLICABLE",
            "requires_human": False,
            "difference": "NONE",
        }

    if req.production_order_id and req.production_order_id.strip():
        return {
            **base,
            "status": "OP_RELATION_PRESENT",
            "requires_human": False,
            "difference": "NONE",
        }

    return {
        **base,
        "status": "BLOCKED_OP_RELATION_MISSING",
        "requires_human": True,
        "human_reason": "LOW_CONFIDENCE",
        "severity": "critical",
        "difference": "OP_RELATION_MISSING",
        "automatic_action": "BLOCK_ONLY_NO_FACEBOOK_CALL",
    }
