from __future__ import annotations

from collections import deque
from dataclasses import dataclass

@dataclass
class Job:
    job_id: str
    request_id: str
    company_id: str
    engine_id: str
    action: str
    payload: dict
    attempts: int = 0
    max_attempts: int = 3

class JobQueue:
    def __init__(self) -> None:
        self._queue: deque[Job] = deque()
        self._seen: set[str] = set()

    def enqueue(self, job: Job) -> bool:
        if job.job_id in self._seen:
            return False
        self._seen.add(job.job_id)
        self._queue.append(job)
        return True

    def pop(self) -> Job | None:
        if not self._queue:
            return None
        job = self._queue.popleft()
        job.attempts += 1
        return job

    def retry(self, job: Job) -> bool:
        if job.attempts >= job.max_attempts:
            return False
        self._queue.append(job)
        return True

    def __len__(self) -> int:
        return len(self._queue)
