from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class QualityInput:
    company_id: str
    engine_id: str
    environment: str
    version: str
    measurement_window: str
    expected_capture_at: datetime
    analytics_state: str
    data_quality: str
    human_validation: str
    eligible_for_cerebro: bool

    def validate(self) -> None:
        if not all(str(v).strip() for v in (self.company_id, self.engine_id, self.environment, self.version, self.measurement_window)):
            raise ValueError("quality gate missing scope")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.expected_capture_at.tzinfo is None:
            raise ValueError("expected_capture_at must be timezone-aware")


def evaluate_quality_gate(data: QualityInput, *, now: datetime | None = None) -> dict:
    data.validate()
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if data.expected_capture_at > now:
        status = "WAITING_CAPTURE"
    elif data.analytics_state != "Capturada" or data.data_quality == "Pendiente de captura":
        status = "TECHNICAL_REVIEW"
    elif data.data_quality == "Parcial":
        status = "PARTIAL_DATA_REVIEW"
    elif data.human_validation != "Validada":
        status = "HUMAN_REVIEW"
    elif data.eligible_for_cerebro:
        status = "ELIGIBLE_FOR_LEARNING"
    else:
        status = "HOLD_NOT_ELIGIBLE"
    return {
        "company_id": data.company_id,
        "engine_id": data.engine_id,
        "environment": data.environment,
        "version": data.version,
        "measurement_window": data.measurement_window,
        "status": status,
        "requires_human": status == "HUMAN_REVIEW",
        "learning_allowed": status == "ELIGIBLE_FOR_LEARNING",
    }
