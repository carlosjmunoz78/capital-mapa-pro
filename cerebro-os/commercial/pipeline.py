from __future__ import annotations

from dataclasses import dataclass

COMMERCIAL_SEQUENCE = (
    "LEAD-001",
    "SALE-001",
    "COM-001",
    "C360-001",
    "CX-001",
    "RET-001",
)
VALID_STATUS = {"PENDING", "GREEN", "RED", "BLOCKED", "HUMAN_REQUIRED"}
VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class CommercialStep:
    company_id: str
    engine_id: str
    status: str
    evidence_ref: str | None = None
    confidence: float = 1.0
    environment: str = "LAB"
    version: str = "1.0.0"

    def validate(self) -> None:
        if not self.company_id.strip() or not self.version.strip():
            raise ValueError("company_id and version required")
        if self.engine_id not in COMMERCIAL_SEQUENCE:
            raise ValueError("non-canonical commercial engine")
        if self.status not in VALID_STATUS:
            raise ValueError("invalid status")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.status == "GREEN" and not (self.evidence_ref and self.evidence_ref.strip()):
            raise ValueError("GREEN requires evidence_ref")


class CommercialPipeline:
    def __init__(self, company_id: str, min_confidence: float = 0.75, environment: str = "LAB", version: str = "1.0.0") -> None:
        if not company_id.strip() or not version.strip():
            raise ValueError("company_id and version required")
        if environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        self.company_id = company_id
        self.min_confidence = min_confidence
        self.environment = environment
        self.version = version
        self._steps = {e: CommercialStep(company_id, e, "PENDING", environment=environment, version=version) for e in COMMERCIAL_SEQUENCE}

    def next_engine(self) -> str | None:
        for engine_id in COMMERCIAL_SEQUENCE:
            if self._steps[engine_id].status != "GREEN":
                return engine_id
        return None

    def update(self, step: CommercialStep) -> None:
        step.validate()
        if step.company_id != self.company_id:
            raise ValueError("cross-company update denied")
        if step.environment != self.environment or step.version != self.version:
            raise ValueError("cross-scope commercial update denied")
        idx = COMMERCIAL_SEQUENCE.index(step.engine_id)
        if any(self._steps[e].status != "GREEN" for e in COMMERCIAL_SEQUENCE[:idx]):
            raise ValueError("commercial sequence dependency not green")
        if step.status == "GREEN" and step.confidence < self.min_confidence:
            step = CommercialStep(step.company_id, step.engine_id, "HUMAN_REQUIRED", step.evidence_ref, step.confidence, step.environment, step.version)
        self._steps[step.engine_id] = step

    def status(self) -> str:
        states = tuple(self._steps[e].status for e in COMMERCIAL_SEQUENCE)
        if all(s == "GREEN" for s in states):
            return "GREEN"
        for severe in ("BLOCKED", "HUMAN_REQUIRED", "RED"):
            if severe in states:
                return severe
        return "IN_PROGRESS"
