from __future__ import annotations

from collections import deque
from dataclasses import dataclass

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass
class Job:
    job_id: str
    request_id: str
    company_id: str
    engine_id: str
    action: str
    payload: dict
    environment: str = "LAB"
    version: str = "1.0.0"
    attempts: int = 0
    max_attempts: int = 3

    def validate(self) -> None:
        required = (self.job_id, self.request_id, self.company_id, self.engine_id, self.action, self.version)
        if any(not value or not str(value).strip() for value in required):
            raise ValueError("job missing required identity fields")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be positive")

    @property
    def idempotency_scope(self) -> tuple[str, str, str, str]:
        return (self.company_id, self.environment, self.engine_id, self.job_id)


class JobQueue:
    def __init__(self) -> None:
        self._queue: deque[Job] = deque()
        self._seen: set[tuple[str, str, str, str]] = set()

    def enqueue(self, job: Job) -> bool:
        job.validate()
        key = job.idempotency_scope
        if key in self._seen:
            return False
        self._seen.add(key)
        self._queue.append(job)
        return True

    def pop(self) -> Job | None:
        if not self._queue:
            return None
        job = self._queue.popleft()
        job.attempts += 1
        return job

    def retry(self, job: Job) -> bool:
        job.validate()
        if job.attempts >= job.max_attempts:
            return False
        self._queue.append(job)
        return True

    def __len__(self) -> int:
        return len(self._queue)
