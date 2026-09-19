from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

VALID_STATUSES = {"OPEN", "WAITING_TEST", "BLOCKED", "HUMAN_REQUIRED", "CLOSED"}
VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}

_PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


@dataclass(frozen=True)
class ProposalRecord:
    company_id: str
    proposal_id: str
    source_key: str
    domain: str
    environment: str
    version: str
    summary: str
    evidence_ref: str
    action: str
    external_mutation_allowed: bool
    cost_limit_eur: float
    priority: str = "P2"
    status: str = "OPEN"

    def validate(self) -> None:
        required = (
            self.company_id, self.proposal_id, self.source_key, self.domain,
            self.environment, self.version, self.summary, self.evidence_ref, self.action,
        )
        if not all(str(x).strip() for x in required):
            raise ValueError("complete proposal identity required")
        if self.priority not in VALID_PRIORITIES:
            raise ValueError("invalid proposal priority")
        if self.status not in VALID_STATUSES:
            raise ValueError("invalid proposal status")
        if self.cost_limit_eur < 0:
            raise ValueError("cost_limit_eur cannot be negative")
        if self.external_mutation_allowed:
            raise ValueError("proposal queue V0 does not allow external mutation")

    def fingerprint(self) -> str:
        self.validate()
        key = "\0".join((
            self.company_id, self.source_key, self.domain,
            self.environment, self.version, self.evidence_ref, self.action,
        ))
        return hashlib.sha256(key.encode("utf-8")).hexdigest()


class ProposalQueue:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS proposal_queue(
              fingerprint TEXT PRIMARY KEY,
              company_id TEXT NOT NULL,
              proposal_id TEXT NOT NULL,
              priority TEXT NOT NULL,
              status TEXT NOT NULL,
              payload_json TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def upsert(self, record: ProposalRecord) -> str:
        fp = record.fingerprint()
        payload = json.dumps(record.__dict__, sort_keys=True)
        self.conn.execute(
            """
            INSERT INTO proposal_queue(fingerprint,company_id,proposal_id,priority,status,payload_json)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(fingerprint) DO UPDATE SET
              proposal_id=excluded.proposal_id,
              priority=excluded.priority,
              payload_json=excluded.payload_json
            """,
            (fp, record.company_id, record.proposal_id, record.priority, record.status, payload),
        )
        self.conn.commit()
        return fp

    def list_open(self, *, company_id: str | None = None) -> tuple[ProposalRecord, ...]:
        if company_id:
            rows = self.conn.execute(
                "SELECT payload_json FROM proposal_queue WHERE company_id=? AND status IN ('OPEN','WAITING_TEST')",
                (company_id,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT payload_json FROM proposal_queue WHERE status IN ('OPEN','WAITING_TEST')"
            ).fetchall()
        items = [ProposalRecord(**json.loads(row[0])) for row in rows]
        items.sort(key=lambda x: (_PRIORITY_ORDER[x.priority], x.company_id, x.proposal_id))
        return tuple(items)

    def set_status(self, fingerprint: str, status: str) -> None:
        if status not in VALID_STATUSES:
            raise ValueError("invalid proposal status")
        row = self.conn.execute(
            "SELECT payload_json FROM proposal_queue WHERE fingerprint=?", (fingerprint,)
        ).fetchone()
        if row is None:
            raise ValueError("proposal not found")
        data = json.loads(row[0])
        data["status"] = status
        self.conn.execute(
            "UPDATE proposal_queue SET status=?, payload_json=? WHERE fingerprint=?",
            (status, json.dumps(data, sort_keys=True), fingerprint),
        )
        self.conn.commit()

    def count(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) FROM proposal_queue").fetchone()[0])

    def summary(self) -> dict:
        items = self.list_open()
        return {
            "queued": len(items),
            "companies": sorted({item.company_id for item in items}),
            "priorities": {
                priority: sum(1 for item in items if item.priority == priority)
                for priority in ("P0", "P1", "P2", "P3")
            },
            "domains": {
                domain: sum(1 for item in items if item.domain == domain)
                for domain in sorted({item.domain for item in items})
            },
            "top": [
                {
                    "company_id": item.company_id,
                    "proposal_id": item.proposal_id,
                    "priority": item.priority,
                    "status": item.status,
                    "domain": item.domain,
                    "summary": item.summary,
                    "evidence_ref": item.evidence_ref,
                }
                for item in items[:20]
            ],
        }

    def close(self) -> None:
        self.conn.close()
