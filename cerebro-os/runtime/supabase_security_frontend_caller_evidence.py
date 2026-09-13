from __future__ import annotations

# Read-only evidence captured from the current main branch of
# carlosjmunoz78/fenix-capital-inmo-map. This module records observed callers
# only; it authorizes no PROD mutation, grant/RLS change, RPC retirement, or
# automatic migration.

TARGET_MUTATORS = (
    "fenix_prod_chat_attachment_add_user",
    "fenix_prod_chat_attachment_add_v2_user",
    "fenix_prod_chat_conversation_create_user",
    "fenix_prod_chat_group_create_user",
    "fenix_prod_chat_send_user",
    "fenix_prod_chat_send_v2_user",
    "fenix_prod_contact_create",
    "fenix_prod_contact_create_v2",
    "fenix_prod_exp_create",
    "fenix_prod_exp_update",
    "fenix_prod_inmo_followup_update_v1",
    "fenix_prod_notification_mark_user",
    "fenix_prod_profile_socials_update_user",
    "fenix_prod_profile_update_user",
    "fenix_prod_sign_create",
)

CURRENT_FRONTEND_EVIDENCE = {
    "fenix_prod_chat_send_user": {
        "classification": "KEEP_AND_WRAP",
        "caller": "src/ChatShell.tsx",
        "direct_rpc_observed": True,
        "notes": "Authenticated chat send; client supplies body and idempotency key, actor identity is server-derived.",
    },
    "fenix_prod_contact_create": {
        "classification": "KEEP_AND_WRAP",
        "caller": "src/ContactCreateShell.tsx",
        "direct_rpc_observed": True,
        "notes": "Current PROD contact-create path calls the RPC directly.",
    },
    "fenix_prod_exp_create": {
        "classification": "KEEP_AND_WRAP",
        "caller": "src/ExpedienteCreateShell.tsx",
        "direct_rpc_observed": True,
        "notes": "Current PROD expediente-create dependency previously verified from source.",
    },
    "fenix_prod_exp_update": {
        "classification": "KEEP_AND_WRAP",
        "caller": "src/ExpedienteRenameGuard.tsx",
        "direct_rpc_observed": True,
        "notes": "Current PROD rename path calls exp_update with expected_version and scoped nullable fields.",
    },
    "fenix_prod_notification_mark_user": {
        "classification": "KEEP_AND_WRAP",
        "caller": "src/NotificationsShell.tsx",
        "direct_rpc_observed": True,
        "notes": "Current authenticated notification state mutation previously verified from source.",
    },
    "fenix_prod_sign_create": {
        "classification": "KEEP_AND_WRAP",
        "caller": "src/FirmaCreateShell.tsx",
        "direct_rpc_observed": True,
        "human_gate": "SIGNATURE_REQUIRED",
        "notes": "Current PROD signature-create dependency previously verified from source.",
    },
}

CURRENT_FRONTEND_NEGATIVE_EVIDENCE = {
    "src/ProfileShell.tsx": {
        "target_mutator_reference_observed": False,
        "write_contract": "EDITING_DISABLED_UNTIL_AUTHORIZED_WRITE_CONTRACT",
    },
    "src/B2BContactCreateShell.tsx": {
        "target_mutator_reference_observed": False,
        "write_contract": "EDGE_B2B_ACTIONS_API",
    },
    "src/InmobiliariaCreateShell.tsx": {
        "target_mutator_reference_observed": False,
        "write_contract": "EDGE_B2B_ACTIONS_OR_LEGACY_TEST_ROUTE",
    },
    "src/InmobiliariaDetailShell.tsx": {
        "target_mutator_reference_observed": False,
        "write_contract": "EDGE_B2B_ACTIONS_API",
    },
    "src/ExpedienteLifecycleGuard.tsx": {
        "target_mutator_reference_observed": False,
        "write_contract": "EDGE_FENIX_EXPEDIENTE_STAGE",
    },
    "src/ExpedienteFollowupConfirmationGuard.tsx": {
        "target_mutator_reference_observed": False,
        "write_contract": "UI_CONFIRMATION_GUARD_ONLY",
    },
    "src/ContactDetailShell.tsx": {
        "target_mutator_reference_observed": False,
        "write_contract": "READ_ONLY_DETAIL_PLUS_PREPARED_CORRECTION",
    },
}


def assess_frontend_mutator_evidence() -> dict:
    observed = tuple(sorted(CURRENT_FRONTEND_EVIDENCE))
    unresolved = tuple(name for name in TARGET_MUTATORS if name not in CURRENT_FRONTEND_EVIDENCE)
    return {
        "target_mutator_count": len(TARGET_MUTATORS),
        "current_frontend_direct_callers_observed": observed,
        "current_frontend_direct_caller_count": len(observed),
        "remaining_mutators_without_current_frontend_direct_caller_proof": unresolved,
        "remaining_count": len(unresolved),
        "all_observed_direct_callers_keep_and_wrap": all(
            row["classification"] == "KEEP_AND_WRAP" for row in CURRENT_FRONTEND_EVIDENCE.values()
        ),
        "signature_gate_preserved": CURRENT_FRONTEND_EVIDENCE["fenix_prod_sign_create"].get("human_gate") == "SIGNATURE_REQUIRED",
        "negative_evidence_file_count": len(CURRENT_FRONTEND_NEGATIVE_EVIDENCE),
        "prod_change_allowed": False,
        "grant_or_rls_change_allowed": False,
        "retirement_allowed": False,
        "status": "FRONTEND_CALLER_MAP_PARTIAL_KEEP_AND_WRAP",
    }
