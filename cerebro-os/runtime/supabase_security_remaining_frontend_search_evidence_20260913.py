from __future__ import annotations

# Evidence-only snapshot from GitHub code search against
# carlosjmunoz78/fenix-capital-inmo-map default branch on 2026-09-13.
# Each unresolved mutator name returned zero indexed matches. This is negative
# evidence for current frontend source only; it is NOT proof that the RPC is unused
# by all callers, generated bundles, external automations, historical clients, or
# non-indexed paths. Therefore it authorizes no retirement or privilege change.

APP_REPOSITORY = "carlosjmunoz78/fenix-capital-inmo-map"
APP_BRANCH = "main"
APP_HEAD_SHA = "95106d8e792257f809033486b7025d81665ea83b"

SEARCHED_MUTATORS = (
    "fenix_prod_chat_attachment_add_user",
    "fenix_prod_chat_attachment_add_v2_user",
    "fenix_prod_chat_conversation_create_user",
    "fenix_prod_chat_group_create_user",
    "fenix_prod_chat_send_v2_user",
    "fenix_prod_contact_create_v2",
    "fenix_prod_inmo_followup_update_v1",
    "fenix_prod_profile_socials_update_user",
    "fenix_prod_profile_update_user",
)

SEARCH_RESULTS = {name: 0 for name in SEARCHED_MUTATORS}


def assess_remaining_frontend_search_evidence() -> dict:
    zero_match = tuple(name for name, count in SEARCH_RESULTS.items() if count == 0)
    return {
        "app_repository": APP_REPOSITORY,
        "app_branch": APP_BRANCH,
        "app_head_sha": APP_HEAD_SHA,
        "searched_mutator_count": len(SEARCHED_MUTATORS),
        "zero_indexed_match_count": len(zero_match),
        "zero_indexed_matches": zero_match,
        "all_nine_zero_indexed_matches": len(zero_match) == 9,
        "frontend_negative_search_evidence_complete": len(zero_match) == 9,
        "global_caller_absence_proven": False,
        "rpc_unused_proven": False,
        "retirement_allowed": False,
        "grant_or_rls_change_allowed": False,
        "prod_change_allowed": False,
        "next_required_evidence": (
            "non_frontend_caller_inventory",
            "runtime_or_query_log_evidence_where_available",
            "mutator_family_parity_complete",
            "human_high_risk_gate_before_any_prod_security_change",
        ),
        "status": "NINE_FRONTEND_INDEX_SEARCHES_ZERO_MATCH_GLOBAL_CALLER_PROOF_PENDING",
    }
