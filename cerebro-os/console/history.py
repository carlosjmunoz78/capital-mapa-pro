from dataclasses import dataclass, field
from typing import List

VALID_STATUSES = {"PENDING", "IN_PROGRESS", "GREEN", "RED", "BLOCKED", "HUMAN_REQUIRED"}
VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class HistoryEntry:
    request_id: str
    company_id: str
    engine_id: str
    status: str
    evidence_ref: str = ""
    environment: str = "LAB"
    version: str = "1.0.0"


@dataclass
class ConsoleHistory:
    entries: List[HistoryEntry] = field(default_factory=list)

    def append(self, entry: HistoryEntry):
        if not all([entry.request_id, entry.company_id, entry.engine_id, entry.status, entry.version]):
            raise ValueError("invalid history entry")
        if entry.status not in VALID_STATUSES:
            raise ValueError("invalid history status")
        if entry.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid history environment")
        if entry.status == "GREEN" and not entry.evidence_ref.strip():
            raise ValueError("GREEN history entry requires evidence_ref")
        self.entries.append(entry)

    def by_company(self, company_id: str):
        if not company_id:
            raise ValueError("company_id required")
        return [e for e in self.entries if e.company_id == company_id]

    def by_scope(self, company_id: str, engine_id: str, environment: str, version: str):
        if not all((company_id, engine_id, version)) or environment not in VALID_ENVIRONMENTS:
            raise ValueError("valid company, engine, environment and version scope required")
        return [
            e for e in self.entries
            if e.company_id == company_id
            and e.engine_id == engine_id
            and e.environment == environment
            and e.version == version
        ]
