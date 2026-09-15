from __future__ import annotations

from dataclasses import dataclass


REQUIRED_GATES = (
    "knowledge_12_of_12",
    "capability_green_lab",
    "representative_e2e",
    "shadow_replay",
    "immutable_nonprod_casepack",
    "observability",
    "rollback_rehearsal",
    "backup_rebuild",
    "zero_additional_cost_default",
    "policy_gate",
    "isolated_preprod_rehearsal",
    "app_crm_excluded",
    "prod_credentials_excluded",
    "customer_data_excluded",
)


@dataclass(frozen=True)
class PreprodActivationVerdict:
    verdict: str
    missing_gates: tuple[str, ...]
    preprod_enabled: bool
    capability_green_global: bool
    autonomy_green: bool
    prod_enabled: bool


def evaluate_preprod_activation(gates: dict[str, bool]) -> PreprodActivationVerdict:
    missing = tuple(gate for gate in REQUIRED_GATES if gates.get(gate) is not True)
    if missing:
        return PreprodActivationVerdict(
            verdict="BLOCKED",
            missing_gates=missing,
            preprod_enabled=False,
            capability_green_global=False,
            autonomy_green=False,
            prod_enabled=False,
        )

    return PreprodActivationVerdict(
        verdict="READY_FOR_PREPROD_ACTIVATION",
        missing_gates=(),
        preprod_enabled=False,
        capability_green_global=False,
        autonomy_green=False,
        prod_enabled=False,
    )


def canonical_preprod_activation_gates() -> dict[str, bool]:
    return {gate: True for gate in REQUIRED_GATES}
