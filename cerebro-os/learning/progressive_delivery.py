from __future__ import annotations

from dataclasses import dataclass

ALLOWED_STEPS = (1, 5, 25, 50, 100)


@dataclass(frozen=True)
class DeliveryEvidence:
    baseline_value: float
    candidate_value: float
    direction: str
    sample_size: int
    minimum_sample_size: int
    live_effect_verified: bool
    rollback_ready: bool
    policy_approved: bool
    environment: str
    current_percent: int

    def validate(self) -> None:
        if self.direction not in {"MAXIMIZE", "MINIMIZE"}:
            raise ValueError("invalid direction")
        if self.environment not in {"LAB", "PREPROD", "PROD"}:
            raise ValueError("invalid environment")
        if self.current_percent not in ALLOWED_STEPS:
            raise ValueError("invalid current_percent")
        if self.sample_size < 0 or self.minimum_sample_size < 1:
            raise ValueError("invalid sample size")


@dataclass(frozen=True)
class DeliveryDecision:
    decision: str
    next_percent: int
    reason: str
    rollback_required: bool


def _improved(e: DeliveryEvidence) -> bool:
    if e.direction == "MAXIMIZE":
        return e.candidate_value > e.baseline_value
    return e.candidate_value < e.baseline_value


def decide_progressive_delivery(e: DeliveryEvidence) -> DeliveryDecision:
    e.validate()
    if e.environment != "PROD":
        return DeliveryDecision("HOLD", e.current_percent, "PROD_EVIDENCE_REQUIRED", False)
    if not e.live_effect_verified:
        return DeliveryDecision("HOLD", e.current_percent, "LIVE_EFFECT_NOT_VERIFIED", False)
    if not e.policy_approved:
        return DeliveryDecision("HOLD", e.current_percent, "POLICY_NOT_APPROVED", False)
    if not e.rollback_ready:
        return DeliveryDecision("HOLD", e.current_percent, "ROLLBACK_NOT_READY", False)
    if e.sample_size < e.minimum_sample_size:
        return DeliveryDecision("HOLD", e.current_percent, "MORE_EVIDENCE", False)
    if not _improved(e):
        return DeliveryDecision("ROLLBACK", e.current_percent, "POST_PROMOTION_REGRESSION", True)
    idx = ALLOWED_STEPS.index(e.current_percent)
    if idx == len(ALLOWED_STEPS) - 1:
        return DeliveryDecision("MONITOR", e.current_percent, "FULL_DELIVERY_MONITOR", False)
    return DeliveryDecision("ADVANCE", ALLOWED_STEPS[idx + 1], "MEASURED_IMPROVEMENT", False)
