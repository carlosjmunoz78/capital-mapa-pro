from __future__ import annotations

# Read-only evidence captured from the current main branch of
# carlosjmunoz78/fenix-capital-inmo-map. This module records observed callers
# only; it authorizes no PROD mutation, grant/RLS change, RPC retirement, or
# automatic migration.

APP_REPOSITORY = "carlosjmunoz78/fenix-capital-inmo-map"
APP_BRANCH = "main"
APP_HEAD_SHA = "95106d8e792257f809033486b7025d81665ea83b"

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
        "caller_blob_sha": "3ff76545a4366c6f4cd02429a489d49ce3c179de",
        "direct_rpc_observed": True,
        "verified_against_app_head": APP_HEAD_SHA,
        "notes": "Authenticated chat send; client supplies body and idempotency key, actor identity is server-derived.",
    },
    "fenix_prod_contact_create": {
        "classification": "KEEP_AND_WRAP",
        "caller": "src/ContactCreateShell.tsx",
        "caller_blob_sha": "c88d4f9b661ac6aa8bb3c0f71d6e0df2844ab2ec",
        "direct_rpc_observed": True,
        "verified_against_app_head": APP_HEAD_SHA,
        "notes": "Current PROD contact-create path calls the RPC directly.",
    },
    "fenix_prod_exp_create": {
        "classification": "KEEP_AND_WRAP",
        "caller": "src/ExpedienteCreateShell.tsx",
        "caller_blob_sha": "e8d6d559848358606f1ea4c12f4c9d31e16e6f20",
        "direct_rpc_observed": True,
        "verified_against_app_head": APP_HEAD_SHA,
        "notes": "Current PROD expediente-create path calls the RPC directly.",
    },
    "fenix_prod_exp_update": {
        "classification": "KEEP_AND_WRAP",
        "caller": "src/ExpedienteRenameGuard.tsx",
        "caller_blob_sha": "8c3ab4d8599379726484e77e16ccbbcd24fea6c7",
        "direct_rpc_observed": True,
        "verified_against_app_head": APP_HEAD_SHA,
        "notes": "Current PROD rename path calls exp_update with expected_version and scoped nullable fields.",
    },
    "fenix_prod_notification_mark_user": {
        "classification": "KEEP_AND_WRAP",
        "caller": "src/NotificationsShell.tsx",
        "caller_blob_sha": "9044aafb40541e9192288c77c7d9c718f2a05e37",
        "direct_rpc_observed": True,
        "verified_against_app_head": APP_HEAD_SHA,
        "notes": "Current authenticated notification state mutation verified from source.",
    },
    "fenix_prod_sign_create": {
        "classification": "KEEP_AND_WRAP",
        "caller": "src/FirmaCreateShell.tsx",
        "caller_blob_sha": "e335914d08f4dfa913326b93476e072a145f2382",
        "direct_rpc_observed": True,
        "verified_against_app_head": APP_HEAD_SHA,
        "human_gate": "SIGNATURE_REQUIRED",
        "notes": "Current PROD signature-create dependency verified from source.",
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
    verified_at_head = tuple(
        name
        for name, row in CURRENT_FRONTEND_EVIDENCE.items()
        if row.get("verified_against_app_head") == APP_HEAD_SHA and bool(row.get("caller_blob_sha"))
    )
    return {
        "app_repository": APP_REPOSITORY,
        "app_branch": APP_BRANCH,
        "app_head_sha": APP_HEAD_SHA,
        "target_mutator_count": len(TARGET_MUTATORS),
        "current_frontend_direct_callers_observed": observed,
        "current_frontend_direct_caller_count": len(observed),
        "current_frontend_callers_verified_at_app_head": tuple(sorted(verified_at_head)),
        "current_frontend_callers_verified_at_app_head_count": len(verified_at_head),
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
        "status": "SIX_CURRENT_FRONTEND_CALLERS_VERIFIED_KEEP_AND_WRAP_NINE_REMAINING",
    }
