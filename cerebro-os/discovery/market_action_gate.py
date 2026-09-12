from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from market_intelligence import MarketSignal

HUMAN_REASONS = {
    "LEGAL_REQUIRED",
    "SIGNATURE_REQUIRED",
    "LOW_CONFIDENCE",
    "HIGH_RISK",
    "POLICY_CONFLICT",
    "SECURITY_INCIDENT",
    "MONEY_LIMIT",
    "CUSTOMER_HUMAN_REQUEST",
}


@dataclass(frozen=True)
class MarketActionDecision:
    company_id: str
    competitor_id: str
    environment: str
    version: str
    decision: str
    evidence_ref: str
    reason: str = ""

    def validate(self) -> None:
        if not all((self.company_id.strip(), self.competitor_id.strip(), self.environment.strip(), self.version.strip(), self.decision.strip(), self.evidence_ref.strip())):
            raise ValueError("market action decision missing required field")
        if self.environment not in {"LAB", "PREPROD", "PROD"}:
            raise ValueError("invalid environment")
        if self.decision not in {"OBSERVE", "REVIEW", "PROPOSAL_READY", "HUMAN_REQUIRED"}:
            raise ValueError("invalid decision")
        if self.decision == "HUMAN_REQUIRED" and self.reason not in HUMAN_REASONS:
            raise ValueError("invalid HUMAN_REQUIRED reason")
        if self.decision != "HUMAN_REQUIRED" and self.reason:
            raise ValueError("reason only allowed for HUMAN_REQUIRED")


def decide_market_action(
    signal: MarketSignal,
    *,
    confidence_floor: float = 0.80,
    high_risk: bool = False,
    money_required: bool = False,
    policy_conflict: bool = False,
) -> MarketActionDecision:
    signal.validate()
    if signal.confidence < confidence_floor:
        decision, reason = "HUMAN_REQUIRED", "LOW_CONFIDENCE"
    elif high_risk:
        decision, reason = "HUMAN_REQUIRED", "HIGH_RISK"
    elif policy_conflict:
        decision, reason = "HUMAN_REQUIRED", "POLICY_CONFLICT"
    elif money_required:
        decision, reason = "HUMAN_REQUIRED", "MONEY_LIMIT"
    elif signal.action == "ACTION_CANDIDATE":
        # A competitor signal may produce a proposal, never an external mutation by itself.
        decision, reason = "PROPOSAL_READY", ""
    elif signal.action == "REVIEW":
        decision, reason = "REVIEW", ""
    else:
        decision, reason = "OBSERVE", ""
    result = MarketActionDecision(
        company_id=signal.company_id,
        competitor_id=signal.competitor_id,
        environment=signal.environment,
        version=signal.version,
        decision=decision,
        evidence_ref=signal.evidence_ref,
        reason=reason,
    )
    result.validate()
    return result


def decide_many(signals: Iterable[MarketSignal]) -> tuple[MarketActionDecision, ...]:
    return tuple(decide_market_action(signal) for signal in signals)
