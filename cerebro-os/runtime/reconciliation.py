from __future__ import annotations

from dataclasses import dataclass

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class ReconciliationInput:
    company_id: str
    engine_id: str
    environment: str
    version: str
    router_status: str
    log_status: str
    capture_status: str
    quality_status: str
    notion_state: str = ""

    def validate(self) -> None:
        required = (self.company_id, self.engine_id, self.environment, self.version, self.router_status, self.log_status, self.capture_status, self.quality_status)
        if any(not str(v).strip() for v in required):
            raise ValueError("reconciliation missing required fields")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")


def reconcile(data: ReconciliationInput) -> dict:
    data.validate()
    if data.capture_status == "REJECTED_EARLY_CAPTURE":
        status = "CONSISTENT_ROLLBACK_PENDING_RECAPTURE"
        difference = "TIMEZONE_ROLLBACK_PENDING_RECAPTURE"
        requires_human = False
    elif data.capture_status == "CAPTURED_PARTIAL":
        status = "CONSISTENT_CAPTURED_PARTIAL_HOLD" if data.quality_status == "PARTIAL_DATA_REVIEW" else "CAPTURE_QUALITY_MISMATCH"
        difference = "LEARNING_BLOCKED_PARTIAL_DATA"
        requires_human = True
    elif data.quality_status == "WAITING_CAPTURE":
        status = "CONSISTENT_WAITING_CAPTURE"
        difference = "NONE"
        requires_human = False
    else:
        status = "REVIEW_REQUIRED"
        difference = "NONE"
        requires_human = False
    return {
        "company_id": data.company_id,
        "engine_id": data.engine_id,
        "environment": data.environment,
        "version": data.version,
        "status": status,
        "difference": difference,
        "requires_human": requires_human,
        "learning_allowed": False,
        "external_action_allowed": False,
        "source_hash": "|".join((data.router_status, data.log_status, data.capture_status, data.quality_status)),
        "notion_state": data.notion_state,
    }
