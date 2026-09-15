from __future__ import annotations

from dataclasses import dataclass
from datetime import date

SOURCE_TYPES = {
    "STABLE_KNOWLEDGE",
    "LIVE_SOURCE",
    "INTERNAL_DOCUMENT",
    "CASE_FACT",
}


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    source_type: str
    locator: str
    jurisdiction: str
    checked_at: str
    confidence: float
    valid_from: str | None = None
    valid_to: str | None = None

    def validate(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.source_id,
                self.source_type,
                self.locator,
                self.jurisdiction,
                self.checked_at,
            )
        ):
            raise ValueError("source identity, locator, jurisdiction and checked_at required")
        if self.source_type not in SOURCE_TYPES:
            raise ValueError(f"unknown source_type: {self.source_type}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        date.fromisoformat(self.checked_at)
        if self.valid_from:
            date.fromisoformat(self.valid_from)
        if self.valid_to:
            date.fromisoformat(self.valid_to)

    def valid_on(self, as_of: date) -> bool:
        self.validate()
        if self.valid_from and as_of < date.fromisoformat(self.valid_from):
            return False
        if self.valid_to and as_of > date.fromisoformat(self.valid_to):
            return False
        return True


@dataclass(frozen=True)
class SourceAssessment:
    status: str
    human_exception: str | None
    accepted_source_ids: tuple[str, ...]
    reasons: tuple[str, ...]


def assess_sources(
    records: tuple[SourceRecord, ...],
    *,
    required_jurisdiction: str,
    as_of: date,
    require_live_source: bool,
    minimum_confidence: float = 0.70,
) -> SourceAssessment:
    """Fail closed when current/jurisdiction/confidence evidence is insufficient."""

    if not records:
        return SourceAssessment(
            status="HUMAN_REQUIRED",
            human_exception="LOW_CONFIDENCE",
            accepted_source_ids=(),
            reasons=("no sources supplied",),
        )

    accepted: list[str] = []
    reasons: list[str] = []
    has_live = False
    for record in records:
        record.validate()
        if record.jurisdiction not in {required_jurisdiction, "GLOBAL"}:
            reasons.append(f"jurisdiction mismatch:{record.source_id}")
            continue
        if not record.valid_on(as_of):
            reasons.append(f"source outside validity window:{record.source_id}")
            continue
        if record.confidence < minimum_confidence:
            reasons.append(f"low confidence:{record.source_id}")
            continue
        accepted.append(record.source_id)
        if record.source_type == "LIVE_SOURCE":
            has_live = True

    if require_live_source and not has_live:
        reasons.append("current live source required")
        return SourceAssessment(
            status="HUMAN_REQUIRED",
            human_exception="LOW_CONFIDENCE",
            accepted_source_ids=tuple(accepted),
            reasons=tuple(reasons),
        )
    if not accepted:
        return SourceAssessment(
            status="HUMAN_REQUIRED",
            human_exception="LOW_CONFIDENCE",
            accepted_source_ids=(),
            reasons=tuple(reasons) or ("no acceptable sources",),
        )
    return SourceAssessment(
        status="GREEN",
        human_exception=None,
        accepted_source_ids=tuple(accepted),
        reasons=tuple(reasons),
    )
