from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}
EVIDENCE_REQUIRED_RESULTS = {"SUCCESS", "GREEN", "ALLOW_EXECUTION", "DELIVERED", "COMPLETED"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class EventEnvelope:
    event_type: str
    engine_id: str
    company_id: str
    environment: str = "LAB"
    version: str = "0.1.0"
    payload: dict = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)

    def validate(self) -> None:
        required = (self.event_type, self.engine_id, self.company_id, self.version, self.request_id, self.created_at)
        if any(not value or not str(value).strip() for value in required):
            raise ValueError("event envelope missing required identity fields")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if not isinstance(self.payload, dict):
            raise ValueError("payload must be a dict")

    def to_dict(self) -> dict:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class AuditRecord:
    request_id: str
    company_id: str
    engine_id: str
    version: str
    environment: str
    action: str
    policy_result: str
    result: str
    duration_ms: int
    cost_eur: float = 0.0
    evidence_ref: str | None = None
    timestamp: str = field(default_factory=utc_now)

    def validate(self) -> None:
        required = (
            self.request_id, self.company_id, self.engine_id, self.version,
            self.action, self.policy_result, self.result, self.timestamp,
        )
        if any(not value or not str(value).strip() for value in required):
            raise ValueError("audit record missing required fields")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.duration_ms < 0 or self.cost_eur < 0:
            raise ValueError("duration and cost must be non-negative")
        if self.result in EVIDENCE_REQUIRED_RESULTS and not str(self.evidence_ref or "").strip():
            raise ValueError("successful audit result requires evidence_ref")

    def to_dict(self) -> dict:
        self.validate()
        return asdict(self)
