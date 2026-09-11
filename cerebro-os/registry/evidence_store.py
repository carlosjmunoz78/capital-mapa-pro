from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from uuid import uuid4

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


class EvidenceStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evidence (
                evidence_id TEXT PRIMARY KEY,
                company_id TEXT NOT NULL,
                engine_id TEXT NOT NULL,
                version TEXT NOT NULL,
                environment TEXT NOT NULL,
                kind TEXT NOT NULL,
                reference TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def append(self, *, company_id: str, engine_id: str, version: str, environment: str, kind: str, reference: str, metadata: dict | None = None, evidence_id: str | None = None) -> str:
        values = (company_id, engine_id, version, environment, kind, reference)
        if not all(isinstance(value, str) and value.strip() for value in values):
            raise ValueError("evidence fields must be non-empty strings")
        if environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        evidence_id = evidence_id or str(uuid4())
        try:
            self.conn.execute(
                "INSERT INTO evidence(evidence_id, company_id, engine_id, version, environment, kind, reference, metadata_json) VALUES(?,?,?,?,?,?,?,?)",
                (evidence_id, company_id, engine_id, version, environment, kind, reference, json.dumps(metadata or {}, sort_keys=True)),
            )
            self.conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("duplicate evidence_id") from exc
        return evidence_id

    def list_engine(self, *, company_id: str, engine_id: str, environment: str | None = None, version: str | None = None) -> tuple[dict, ...]:
        if not all(isinstance(value, str) and value.strip() for value in (company_id, engine_id)):
            raise ValueError("company_id and engine_id required")
        query = "SELECT evidence_id, company_id, engine_id, version, environment, kind, reference, metadata_json FROM evidence WHERE company_id=? AND engine_id=?"
        args: list[str] = [company_id, engine_id]
        if environment is not None:
            if environment not in VALID_ENVIRONMENTS:
                raise ValueError("invalid environment")
            query += " AND environment=?"
            args.append(environment)
        if version is not None:
            if not isinstance(version, str) or not version.strip():
                raise ValueError("version must be a non-empty string")
            query += " AND version=?"
            args.append(version)
        query += " ORDER BY rowid"
        rows = []
        for row in self.conn.execute(query, args):
            rows.append({
                "evidence_id": row[0], "company_id": row[1], "engine_id": row[2],
                "version": row[3], "environment": row[4], "kind": row[5],
                "reference": row[6], "metadata": json.loads(row[7]),
            })
        return tuple(rows)

    def close(self) -> None:
        self.conn.close()
