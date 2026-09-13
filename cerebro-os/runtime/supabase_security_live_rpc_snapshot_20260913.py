from __future__ import annotations

# Read-only live PROD metadata snapshot captured on 2026-09-13.
# No DDL, grant, RLS, function-body, App, CRM or provider mutation was performed.
# The aggregate fingerprint is derived from the 15 observed function-definition
# fingerprints and is used only as an OLD-contract parity anchor.

RPC_COUNT = 15
AGGREGATE_CONTRACT_SHA256 = "f93c9a2869004808ac365f2ca8a01dcda7ad37237bd7332759ff8936996cb6cd"


def assess_live_rpc_snapshot() -> dict:
    return {
        "rpc_count": RPC_COUNT,
        "all_15_present_live": True,
        "all_15_security_definer_live": True,
        "all_15_authenticated_execute_live": True,
        "all_15_service_role_execute_live": True,
        "all_15_postgres_owned_live": True,
        "all_15_return_jsonb_live": True,
        "aggregate_contract_sha256": AGGREGATE_CONTRACT_SHA256,
        "parity_baseline_ready": True,
        "prod_mutation_performed": False,
        "grant_or_rls_change_performed": False,
        "retirement_performed": False,
        "security_green": False,
        "next_required_evidence": (
            "behavioral_parity_per_mutator_family",
            "non_frontend_and_runtime_caller_closure",
            "rollback_path_proven_before_security_change",
            "human_high_risk_gate_before_prod_security_change",
        ),
        "status": "LIVE_15_RPC_METADATA_GREEN_SECURITY_PARITY_PENDING",
    }
