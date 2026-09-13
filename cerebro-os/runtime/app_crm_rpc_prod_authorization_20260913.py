from __future__ import annotations

EVIDENCE = {
    "captured_at": "2026-09-13",
    "authorization": "APPROVED",
    "scope": {
        "create_five_server_only_wrappers": True,
        "controlled_gateway_routing": True,
        "migrate_callers_one_by_one": True,
        "old_vs_new_required": True,
        "rollback_required": True,
        "permission_retirement_allowed_before_zero_callers": False,
    },
    "execution": {
        "supabase_wrapper_migration_applied": False,
        "supabase_block_reason": "EXECUTION_LAYER_BLOCKED",
        "github_caller_persist_applied": False,
        "github_block_reason": "EXECUTION_LAYER_BLOCKED",
        "prod_permissions_changed": False,
        "prod_gateway_changed": False,
    },
    "safe_parallel_evidence": {
        "caller_inventory_green": True,
        "direct_call_count": 10,
        "unique_rpc_count": 8,
        "runner_rehearsal_green": True,
        "existing_server_wrappers": 3,
        "missing_server_wrappers": 5,
    },
}


def assess() -> dict:
    return {
        **EVIDENCE,
        "authorization_green": True,
        "prod_execution_green": False,
        "permission_retirement_blocked": True,
        "status": "AUTHORIZED_EXECUTION_BLOCKED_FAIL_CLOSED",
    }
