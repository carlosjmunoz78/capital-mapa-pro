from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class EvaluationResult:
    engine_id: str
    score: float
    threshold: float
    evidence_refs: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.engine_id:
            raise ValueError("engine_id required")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0 and 1")
        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError("threshold must be between 0 and 1")

    @property
    def passed(self) -> bool:
        self.validate()
        return self.score >= self.threshold and bool(self.evidence_refs)


def aggregate(results: Iterable[EvaluationResult]) -> bool:
    values = tuple(results)
    return bool(values) and all(item.passed for item in values)
