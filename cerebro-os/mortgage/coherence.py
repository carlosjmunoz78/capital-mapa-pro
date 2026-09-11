from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fact:
    company_id: str
    entity_id: str
    attribute: str
    value: str
    source_ref: str
    confidence: float = 1.0

    def validate(self) -> None:
        if not all((self.company_id.strip(), self.entity_id.strip(), self.attribute.strip(), self.value.strip(), self.source_ref.strip())):
            raise ValueError("company_id, entity_id, attribute, value and source_ref are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class Contradiction:
    entity_id: str
    attribute: str
    values: tuple[str, ...]
    source_refs: tuple[str, ...]


class CoherenceGraph:
    """Deterministic, tenant-scoped contradiction graph for COH-001.

    It does not infer truth. It only detects incompatible asserted values for the
    same entity/attribute and preserves provenance for review.
    """

    def __init__(self, company_id: str, min_confidence: float = 0.5) -> None:
        if not company_id.strip():
            raise ValueError("company_id required")
        if not 0.0 <= min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0 and 1")
        self.company_id = company_id
        self.min_confidence = min_confidence
        self._facts: list[Fact] = []

    def add(self, fact: Fact) -> None:
        fact.validate()
        if fact.company_id != self.company_id:
            raise ValueError("cross-company fact denied")
        self._facts.append(fact)

    @staticmethod
    def _norm(value: str) -> str:
        return " ".join(value.strip().casefold().split())

    def contradictions(self) -> tuple[Contradiction, ...]:
        grouped: dict[tuple[str, str], list[Fact]] = {}
        for fact in self._facts:
            if fact.confidence < self.min_confidence:
                continue
            grouped.setdefault((fact.entity_id, fact.attribute), []).append(fact)

        result: list[Contradiction] = []
        for (entity_id, attribute), facts in grouped.items():
            values = {self._norm(f.value) for f in facts}
            if len(values) <= 1:
                continue
            result.append(
                Contradiction(
                    entity_id=entity_id,
                    attribute=attribute,
                    values=tuple(sorted(values)),
                    source_refs=tuple(sorted({f.source_ref for f in facts})),
                )
            )
        return tuple(sorted(result, key=lambda x: (x.entity_id, x.attribute)))

    def status(self) -> str:
        if not self._facts:
            return "RED"
        if any(f.confidence < self.min_confidence for f in self._facts):
            return "HUMAN_REQUIRED"
        return "RED" if self.contradictions() else "GREEN"

    def evidence_refs(self) -> tuple[str, ...]:
        return tuple(sorted({f.source_ref for f in self._facts}))
