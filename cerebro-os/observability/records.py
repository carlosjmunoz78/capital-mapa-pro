from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class ExecutionRecord:
    company_id: str
    engine_id: str
    version: str
    environment: str
    action: str
    result: str
    evidence_ref: str
    duration_ms: int
    cost_eur: float = 0.0
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def validate(self) -> None:
        required = (self.company_id, self.engine_id, self.version, self.environment, self.action, self.result, self.evidence_ref, self.request_id)
        if any(not value or (isinstance(value, str) and not value.strip()) for value in required):
            raise ValueError("observability record missing required field")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.duration_ms < 0 or self.cost_eur < 0:
            raise ValueError("duration and cost must be non-negative")
