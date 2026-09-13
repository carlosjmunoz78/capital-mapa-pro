from __future__ import annotations

# Non-executing parity plan for authenticated SECURITY DEFINER mutators.
# This file does not call RPCs, mutate PROD, alter grants/RLS, or retire functions.
# It groups the 15 mutators into families so evidence can be closed deterministically.

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

FAMILIES = {
    "chat": {
        "mutators": (
            "fenix_prod_chat_attachment_add_user",
            "fenix_prod_chat_attachment_add_v2_user",
            "fenix_prod_chat_conversation_create_user",
            "fenix_prod_chat_group_create_user",
            "fenix_prod_chat_send_user",
            "fenix_prod_chat_send_v2_user",
        ),
        "risk": "HIGH_RISK",
        "known_wrapper_relationships": (
            ("fenix_prod_chat_send_user", "server_wrapper_observed"),
        ),
        "exact_nonprod_parity_proven": False,
    },
    "contacts": {
        "mutators": (
            "fenix_prod_contact_create",
            "fenix_prod_contact_create_v2",
        ),
        "risk": "HIGH_RISK",
        "known_wrapper_relationships": (),
        "exact_nonprod_parity_proven": False,
    },
    "notifications": {
        "mutators": ("fenix_prod_notification_mark_user",),
        "risk": "HIGH_RISK",
        "known_wrapper_relationships": (),
        "exact_nonprod_parity_proven": False,
    },
    "profile": {
        "mutators": (
            "fenix_prod_profile_socials_update_user",
            "fenix_prod_profile_update_user",
        ),
        "risk": "HIGH_RISK",
        "known_wrapper_relationships": (),
        "exact_nonprod_parity_proven": False,
    },
    "expediente_followup": {
        "mutators": (
            "fenix_prod_exp_create",
            "fenix_prod_exp_update",
            "fenix_prod_inmo_followup_update_v1",
        ),
        "risk": "HIGH_RISK",
        "known_wrapper_relationships": (
            ("fenix_prod_exp_update", "server_wrapper_observed"),
        ),
        "exact_nonprod_parity_proven": False,
    },
    "signature": {
        "mutators": ("fenix_prod_sign_create",),
        "risk": "SIGNATURE_REQUIRED",
        "known_wrapper_relationships": (),
        "exact_nonprod_parity_proven": False,
    },
}


def assess_mutator_family_parity() -> dict:
    mutators = tuple(m for row in FAMILIES.values() for m in row["mutators"])
    duplicate_count = len(mutators) - len(set(mutators))
    pending_families = tuple(name for name, row in FAMILIES.items() if not row["exact_nonprod_parity_proven"])
    return {
        "family_count": len(FAMILIES),
        "mutator_count": len(mutators),
        "duplicate_count": duplicate_count,
        "all_15_accounted_for": len(mutators) == 15 and duplicate_count == 0,
        "parity_requirements": PARITY_REQUIREMENTS,
        "pending_families": pending_families,
        "security_green": not pending_families,
        "automatic_prod_rpc_execution_allowed": False,
        "automatic_grant_or_rls_change_allowed": False,
        "automatic_retirement_allowed": False,
        "signature_family_human_gate": "SIGNATURE_REQUIRED",
        "status": "MUTATOR_FAMILIES_MAPPED_PARITY_PENDING" if pending_families else "MUTATOR_FAMILY_PARITY_GREEN",
    }
