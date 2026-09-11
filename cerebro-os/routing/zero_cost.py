from __future__ import annotations

from dataclasses import dataclass

ROUTE_ORDER = ("DETERMINISTIC", "LOCAL", "EXISTING_TOOL", "FREE_TIER", "SELF_HOSTED", "CHEAP_EXTERNAL", "PAID")
HEAVY_WORKLOADS = {"RESEARCH_HEAVY", "TRAINING", "LONG_JOB", "EXPERIMENT", "SIMULATION", "OCR_HEAVY", "BACKUP", "HEAVY_LOGS"}

@dataclass(frozen=True)
class ExecutionOption:
    route_type: str
    available: bool = True
    estimated_cost_eur: float = 0.0

    def validate(self) -> None:
        if self.route_type not in ROUTE_ORDER:
            raise ValueError("unsupported route_type")
        if self.estimated_cost_eur < 0:
            raise ValueError("estimated_cost_eur cannot be negative")

@dataclass(frozen=True)
class RouteDecision:
    route_type: str | None
    allowed: bool
    reason: str
    offload_from_supabase: bool


def choose_route(options: tuple[ExecutionOption, ...], workload_type: str, approved_limit_eur: float = 0.0) -> RouteDecision:
    if approved_limit_eur < 0:
        raise ValueError("approved_limit_eur cannot be negative")
    ranked = []
    for option in options:
        option.validate()
        if option.available:
            ranked.append(option)
    ranked.sort(key=lambda item: ROUTE_ORDER.index(item.route_type))
    offload = workload_type in HEAVY_WORKLOADS
    for option in ranked:
        if option.estimated_cost_eur <= approved_limit_eur:
            return RouteDecision(option.route_type, True, "WITHIN_APPROVED_LIMIT", offload)
    return RouteDecision(None, False, "MONEY_LIMIT", offload)
