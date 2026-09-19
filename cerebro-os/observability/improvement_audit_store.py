from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class ImprovementAuditRecord:
    company_id: str
    engine_id: str
    environment: str
    version: str
    cycle_id: str
    stage: str
    status: str
    evidence_ref: str
    old_ref: str | None = None
    new_ref: str | None = None
    rollback_ref: str | None = None
    cost_eur: float = 0.0
    occurred_at: str = ""

    def validate(self) -> None:
        required = (self.company_id, self.engine_id, self.environment, self.version, self.cycle_id, self.stage, self.status, self.evidence_ref)
        if not all(x and x.strip() for x in required):
            raise ValueError("complete audit scope and evidence required")
        if self.cost_eur < 0:
            raise ValueError("cost_eur cannot be negative")

    def canonical(self) -> dict:
        self.validate()
        return asdict(self)


class ImprovementAuditStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS improvement_audit (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id TEXT NOT NULL,
                environment TEXT NOT NULL,
                cycle_id TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                record_hash TEXT NOT NULL UNIQUE
            )
            """
        )
        self.conn.commit()

    def append(self, record: ImprovementAuditRecord) -> str:
        payload = record.canonical()
        if not payload["occurred_at"]:
            payload["occurred_at"] = datetime.now(timezone.utc).isoformat()
        previous = self.conn.execute(
            "SELECT record_hash FROM improvement_audit WHERE company_id=? AND environment=? ORDER BY seq DESC LIMIT 1",
            (record.company_id, record.environment),
        ).fetchone()
        previous_hash = previous[0] if previous else "GENESIS"
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        record_hash = hashlib.sha256((previous_hash + encoded).encode()).hexdigest()
        self.conn.execute(
            "INSERT INTO improvement_audit(company_id,environment,cycle_id,payload_json,previous_hash,record_hash) VALUES(?,?,?,?,?,?)",
            (record.company_id, record.environment, record.cycle_id, encoded, previous_hash, record_hash),
        )
        self.conn.commit()
        return record_hash

    def verify_chain(self, *, company_id: str, environment: str) -> bool:
        rows = self.conn.execute(
            "SELECT payload_json,previous_hash,record_hash FROM improvement_audit WHERE company_id=? AND environment=? ORDER BY seq",
            (company_id, environment),
        ).fetchall()
        previous = "GENESIS"
        for payload, stored_previous, stored_hash in rows:
            if stored_previous != previous:
                return False
            calculated = hashlib.sha256((previous + payload).encode()).hexdigest()
            if calculated != stored_hash:
                return False
            previous = stored_hash
        return True

    def cycle_records(self, *, company_id: str, environment: str, cycle_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT payload_json,record_hash FROM improvement_audit WHERE company_id=? AND environment=? AND cycle_id=? ORDER BY seq",
            (company_id, environment, cycle_id),
        ).fetchall()
        return [{**json.loads(payload), "record_hash": digest} for payload, digest in rows]

    def close(self) -> None:
        self.conn.close()
