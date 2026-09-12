from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from competitor_change_detection import CompetitorChange

VALID_ACTIONS = {"OBSERVE", "REVIEW", "ACTION_CANDIDATE"}
VALID_PRIORITIES = {"LOW", "MEDIUM", "HIGH"}


@dataclass(frozen=True)
class MarketSignal:
    company_id: str
    competitor_id: str
    environment: str
    version: str
    source_engine_id: str
    target_engine_id: str
    signal_type: str
    priority: str
    action: str
    summary: str
    evidence_ref: str
    confidence: float

    def validate(self) -> None:
        if not all((
            self.company_id.strip(), self.competitor_id.strip(), self.environment.strip(),
            self.version.strip(), self.source_engine_id.strip(), self.target_engine_id.strip(),
            self.signal_type.strip(), self.priority.strip(), self.action.strip(),
            self.summary.strip(), self.evidence_ref.strip(),
        )):
            raise ValueError("market signal missing required field")
        if self.environment not in {"LAB", "PREPROD", "PROD"}:
            raise ValueError("invalid environment")
        if self.source_engine_id != "COMPET-001":
            raise ValueError("market signal source must be COMPET-001")
        if self.target_engine_id != "MKT-002":
            raise ValueError("market signal target must be MKT-002")
        if self.priority not in VALID_PRIORITIES:
            raise ValueError("invalid priority")
        if self.action not in VALID_ACTIONS:
            raise ValueError("invalid action")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


def _action_for(change: CompetitorChange) -> str:
    if change.priority == "HIGH" and change.confidence >= 0.85:
        return "ACTION_CANDIDATE"
    if change.priority in {"HIGH", "MEDIUM"}:
        return "REVIEW"
    return "OBSERVE"


def _signal_type(change: CompetitorChange) -> str:
    metric = change.metric_or_fact
    if metric in {"title", "h1", "canonical", "schema_types", "page_fingerprint"}:
        return "COMPETITOR_WEB_CHANGE"
    if metric in {"price", "cta"}:
        return "COMPETITOR_OFFER_CHANGE"
    if metric in {"rating", "review_count"}:
        return "COMPETITOR_REPUTATION_CHANGE"
    return "COMPETITOR_OTHER_CHANGE"


def to_market_signal(change: CompetitorChange) -> MarketSignal:
    change.validate()
    signal = MarketSignal(
        company_id=change.company_id,
        competitor_id=change.competitor_id,
        environment=change.environment,
        version=change.version,
        source_engine_id="COMPET-001",
        target_engine_id="MKT-002",
        signal_type=_signal_type(change),
        priority=change.priority,
        action=_action_for(change),
        summary=(
            f"{change.metric_or_fact} changed for {change.competitor_id}: "
            f"{change.previous_value!r} -> {change.current_value!r}"
        ),
        evidence_ref=change.evidence_ref,
        confidence=change.confidence,
    )
    signal.validate()
    return signal


def build_market_signals(changes: Iterable[CompetitorChange]) -> tuple[MarketSignal, ...]:
    result: list[MarketSignal] = []
    seen: set[tuple[str, str, str, str, str, str]] = set()
    for change in changes:
        signal = to_market_signal(change)
        key = (
            signal.company_id,
            signal.competitor_id,
            signal.environment,
            signal.version,
            signal.signal_type,
            signal.evidence_ref,
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(signal)
    return tuple(sorted(result, key=lambda x: ({"HIGH": 0, "MEDIUM": 1, "LOW": 2}[x.priority], x.competitor_id, x.signal_type)))
