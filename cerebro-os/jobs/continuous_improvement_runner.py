from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from jobs.continuous_improvement_schedule import ImprovementSchedule, ScheduleState, due, finish, start
from learning.continuous_improvement_runtime import ContinuousImprovementRuntime, RuntimeSnapshot, StageResult


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
    ) -> JobOutcome:
        schedule = job.schedule
        if not due(schedule, job.state, now):
            return JobOutcome(schedule.company_id, "NOT_DUE", job.state, None)

        running = start(schedule, job.state, now)
        runtime = ContinuousImprovementRuntime(
            schedule.company_id,
            schedule.autonomy_profile,
            environment=schedule.environment,
            version=schedule.version,
        )
        snapshot = runtime.run_until_pause(execute_stage)

        # WAITING means the job remains logically active; a shared worker can resume
        # the same stage later rather than pretending completion.
        if snapshot.status == "WAITING":
            return JobOutcome(schedule.company_id, "WAITING", running, snapshot)

        finished = finish(running, now)
        return JobOutcome(schedule.company_id, snapshot.status, finished, snapshot)
