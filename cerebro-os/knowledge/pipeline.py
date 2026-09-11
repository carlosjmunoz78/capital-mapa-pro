from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

ALLOWED_SOURCES = {"INTERNAL", "OFFICIAL", "WEB", "CONNECTOR", "HUMAN"}

@dataclass(frozen=True)
class KnowledgeItem:
    company_id: str
    source_id: str
    source_type: str
    content_ref: str
    version: str
    observed_at: str
    provenance_ref: str

    def validate(self) -> None:
        if not all((self.company_id, self.source_id, self.content_ref, self.version, self.provenance_ref)):
            raise ValueError("knowledge identity, version and provenance are required")
        if self.source_type not in ALLOWED_SOURCES:
            raise ValueError("unsupported source_type")
        datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))

    def is_stale(self, max_age_seconds: int, now: datetime | None = None) -> bool:
        self.validate()
        if max_age_seconds < 0:
            raise ValueError("max_age_seconds cannot be negative")
        now = now or datetime.now(timezone.utc)
        seen = datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))
        if seen.tzinfo is None:
            seen = seen.replace(tzinfo=timezone.utc)
        return (now - seen).total_seconds() > max_age_seconds

class KnowledgeIndex:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], KnowledgeItem] = {}

    def upsert(self, item: KnowledgeItem) -> None:
        item.validate()
        self._items[(item.company_id, item.source_id)] = item

    def get(self, company_id: str, source_id: str) -> KnowledgeItem | None:
        return self._items.get((company_id, source_id))

    def list_company(self, company_id: str) -> tuple[KnowledgeItem, ...]:
        return tuple(item for (cid, _), item in sorted(self._items.items()) if cid == company_id)
