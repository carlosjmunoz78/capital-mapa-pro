from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from jobs.continuous_improvement_schedule import ImprovementSchedule, ScheduleState, due, finish, start
from learning.continuous_improvement_runtime import ContinuousImprovementRuntime, RuntimeSnapshot, StageResult
from learning.improvement_checkpoint_store import ImprovementCheckpointStore
from observability.improvement_audit_store import ImprovementAuditRecord, ImprovementAuditStore


@dataclass(frozen=True)
class CompanyImprovementJob:
    schedule: ImprovementSchedule
    state: ScheduleState


@dataclass(frozen=True)
class ImprovementEvidenceContext:
    old_ref: str | None = None
    new_ref: str | None = None
    rollback_ref: str | None = None
    cost_eur: float = 0.0

    def validate(self) -> None:
        if self.cost_eur < 0:
            raise ValueError("cost_eur cannot be negative")


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
        audit_store: ImprovementAuditStore | None = None,
        cycle_id: str | None = None,
        engine_id: str = "SUP-IMPROVEMENT",
        evidence_context: ImprovementEvidenceContext | None = None,
    ) -> JobOutcome:
        schedule = job.schedule
        context = evidence_context or ImprovementEvidenceContext()
        context.validate()
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
        before = {r.stage: r for r in (saved.stage_results if saved else ())}
        snapshot = runtime.run_until_pause(execute_stage)
        if audit_store:
            cid = cycle_id or f"{schedule.company_id}:{schedule.environment}:{schedule.version}"
            for result in snapshot.stage_results:
                if before.get(result.stage) == result:
                    continue
                audit_store.append(ImprovementAuditRecord(
                    company_id=schedule.company_id, engine_id=engine_id, environment=schedule.environment,
                    version=schedule.version, cycle_id=cid, stage=result.stage, status=result.status,
                    evidence_ref=result.evidence_ref or "evidence://missing", old_ref=context.old_ref,
                    new_ref=context.new_ref, rollback_ref=context.rollback_ref, cost_eur=context.cost_eur,
                ))
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
