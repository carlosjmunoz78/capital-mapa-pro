from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


GLOBAL_PROMOTION_GATES = (
    "customer_data_authorized",
    "security_gate_green",
    "cost_measured",
    "prod_credentials_controlled",
    "external_write_policy_green",
    "legal_signature_policy_green",
    "global_observability_green",
    "global_backup_rebuild_rollback_green",
    "prod_promotion_explicitly_authorized",
)


@dataclass(frozen=True)
class GlobalAutonomyReadinessVerdict:
    verdict: str
    gates: dict[str, bool]
    blockers: tuple[str, ...]
    capability_green_global: bool
    autonomy_green: bool
    prod_enabled: bool


def evaluate_global_autonomy_readiness(
    evidence: Mapping[str, bool],
) -> GlobalAutonomyReadinessVerdict:
    """Evaluate global/PROD readiness without performing promotion.

    This gate is deliberately fail-closed. Even when every readiness gate is
    evidenced, this function only returns READY_FOR_EXPLICIT_PROD_PROMOTION;
    it never mutates runtime flags, credentials, external integrations or PROD.
    """

    gates = {name: evidence.get(name) is True for name in GLOBAL_PROMOTION_GATES}
    blockers = tuple(name for name, passed in gates.items() if not passed)

    if blockers:
        return GlobalAutonomyReadinessVerdict(
            verdict="BLOCKED",
            gates=gates,
            blockers=blockers,
            capability_green_global=False,
            autonomy_green=False,
            prod_enabled=False,
        )

    return GlobalAutonomyReadinessVerdict(
        verdict="READY_FOR_EXPLICIT_PROD_PROMOTION",
        gates=gates,
        blockers=(),
        capability_green_global=False,
        autonomy_green=False,
        prod_enabled=False,
    )
