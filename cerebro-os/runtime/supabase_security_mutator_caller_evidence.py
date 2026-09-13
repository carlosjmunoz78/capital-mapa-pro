from __future__ import annotations

# Conservative caller/wrapper evidence for the 15 authenticated SECURITY DEFINER mutators.
# This module is evidence-only: it does not execute RPCs, alter grants/RLS, mutate PROD,
# or retire any function. Exact caller coverage remains required before remediation.

MUTATORS = {
    "fenix_prod_chat_attachment_add_user": {"family": "chat", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_chat_attachment_add_v2_user": {"family": "chat", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_chat_conversation_create_user": {"family": "chat", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_chat_group_create_user": {"family": "chat", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_chat_send_user": {"family": "chat", "wrapper_evidence": "SERVER_WRAPPER_OBSERVED", "caller_evidence": "PARTIAL"},
    "fenix_prod_chat_send_v2_user": {"family": "chat", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_contact_create": {"family": "contacts", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_contact_create_v2": {"family": "contacts", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_exp_create": {"family": "expediente_followup", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_exp_update": {"family": "expediente_followup", "wrapper_evidence": "SERVER_WRAPPER_OBSERVED", "caller_evidence": "PARTIAL"},
    "fenix_prod_inmo_followup_update_v1": {"family": "expediente_followup", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_notification_mark_user": {"family": "notifications", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_profile_socials_update_user": {"family": "profile", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_profile_update_user": {"family": "profile", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING"},
    "fenix_prod_sign_create": {"family": "signature", "wrapper_evidence": "UNKNOWN", "caller_evidence": "PENDING", "human_gate": "SIGNATURE_REQUIRED"},
}


def assess_mutator_caller_evidence() -> dict:
    wrapper_observed = tuple(name for name, row in MUTATORS.items() if row["wrapper_evidence"] == "SERVER_WRAPPER_OBSERVED")
    exact_caller_green = tuple(name for name, row in MUTATORS.items() if row["caller_evidence"] == "GREEN")
    pending = tuple(name for name in MUTATORS if name not in exact_caller_green)
    return {
        "mutator_count": len(MUTATORS),
        "wrapper_observed_count": len(wrapper_observed),
        "wrapper_observed": wrapper_observed,
        "exact_caller_green_count": len(exact_caller_green),
        "pending_exact_caller_evidence": pending,
        "all_exact_callers_proven": not pending,
        "security_remediation_allowed": False,
        "automatic_prod_mutation_allowed": False,
        "automatic_grant_or_rls_change_allowed": False,
        "automatic_retirement_allowed": False,
        "signature_human_gate": "SIGNATURE_REQUIRED",
        "status": "CALLER_EVIDENCE_PARTIAL_WRAPPERS_OBSERVED" if wrapper_observed else "CALLER_EVIDENCE_PENDING",
    }
