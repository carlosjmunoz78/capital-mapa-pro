from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from learning.continuous_improvement_runtime import (
    ContinuousImprovementRuntime,
    RuntimeSnapshot,
    StageResult,
)


class ImprovementCheckpointStore:
    """Durable checkpoints scoped to company, environment and version.

    A prior GREEN stage is immutable. Only a final unresolved stage may be
    replaced, and new stages can be appended after every preceding stage is
    GREEN. The SQLite lock protects the read/validate/write as one operation.
    This is not an authorization to promote or apply learning strategies.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, timeout=30)
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

    @staticmethod
    def _payload(snapshot: RuntimeSnapshot) -> str:
        if not isinstance(snapshot, RuntimeSnapshot) or not all(
            isinstance(x, str) and x.strip() for x in (
                snapshot.company_id, snapshot.autonomy_profile,
                snapshot.environment, snapshot.version, snapshot.status,
            )
        ):
            raise ValueError("checkpoint scope required")
        if snapshot.environment not in {"LAB", "PREPROD", "PROD"}:
            raise ValueError("invalid checkpoint environment")
        if snapshot.status not in {"GREEN", "RED", "WAITING", "BLOCKED", "HUMAN_REQUIRED", "IN_PROGRESS"}:
            raise ValueError("invalid checkpoint status")
        # The runtime verifies ordered, contiguous stages and each StageResult.
        ContinuousImprovementRuntime.from_snapshot(snapshot)
        if snapshot.status == "GREEN" and (
            len(snapshot.stage_results) != len(ContinuousImprovementRuntime.from_snapshot(snapshot).cycle.stages())
            or any(stage.status != "GREEN" for stage in snapshot.stage_results)
        ):
            raise ValueError("GREEN checkpoint must have complete evidence")
        return json.dumps([
            {
                "stage": r.stage,
                "status": r.status,
                "evidence_ref": r.evidence_ref,
                "human_reason": r.human_reason,
            }
            for r in snapshot.stage_results
        ], sort_keys=True)

    @staticmethod
    def _guard_progress(old: tuple[StageResult, ...], new: tuple[StageResult, ...]) -> None:
        if len(new) < len(old):
            raise PermissionError("checkpoint stage regression denied")
        for i, previous in enumerate(old):
            current = new[i]
            if previous.stage != current.stage:
                raise PermissionError("checkpoint stage identity conflict")
            last = i == len(old) - 1
            if not last or previous.status in {"GREEN", "BLOCKED", "HUMAN_REQUIRED"}:
                if current != previous:
                    raise PermissionError("checkpoint confirmed evidence immutable")
            # Only the last unresolved stage is allowed to evolve.
        if len(new) > len(old) and old and new[len(old) - 1].status != "GREEN":
            raise PermissionError("checkpoint cannot skip unresolved stage")
        if old and old[-1].status in {"BLOCKED", "HUMAN_REQUIRED"} and new != old:
            raise PermissionError("checkpoint human/blocked gate immutable")

    def save(self, snapshot: RuntimeSnapshot) -> None:
        payload = self._payload(snapshot)
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            row = self.conn.execute(
                "SELECT autonomy_profile, status, stage_results_json FROM improvement_checkpoints "
                "WHERE company_id=? AND environment=? AND version=?",
                (snapshot.company_id, snapshot.environment, snapshot.version),
            ).fetchone()
            if row is not None:
                if row[0] != snapshot.autonomy_profile:
                    raise PermissionError("checkpoint autonomy profile scope conflict")
                before = tuple(StageResult(**part) for part in json.loads(row[2]))
                self._guard_progress(before, snapshot.stage_results)
                if row[1] in {"GREEN", "HUMAN_REQUIRED", "BLOCKED"} and (
                    row[1] != snapshot.status or before != snapshot.stage_results
                ):
                    raise PermissionError("terminal checkpoint is immutable")
            self.conn.execute(
                """
                INSERT INTO improvement_checkpoints(company_id, autonomy_profile, environment, version, status, stage_results_json)
                VALUES(?,?,?,?,?,?)
                ON CONFLICT(company_id, environment, version) DO UPDATE SET
                    autonomy_profile=excluded.autonomy_profile,
                    status=excluded.status,
                    stage_results_json=excluded.stage_results_json
                """,
                (snapshot.company_id, snapshot.autonomy_profile, snapshot.environment,
                 snapshot.version, snapshot.status, payload),
            )
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

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