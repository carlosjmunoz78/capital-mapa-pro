from __future__ import annotations

from dataclasses import dataclass

MORTGAGE_SEQUENCE = (
    "DOC-001","DOC-002","DOC-003","DOC-004",
    "KYC-001","AML-001","BNK-001","BNK-002","BNK-003","BNK-004","BNK-005","BNK-006",
    "OFR-001","REC-001","TAS-001","PROP-001",
)
VALID_STATUS = {"PENDING", "GREEN", "RED", "BLOCKED", "HUMAN_REQUIRED"}
HUMAN_CODES = {"LEGAL_REQUIRED", "SIGNATURE_REQUIRED", "LOW_CONFIDENCE", "HIGH_RISK", "POLICY_CONFLICT", "SECURITY_INCIDENT", "MONEY_LIMIT", "CUSTOMER_HUMAN_REQUEST"}


@dataclass(frozen=True)
class MortgageStep:
    company_id: str
    engine_id: str
    status: str
    evidence_ref: str | None = None
    human_code: str | None = None

    def validate(self) -> None:
        if not self.company_id.strip():
            raise ValueError("company_id required")
        if self.engine_id not in MORTGAGE_SEQUENCE:
            raise ValueError("non-canonical mortgage engine")
        if self.status not in VALID_STATUS:
            raise ValueError("invalid status")
        if self.status == "GREEN" and not (self.evidence_ref and self.evidence_ref.strip()):
            raise ValueError("GREEN requires evidence_ref")
        if self.status == "HUMAN_REQUIRED" and self.human_code not in HUMAN_CODES:
            raise ValueError("HUMAN_REQUIRED requires canonical human_code")


class MortgagePipeline:
    def __init__(self, company_id: str) -> None:
        if not company_id.strip():
            raise ValueError("company_id required")
        self.company_id = company_id
        self._steps = {e: MortgageStep(company_id, e, "PENDING") for e in MORTGAGE_SEQUENCE}

    def next_engine(self) -> str | None:
        for engine_id in MORTGAGE_SEQUENCE:
            if self._steps[engine_id].status != "GREEN":
                return engine_id
        return None

    def update(self, step: MortgageStep) -> None:
        step.validate()
        if step.company_id != self.company_id:
            raise ValueError("cross-company update denied")
        idx = MORTGAGE_SEQUENCE.index(step.engine_id)
        if any(self._steps[e].status != "GREEN" for e in MORTGAGE_SEQUENCE[:idx]):
            raise ValueError("mortgage dependency not green")
        self._steps[step.engine_id] = step

    def status(self) -> str:
        states = tuple(self._steps[e].status for e in MORTGAGE_SEQUENCE)
        if all(s == "GREEN" for s in states):
            return "GREEN"
        for severe in ("BLOCKED", "HUMAN_REQUIRED", "RED"):
            if severe in states:
                return severe
        return "IN_PROGRESS"
