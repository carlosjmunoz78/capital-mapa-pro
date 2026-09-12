from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from sqlite_store import SQLiteRuntimeStore

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class IdempotencyClaim:
    idempotency_key: str
    company_id: str
    engine_id: str
    operation_type: str
    external_id: str
    environment: str = "LAB"
    version: str = "1.0.0"
    network: str | None = None
    run_id: str | None = None

    def validate(self) -> None:
        required = (
            self.idempotency_key,
            self.company_id,
            self.engine_id,
            self.operation_type,
            self.external_id,
            self.version,
        )
        if any(not str(value or "").strip() for value in required):
            raise ValueError("idempotency claim missing required identity fields")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")

    @property
    def effective_run_id(self) -> str:
        if self.run_id and self.run_id.strip():
            return self.run_id.strip()
        return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")[:-3]


class IdempotencyRegistry:
    """Deterministic replacement target for Make CORE 9524837.

    Claims are persisted in SQLite and isolated by company_id, engine_id,
    environment and version. Duplicate claims in the same scope are blocked.
    """

    KIND = "idempotency"

    def __init__(self, store: SQLiteRuntimeStore):
        self.store = store

    def claim(self, claim: IdempotencyClaim) -> dict:
        claim.validate()
        run_id = claim.effective_run_id
        payload = asdict(claim)
        payload["run_id"] = run_id
        payload["phase"] = "pre_execution"
        payload["first_seen_at"] = utc_now()
        payload["last_seen_at"] = payload["first_seen_at"]
        payload["record_type"] = self.KIND

        inserted = self.store.put(
            kind=self.KIND,
            idempotency_key=claim.idempotency_key,
            company_id=claim.company_id,
            engine_id=claim.engine_id,
            version=claim.version,
            environment=claim.environment,
            payload=payload,
        )

        if inserted:
            return {
                "allowed": True,
                "status": "FIRST_SEEN",
                "automatic_action": "REGISTER_IDEMPOTENCY_KEY",
                "run_id": run_id,
                "scope": {
                    "company_id": claim.company_id,
                    "engine_id": claim.engine_id,
                    "environment": claim.environment,
                    "version": claim.version,
                },
            }
        return {
            "allowed": False,
            "status": "BLOCKED_DUPLICATE",
            "automatic_action": "BLOCK_FOLLOWING_ACTION",
            "run_id": run_id,
            "scope": {
                "company_id": claim.company_id,
                "engine_id": claim.engine_id,
                "environment": claim.environment,
                "version": claim.version,
            },
        }
