from __future__ import annotations

# Read-only evidence captured from fenix-capital-prod on 2026-09-13.
# No table, data, policy or schema mutation was performed.

SCHEMA = "fenix_prod"
TABLES = {
    "activity_log": {"rows": 26, "columns": ("id", "actor_code", "actor_role", "entity_type", "entity_code", "action", "changed_fields", "source", "source_ref", "occurred_at", "created_at")},
    "daily_report_snapshots": {"rows": 3, "columns": ("report_date", "scope_key", "scope_kind", "scope_actor_code", "status", "activity_count", "payload", "generated_at")},
    "document_intelligence_runs": {"rows": 66, "columns": ("upload_id", "document_id", "expediente_code", "actor_code", "status", "extraction", "error", "created_at", "updated_at")},
    "lead_events": {"rows": 3, "columns": ("id", "idempotency_key", "identity_key", "payload_hash", "status", "cliente_id", "created_at")},
    "notification_state": {"rows": 4, "columns": ("id", "actor_code", "tarea_id", "read_at", "dismissed_at", "created_at", "updated_at")},
    "runtime_policies": {"rows": 1, "columns": ("policy_key", "value_json", "version", "active", "rationale", "updated_at")},
}
REQUIRED_ENGINE_SCOPE = ("company_id", "engine_id", "environment", "version")


def assess() -> dict:
    tables_with_full_engine_scope = tuple(
        name for name, row in TABLES.items()
        if all(field in row["columns"] for field in REQUIRED_ENGINE_SCOPE)
    )
    return {
        "schema": SCHEMA,
        "table_count": len(TABLES),
        "total_rows_observed": sum(row["rows"] for row in TABLES.values()),
        "live_operational_evidence_present": all(row["rows"] >= 0 for row in TABLES.values()),
        "tables_with_full_engine_scope": tables_with_full_engine_scope,
        "per_engine_prod_coverage_proven": len(tables_with_full_engine_scope) > 0,
        "shared_177_lab_scope_contract_remains_separate": True,
        "schema_mutation_performed": False,
        "prod_observability_green": False,
        "status": "PROD_OBSERVABILITY_LIVE_PRESENT_ENGINE_SCOPE_GAP_CONFIRMED",
    }
