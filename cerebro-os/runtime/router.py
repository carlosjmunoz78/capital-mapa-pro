from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from sqlite_store import SQLiteRuntimeStore

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class RouteDecision:
    company_id: str
    engine_id: str
    route_id: str
    operation_type: str
    external_id: str
    destination: str
    status: str
    message: str
    environment: str = "LAB"
    version: str = "1.0.0"
    network: str | None = None
    run_id: str | None = None
    requires_human: bool = False
    automatic_action: str = "EMIT_ROUTE_DECISION_ONLY"
    evidence_ref: str | None = None

    def validate(self) -> None:
        required = (
            self.company_id,
            self.engine_id,
            self.route_id,
            self.operation_type,
            self.external_id,
            self.destination,
            self.status,
            self.message,
            self.version,
        )
        if any(not str(value or "").strip() for value in required):
            raise ValueError("route decision missing required fields")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.automatic_action != "EMIT_ROUTE_DECISION_ONLY":
            raise ValueError("router may only emit a decision; external action is forbidden")

    @property
    def effective_run_id(self) -> str:
        return self.run_id.strip() if self.run_id and self.run_id.strip() else datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")[:-3]


class DeterministicRouter:
    KIND = "router_decision"

    def __init__(self, store: SQLiteRuntimeStore):
        self.store = store

    def emit(self, decision: RouteDecision) -> dict:
        decision.validate()
        run_id = decision.effective_run_id
        payload = asdict(decision)
        payload.update({
            "run_id": run_id,
            "phase": "routing",
            "record_type": self.KIND,
            "first_seen_at": utc_now(),
            "last_seen_at": utc_now(),
        })
        inserted = self.store.put(
            kind=self.KIND,
            idempotency_key=decision.route_id,
            company_id=decision.company_id,
            engine_id=decision.engine_id,
            version=decision.version,
            environment=decision.environment,
            payload=payload,
        )
        return {
            "emitted": inserted,
            "status": decision.status if inserted else "DUPLICATE_ROUTE_BLOCKED",
            "run_id": run_id,
            "destination": decision.destination,
            "external_action_executed": False,
        }
