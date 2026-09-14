from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

ENGINE_ID = "TAX-001"
ENVIRONMENT = "LAB"
VERSION = "0.1.0"

ALLOWED_OPERATIONS = {"CLASSIFY", "CALCULATE", "EXPLAIN", "CHECK_DEADLINE"}
REGULATED_ACTION_OPERATIONS = {"FILE", "SUBMIT", "SIGN", "PAY", "AMEND", "APPEAL"}


@dataclass(frozen=True)
class TaxDecisionSupportResult:
    request_id: str
    company_id: str
    engine_id: str
    version: str
    environment: str
    status: str
    operation: str
    confidence: float
    evidence_refs: list[str]
    human_required: str | None
    reason: str
    cost_eur: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _require_text(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value.strip()


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    """Fail-closed TAX-001 LAB boundary.

    This V0 proves the capability envelope and governance contract only. It never
    files, signs, pays, amends or appeals a real tax obligation and it never
    invents rates/deadlines. Rule execution must be evidence-bound before this
    boundary returns decision support.
    """
    request_id = _require_text(payload, "request_id")
    company_id = _require_text(payload, "company_id")
    operation = _require_text(payload, "operation").upper()

    if operation in REGULATED_ACTION_OPERATIONS:
        return TaxDecisionSupportResult(
            request_id=request_id,
            company_id=company_id,
            engine_id=ENGINE_ID,
            version=VERSION,
            environment=ENVIRONMENT,
            status="HUMAN_REQUIRED",
            operation=operation,
            confidence=1.0,
            evidence_refs=[],
            human_required="LEGAL_REQUIRED",
            reason="TAX-001 V0 is decision-support only; regulated external action is disabled.",
        ).to_dict()

    if operation not in ALLOWED_OPERATIONS:
        return TaxDecisionSupportResult(
            request_id=request_id,
            company_id=company_id,
            engine_id=ENGINE_ID,
            version=VERSION,
            environment=ENVIRONMENT,
            status="DENY",
            operation=operation,
            confidence=1.0,
            evidence_refs=[],
            human_required="POLICY_CONFLICT",
            reason="Operation is outside the TAX-001 V0 allow-list.",
        ).to_dict()

    _require_text(payload, "effective_date")
    _require_text(payload, "jurisdiction")
    evidence_refs = payload.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not evidence_refs or not all(isinstance(x, str) and x.strip() for x in evidence_refs):
        return TaxDecisionSupportResult(
            request_id=request_id,
            company_id=company_id,
            engine_id=ENGINE_ID,
            version=VERSION,
            environment=ENVIRONMENT,
            status="HUMAN_REQUIRED",
            operation=operation,
            confidence=0.0,
            evidence_refs=[],
            human_required="LOW_CONFIDENCE",
            reason="Official evidence reference is required before tax decision support can run.",
        ).to_dict()

    facts = payload.get("facts")
    if not isinstance(facts, dict) or not facts:
        return TaxDecisionSupportResult(
            request_id=request_id,
            company_id=company_id,
            engine_id=ENGINE_ID,
            version=VERSION,
            environment=ENVIRONMENT,
            status="HUMAN_REQUIRED",
            operation=operation,
            confidence=0.0,
            evidence_refs=evidence_refs,
            human_required="LOW_CONFIDENCE",
            reason="Concrete case facts are required; TAX-001 does not infer missing taxable facts.",
        ).to_dict()

    return TaxDecisionSupportResult(
        request_id=request_id,
        company_id=company_id,
        engine_id=ENGINE_ID,
        version=VERSION,
        environment=ENVIRONMENT,
        status="READY_FOR_RULE_EXECUTION",
        operation=operation,
        confidence=1.0,
        evidence_refs=evidence_refs,
        human_required=None,
        reason="Envelope gates passed. A versioned evidence-bound fiscal rule may execute next.",
    ).to_dict()
