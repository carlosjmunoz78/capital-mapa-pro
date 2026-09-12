from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}
VALID_PLATFORMS = {"FACEBOOK", "INSTAGRAM", "LINKEDIN", "YOUTUBE"}
VALID_SIGNAL_TYPES = {"COMMENT", "ENGAGEMENT", "MENTION", "REACTION", "OPPORTUNITY"}
VALID_ENGINE_IDS = {"SOCAUD-001", "SOCBOOT-001", "OPP-001", "MKT-002"}
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class OwnSocialSignal:
    company_id: str
    engine_id: str
    environment: str
    version: str
    platform: str
    signal_type: str
    observed_at: str
    external_id: str
    source_account_id: str
    source_content_id: str
    value: str
    content_hash: str
    evidence_ref: str
    confidence: float
    cost_units: float = 0.0

    def validate(self) -> None:
        required = (
            self.company_id,
            self.engine_id,
            self.environment,
            self.version,
            self.platform,
            self.signal_type,
            self.observed_at,
            self.external_id,
            self.source_account_id,
            self.source_content_id,
            self.content_hash,
            self.evidence_ref,
        )
        if not all(str(value).strip() for value in required):
            raise ValueError("own social signal missing required field")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.platform not in VALID_PLATFORMS:
            raise ValueError("invalid platform")
        if self.signal_type not in VALID_SIGNAL_TYPES:
            raise ValueError("invalid signal_type")
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
    def dedupe_key(self) -> tuple[str, str, str, str]:
        return (
            self.platform,
            self.source_account_id,
            self.external_id,
            self.content_hash.lower(),
        )


@dataclass
class OwnSocialSignalStore:
    company_id: str
    environment: str = "LAB"
    version: str = "1.0.0"
    signals: list[OwnSocialSignal] = field(default_factory=list)
    _seen: set[tuple[str, str, str, str]] = field(default_factory=set, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.company_id.strip() or not self.version.strip():
            raise ValueError("company_id and version are required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")

    def add(self, signal: OwnSocialSignal) -> bool:
        signal.validate()
        if signal.company_id != self.company_id:
            raise ValueError("cross-company own social signal denied")
        if signal.environment != self.environment or signal.version != self.version:
            raise ValueError("cross-environment/version own social signal denied")
        if signal.dedupe_key in self._seen:
            return False
        self._seen.add(signal.dedupe_key)
        self.signals.append(signal)
        return True

    def by_platform(self, platform: str) -> tuple[OwnSocialSignal, ...]:
        if platform not in VALID_PLATFORMS:
            raise ValueError("invalid platform")
        return tuple(item for item in self.signals if item.platform == platform)

    def cost_units(self) -> float:
        return sum(item.cost_units for item in self.signals)
