from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}
VALID_PROFILES = {"FENIX_SENSITIVE", "FENIX_DIGITAL", "AUTONOMOUS_VENTURE"}


@dataclass(frozen=True)
class ImprovementSchedule:
    company_id: str
    autonomy_profile: str
    environment: str = "LAB"
    version: str = "1.0.0"
    interval_hours: int = 24
    enabled: bool = True

    def validate(self) -> None:
        if not self.company_id.strip() or not self.version.strip():
            raise ValueError("company_id and version required")
        if self.autonomy_profile not in VALID_PROFILES:
            raise ValueError("invalid autonomy profile")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.interval_hours < 1:
            raise ValueError("interval_hours must be >= 1")


@dataclass(frozen=True)
class ScheduleState:
    last_started_at: datetime | None = None
    last_finished_at: datetime | None = None
    running: bool = False


def due(schedule: ImprovementSchedule, state: ScheduleState, now: datetime) -> bool:
    schedule.validate()
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if not schedule.enabled or state.running:
        return False
    if state.last_started_at is None:
        return True
    return now >= state.last_started_at + timedelta(hours=schedule.interval_hours)


def start(schedule: ImprovementSchedule, state: ScheduleState, now: datetime) -> ScheduleState:
    if not due(schedule, state, now):
        raise ValueError("schedule not due")
    return ScheduleState(last_started_at=now.astimezone(timezone.utc), last_finished_at=state.last_finished_at, running=True)


def finish(state: ScheduleState, now: datetime) -> ScheduleState:
    if not state.running:
        raise ValueError("schedule is not running")
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return ScheduleState(last_started_at=state.last_started_at, last_finished_at=now.astimezone(timezone.utc), running=False)


def default_schedule(company_id: str, autonomy_profile: str, environment: str = "LAB", version: str = "1.0.0") -> ImprovementSchedule:
    # Daily by default, zero paid infrastructure requirement. An external/shared
    # worker may call this deterministic contract; it does not require one server per engine.
    return ImprovementSchedule(company_id, autonomy_profile, environment, version, 24, True)
