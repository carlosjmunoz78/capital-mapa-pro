from dataclasses import dataclass, field
from typing import Dict

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class JobSpec:
    job_id: str
    company_id: str
    engine_id: str
    idempotency_key: str
    max_attempts: int = 3
    environment: str = "LAB"
    version: str = "1.0.0"

    def validate(self):
        if not all([self.job_id, self.company_id, self.engine_id, self.idempotency_key, self.version]):
            raise ValueError("missing job field")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >=1")
        return True

    @property
    def scope_key(self) -> tuple[str, str, str, str, str]:
        return (self.company_id, self.engine_id, self.environment, self.version, self.idempotency_key)


@dataclass
class JobStore:
    states: Dict[tuple[str, str, str, str, str], str] = field(default_factory=dict)
    evidence_refs: Dict[tuple[str, str, str, str, str], str] = field(default_factory=dict)

    def reserve(self, job: JobSpec):
        job.validate()
        key = job.scope_key
        if key in self.states:
            return False
        self.states[key] = "PENDING"
        return True

    def complete(self, job: JobSpec, evidence_ref: str):
        job.validate()
        key = job.scope_key
        if key not in self.states:
            raise ValueError("job must be reserved in the same scope before completion")
        if self.states[key] != "PENDING":
            raise ValueError("only pending jobs can complete")
        if not isinstance(evidence_ref, str) or not evidence_ref.strip():
            raise ValueError("successful job completion requires evidence_ref")
        self.evidence_refs[key] = evidence_ref.strip()
        self.states[key] = "SUCCESS"

    def fail(self, job: JobSpec):
        job.validate()
        key = job.scope_key
        if key not in self.states:
            raise ValueError("job must be reserved in the same scope before failure")
        if self.states[key] != "PENDING":
            raise ValueError("only pending jobs can fail")
        self.states[key] = "FAILED"
