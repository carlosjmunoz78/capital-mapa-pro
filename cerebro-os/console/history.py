from dataclasses import dataclass, field
from typing import List

@dataclass(frozen=True)
class HistoryEntry:
    request_id: str
    company_id: str
    engine_id: str
    status: str
    evidence_ref: str

@dataclass
class ConsoleHistory:
    entries: List[HistoryEntry] = field(default_factory=list)

    def append(self, entry: HistoryEntry):
        if not all([entry.request_id,entry.company_id,entry.engine_id,entry.status]):
            raise ValueError("invalid history entry")
        self.entries.append(entry)

    def by_company(self, company_id: str):
        return [e for e in self.entries if e.company_id == company_id]
