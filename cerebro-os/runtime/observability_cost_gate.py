from __future__ import annotations

from dataclasses import dataclass

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class ObservabilityCostEvidence:
    company_id: str
    engine_id: str
    environment: str
    version: str
    logs_ref: str = ""
    metrics_ref: str = ""
    incident_ref: str = ""
    cost_ref: str = ""
    monthly_cost_eur: float | None = None
    money_limit_eur: float | None = None


def assess_observability_cost(evidence: ObservabilityCostEvidence) -> dict:
    if not all((evidence.company_id.strip(), evidence.engine_id.strip(), evidence.version.strip())):
        raise ValueError("company_id, engine_id and version required")
    if evidence.environment not in VALID_ENVIRONMENTS:
        raise ValueError("invalid environment")
    if evidence.monthly_cost_eur is not None and evidence.monthly_cost_eur < 0:
        raise ValueError("monthly_cost_eur cannot be negative")
    if evidence.money_limit_eur is not None and evidence.money_limit_eur < 0:
        raise ValueError("money_limit_eur cannot be negative")

    checks = {
        "logs": bool(evidence.logs_ref.strip()),
        "metrics": bool(evidence.metrics_ref.strip()),
        "incidents": bool(evidence.incident_ref.strip()),
        "cost_measured": bool(evidence.cost_ref.strip()) and evidence.monthly_cost_eur is not None,
    }
    missing = tuple(name for name, ok in checks.items() if not ok)
    limit_exceeded = (
        evidence.monthly_cost_eur is not None
        and evidence.money_limit_eur is not None
        and evidence.monthly_cost_eur > evidence.money_limit_eur
    )
    green = not missing and not limit_exceeded

    return {
        "company_id": evidence.company_id,
        "engine_id": evidence.engine_id,
        "environment": evidence.environment,
        "version": evidence.version,
        "checks": checks,
        "missing": missing,
        "limit_exceeded": limit_exceeded,
        "green": green,
        "prod_candidate_allowed": green,
        "human_reason": "MONEY_LIMIT" if limit_exceeded else None,
        "additional_paid_ai_required": False,
    }
