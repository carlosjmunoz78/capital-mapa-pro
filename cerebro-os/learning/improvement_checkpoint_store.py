from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from learning.continuous_improvement_runtime import RuntimeSnapshot, StageResult


class ImprovementCheckpointStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS improvement_checkpoints (
                company_id TEXT NOT NULL,
                autonomy_profile TEXT NOT NULL,
                environment TEXT NOT NULL,
                version TEXT NOT NULL,
                status TEXT NOT NULL,
                stage_results_json TEXT NOT NULL,
                PRIMARY KEY(company_id, environment, version)
            )
            """
        )
        self.conn.commit()

    def save(self, snapshot: RuntimeSnapshot) -> None:
        if not all((snapshot.company_id.strip(), snapshot.autonomy_profile.strip(), snapshot.environment.strip(), snapshot.version.strip(), snapshot.status.strip())):
            raise ValueError("checkpoint scope required")
        payload = json.dumps([
            {
                "stage": r.stage,
                "status": r.status,
                "evidence_ref": r.evidence_ref,
                "human_reason": r.human_reason,
            }
            for r in snapshot.stage_results
        ], sort_keys=True)
        self.conn.execute(
            """
            INSERT INTO improvement_checkpoints(company_id, autonomy_profile, environment, version, status, stage_results_json)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(company_id, environment, version) DO UPDATE SET
                autonomy_profile=excluded.autonomy_profile,
                status=excluded.status,
                stage_results_json=excluded.stage_results_json
            """,
            (snapshot.company_id, snapshot.autonomy_profile, snapshot.environment, snapshot.version, snapshot.status, payload),
        )
        self.conn.commit()

    def load(self, *, company_id: str, environment: str, version: str) -> RuntimeSnapshot | None:
        row = self.conn.execute(
            "SELECT autonomy_profile,status,stage_results_json FROM improvement_checkpoints WHERE company_id=? AND environment=? AND version=?",
            (company_id, environment, version),
        ).fetchone()
        if row is None:
            return None
        stages = tuple(StageResult(**item) for item in json.loads(row[2]))
        for stage in stages:
            stage.validate()
        return RuntimeSnapshot(company_id, row[0], environment, version, stages, row[1])

    def delete(self, *, company_id: str, environment: str, version: str) -> None:
        self.conn.execute(
            "DELETE FROM improvement_checkpoints WHERE company_id=? AND environment=? AND version=?",
            (company_id, environment, version),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
