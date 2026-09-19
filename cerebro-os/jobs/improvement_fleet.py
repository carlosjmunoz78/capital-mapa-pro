from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from jobs.continuous_improvement_runner import CompanyImprovementJob, ImprovementEvidenceContext, ImprovementRunner, JobOutcome
from learning.continuous_improvement_runtime import StageResult


@dataclass(frozen=True)
class FleetJob:
    job: CompanyImprovementJob
    execute_stage: Callable[[str, int], StageResult]
    evidence_context: ImprovementEvidenceContext = ImprovementEvidenceContext()


@dataclass(frozen=True)
class FleetResult:
    outcomes: tuple[JobOutcome, ...]
    status: str
    green: int
    waiting: int
    blocked: int
    human_required: int
    not_due: int


class ImprovementFleetRunner:
    def execute(self, jobs: tuple[FleetJob, ...], now: datetime) -> FleetResult:
        if not jobs:
            return FleetResult((), "GREEN", 0, 0, 0, 0, 0)

        seen: set[tuple[str, str, str]] = set()
        outcomes: list[JobOutcome] = []
        runner = ImprovementRunner()

        for item in jobs:
            schedule = item.job.schedule
            scope = (schedule.company_id, schedule.environment, schedule.version)
            if scope in seen:
                raise ValueError("duplicate company improvement scope")
            seen.add(scope)

            try:
                outcome = runner.execute_due(
                    item.job,
                    now,
                    item.execute_stage,
                    evidence_context=item.evidence_context,
                )
            except Exception:
                # One company must not crash or suppress the rest of the fleet.
                outcome = JobOutcome(schedule.company_id, "BLOCKED", item.job.state, None)
            outcomes.append(outcome)

        statuses = [o.status for o in outcomes]
        human = statuses.count("HUMAN_REQUIRED")
        blocked = statuses.count("BLOCKED")
        waiting = statuses.count("WAITING")
        green = statuses.count("GREEN")
        not_due = statuses.count("NOT_DUE")

        if human:
            status = "HUMAN_REQUIRED"
        elif blocked:
            status = "BLOCKED"
        elif waiting:
            status = "WAITING"
        elif green + not_due == len(statuses):
            status = "GREEN"
        else:
            status = "IN_PROGRESS"

        return FleetResult(tuple(outcomes), status, green, waiting, blocked, human, not_due)


def supervisor_snapshot(result: FleetResult) -> dict:
    return {
        "status": result.status,
        "companies": len(result.outcomes),
        "green": result.green,
        "waiting": result.waiting,
        "blocked": result.blocked,
        "human_required": result.human_required,
        "not_due": result.not_due,
        "attention_company_ids": tuple(
            o.company_id for o in result.outcomes if o.status in {"BLOCKED", "HUMAN_REQUIRED", "WAITING"}
        ),
    }
