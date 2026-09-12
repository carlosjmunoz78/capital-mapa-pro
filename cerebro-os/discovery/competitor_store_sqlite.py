from __future__ import annotations

from dataclasses import asdict
import sqlite3
from typing import Iterable

from competitor_observation import CompetitorObservation


class CompetitorSqliteStore:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS competitor_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id TEXT NOT NULL,
                competitor_id TEXT NOT NULL,
                engine_id TEXT NOT NULL,
                environment TEXT NOT NULL,
                version TEXT NOT NULL,
                source TEXT NOT NULL,
                source_type TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                url_or_external_id TEXT NOT NULL,
                metric_or_fact TEXT NOT NULL,
                value TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                evidence_ref TEXT NOT NULL,
                confidence REAL NOT NULL,
                cost_units REAL NOT NULL DEFAULT 0,
                UNIQUE(company_id, competitor_id, engine_id, environment, version, source,
                       url_or_external_id, metric_or_fact, content_hash)
            )
            """
        )
        self.connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_competitor_obs_scope_latest
            ON competitor_observations (
                company_id, competitor_id, engine_id, environment, version,
                source, url_or_external_id, metric_or_fact, observed_at DESC
            )
            """
        )
        self.connection.commit()

    def add(self, observation: CompetitorObservation) -> bool:
        observation.validate()
        payload = asdict(observation)
        columns = tuple(payload.keys())
        placeholders = ",".join("?" for _ in columns)
        sql = (
            f"INSERT OR IGNORE INTO competitor_observations "
            f"({','.join(columns)}) VALUES ({placeholders})"
        )
        cursor = self.connection.execute(sql, tuple(payload[col] for col in columns))
        self.connection.commit()
        return cursor.rowcount == 1

    def add_many(self, observations: Iterable[CompetitorObservation]) -> int:
        inserted = 0
        for observation in observations:
            inserted += 1 if self.add(observation) else 0
        return inserted

    def latest(
        self,
        *,
        company_id: str,
        competitor_id: str,
        engine_id: str,
        environment: str,
        version: str,
        source: str,
        url_or_external_id: str,
        metric_or_fact: str,
    ) -> CompetitorObservation | None:
        required = (
            company_id,
            competitor_id,
            engine_id,
            environment,
            version,
            source,
            url_or_external_id,
            metric_or_fact,
        )
        if not all(str(value).strip() for value in required):
            raise ValueError("exact observation scope is required")
        row = self.connection.execute(
            """
            SELECT company_id, competitor_id, engine_id, environment, version,
                   source, source_type, observed_at, url_or_external_id,
                   metric_or_fact, value, content_hash, evidence_ref, confidence, cost_units
            FROM competitor_observations
            WHERE company_id=? AND competitor_id=? AND engine_id=? AND environment=? AND version=?
              AND source=? AND url_or_external_id=? AND metric_or_fact=?
            ORDER BY observed_at DESC, id DESC
            LIMIT 1
            """,
            (
                company_id,
                competitor_id,
                engine_id,
                environment,
                version,
                source,
                url_or_external_id,
                metric_or_fact,
            ),
        ).fetchone()
        if row is None:
            return None
        item = CompetitorObservation(**dict(row))
        item.validate()
        return item

    def count_scope(self, *, company_id: str, environment: str, version: str) -> int:
        if not company_id.strip() or not environment.strip() or not version.strip():
            raise ValueError("company_id, environment and version are required")
        row = self.connection.execute(
            "SELECT COUNT(*) AS n FROM competitor_observations WHERE company_id=? AND environment=? AND version=?",
            (company_id, environment, version),
        ).fetchone()
        return int(row["n"])
