from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


class SQLiteRuntimeStore:
    """Zero-additional-cost persistence for events/jobs/audit history.

    Runtime identity and idempotency are scoped by company, engine and environment so
    one tenant cannot suppress another tenant's legitimate record.
    """

    def __init__(self, path: str | Path):
        self.path = str(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._migrate()

    def _create_runtime_table(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS runtime_records (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              kind TEXT NOT NULL,
              idempotency_key TEXT NOT NULL,
              company_id TEXT NOT NULL,
              engine_id TEXT NOT NULL,
              version TEXT NOT NULL,
              environment TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'PENDING',
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              UNIQUE(kind, idempotency_key, company_id, engine_id, environment)
            );
            CREATE INDEX IF NOT EXISTS idx_runtime_company_engine
              ON runtime_records(company_id, engine_id, environment, kind);
            """
        )

    def _migrate(self) -> None:
        existing = self.conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='runtime_records'"
        ).fetchone()
        old_global_idempotency = bool(existing and existing[0] and "UNIQUE(kind, idempotency_key)" in existing[0])
        if old_global_idempotency:
            self.conn.execute("ALTER TABLE runtime_records RENAME TO runtime_records_legacy")
            self._create_runtime_table()
            self.conn.execute(
                """
                INSERT OR IGNORE INTO runtime_records(
                  id,kind,idempotency_key,company_id,engine_id,version,environment,
                  payload_json,status,created_at
                )
                SELECT id,kind,idempotency_key,company_id,engine_id,version,environment,
                       payload_json,status,created_at
                FROM runtime_records_legacy
                """
            )
            self.conn.execute("DROP TABLE runtime_records_legacy")
        else:
            self._create_runtime_table()
        self.conn.commit()

    def put(self, *, kind: str, idempotency_key: str, company_id: str, engine_id: str,
            version: str, environment: str, payload: dict[str, Any]) -> bool:
        if not all([kind, idempotency_key, company_id, engine_id, version, environment]):
            raise ValueError("runtime record missing required identity fields")
        if environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        try:
            self.conn.execute(
                "INSERT INTO runtime_records(kind,idempotency_key,company_id,engine_id,version,environment,payload_json) VALUES(?,?,?,?,?,?,?)",
                (kind, idempotency_key, company_id, engine_id, version, environment, json.dumps(payload, ensure_ascii=False, sort_keys=True)),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def list_for_company(self, company_id: str) -> list[dict[str, Any]]:
        if not company_id:
            raise ValueError("company_id is required")
        rows = self.conn.execute(
            "SELECT kind,idempotency_key,company_id,engine_id,version,environment,payload_json,status FROM runtime_records WHERE company_id=? ORDER BY id",
            (company_id,),
        ).fetchall()
        return [
            {"kind": r[0], "idempotency_key": r[1], "company_id": r[2], "engine_id": r[3], "version": r[4], "environment": r[5], "payload": json.loads(r[6]), "status": r[7]}
            for r in rows
        ]

    def close(self) -> None:
        self.conn.close()
