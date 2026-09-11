from __future__ import annotations

from dataclasses import dataclass

CANONICAL_HUMAN_REQUIRED = {
    "LEGAL_REQUIRED",
    "SIGNATURE_REQUIRED",
    "LOW_CONFIDENCE",
    "HIGH_RISK",
    "POLICY_CONFLICT",
    "SECURITY_INCIDENT",
    "MONEY_LIMIT",
    "CUSTOMER_HUMAN_REQUEST",
}

@dataclass(frozen=True)
class PolicyRequest:
    company_id: str | None
    target_company_id: str | None
    environment: str
    action: str
    irreversible: bool = False
    touches_prod: bool = False
    cost_eur: float = 0.0
    money_limit_eur: float = 0.0
    risk: str = "LOW"
    confidence: float = 1.0
    legal_required: bool = False
    signature_required: bool = False
    customer_human_request: bool = False


def evaluate(req: PolicyRequest) -> dict:
    reasons: list[str] = []
    if req.company_id and req.target_company_id and req.company_id != req.target_company_id:
        return {"decision": "DENY", "reasons": ["CROSS_COMPANY_DENIED"]}
    if req.legal_required:
        reasons.append("LEGAL_REQUIRED")
    if req.signature_required:
        reasons.append("SIGNATURE_REQUIRED")
    if req.customer_human_request:
        reasons.append("CUSTOMER_HUMAN_REQUEST")
    if req.confidence < 0.75:
        reasons.append("LOW_CONFIDENCE")
    if req.risk.upper() == "HIGH":
        reasons.append("HIGH_RISK")
    if req.cost_eur > req.money_limit_eur:
        reasons.append("MONEY_LIMIT")
    if req.touches_prod and req.irreversible:
        reasons.append("HIGH_RISK")
    if reasons:
        deduped = sorted(set(reasons))
        assert set(deduped).issubset(CANONICAL_HUMAN_REQUIRED)
        return {"decision": "HUMAN_REQUIRED", "reasons": deduped}
    return {"decision": "ALLOW", "reasons": []}
