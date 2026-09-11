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
        if self.max_attempts < 1: raise ValueError("max_attempts must be >=1")
        return True

@dataclass
class JobStore:
    states: Dict[str, str] = field(default_factory=dict)

    def reserve(self, job: JobSpec):
        job.validate()
        if job.idempotency_key in self.states: return False
        self.states[job.idempotency_key] = "PENDING"; return True

    def complete(self, key: str): self.states[key] = "SUCCESS"
    def fail(self, key: str): self.states[key] = "FAILED"
