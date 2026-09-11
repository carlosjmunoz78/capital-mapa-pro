from __future__ import annotations

from dataclasses import dataclass

CANONICAL_HUMAN_REASONS = {
    "LEGAL_REQUIRED",
    "SIGNATURE_REQUIRED",
    "LOW_CONFIDENCE",
    "HIGH_RISK",
    "POLICY_CONFLICT",
    "SECURITY_INCIDENT",
    "MONEY_LIMIT",
    "CUSTOMER_HUMAN_REQUEST",
}

VALID_STATUSES = {"PENDING", "GREEN", "RED", "BLOCKED", "HUMAN_REQUIRED"}


@dataclass(frozen=True)
class ProcessStep:
    company_id: str
    engine_id: str
    status: str
    evidence_ref: str | None = None
    human_reason: str | None = None

    def validate(self, allowed_engines: tuple[str, ...]) -> None:
        if not self.company_id.strip():
            raise ValueError("company_id required")
        if self.engine_id not in allowed_engines:
            raise ValueError("engine_id not allowed in process family")
        if self.status not in VALID_STATUSES:
            raise ValueError("invalid status")
        if self.status == "GREEN" and not (self.evidence_ref and self.evidence_ref.strip()):
            raise ValueError("GREEN requires evidence_ref")
        if self.status == "HUMAN_REQUIRED" and self.human_reason not in CANONICAL_HUMAN_REASONS:
            raise ValueError("invalid HUMAN_REQUIRED reason")


class OrderedFamilyPipeline:
    def __init__(self, company_id: str, sequence: tuple[str, ...]) -> None:
        if not company_id.strip():
            raise ValueError("company_id required")
        if not sequence or len(sequence) != len(set(sequence)):
            raise ValueError("sequence must be non-empty and unique")
        self.company_id = company_id
        self.sequence = sequence
        self._steps = {engine_id: ProcessStep(company_id, engine_id, "PENDING") for engine_id in sequence}

    def next_engine(self) -> str | None:
        for engine_id in self.sequence:
            if self._steps[engine_id].status != "GREEN":
                return engine_id
        return None

    def can_advance(self, engine_id: str) -> bool:
        idx = self.sequence.index(engine_id)
        return all(self._steps[e].status == "GREEN" for e in self.sequence[:idx])

    def update(self, step: ProcessStep) -> None:
        step.validate(self.sequence)
        if step.company_id != self.company_id:
            raise ValueError("cross-company update denied")
        if step.status == "GREEN" and not self.can_advance(step.engine_id):
            raise ValueError("dependencies not GREEN")
        self._steps[step.engine_id] = step

    def status(self) -> str:
        states = tuple(step.status for step in self._steps.values())
        if all(s == "GREEN" for s in states):
            return "GREEN"
        if "BLOCKED" in states:
            return "BLOCKED"
        if "HUMAN_REQUIRED" in states:
            return "HUMAN_REQUIRED"
        if "RED" in states:
            return "RED"
        return "IN_PROGRESS"

    def snapshot(self) -> dict[str, ProcessStep]:
        return dict(self._steps)
