from __future__ import annotations

FAMILIES = {
    "core_specific_replay": {
        "structural_status": "GREEN_CODE_CI",
        "external_gaps": (),
        "prod_candidate": False,
        "reason": "Specific legacy CORE contracts captured and fail-closed replay gate tested; no PROD cutover authorized.",
    },
    "factory_legacy": {
        "structural_status": "GREEN_CODE_CI",
        "external_gaps": (),
        "prod_candidate": False,
        "reason": "Six legacy factory adapters mapped to runtime targets; OLD preserved and external action disabled.",
    },
    "recovery": {
        "structural_status": "GREEN_CODE_CI",
        "external_gaps": ("SOURCE_BACKUP_PROOF", "PROVIDER_RESTORE_PROOF", "PROD_ROLLBACK_REHEARSAL_PROOF"),
        "prod_candidate": False,
        "reason": "Runtime recovery gate is green but real provider restore and PROD rollback evidence are not proven.",
    },
    "observability_cost": {
        "structural_status": "GREEN_CODE_CI",
        "external_gaps": ("ENGINE_LOGS_REF", "ENGINE_METRICS_REF", "ENGINE_INCIDENT_REF", "ENGINE_COST_MEASUREMENT"),
        "prod_candidate": False,
        "reason": "Gate exists; evidence must be attached per engine/family without inventing cost or telemetry.",
    },
}


def get_family(name: str) -> dict:
    try:
        return FAMILIES[name]
    except KeyError as exc:
        raise ValueError("unknown family") from exc


def external_evidence_queue() -> tuple[dict, ...]:
    queue = []
    for family, item in FAMILIES.items():
        for gap in item["external_gaps"]:
            queue.append({
                "family": family,
                "gap": gap,
                "status": "EXTERNAL_PROOF_PENDING",
                "blocks_prod_candidate": True,
                "automatic_external_action_allowed": False,
            })
    return tuple(queue)


def all_structural_green() -> bool:
    return all(item["structural_status"] == "GREEN_CODE_CI" for item in FAMILIES.values())


def global_prod_green() -> bool:
    # Deliberately impossible from structural evidence alone.
    return False
