from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from learning.continuous_improvement import DailyImprovementCycle

TERMINAL = {"GREEN", "HUMAN_REQUIRED", "BLOCKED"}
VALID_RESULTS = {"GREEN", "RED", "WAITING", "HUMAN_REQUIRED", "BLOCKED"}
CANONICAL_HUMAN_REASONS = {
    "LEGAL_REQUIRED", "SIGNATURE_REQUIRED", "LOW_CONFIDENCE", "HIGH_RISK",
    "POLICY_CONFLICT", "SECURITY_INCIDENT", "MONEY_LIMIT", "CUSTOMER_HUMAN_REQUEST",
}


@dataclass(frozen=True)
class StageResult:
    stage: str
    status: str
    evidence_ref: str = ""
    human_reason: str | None = None

    def validate(self) -> None:
        if self.status not in VALID_RESULTS:
            raise ValueError("invalid stage status")
        if self.status == "GREEN" and not self.evidence_ref.strip():
            raise ValueError("GREEN requires evidence")
        if self.status == "HUMAN_REQUIRED" and self.human_reason not in CANONICAL_HUMAN_REASONS:
            raise ValueError("invalid HUMAN_REQUIRED reason")


@dataclass(frozen=True)
class RuntimeSnapshot:
    company_id: str
    autonomy_profile: str
    environment: str
    version: str
    stage_results: tuple[StageResult, ...]
    status: str


class ContinuousImprovementRuntime:
    def __init__(self, company_id: str, autonomy_profile: str, *, environment: str = "LAB", version: str = "1.0.0", max_red_retries: int = 3) -> None:
        if max_red_retries < 1:
            raise ValueError("max_red_retries must be >= 1")
        self.cycle = DailyImprovementCycle(company_id, autonomy_profile, environment, version)
        self.company_id = company_id
        self.autonomy_profile = autonomy_profile
        self.environment = environment
        self.version = version
        self.max_red_retries = max_red_retries
        self._results: dict[str, StageResult] = {}
        self._attempts: dict[str, int] = {}

    def next_stage(self) -> str | None:
        for stage in self.cycle.stages():
            result = self._results.get(stage)
            if result is None or result.status not in TERMINAL:
                return stage
            if result.status != "GREEN":
                return None
        return None

    def run_once(self, execute: Callable[[str, int], StageResult]) -> RuntimeSnapshot:
        stage = self.next_stage()
        if stage is None:
            return self.snapshot()

        attempt = self._attempts.get(stage, 0) + 1
        result = execute(stage, attempt)
        if result.stage != stage:
            raise ValueError("executor returned result for wrong stage")
        result.validate()
        self._attempts[stage] = attempt

        if result.status == "RED":
            if attempt >= self.max_red_retries:
                self._results[stage] = StageResult(stage, "BLOCKED", result.evidence_ref)
            else:
                self._results[stage] = result
        elif result.status == "WAITING":
            self._results[stage] = result
        else:
            self._results[stage] = result
        return self.snapshot()

    def run_until_pause(self, execute: Callable[[str, int], StageResult], *, max_iterations: int = 100) -> RuntimeSnapshot:
        for _ in range(max_iterations):
            before = self.snapshot()
            if before.status in {"GREEN", "HUMAN_REQUIRED", "BLOCKED"}:
                return before
            current = self.next_stage()
            after = self.run_once(execute)
            if after.status == "WAITING":
                return after
            if current is not None and self._results[current].status == "RED":
                continue
        return self.snapshot(status_override="BLOCKED")

    def snapshot(self, status_override: str | None = None) -> RuntimeSnapshot:
        ordered = tuple(self._results[s] for s in self.cycle.stages() if s in self._results)
        if status_override:
            status = status_override
        elif ordered and ordered[-1].status in {"HUMAN_REQUIRED", "BLOCKED", "WAITING"}:
            status = ordered[-1].status
        elif len(ordered) == len(self.cycle.stages()) and all(r.status == "GREEN" for r in ordered):
            status = "GREEN"
        elif ordered and ordered[-1].status == "RED":
            status = "RED"
        else:
            status = "IN_PROGRESS"
        return RuntimeSnapshot(self.company_id, self.autonomy_profile, self.environment, self.version, ordered, status)
