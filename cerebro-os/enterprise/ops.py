from __future__ import annotations

from dataclasses import dataclass

ENTERPRISE_SEQUENCE = (
    "HR-001","HR-002","HR-003","HR-004","HR-005","HR-006",
    "LEG-001","TAX-001","CMP-002","DPO-001","CONS-001",
    "INV-001","COL-001","TRE-001","ACC-001","FINOPS-001",
    "VEN-001","BUY-001","VREP-001","VCON-001",
)
VALID_STATUS = {"PENDING", "GREEN", "RED", "BLOCKED", "HUMAN_REQUIRED"}
HUMAN_CODES = {"LEGAL_REQUIRED", "SIGNATURE_REQUIRED", "LOW_CONFIDENCE", "HIGH_RISK", "POLICY_CONFLICT", "SECURITY_INCIDENT", "MONEY_LIMIT", "CUSTOMER_HUMAN_REQUEST"}


@dataclass(frozen=True)
class EnterpriseStep:
    company_id: str
    engine_id: str
    status: str
    evidence_ref: str | None = None
    human_code: str | None = None
    cost_eur: float = 0.0
    approved_limit_eur: float = 0.0

    def validate(self) -> None:
        if not self.company_id.strip():
            raise ValueError("company_id required")
        if self.engine_id not in ENTERPRISE_SEQUENCE:
            raise ValueError("non-canonical enterprise engine")
        if self.status not in VALID_STATUS:
            raise ValueError("invalid status")
        if self.cost_eur < 0 or self.approved_limit_eur < 0:
            raise ValueError("cost values cannot be negative")
        if self.status == "GREEN" and not (self.evidence_ref and self.evidence_ref.strip()):
            raise ValueError("GREEN requires evidence_ref")
        if self.status == "HUMAN_REQUIRED" and self.human_code not in HUMAN_CODES:
            raise ValueError("HUMAN_REQUIRED requires canonical human_code")


class EnterpriseOps:
    def __init__(self, company_id: str) -> None:
        if not company_id.strip():
            raise ValueError("company_id required")
        self.company_id = company_id
        self._steps = {e: EnterpriseStep(company_id, e, "PENDING") for e in ENTERPRISE_SEQUENCE}

    def next_engine(self) -> str | None:
        for engine_id in ENTERPRISE_SEQUENCE:
            if self._steps[engine_id].status != "GREEN":
                return engine_id
        return None

    def update(self, step: EnterpriseStep) -> None:
        step.validate()
        if step.company_id != self.company_id:
            raise ValueError("cross-company update denied")
        idx = ENTERPRISE_SEQUENCE.index(step.engine_id)
        if any(self._steps[e].status != "GREEN" for e in ENTERPRISE_SEQUENCE[:idx]):
            raise ValueError("enterprise dependency not green")
        if step.status == "GREEN" and step.cost_eur > step.approved_limit_eur:
            step = EnterpriseStep(step.company_id, step.engine_id, "HUMAN_REQUIRED", step.evidence_ref, "MONEY_LIMIT", step.cost_eur, step.approved_limit_eur)
        self._steps[step.engine_id] = step

    def status(self) -> str:
        states = tuple(self._steps[e].status for e in ENTERPRISE_SEQUENCE)
        if all(s == "GREEN" for s in states):
            return "GREEN"
        for severe in ("BLOCKED", "HUMAN_REQUIRED", "RED"):
            if severe in states:
                return severe
        return "IN_PROGRESS"
