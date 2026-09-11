from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class CoverageReport:
    canonical_count: int
    covered_count: int
    missing: tuple[str, ...]
    unknown: tuple[str, ...]

    @property
    def status(self) -> str:
        return "GREEN" if not self.missing and not self.unknown and self.covered_count == self.canonical_count else "RED"


def audit_controller_coverage(canonical_ids: Iterable[str], groups: Mapping[str, Iterable[str]]) -> CoverageReport:
    canonical = tuple(canonical_ids)
    canonical_set = set(canonical)
    if len(canonical) != len(canonical_set):
        raise ValueError("canonical ids must be unique")
    covered: set[str] = set()
    for name, engine_ids in groups.items():
        if not name.strip():
            raise ValueError("coverage group name required")
        covered.update(engine_ids)
    return CoverageReport(
        canonical_count=len(canonical_set),
        covered_count=len(covered & canonical_set),
        missing=tuple(sorted(canonical_set - covered)),
        unknown=tuple(sorted(covered - canonical_set)),
    )
