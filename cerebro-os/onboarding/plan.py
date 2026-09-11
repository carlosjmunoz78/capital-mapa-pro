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

@dataclass(frozen=True)
class CompanyOnboardingPlan:
    company_id: str
    phases: tuple[str, ...] = DEFAULT_PHASES

    def validate(self) -> None:
        if not self.company_id:
            raise ValueError("company_id required")
        if self.phases != DEFAULT_PHASES:
            raise ValueError("canonical onboarding phase order must be preserved")

    def next_phase(self, completed: tuple[str, ...]) -> str | None:
        self.validate()
        for phase in self.phases:
            if phase not in completed:
                return phase
        return None
