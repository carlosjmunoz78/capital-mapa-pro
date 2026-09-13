from __future__ import annotations

# Conservative disposition matrix for the 15 authenticated SECURITY DEFINER mutators.
# This module is intentionally non-executable: it does not alter grants, functions,
# RLS policies, routing, or PROD data. It records the migration decision gate only.

MUTATOR_DISPOSITION = {
    "fenix_prod_chat_attachment_add_user": "WRAP_REVIEW",
    "fenix_prod_chat_attachment_add_v2_user": "WRAP_REVIEW",
    "fenix_prod_chat_conversation_create_user": "WRAP_REVIEW",
    "fenix_prod_chat_group_create_user": "WRAP_REVIEW",
    "fenix_prod_chat_send_user": "WRAP_REVIEW",
    "fenix_prod_chat_send_v2_user": "WRAP_REVIEW",
    "fenix_prod_contact_create": "WRAP_REVIEW",
    "fenix_prod_contact_create_v2": "WRAP_REVIEW",
    "fenix_prod_exp_create": "WRAP_REVIEW",
    "fenix_prod_exp_update": "WRAP_REVIEW",
    "fenix_prod_inmo_followup_update_v1": "WRAP_REVIEW",
    "fenix_prod_notification_mark_user": "WRAP_REVIEW",
    "fenix_prod_profile_socials_update_user": "WRAP_REVIEW",
    "fenix_prod_profile_update_user": "WRAP_REVIEW",
    "fenix_prod_sign_create": "WRAP_REVIEW",
}

PARITY_REQUIREMENTS = (
    "authn_identity_equivalence",
    "authz_scope_equivalence",
    "input_validation_equivalence",
    "idempotency_or_versioning_equivalence",
    "write_set_equivalence",
    "error_contract_equivalence",
    "audit_event_equivalence",
    "rollback_path_proven",
)

SENSITIVE_MUTATORS = (
    "fenix_prod_exp_create",
    "fenix_prod_exp_update",
    "fenix_prod_inmo_followup_update_v1",
    "fenix_prod_profile_update_user",
    "fenix_prod_sign_create",
)


def assess_mutator_disposition() -> dict:
    values = tuple(MUTATOR_DISPOSITION.values())
    return {
        "mutator_count": len(MUTATOR_DISPOSITION),
        "all_unique": len(MUTATOR_DISPOSITION) == len(set(MUTATOR_DISPOSITION)),
        "keep_count": values.count("KEEP"),
        "wrap_review_count": values.count("WRAP_REVIEW"),
        "retire_count": values.count("RETIRE"),
        "parity_requirements": PARITY_REQUIREMENTS,
        "sensitive_mutators": SENSITIVE_MUTATORS,
        "automatic_prod_change_allowed": False,
        "automatic_grant_revoke_allowed": False,
        "automatic_retire_allowed": False,
        "human_reason": "HIGH_RISK",
        "status": "DISPOSITION_DEFINED_PARITY_PENDING",
    }
