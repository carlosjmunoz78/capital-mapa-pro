from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class BudgetDecision:
    allowed: bool
    reason: str


def check_additional_cost(cost_eur: float, approved_limit_eur: float = 0.0) -> BudgetDecision:
    if cost_eur < 0:
        raise ValueError("cost_eur cannot be negative")
    if approved_limit_eur < 0:
        raise ValueError("approved_limit_eur cannot be negative")
    if cost_eur <= approved_limit_eur:
        return BudgetDecision(True, "WITHIN_APPROVED_LIMIT")
    return BudgetDecision(False, "MONEY_LIMIT")
