from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Iterable

from competitor_change_detection import CompetitorChange, detect_change
from competitor_observation import CompetitorObservation
from competitor_store_sqlite import CompetitorSqliteStore


@dataclass(frozen=True)
class MonitorTarget:
    company_id: str
    competitor_id: str
    url: str
    environment: str = "LAB"
    version: str = "1.0.0"
    engine_id: str = "COMPET-001"
    interval_seconds: int = 21600

    def validate(self) -> None:
        if not all((self.company_id.strip(), self.competitor_id.strip(), self.url.strip(), self.version.strip())):
            raise ValueError("monitor target missing required field")
        if self.environment not in {"LAB", "PREPROD", "PROD"}:
            raise ValueError("invalid environment")
        if self.interval_seconds < 300:
            raise ValueError("monitor interval cannot be below 300 seconds")


@dataclass
class MonitorScheduleState:
    last_run: dict[tuple[str, str, str, str], datetime] = field(default_factory=dict)

    def due(self, target: MonitorTarget, now: datetime | None = None) -> bool:
        target.validate()
        instant = now or datetime.now(timezone.utc)
        if instant.tzinfo is None:
            raise ValueError("now must include timezone")
        key = (target.company_id, target.competitor_id, target.environment, target.version)
        previous = self.last_run.get(key)
        if previous is None:
            return True
        return instant >= previous + timedelta(seconds=target.interval_seconds)

    def mark_run(self, target: MonitorTarget, now: datetime | None = None) -> None:
        target.validate()
        instant = now or datetime.now(timezone.utc)
        if instant.tzinfo is None:
            raise ValueError("now must include timezone")
        key = (target.company_id, target.competitor_id, target.environment, target.version)
        self.last_run[key] = instant


@dataclass(frozen=True)
class MonitorIngestResult:
    inserted: int
    unchanged_or_duplicate: int
    changes: tuple[CompetitorChange, ...]


def ingest_delta_only(
    store: CompetitorSqliteStore,
    observations: Iterable[CompetitorObservation],
) -> MonitorIngestResult:
    inserted = 0
    skipped = 0
    changes: list[CompetitorChange] = []
    for current in observations:
        current.validate()
        previous = store.latest(
            company_id=current.company_id,
            competitor_id=current.competitor_id,
            engine_id=current.engine_id,
            environment=current.environment,
            version=current.version,
            source=current.source,
            url_or_external_id=current.url_or_external_id,
            metric_or_fact=current.metric_or_fact,
        )
        if previous is not None:
            change = detect_change(previous, current)
            if change is not None:
                changes.append(change)
        if store.add(current):
            inserted += 1
        else:
            skipped += 1
    return MonitorIngestResult(inserted=inserted, unchanged_or_duplicate=skipped, changes=tuple(changes))
