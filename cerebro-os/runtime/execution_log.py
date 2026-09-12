from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from sqlite_store import SQLiteRuntimeStore

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}
VALID_PHASES = {"start", "final"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ExecutionLogEntry:
    company_id: str
    engine_id: str
    scenario_id: str
    operation_type: str
    external_id: str
    run_id: str
    phase: str
    status: str
    message: str
    environment: str = "LAB"
    version: str = "1.0.0"
    network: str | None = None
    attempts: int = 0
    severity: str = "informative"
    requires_human: bool = False
    automatic_action: str | None = None
    notion_record_id: str | None = None
    first_seen_at: str | None = None
    last_seen_at: str | None = None

    def validate(self) -> None:
        required = (
            self.company_id,
            self.engine_id,
            self.scenario_id,
            self.operation_type,
            self.external_id,
            self.run_id,
            self.phase,
            self.status,
            self.message,
            self.version,
        )
        if any(not str(value or "").strip() for value in required):
            raise ValueError("execution log entry missing required fields")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.phase not in VALID_PHASES:
            raise ValueError("invalid phase")
        if self.attempts < 0:
            raise ValueError("attempts must be non-negative")

    @property
    def storage_key(self) -> str:
        return f"{self.run_id}:{self.phase}"


class ExecutionLogStore:
    KIND = "execution_log"

    def __init__(self, store: SQLiteRuntimeStore):
        self.store = store

    def append(self, entry: ExecutionLogEntry) -> bool:
        entry.validate()
        now = utc_now()
        payload = asdict(entry)
        payload["record_type"] = self.KIND
        payload["first_seen_at"] = entry.first_seen_at or now
        payload["last_seen_at"] = entry.last_seen_at or now
        return self.store.put(
            kind=self.KIND,
            idempotency_key=entry.storage_key,
            company_id=entry.company_id,
            engine_id=entry.engine_id,
            version=entry.version,
            environment=entry.environment,
            payload=payload,
        )

    def start(self, **kwargs) -> ExecutionLogEntry:
        entry = ExecutionLogEntry(phase="start", status="STARTED", **kwargs)
        if not self.append(entry):
            raise ValueError("duplicate start execution log")
        return entry

    def finish(self, *, first_seen_at: str | None = None, **kwargs) -> ExecutionLogEntry:
        entry = ExecutionLogEntry(phase="final", first_seen_at=first_seen_at, **kwargs)
        if not self.append(entry):
            raise ValueError("duplicate final execution log")
        return entry
