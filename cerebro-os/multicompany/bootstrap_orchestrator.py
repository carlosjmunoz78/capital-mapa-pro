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

@dataclass(frozen=True)
class BootstrapState:
    company_id: str
    required_engine_ids: tuple[str, ...]
    completed_phases: tuple[str, ...] = ()
    failed_phase: str | None = None

    def validate(self, canonical_engine_ids: set[str]) -> None:
        if not self.company_id:
            raise ValueError("company_id required")
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

    def next_phase(self) -> str | None:
        if self.failed_phase:
            return self.failed_phase
        if len(self.completed_phases) >= len(CANONICAL_PHASES):
            return None
        return CANONICAL_PHASES[len(self.completed_phases)]

    @property
    def ready_for_health_gate(self) -> bool:
        return self.failed_phase is None and len(self.completed_phases) == len(CANONICAL_PHASES)


def advance(state: BootstrapState, phase: str, success: bool) -> BootstrapState:
    expected = state.next_phase()
    if expected is None:
        raise ValueError("bootstrap already complete")
    if phase != expected:
        raise ValueError(f"expected phase {expected}, got {phase}")
    if not success:
        return BootstrapState(state.company_id, state.required_engine_ids, state.completed_phases, phase)
    completed = state.completed_phases
    if state.failed_phase == phase:
        completed = completed + (phase,)
    else:
        completed = completed + (phase,)
    return BootstrapState(state.company_id, state.required_engine_ids, completed, None)
