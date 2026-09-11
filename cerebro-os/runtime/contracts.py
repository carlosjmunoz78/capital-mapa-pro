from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


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

    def to_dict(self) -> dict:
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

    def to_dict(self) -> dict:
        return asdict(self)
