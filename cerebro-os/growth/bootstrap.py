from __future__ import annotations

from dataclasses import dataclass

CANONICAL_GROWTH_SEQUENCE = (
    "SEOBOOT-001",
    "SOCBOOT-001",
    "MKTBOOT-001",
    "CRMBOOT-001",
    "APPBOOT-001",
    "AUTBOOT-001",
    "TRNBOOT-001",
)
VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class BootstrapStep:
    company_id: str
    engine_id: str
    status: str
    evidence_ref: str | None = None
    environment: str = "LAB"
    version: str = "1.0.0"

    def validate(self) -> None:
        if self.engine_id not in CANONICAL_GROWTH_SEQUENCE:
            raise ValueError("non-canonical bootstrap engine")
        if not self.company_id.strip() or not self.version.strip():
            raise ValueError("company_id and version required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.status not in {"PENDING", "GREEN", "RED", "BLOCKED", "HUMAN_REQUIRED"}:
            raise ValueError("invalid bootstrap status")
        if self.status == "GREEN" and not (self.evidence_ref and self.evidence_ref.strip()):
            raise ValueError("GREEN requires evidence_ref")


class GrowthBootstrap:
    def __init__(self, company_id: str, environment: str = "LAB", version: str = "1.0.0") -> None:
        if not company_id.strip() or not version.strip():
            raise ValueError("company_id and version required")
        if environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        self.company_id = company_id
        self.environment = environment
        self.version = version
        self._steps: dict[str, BootstrapStep] = {
            engine_id: BootstrapStep(company_id, engine_id, "PENDING", environment=environment, version=version)
            for engine_id in CANONICAL_GROWTH_SEQUENCE
        }

    def update(self, step: BootstrapStep) -> None:
        step.validate()
        if step.company_id != self.company_id:
            raise ValueError("cross-company bootstrap update denied")
        if step.environment != self.environment or step.version != self.version:
            raise ValueError("cross-scope bootstrap update denied")
        if step.status == "GREEN" and not self.can_advance(step.engine_id):
            raise ValueError("bootstrap dependency incomplete")
        self._steps[step.engine_id] = step

    def next_engine(self) -> str | None:
        for engine_id in CANONICAL_GROWTH_SEQUENCE:
            state = self._steps[engine_id].status
            if state != "GREEN":
                return engine_id
        return None

    def can_advance(self, engine_id: str) -> bool:
        if engine_id not in CANONICAL_GROWTH_SEQUENCE:
            raise ValueError("non-canonical bootstrap engine")
        idx = CANONICAL_GROWTH_SEQUENCE.index(engine_id)
        return all(
            self._steps[e].status == "GREEN"
            and bool(self._steps[e].evidence_ref and self._steps[e].evidence_ref.strip())
            for e in CANONICAL_GROWTH_SEQUENCE[:idx]
        )

    def system_status(self) -> str:
        steps = tuple(self._steps.values())
        if all(
            step.status == "GREEN"
            and bool(step.evidence_ref and step.evidence_ref.strip())
            and step.company_id == self.company_id
            and step.environment == self.environment
            and step.version == self.version
            for step in steps
        ):
            return "GREEN"
        statuses = tuple(step.status for step in steps)
        if "BLOCKED" in statuses:
            return "BLOCKED"
        if "HUMAN_REQUIRED" in statuses:
            return "HUMAN_REQUIRED"
        if "RED" in statuses:
            return "RED"
        return "IN_PROGRESS"
