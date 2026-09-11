from dataclasses import dataclass

DEFAULT_PHASES = (
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
class CompanyOnboardingPlan:
    company_id: str
    phases: tuple[str, ...] = DEFAULT_PHASES
    environment: str = "LAB"
    version: str = "1.0.0"

    def validate(self) -> None:
        if not self.company_id.strip() or not self.version.strip():
            raise ValueError("company_id and version required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.phases != DEFAULT_PHASES:
            raise ValueError("canonical onboarding phase order must be preserved")

    def next_phase(self, completed: tuple[str, ...]) -> str | None:
        self.validate()
        if any(phase not in self.phases for phase in completed):
            raise ValueError("completed contains non-canonical onboarding phase")
        for phase in self.phases:
            if phase not in completed:
                return phase
        return None
