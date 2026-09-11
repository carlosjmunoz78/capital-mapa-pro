from __future__ import annotations

from dataclasses import dataclass, field

CANONICAL_DISCOVERY_ENGINES = (
    "SCAN-001",
    "KW-001",
    "WAUD-001",
    "SOCAUD-001",
    "LOCALP-001",
    "COMPET-001",
    "RSH-001",
)
VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class DiscoveryFinding:
    company_id: str
    engine_id: str
    subject: str
    evidence_ref: str
    confidence: float
    status: str = "FOUND"
    environment: str = "LAB"
    version: str = "1.0.0"

    def validate(self) -> None:
        if self.engine_id not in CANONICAL_DISCOVERY_ENGINES:
            raise ValueError("engine_id is not part of canonical discovery group")
        if not self.company_id.strip() or not self.subject.strip() or not self.evidence_ref.strip() or not self.version.strip():
            raise ValueError("company_id, subject, evidence_ref and version are required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass
class DiscoveryRun:
    company_id: str
    environment: str = "LAB"
    version: str = "1.0.0"
    findings: list[DiscoveryFinding] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.company_id.strip() or not self.version.strip():
            raise ValueError("company_id and version are required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")

    def add(self, finding: DiscoveryFinding) -> None:
        finding.validate()
        if finding.company_id != self.company_id:
            raise ValueError("cross-company discovery finding denied")
        if finding.environment != self.environment or finding.version != self.version:
            raise ValueError("cross-environment/version discovery finding denied")
        self.findings.append(finding)

    def engine_status(self, engine_id: str, min_confidence: float = 0.70) -> str:
        if engine_id not in CANONICAL_DISCOVERY_ENGINES:
            raise ValueError("unknown discovery engine")
        matches = [
            f for f in self.findings
            if f.engine_id == engine_id and f.environment == self.environment and f.version == self.version
        ]
        if not matches:
            return "UNKNOWN"
        if any(f.confidence < min_confidence for f in matches):
            return "HUMAN_REQUIRED"
        return "GREEN"

    def summary(self) -> dict[str, str]:
        return {engine_id: self.engine_status(engine_id) for engine_id in CANONICAL_DISCOVERY_ENGINES}
