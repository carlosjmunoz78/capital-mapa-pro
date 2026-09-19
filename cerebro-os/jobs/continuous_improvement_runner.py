from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from jobs.continuous_improvement_schedule import ImprovementSchedule, ScheduleState, due, finish, start
from learning.continuous_improvement_runtime import ContinuousImprovementRuntime, RuntimeSnapshot, StageResult
from learning.improvement_checkpoint_store import ImprovementCheckpointStore


@dataclass(frozen=True)
class CompanyImprovementJob:
    schedule: ImprovementSchedule
    state: ScheduleState


@dataclass(frozen=True)
class JobOutcome:
    company_id: str
    status: str
    state: ScheduleState
    runtime: RuntimeSnapshot | None


class ImprovementRunner:
    def execute_due(
        self,
        job: CompanyImprovementJob,
        now: datetime,
        execute_stage: Callable[[str, int], StageResult],
        checkpoint_store: ImprovementCheckpointStore | None = None,
    ) -> JobOutcome:
        schedule = job.schedule
        if not due(schedule, job.state, now):
            return JobOutcome(schedule.company_id, "NOT_DUE", job.state, None)

        running = start(schedule, job.state, now)
        saved = checkpoint_store.load(company_id=schedule.company_id, environment=schedule.environment, version=schedule.version) if checkpoint_store else None
        runtime = ContinuousImprovementRuntime.from_snapshot(saved) if saved else ContinuousImprovementRuntime(
            schedule.company_id,
            schedule.autonomy_profile,
            environment=schedule.environment,
            version=schedule.version,
        )
        snapshot = runtime.run_until_pause(execute_stage)
        if checkpoint_store:
            checkpoint_store.save(snapshot)

        # WAITING means the job remains logically active; a shared worker can resume
        # the same stage later rather than pretending completion.
        if snapshot.status == "WAITING":
            return JobOutcome(schedule.company_id, "WAITING", running, snapshot)

        finished = finish(running, now)
        if checkpoint_store and snapshot.status == "GREEN":
            checkpoint_store.delete(company_id=schedule.company_id, environment=schedule.environment, version=schedule.version)
        return JobOutcome(schedule.company_id, snapshot.status, finished, snapshot)
