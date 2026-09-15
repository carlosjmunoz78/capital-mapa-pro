from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

INTEGRATION_TARGETS = {
    "CRM",
    "COMPANY_REGISTRY",
    "VENTURE_FACTORY",
    "CONTRACTS",
    "HR",
    "FINANCE",
    "OPERATIONS",
    "EXTENSION",
}

DELIVERY_STATES = {"PENDING", "RETRY", "DELIVERED", "BLOCKED"}


@dataclass(frozen=True)
class AdvisoryIntegrationEvent:
    event_id: str
    idempotency_key: str
    correlation_id: str
    company_id: str
    case_id: str
    target: str
    event_type: str
    payload: Mapping[str, object] = field(default_factory=dict)

    def validate(self) -> None:
        required = (
            self.event_id,
            self.idempotency_key,
            self.correlation_id,
            self.company_id,
            self.case_id,
            self.target,
            self.event_type,
        )
        if not all(value.strip() for value in required):
            raise ValueError("integration event identity fields required")
        if self.target not in INTEGRATION_TARGETS:
            raise ValueError(f"unknown integration target: {self.target}")


@dataclass(frozen=True)
class DeliveryRecord:
    idempotency_key: str
    state: str
    attempts: int
    last_error: str | None = None

    def validate(self) -> None:
        if self.state not in DELIVERY_STATES:
            raise ValueError("invalid delivery state")
        if self.attempts < 0:
            raise ValueError("attempts cannot be negative")


IntegrationAdapter = Callable[[AdvisoryIntegrationEvent], None]


class IntegrationOutbox:
    """Deterministic, side-effect-free-until-injected advisory integration outbox.

    No connector is called unless an adapter is explicitly supplied. Event
    identity is company/case/correlation aware and idempotency keys prevent
    duplicate delivery when workflows retry.
    """

    def __init__(self) -> None:
        self._events: dict[str, AdvisoryIntegrationEvent] = {}
        self._records: dict[str, DeliveryRecord] = {}

    def enqueue(self, event: AdvisoryIntegrationEvent) -> bool:
        event.validate()
        key = event.idempotency_key
        existing = self._events.get(key)
        if existing is not None:
            if existing != event:
                raise ValueError(f"idempotency key collision: {key}")
            return False
        self._events[key] = event
        self._records[key] = DeliveryRecord(key, "PENDING", 0)
        return True

    def record(self, idempotency_key: str) -> DeliveryRecord:
        return self._records[idempotency_key]

    def pending(self) -> tuple[AdvisoryIntegrationEvent, ...]:
        return tuple(
            event
            for key, event in self._events.items()
            if self._records[key].state in {"PENDING", "RETRY"}
        )

    def deliver(
        self,
        adapters: Mapping[str, IntegrationAdapter],
        *,
        max_attempts: int = 3,
    ) -> tuple[DeliveryRecord, ...]:
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")

        for event in self.pending():
            key = event.idempotency_key
            current = self._records[key]
            adapter = adapters.get(event.target)
            if adapter is None:
                self._records[key] = DeliveryRecord(
                    key,
                    "BLOCKED",
                    current.attempts,
                    f"missing adapter:{event.target}",
                )
                continue

            attempts = current.attempts + 1
            try:
                adapter(event)
            except Exception as exc:  # adapter boundary; retain evidence, do not swallow state
                state = "BLOCKED" if attempts >= max_attempts else "RETRY"
                self._records[key] = DeliveryRecord(key, state, attempts, str(exc))
            else:
                self._records[key] = DeliveryRecord(key, "DELIVERED", attempts)

        return tuple(self._records.values())
