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
VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


class OnboardingExecutor:
    def __init__(self, company_id: str, *, environment: str = "LAB", version: str = "1.0.0"):
        if not company_id.strip() or not version.strip():
            raise ValueError("company_id and version required")
        if environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        self.company_id = company_id
        self.environment = environment
        self.version = version
        self.completed: list[str] = []
        self.failed: dict[str, str] = {}
        self.evidence_refs: dict[str, tuple[str, ...]] = {}

    def next_phase(self) -> str | None:
        for phase in CANONICAL_PHASES:
            if phase not in self.completed:
                return phase
        return None

    def mark_green(self, phase: str, *, evidence_refs=(), company_id: str | None = None, environment: str | None = None, version: str | None = None) -> None:
        expected = self.next_phase()
        if phase != expected:
            raise ValueError(f"out-of-order phase: expected {expected}, got {phase}")
        if company_id is not None and company_id != self.company_id:
            raise ValueError("cross-company phase update denied")
        if environment is not None and environment != self.environment:
            raise ValueError("cross-environment phase update denied")
        if version is not None and version != self.version:
            raise ValueError("cross-version phase update denied")
        refs = tuple(ref for ref in evidence_refs if isinstance(ref, str) and ref.strip())
        if not refs:
            raise ValueError("green phase requires evidence_refs")
        self.failed.pop(phase, None)
        self.evidence_refs[phase] = refs
        self.completed.append(phase)

    def mark_red(self, phase: str, reason: str) -> None:
        if phase != self.next_phase():
            raise ValueError("only current phase can be marked red")
        if not reason.strip():
            raise ValueError("red phase requires reason")
        self.failed[phase] = reason
        self.evidence_refs.pop(phase, None)

    def retry(self, phase: str) -> None:
        if phase != self.next_phase() or phase not in self.failed:
            raise ValueError("retry requires current failed phase")
        self.failed.pop(phase, None)

    @property
    def state(self) -> str:
        if self.failed:
            return "RED"
        if self.next_phase() is None:
            if all(self.evidence_refs.get(phase) for phase in CANONICAL_PHASES):
                return "GREEN"
            return "RED"
        return "IN_PROGRESS"
