from __future__ import annotations

from dataclasses import dataclass, field

VALID_EXECUTION_MODES = {"RUNTIME", "MAKE", "DISABLED"}


@dataclass(frozen=True)
class CollectorCandidate:
    collector_id: str
    source_type: str
    execution_mode: str
    estimated_cost_units: float
    expected_signal_score: float
    requires_saas_connector: bool = False

    def validate(self) -> None:
        if not self.collector_id.strip() or not self.source_type.strip():
            raise ValueError("collector_id and source_type are required")
        if self.execution_mode not in VALID_EXECUTION_MODES:
            raise ValueError("invalid execution_mode")
        if self.estimated_cost_units < 0:
            raise ValueError("estimated_cost_units cannot be negative")
        if not 0.0 <= self.expected_signal_score <= 1.0:
            raise ValueError("expected_signal_score must be between 0 and 1")

    @property
    def signal_per_cost(self) -> float:
        self.validate()
        if self.estimated_cost_units == 0:
            return float("inf") if self.expected_signal_score > 0 else 0.0
        return self.expected_signal_score / self.estimated_cost_units


@dataclass
class MonthlyCollectorBudget:
    make_credit_limit: float = 10_000.0
    make_reserve: float = 1_000.0
    make_spent: float = 0.0
    allocations: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.make_credit_limit <= 0:
            raise ValueError("make_credit_limit must be positive")
        if self.make_reserve < 0 or self.make_reserve >= self.make_credit_limit:
            raise ValueError("make_reserve must be non-negative and below limit")
        if self.make_spent < 0:
            raise ValueError("make_spent cannot be negative")

    @property
    def make_available(self) -> float:
        return max(0.0, self.make_credit_limit - self.make_reserve - self.make_spent)

    def can_allocate(self, candidate: CollectorCandidate) -> bool:
        candidate.validate()
        if candidate.execution_mode != "MAKE":
            return True
        return candidate.estimated_cost_units <= self.make_available

    def allocate(self, candidate: CollectorCandidate) -> str:
        candidate.validate()
        if candidate.execution_mode == "DISABLED":
            return "DISABLED"
        if candidate.execution_mode == "RUNTIME":
            self.allocations[candidate.collector_id] = 0.0
            return "RUNTIME"
        if not self.can_allocate(candidate):
            return "BUDGET_BLOCKED"
        self.make_spent += candidate.estimated_cost_units
        self.allocations[candidate.collector_id] = candidate.estimated_cost_units
        return "MAKE"


def choose_execution_mode(
    *,
    requires_saas_connector: bool,
    runtime_supported: bool,
    make_supported: bool,
    estimated_make_cost_units: float,
    expected_signal_score: float,
    minimum_signal_per_cost: float = 0.01,
) -> str:
    if runtime_supported and not requires_saas_connector:
        return "RUNTIME"
    if not make_supported:
        return "RUNTIME" if runtime_supported else "DISABLED"
    if estimated_make_cost_units < 0 or not 0.0 <= expected_signal_score <= 1.0:
        raise ValueError("invalid cost or signal score")
    if estimated_make_cost_units == 0:
        return "MAKE"
    efficiency = expected_signal_score / estimated_make_cost_units
    if efficiency < minimum_signal_per_cost and runtime_supported:
        return "RUNTIME"
    return "MAKE"
