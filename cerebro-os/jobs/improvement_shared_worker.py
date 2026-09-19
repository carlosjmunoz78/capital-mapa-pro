from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from jobs.continuous_improvement_runner import CompanyImprovementJob, ImprovementEvidenceContext
from jobs.continuous_improvement_schedule import ScheduleState, ImprovementSchedule
from jobs.improvement_fleet import FleetJob, ImprovementFleetRunner, FleetResult, supervisor_snapshot
from jobs.improvement_operations_registry import ImprovementOperationsRegistry
from learning.continuous_improvement_runtime import StageResult
from learning.improvement_checkpoint_store import ImprovementCheckpointStore
from observability.improvement_audit_store import ImprovementAuditStore


@dataclass(frozen=True)
class WorkerPaths:
    root: Path

    def company_dir(self, company_id: str, environment: str, version: str) -> Path:
        return self.root / company_id / environment / version


class SharedImprovementWorker:
    def __init__(self, registry: ImprovementOperationsRegistry, paths: WorkerPaths):
        self.registry = registry
        self.paths = paths

    def run(
        self,
        now: datetime,
        executor_factory: Callable[[str], Callable[[str, int], StageResult]],
    ) -> tuple[FleetResult, dict]:
        jobs: list[FleetJob] = []
        stores: list[object] = []
        try:
            for config in self.registry.active():
                base = self.paths.company_dir(config.company_id, config.environment, config.version)
                checkpoint = ImprovementCheckpointStore(base / "checkpoint.db")
                audit = ImprovementAuditStore(base / "audit.db")
                stores.extend((checkpoint, audit))
                schedule = ImprovementSchedule(
                    config.company_id, config.autonomy_profile, config.environment,
                    config.version, config.interval_hours, config.enabled,
                )
                jobs.append(FleetJob(
                    CompanyImprovementJob(schedule, ScheduleState()),
                    executor_factory(config.company_id),
                    ImprovementEvidenceContext(),
                    checkpoint,
                    audit,
                    f"{config.company_id}:{now.isoformat()}",
                ))
            result = ImprovementFleetRunner().execute(tuple(jobs), now)
            return result, supervisor_snapshot(result)
        finally:
            for store in stores:
                store.close()
