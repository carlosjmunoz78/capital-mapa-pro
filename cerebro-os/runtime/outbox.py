from dataclasses import dataclass, field
from typing import List

@dataclass(frozen=True)
class OutboxEvent:
    event_id: str
    company_id: str
    engine_id: str
    event_type: str
    version: str
    payload_ref: str
    idempotency_key: str

    def validate(self):
        if not all([self.event_id, self.company_id, self.engine_id, self.event_type, self.version, self.idempotency_key]):
            raise ValueError("missing outbox event field")
        return True

@dataclass
class Outbox:
    pending: List[OutboxEvent] = field(default_factory=list)
    delivered: set = field(default_factory=set)

    def enqueue(self, event: OutboxEvent):
        event.validate()
        if event.idempotency_key in {e.idempotency_key for e in self.pending} or event.idempotency_key in self.delivered:
            return False
        self.pending.append(event); return True

    def mark_delivered(self, idempotency_key: str):
        self.pending = [e for e in self.pending if e.idempotency_key != idempotency_key]
        self.delivered.add(idempotency_key)
