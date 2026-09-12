from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from competitor_observation import CompetitorObservation


@dataclass(frozen=True)
class CompetitorChange:
    company_id: str
    competitor_id: str
    engine_id: str
    environment: str
    version: str
    source: str
    metric_or_fact: str
    previous_value: str
    current_value: str
    previous_hash: str
    current_hash: str
    previous_observed_at: str
    current_observed_at: str
    evidence_ref: str
    confidence: float
    priority: str

    def validate(self) -> None:
        required = (
            self.company_id,
            self.competitor_id,
            self.engine_id,
            self.environment,
            self.version,
            self.source,
            self.metric_or_fact,
            self.previous_hash,
            self.current_hash,
            self.previous_observed_at,
            self.current_observed_at,
            self.evidence_ref,
            self.priority,
        )
        if not all(str(value).strip() for value in required):
            raise ValueError("competitor change missing required field")
        if self.previous_hash == self.current_hash:
            raise ValueError("unchanged observations are not changes")
        if self.priority not in {"LOW", "MEDIUM", "HIGH"}:
            raise ValueError("invalid priority")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        previous = datetime.fromisoformat(self.previous_observed_at.replace("Z", "+00:00"))
        current = datetime.fromisoformat(self.current_observed_at.replace("Z", "+00:00"))
        if previous.tzinfo is None or current.tzinfo is None:
            raise ValueError("change timestamps must include timezone")
        if current < previous:
            raise ValueError("current observation cannot predate previous observation")


def _same_scope(left: CompetitorObservation, right: CompetitorObservation) -> bool:
    return (
        left.company_id == right.company_id
        and left.competitor_id == right.competitor_id
        and left.engine_id == right.engine_id
        and left.environment == right.environment
        and left.version == right.version
        and left.source == right.source
        and left.url_or_external_id == right.url_or_external_id
        and left.metric_or_fact == right.metric_or_fact
    )


def priority_for_metric(metric_or_fact: str) -> str:
    if metric_or_fact in {"canonical", "h1", "title", "schema_types"}:
        return "HIGH"
    if metric_or_fact in {"page_fingerprint", "price", "rating", "review_count", "cta"}:
        return "MEDIUM"
    return "LOW"


def detect_change(previous: CompetitorObservation, current: CompetitorObservation) -> CompetitorChange | None:
    previous.validate()
    current.validate()
    if not _same_scope(previous, current):
        raise ValueError("competitor observations are not comparable in exact scope")
    if previous.content_hash.lower() == current.content_hash.lower():
        return None
    change = CompetitorChange(
        company_id=current.company_id,
        competitor_id=current.competitor_id,
        engine_id=current.engine_id,
        environment=current.environment,
        version=current.version,
        source=current.source,
        metric_or_fact=current.metric_or_fact,
        previous_value=previous.value,
        current_value=current.value,
        previous_hash=previous.content_hash.lower(),
        current_hash=current.content_hash.lower(),
        previous_observed_at=previous.observed_at,
        current_observed_at=current.observed_at,
        evidence_ref=current.evidence_ref,
        confidence=min(previous.confidence, current.confidence),
        priority=priority_for_metric(current.metric_or_fact),
    )
    change.validate()
    return change


def latest_by_fact(observations: Iterable[CompetitorObservation]) -> dict[tuple[str, str, str], CompetitorObservation]:
    latest: dict[tuple[str, str, str], CompetitorObservation] = {}
    for item in observations:
        item.validate()
        key = (item.competitor_id, item.source, item.metric_or_fact)
        current = latest.get(key)
        if current is None:
            latest[key] = item
            continue
        current_ts = datetime.fromisoformat(current.observed_at.replace("Z", "+00:00"))
        item_ts = datetime.fromisoformat(item.observed_at.replace("Z", "+00:00"))
        if item_ts > current_ts:
            latest[key] = item
    return latest
