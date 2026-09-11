from dataclasses import dataclass, field
from typing import Dict, List

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class OutboxEvent:
    event_id: str
    company_id: str
    engine_id: str
    event_type: str
    version: str
    payload_ref: str
    idempotency_key: str
    environment: str = "LAB"

    def validate(self):
        if not all([self.event_id, self.company_id, self.engine_id, self.event_type, self.version, self.payload_ref, self.idempotency_key]):
            raise ValueError("missing outbox event field")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        return True

    @property
    def scope_key(self) -> tuple[str, str, str, str, str]:
        return (self.company_id, self.engine_id, self.environment, self.version, self.idempotency_key)


@dataclass
class Outbox:
    pending: List[OutboxEvent] = field(default_factory=list)
    delivered: set[tuple[str, str, str, str, str]] = field(default_factory=set)
    delivery_evidence: Dict[tuple[str, str, str, str, str], str] = field(default_factory=dict)

    def enqueue(self, event: OutboxEvent):
        event.validate()
        key = event.scope_key
        if key in {e.scope_key for e in self.pending} or key in self.delivered:
            return False
        self.pending.append(event)
        return True

    def mark_delivered(self, event: OutboxEvent, evidence_ref: str):
        event.validate()
        if not isinstance(evidence_ref, str) or not evidence_ref.strip():
            raise ValueError("delivery requires evidence_ref")
        key = event.scope_key
        if key in self.delivered:
            raise ValueError("event already delivered")
        if key not in {e.scope_key for e in self.pending}:
            raise ValueError("event must be pending in the same scope before delivery")
        self.pending = [e for e in self.pending if e.scope_key != key]
        self.delivered.add(key)
        self.delivery_evidence[key] = evidence_ref.strip()
