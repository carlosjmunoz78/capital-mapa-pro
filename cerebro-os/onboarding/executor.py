from __future__ import annotations

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


class OnboardingExecutor:
    def __init__(self, company_id: str):
        if not company_id:
            raise ValueError("company_id required")
        self.company_id = company_id
        self.completed: list[str] = []
        self.failed: dict[str, str] = {}

    def next_phase(self) -> str | None:
        for phase in CANONICAL_PHASES:
            if phase not in self.completed:
                return phase
        return None

    def mark_green(self, phase: str) -> None:
        expected = self.next_phase()
        if phase != expected:
            raise ValueError(f"out-of-order phase: expected {expected}, got {phase}")
        self.failed.pop(phase, None)
        self.completed.append(phase)

    def mark_red(self, phase: str, reason: str) -> None:
        if phase != self.next_phase():
            raise ValueError("only current phase can be marked red")
        if not reason:
            raise ValueError("red phase requires reason")
        self.failed[phase] = reason

    def retry(self, phase: str) -> None:
        if phase != self.next_phase() or phase not in self.failed:
            raise ValueError("retry requires current failed phase")
        self.failed.pop(phase, None)

    @property
    def state(self) -> str:
        if self.failed:
            return "RED"
        if self.next_phase() is None:
            return "GREEN"
        return "IN_PROGRESS"
