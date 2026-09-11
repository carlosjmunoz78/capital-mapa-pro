from __future__ import annotations

HUMAN_CODES = {
    "LEGAL_REQUIRED", "SIGNATURE_REQUIRED", "LOW_CONFIDENCE", "HIGH_RISK",
    "POLICY_CONFLICT", "SECURITY_INCIDENT", "MONEY_LIMIT", "CUSTOMER_HUMAN_REQUEST",
}

PROMOTION_BY_ENVIRONMENT = {
    "LAB": "LAB_GREEN",
    "PREPROD": "PREPROD_GREEN",
    "PROD": "PROD_CANDIDATE",
}

EXECUTION_EVIDENCE_KEYS = (
    "route",
    "policy",
    "supervisor",
    "tribunal",
    "promotion",
)


def control_decision(*, route_status: str, policy_decision: str, supervisor_state: str,
                     tribunal_approved: bool, promotion_decision: str,
                     environment: str = "LAB", evidence_refs: dict[str, str] | None = None) -> dict:
    if environment not in PROMOTION_BY_ENVIRONMENT:
        raise ValueError("invalid environment")
    if policy_decision == "DENY":
        return {"status": "BLOCKED", "reason": "POLICY_DENY"}
    if policy_decision == "HUMAN_REQUIRED" or supervisor_state == "HUMAN_REQUIRED":
        return {"status": "HUMAN_REQUIRED", "reason": "POLICY_CONFLICT"}
    if route_status != "ROUTED":
        return {"status": "HUMAN_REQUIRED", "reason": "LOW_CONFIDENCE"}
    if supervisor_state != "GREEN":
        return {"status": "BLOCKED", "reason": "SUPERVISOR_RED"}
    if not tribunal_approved:
        return {"status": "BLOCKED", "reason": "TRIBUNAL_REJECTED"}
    expected_promotion = PROMOTION_BY_ENVIRONMENT[environment]
    if promotion_decision != expected_promotion:
        return {"status": "BLOCKED", "reason": "PROMOTION_SCOPE_MISMATCH"}

    refs = evidence_refs or {}
    missing = tuple(key for key in EXECUTION_EVIDENCE_KEYS if not str(refs.get(key, "")).strip())
    if missing:
        return {"status": "BLOCKED", "reason": "EVIDENCE_MISSING", "missing": missing}

    return {"status": "ALLOW_EXECUTION", "reason": "CONTROL_PLANE_GREEN"}


def validate_human_reason(reason: str) -> None:
    if reason not in HUMAN_CODES:
        raise ValueError(f"non-canonical human exception: {reason}")
