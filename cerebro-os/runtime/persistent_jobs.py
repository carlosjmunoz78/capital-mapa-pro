from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class JobSpec:
    job_id: str
    company_id: str
    engine_id: str
    idempotency_key: str
    max_attempts: int = 3

    def validate(self):
        if not all([self.job_id, self.company_id, self.engine_id, self.idempotency_key]):
            raise ValueError("missing job field")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >=1")
        return True


@dataclass
class JobStore:
    states: Dict[str, str] = field(default_factory=dict)
    evidence_refs: Dict[str, str] = field(default_factory=dict)

    def reserve(self, job: JobSpec):
        job.validate()
        if job.idempotency_key in self.states:
            return False
        self.states[job.idempotency_key] = "PENDING"
        return True

    def complete(self, key: str, evidence_ref: str):
        if key not in self.states:
            raise ValueError("job must be reserved before completion")
        if self.states[key] != "PENDING":
            raise ValueError("only pending jobs can complete")
        if not isinstance(evidence_ref, str) or not evidence_ref.strip():
            raise ValueError("successful job completion requires evidence_ref")
        self.evidence_refs[key] = evidence_ref.strip()
        self.states[key] = "SUCCESS"

    def fail(self, key: str):
        if key not in self.states:
            raise ValueError("job must be reserved before failure")
        if self.states[key] != "PENDING":
            raise ValueError("only pending jobs can fail")
        self.states[key] = "FAILED"
