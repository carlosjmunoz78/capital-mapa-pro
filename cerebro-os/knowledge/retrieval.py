from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256


@dataclass(frozen=True)
class KnowledgeRecord:
    company_id: str
    record_id: str
    text: str
    source_ref: str
    observed_at: str
    version: str = "1.0.0"

    def validate(self) -> None:
        if not all((self.company_id.strip(), self.record_id.strip(), self.text.strip(), self.source_ref.strip())):
            raise ValueError("company_id, record_id, text and source_ref are required")
        datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))

    @property
    def content_hash(self) -> str:
        return sha256(self.text.encode("utf-8")).hexdigest()


class KnowledgeIndex:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str], KnowledgeRecord] = {}
        self._cache: dict[tuple[str, str], tuple[str, ...]] = {}

    def upsert(self, record: KnowledgeRecord) -> bool:
        record.validate()
        key = (record.company_id, record.record_id)
        previous = self._records.get(key)
        changed = previous is None or previous.content_hash != record.content_hash or previous.version != record.version
        self._records[key] = record
        if changed:
            self.invalidate_company(record.company_id)
        return changed

    def invalidate_company(self, company_id: str) -> None:
        for key in [k for k in self._cache if k[0] == company_id]:
            self._cache.pop(key, None)

    def retrieve(self, company_id: str, query: str, limit: int = 5) -> tuple[str, ...]:
        if not company_id.strip() or not query.strip():
            raise ValueError("company_id and query are required")
        if limit < 1:
            raise ValueError("limit must be positive")
        cache_key = (company_id, query.strip().lower())
        if cache_key in self._cache:
            return self._cache[cache_key]
        terms = tuple(t for t in query.lower().split() if t)
        scored: list[tuple[int, str]] = []
        for (cid, rid), record in self._records.items():
            if cid != company_id:
                continue
            haystack = record.text.lower()
            if not all(term in haystack for term in terms):
                continue
            score = sum(haystack.count(term) for term in terms)
            scored.append((score, rid))
        result = tuple(rid for _, rid in sorted(scored, key=lambda x: (-x[0], x[1]))[:limit])
        self._cache[cache_key] = result
        return result

    def stale(self, company_id: str, max_age_seconds: int, now: datetime | None = None) -> tuple[str, ...]:
        if max_age_seconds < 0:
            raise ValueError("max_age_seconds cannot be negative")
        now = now or datetime.now(timezone.utc)
        stale_ids: list[str] = []
        for (cid, rid), record in self._records.items():
            if cid != company_id:
                continue
            observed = datetime.fromisoformat(record.observed_at.replace("Z", "+00:00"))
            if (now - observed).total_seconds() > max_age_seconds:
                stale_ids.append(rid)
        return tuple(sorted(stale_ids))
