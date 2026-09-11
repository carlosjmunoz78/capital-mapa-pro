from dataclasses import dataclass
from typing import Iterable

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class EvaluationResult:
    engine_id: str
    score: float
    threshold: float
    evidence_refs: tuple[str, ...] = ()
    company_id: str = "GLOBAL"
    environment: str = "LAB"
    version: str = "1.0.0"

    def validate(self) -> None:
        if not self.engine_id.strip():
            raise ValueError("engine_id required")
        if not self.company_id.strip():
            raise ValueError("company_id required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if not self.version.strip():
            raise ValueError("version required")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0 and 1")
        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError("threshold must be between 0 and 1")

    @property
    def passed(self) -> bool:
        self.validate()
        refs = tuple(ref for ref in self.evidence_refs if isinstance(ref, str) and ref.strip())
        return self.score >= self.threshold and bool(refs)


def aggregate(
    results: Iterable[EvaluationResult],
    *,
    company_id: str | None = None,
    environment: str | None = None,
    version: str | None = None,
) -> bool:
    values = tuple(results)
    if not values:
        return False
    for item in values:
        item.validate()
    companies = {item.company_id for item in values}
    environments = {item.environment for item in values}
    versions = {item.version for item in values}
    if len(companies) != 1 or len(environments) != 1 or len(versions) != 1:
        return False
    if company_id is not None and companies != {company_id}:
        return False
    if environment is not None and environments != {environment}:
        return False
    if version is not None and versions != {version}:
        return False
    return all(item.passed for item in values)
