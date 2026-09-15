from __future__ import annotations

from dataclasses import dataclass

REQUIRED_GATES = (
    "knowledge_12_12",
    "lab_capability_green",
    "controlled_shadow_replay",
    "immutable_nonprod_casepack",
    "observability_contract",
    "rollback_rehearsal",
    "backup_rebuild_contract",
    "zero_additional_cost_default",
    "policy_gate",
    "preprod_tribunal",
)


@dataclass(frozen=True)
class PreprodReadiness:
    gates: dict[str, bool]
    app_crm_prod_touched: bool = False

    @property
    def missing(self) -> tuple[str, ...]:
        return tuple(gate for gate in REQUIRED_GATES if not self.gates.get(gate, False))

    @property
    def ready_for_preprod_candidate(self) -> bool:
        return not self.missing and not self.app_crm_prod_touched


DEFAULT_READINESS = PreprodReadiness(
    gates={
        "knowledge_12_12": True,
        "lab_capability_green": True,
        "controlled_shadow_replay": True,
        "immutable_nonprod_casepack": True,
        # These are readiness contracts/rehearsals only. They do not enable PREPROD.
        "observability_contract": True,
        "rollback_rehearsal": True,
        "backup_rebuild_contract": True,
        "zero_additional_cost_default": True,
        "policy_gate": True,
        "preprod_tribunal": True,
    },
    app_crm_prod_touched=False,
)


def preprod_readiness_report() -> dict[str, object]:
    r = DEFAULT_READINESS
    return {
        "required_gates": REQUIRED_GATES,
        "missing": r.missing,
        "ready_for_preprod_candidate": r.ready_for_preprod_candidate,
        "preprod_enabled": False,
        "autonomy_green": False,
        "prod_enabled": False,
        "app_crm_prod_touched": r.app_crm_prod_touched,
        "cost_policy": "0 EUR additional by default",
        "promotion_note": "Candidate readiness is not PREPROD activation or production authorization.",
    }
