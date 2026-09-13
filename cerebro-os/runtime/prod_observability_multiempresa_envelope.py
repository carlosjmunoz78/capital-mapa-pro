REQUIRED_SCOPE = ("company_id", "engine_id", "environment", "version")
LEGACY_TABLES = ("activity_log", "daily_report_snapshots", "document_intelligence_runs", "lead_events", "notification_state", "runtime_policies")


def assess():
    return {
        "required_scope": REQUIRED_SCOPE,
        "legacy_table_count": len(LEGACY_TABLES),
        "legacy_tables_modified": False,
        "parallel_contract_defined": True,
        "zero_cost_auxiliary_sink_preferred": True,
        "prod_mirroring_enabled": False,
        "prod_per_engine_coverage_proven": False,
        "automatic_prod_promotion_allowed": False,
        "status": "MULTIEMPRESA_OBSERVABILITY_ENVELOPE_DEFINED_MIRRORING_PENDING",
    }
