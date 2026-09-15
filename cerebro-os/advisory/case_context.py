from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class CaseSnapshot:
    company_id: str
    case_id: str
    environment: str
    version: str
    facts: Mapping[str, object]
    internal_document_refs: tuple[str, ...] = field(default_factory=tuple)
    source_ids: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> None:
        if not all((self.company_id.strip(), self.case_id.strip(), self.version.strip())):
            raise ValueError("company_id, case_id and version required")
        if self.environment not in {"LAB", "PREPROD", "PROD"}:
            raise ValueError("invalid environment")
        if not self.facts:
            raise ValueError("facts required")


class CaseStore:
    """Small deterministic case store abstraction.

    V0 is in-memory on purpose: callers can wrap it with file/SQL persistence
    without changing the advisory contract. Keys always include company_id to
    prevent cross-company case leakage. Snapshots are defensively copied on
    save and recover so mutable caller objects cannot alter stored state.
    """

    def __init__(self) -> None:
        self._cases: dict[tuple[str, str], CaseSnapshot] = {}

    @staticmethod
    def _copy(snapshot: CaseSnapshot) -> CaseSnapshot:
        return CaseSnapshot(
            company_id=snapshot.company_id,
            case_id=snapshot.case_id,
            environment=snapshot.environment,
            version=snapshot.version,
            facts=deepcopy(dict(snapshot.facts)),
            internal_document_refs=tuple(snapshot.internal_document_refs),
            source_ids=tuple(snapshot.source_ids),
        )

    def save(self, snapshot: CaseSnapshot) -> None:
        snapshot.validate()
        self._cases[(snapshot.company_id, snapshot.case_id)] = self._copy(snapshot)

    def recover(self, company_id: str, case_id: str) -> CaseSnapshot:
        try:
            return self._copy(self._cases[(company_id, case_id)])
        except KeyError as exc:
            raise KeyError(f"case not found for company={company_id} case={case_id}") from exc

    def exists(self, company_id: str, case_id: str) -> bool:
        return (company_id, case_id) in self._cases
