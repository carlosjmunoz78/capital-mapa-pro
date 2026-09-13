import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Union

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}
VALID_KINDS = {"log", "metric", "incident"}


@dataclass(frozen=True)
class ObservabilityEvent:
    company_id: str
    engine_id: str
    environment: str
    version: str
    kind: str
    name: str
    payload: dict
    evidence_ref: str
    cost_eur: float = 0.0

    def validate(self):
        required = (self.company_id, self.engine_id, self.environment, self.version, self.kind, self.name, self.evidence_ref)
        if any(not str(v).strip() for v in required):
            raise ValueError("observability event missing required identity/evidence fields")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.kind not in VALID_KINDS:
            raise ValueError("invalid observability kind")
        if self.cost_eur < 0:
            raise ValueError("cost_eur must be non-negative")
        if not isinstance(self.payload, dict):
            raise ValueError("payload must be a dict")


class SQLiteObservabilityStore:
    """Zero-subscription local/shared-worker observability sink.

    Intended for CEREBRO runtime evidence and heavy auxiliary telemetry outside the
    transactional App/CRM database. A deployment may point this at a persistent
    worker volume. It does not claim PROD live coverage by itself.
    """

    def __init__(self, path: Union[str, Path]):
        self.path = str(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute(
            """
            create table if not exists observability_events (
                id integer primary key autoincrement,
                company_id text not null,
                engine_id text not null,
                environment text not null,
                version text not null,
                kind text not null,
                name text not null,
                payload_json text not null,
                evidence_ref text not null,
                cost_eur real not null default 0,
                created_at text not null default (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            )
            """
        )
        self.conn.execute(
            "create index if not exists idx_obs_scope on observability_events(company_id,engine_id,environment,version,kind)"
        )
        self.conn.commit()

    def append(self, event):
        event.validate()
        cur = self.conn.execute(
            "insert into observability_events(company_id,engine_id,environment,version,kind,name,payload_json,evidence_ref,cost_eur) values(?,?,?,?,?,?,?,?,?)",
            (
                event.company_id,
                event.engine_id,
                event.environment,
                event.version,
                event.kind,
                event.name,
                json.dumps(event.payload, sort_keys=True, separators=(",", ":")),
                event.evidence_ref,
                float(event.cost_eur),
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def coverage(self, company_id, environment, engine_ids):
        required = set(engine_ids)
        by_kind = {}
        for kind in sorted(VALID_KINDS):
            rows = self.conn.execute(
                "select distinct engine_id from observability_events where company_id=? and environment=? and kind=?",
                (company_id, environment, kind),
            ).fetchall()
            by_kind[kind] = {r[0] for r in rows}
        return {
            "company_id": company_id,
            "environment": environment,
            "required_engine_count": len(required),
            "log_engine_count": len(by_kind["log"] & required),
            "metric_engine_count": len(by_kind["metric"] & required),
            "incident_engine_count": len(by_kind["incident"] & required),
            "all_required_engines_have_log": required <= by_kind["log"],
            "all_required_engines_have_metric": required <= by_kind["metric"],
            "all_required_engines_have_incident": required <= by_kind["incident"],
            "additional_subscription_required": False,
        }

    def close(self):
        self.conn.close()
