from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}
VALID_SOURCE_TYPES = {"WEB", "SEARCH", "SOCIAL", "LOCAL", "RSS", "API", "DIRECTORY", "NEWS"}
VALID_ENGINE_IDS = {"COMPET-001", "MKT-002", "RSH-001", "SCAN-001", "KW-001", "SOCAUD-001", "LOCALP-001"}
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class CompetitorObservation:
    company_id: str
    competitor_id: str
    engine_id: str
    environment: str
    version: str
    source: str
    source_type: str
    observed_at: str
    url_or_external_id: str
    metric_or_fact: str
    value: str
    content_hash: str
    evidence_ref: str
    confidence: float
    cost_units: float = 0.0

    def validate(self) -> None:
        required = (
            self.company_id,
            self.competitor_id,
            self.engine_id,
            self.version,
            self.source,
            self.source_type,
            self.observed_at,
            self.url_or_external_id,
            self.metric_or_fact,
            self.content_hash,
            self.evidence_ref,
        )
        if not all(str(value).strip() for value in required):
            raise ValueError("competitor observation missing required field")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.source_type not in VALID_SOURCE_TYPES:
            raise ValueError("invalid source_type")
        if self.engine_id not in VALID_ENGINE_IDS:
            raise ValueError("invalid engine_id")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.cost_units < 0:
            raise ValueError("cost_units cannot be negative")
        if not _SHA256_RE.fullmatch(self.content_hash.lower()):
            raise ValueError("content_hash must be sha256 hex")
        try:
            observed = datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("observed_at must be ISO-8601") from exc
        if observed.tzinfo is None:
            raise ValueError("observed_at must include timezone")

    @property
    def dedupe_key(self) -> tuple[str, str, str, str, str]:
        return (
            self.competitor_id,
            self.source,
            self.url_or_external_id,
            self.metric_or_fact,
            self.content_hash.lower(),
        )


@dataclass
class CompetitorObservationStore:
    company_id: str
    environment: str = "LAB"
    version: str = "1.0.0"
    observations: list[CompetitorObservation] = field(default_factory=list)
    _seen: set[tuple[str, str, str, str, str]] = field(default_factory=set, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.company_id.strip() or not self.version.strip():
            raise ValueError("company_id and version are required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")

    def add(self, observation: CompetitorObservation) -> bool:
        observation.validate()
        if observation.company_id != self.company_id:
            raise ValueError("cross-company competitor observation denied")
        if observation.environment != self.environment or observation.version != self.version:
            raise ValueError("cross-environment/version competitor observation denied")
        if observation.dedupe_key in self._seen:
            return False
        self._seen.add(observation.dedupe_key)
        self.observations.append(observation)
        return True

    def by_competitor(self, competitor_id: str) -> tuple[CompetitorObservation, ...]:
        if not competitor_id.strip():
            raise ValueError("competitor_id is required")
        return tuple(item for item in self.observations if item.competitor_id == competitor_id)

    def cost_units(self) -> float:
        return sum(item.cost_units for item in self.observations)
