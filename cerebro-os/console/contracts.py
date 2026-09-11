from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class ConsoleCommand:
    user_id: str
    company_id: str
    context_type: str
    context_id: str | None
    message: str
    environment: str = "LAB"
    version: str = "1.0.0"
    attachments: tuple[str, ...] = field(default_factory=tuple)
    request_id: str = field(default_factory=lambda: str(uuid4()))

    def validate(self) -> None:
        if not self.user_id.strip():
            raise ValueError("user_id required")
        if not self.company_id.strip():
            raise ValueError("company_id required")
        if not self.context_type.strip():
            raise ValueError("context_type required")
        if not self.message.strip():
            raise ValueError("message required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if not self.version.strip():
            raise ValueError("version required")
