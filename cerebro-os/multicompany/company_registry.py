from __future__ import annotations

from dataclasses import dataclass

VALID_STATES = {
    "DISCOVERED", "REGISTERED", "AUTHORIZED", "SCANNING", "PROFILED",
    "DIGITAL_FOUNDATION_READY", "SEO_SOCIAL_READY", "CRM_READY", "APP_READY",
    "AUTOMATIONS_READY", "TRAINING_READY", "PREPROD_READY", "PRODUCTION", "OPTIMIZING"
}
VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class CompanyRecord:
    company_id: str
    legal_name: str
    environment: str = "LAB"
    state: str = "DISCOVERED"
    version: str = "0.1.0"

    def validate(self) -> None:
        if not all((self.company_id.strip(), self.legal_name.strip(), self.version.strip())):
            raise ValueError("company_id, legal_name and version required")
        if self.state not in VALID_STATES:
            raise ValueError(f"invalid company state: {self.state}")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError(f"invalid environment: {self.environment}")
