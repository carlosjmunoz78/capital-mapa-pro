from __future__ import annotations

from dataclasses import dataclass

CANONICAL_PHASES = (
    "company_registry",
    "business_discovery",
    "digital_footprint",
    "web_audit",
    "keyword_research",
    "seo",
    "local_seo",
    "social_audit",
    "competitor_intelligence",
    "market_intelligence",
    "marketing",
    "knowledge_bootstrap",
    "crm_bootstrap",
    "app_bootstrap",
    "automation_bootstrap",
    "training_bootstrap",
    "supervisor",
    "backup_rebuild",
)
VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class BootstrapState:
    company_id: str
    required_engine_ids: tuple[str, ...]
    completed_phases: tuple[str, ...] = ()
    failed_phase: str | None = None
    environment: str = "LAB"
    version: str = "1.0.0"
    evidence_by_phase: tuple[tuple[str, str], ...] = ()

    def validate(self, canonical_engine_ids: set[str]) -> None:
        if not self.company_id.strip() or not self.version.strip():
            raise ValueError("company_id and version required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        unknown = set(self.required_engine_ids) - canonical_engine_ids
        if unknown:
            raise ValueError(f"unknown engine ids: {sorted(unknown)}")
        if any(phase not in CANONICAL_PHASES for phase in self.completed_phases):
            raise ValueError("unknown completed phase")
        expected = CANONICAL_PHASES[: len(self.completed_phases)]
        if tuple(self.completed_phases) != expected:
            raise ValueError("completed phases must preserve canonical order")
        if self.failed_phase is not None and self.failed_phase not in CANONICAL_PHASES:
            raise ValueError("unknown failed phase")
        evidence = dict(self.evidence_by_phase)
        if len(evidence) != len(self.evidence_by_phase):
            raise ValueError("duplicate phase evidence")
        if any(phase not in self.completed_phases or not ref.strip() for phase, ref in self.evidence_by_phase):
            raise ValueError("phase evidence must be non-empty and belong to a completed phase")

    def next_phase(self) -> str | None:
        if self.failed_phase:
            return self.failed_phase
        if len(self.completed_phases) >= len(CANONICAL_PHASES):
            return None
        return CANONICAL_PHASES[len(self.completed_phases)]

    @property
    def ready_for_health_gate(self) -> bool:
        evidence = dict(self.evidence_by_phase)
        return (
            self.failed_phase is None
            and len(self.completed_phases) == len(CANONICAL_PHASES)
            and all(evidence.get(phase, "").strip() for phase in CANONICAL_PHASES)
        )


def advance(state: BootstrapState, phase: str, success: bool, *, evidence_ref: str = "", company_id: str | None = None, environment: str | None = None, version: str | None = None) -> BootstrapState:
    expected = state.next_phase()
    if expected is None:
        raise ValueError("bootstrap already complete")
    if phase != expected:
        raise ValueError(f"expected phase {expected}, got {phase}")
    if company_id is not None and company_id != state.company_id:
        raise ValueError("cross-company bootstrap advance denied")
    if environment is not None and environment != state.environment:
        raise ValueError("cross-environment bootstrap advance denied")
    if version is not None and version != state.version:
        raise ValueError("cross-version bootstrap advance denied")
    if not success:
        return BootstrapState(state.company_id, state.required_engine_ids, state.completed_phases, phase, state.environment, state.version, state.evidence_by_phase)
    if not evidence_ref.strip():
        raise ValueError("successful bootstrap phase requires evidence_ref")
    completed = state.completed_phases + (phase,)
    evidence = dict(state.evidence_by_phase)
    evidence[phase] = evidence_ref.strip()
    return BootstrapState(state.company_id, state.required_engine_ids, completed, None, state.environment, state.version, tuple(evidence.items()))
