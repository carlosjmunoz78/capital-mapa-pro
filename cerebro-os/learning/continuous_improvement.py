from __future__ import annotations

from dataclasses import dataclass

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}
AUTONOMY_PROFILES = {"FENIX_SENSITIVE", "FENIX_DIGITAL", "AUTONOMOUS_VENTURE"}
REQUIRED_PROMOTION_EVIDENCE = (
    "baseline", "candidate", "tests", "evaluation", "tribunal",
    "rollback", "backup", "observability", "cost", "policy",
)


@dataclass(frozen=True)
class ImprovementObjective:
    company_id: str
    engine_id: str
    domain: str
    metric: str
    baseline: float
    direction: str
    autonomy_profile: str
    environment: str = "LAB"
    version: str = "1.0.0"

    def validate(self) -> None:
        if not all((self.company_id.strip(), self.engine_id.strip(), self.domain.strip(), self.metric.strip(), self.version.strip())):
            raise ValueError("improvement objective identity required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.direction not in {"MAXIMIZE", "MINIMIZE"}:
            raise ValueError("direction must be MAXIMIZE or MINIMIZE")
        if self.autonomy_profile not in AUTONOMY_PROFILES:
            raise ValueError("invalid autonomy profile")


@dataclass(frozen=True)
class ImprovementCandidate:
    objective: ImprovementObjective
    candidate_version: str
    candidate_value: float
    evidence_refs: tuple[tuple[str, str], ...]
    risk: str = "LOW"
    cost_delta_eur: float = 0.0
    reversible: bool = True

    def validate(self) -> None:
        self.objective.validate()
        if not self.candidate_version.strip():
            raise ValueError("candidate_version required")
        refs = dict(self.evidence_refs)
        if len(refs) != len(self.evidence_refs):
            raise ValueError("duplicate evidence keys")
        if any(not str(refs.get(key, "")).strip() for key in REQUIRED_PROMOTION_EVIDENCE):
            raise ValueError("candidate promotion evidence incomplete")

    @property
    def improves_baseline(self) -> bool:
        if self.objective.direction == "MAXIMIZE":
            return self.candidate_value > self.objective.baseline
        return self.candidate_value < self.objective.baseline


@dataclass(frozen=True)
class ImprovementDecision:
    decision: str
    reasons: tuple[str, ...]
    next_stage: str


def decide(candidate: ImprovementCandidate) -> ImprovementDecision:
    candidate.validate()
    profile = candidate.objective.autonomy_profile

    if not candidate.improves_baseline:
        return ImprovementDecision("REJECT", ("NO_MEASURED_IMPROVEMENT",), "LEARN")
    if not candidate.reversible:
        return ImprovementDecision("HUMAN_REQUIRED", ("HIGH_RISK",), "HUMAN")
    if candidate.risk.upper() == "HIGH":
        return ImprovementDecision("HUMAN_REQUIRED", ("HIGH_RISK",), "HUMAN")
    if candidate.cost_delta_eur > 0:
        return ImprovementDecision("HUMAN_REQUIRED", ("MONEY_LIMIT",), "HUMAN")

    if profile == "FENIX_SENSITIVE":
        return ImprovementDecision("HUMAN_REQUIRED", ("HIGH_RISK",), "HUMAN")
    if candidate.objective.environment == "PROD":
        return ImprovementDecision("PROMOTE_CANDIDATE", (), "CANARY")
    return ImprovementDecision("PROMOTE_CANDIDATE", (), "PREPROD")


@dataclass(frozen=True)
class DailyImprovementCycle:
    company_id: str
    autonomy_profile: str
    environment: str = "LAB"
    version: str = "1.0.0"

    def stages(self) -> tuple[str, ...]:
        if self.autonomy_profile not in AUTONOMY_PROFILES:
            raise ValueError("invalid autonomy profile")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        return (
            "OBSERVE", "MEASURE", "DETECT", "PROPOSE", "LAB", "TEST",
            "EVALUATE", "TRIBUNAL", "OLD_VS_NEW", "CANARY",
            "PROMOTE_OR_ROLLBACK", "LEARN",
        )

    @property
    def automatic_by_default(self) -> bool:
        return self.autonomy_profile in {"FENIX_DIGITAL", "AUTONOMOUS_VENTURE"}
