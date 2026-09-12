from __future__ import annotations

ALERT_FOLDER_ID = 520866

SCENARIOS = {
    9527636: {"kind": "alert_classification_dedup", "mode": "INTERNAL", "status": "inactive", "incomplete": 0, "credits_snapshot": 0, "data_transfer_snapshot": 0},
    9527843: {"kind": "alert_queue_silencing", "mode": "INTERNAL", "status": "inactive", "incomplete": 0, "credits_snapshot": 0, "data_transfer_snapshot": 0},
    9527663: {"kind": "facebook_oauth_permissions", "mode": "READ_ONLY", "status": "inactive", "incomplete": 0, "credits_snapshot": 0, "data_transfer_snapshot": 0},
    9527908: {"kind": "facebook_pages_metrics", "mode": "READ_ONLY", "status": "inactive", "incomplete": 0, "credits_snapshot": 6, "data_transfer_snapshot": 1208},
    9522860: {"kind": "linkedin_health", "mode": "READ_ONLY", "status": "inactive", "incomplete": 0, "credits_snapshot": 0, "data_transfer_snapshot": 0},
    9527602: {"kind": "core_deterministic_monitor", "mode": "INTERNAL", "status": "inactive", "incomplete": 0, "credits_snapshot": 0, "data_transfer_snapshot": 0},
    9527718: {"kind": "facebook_capture_windows", "mode": "INTERNAL", "status": "inactive", "incomplete": 0, "credits_snapshot": 0, "data_transfer_snapshot": 0},
    9537666: {"kind": "youtube_health", "mode": "READ_ONLY", "status": "inactive", "incomplete": 0, "credits_snapshot": 0, "data_transfer_snapshot": 0},
}


def inventory() -> dict:
    return {
        "folder_id": ALERT_FOLDER_ID,
        "scenario_count": len(SCENARIOS),
        "scenario_ids": tuple(sorted(SCENARIOS)),
        "all_inactive": all(item["status"] == "inactive" for item in SCENARIOS.values()),
        "all_no_incomplete": all(item["incomplete"] == 0 for item in SCENARIOS.values()),
        "external_mutation_allowed": False,
        "publication_allowed": False,
        "auto_activate_allowed": False,
    }


def assess_observability_evidence() -> dict:
    """Classify only what the Make inventory proves; never infer monthly cost or live monitoring."""
    inv = inventory()
    read_only_edges = tuple(sorted(sid for sid, item in SCENARIOS.items() if item["mode"] == "READ_ONLY"))
    internal_monitors = tuple(sorted(sid for sid, item in SCENARIOS.items() if item["mode"] == "INTERNAL"))
    credits_snapshot_total = sum(item["credits_snapshot"] for item in SCENARIOS.values())
    transfer_snapshot_total = sum(item["data_transfer_snapshot"] for item in SCENARIOS.values())
    return {
        **inv,
        "read_only_edges": read_only_edges,
        "internal_monitors": internal_monitors,
        "credits_snapshot_total": credits_snapshot_total,
        "data_transfer_snapshot_total": transfer_snapshot_total,
        "logs_evidence": "PARTIAL_INVENTORY_ONLY",
        "metrics_evidence": "PARTIAL_READ_ONLY_SCENARIOS",
        "incident_evidence": "PARTIAL_ALERT_PIPELINE_INACTIVE",
        "cost_evidence": "SNAPSHOT_ONLY_NOT_MONTHLY_COST",
        "monthly_cost_eur": None,
        "observability_green": False,
        "cost_measured_green": False,
        "prod_candidate_allowed": False,
        "external_proof_pending": True,
    }
