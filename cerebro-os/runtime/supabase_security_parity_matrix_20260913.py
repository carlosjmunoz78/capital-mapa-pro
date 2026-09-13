from __future__ import annotations

# Evidence-only parity matrix derived from live read-only inspection of fenix-capital-prod.
# No PROD mutation, grant revoke, RLS change, function replacement or retirement is authorized here.

PARITY_DIMENSIONS = (
    "authn_identity_equivalence",
    "authz_scope_equivalence",
    "input_validation_equivalence",
    "idempotency_or_versioning_equivalence",
    "write_set_equivalence",
    "error_contract_equivalence",
    "audit_event_equivalence",
    "rollback_path_proven",
)


def _dims(*green: str) -> dict[str, bool]:
    selected = set(green)
    return {name: name in selected for name in PARITY_DIMENSIONS}


TARGETS = {
    "fenix_prod_chat_send_user": {
        "server_target": "fenix_prod_chat_send_server",
        "evidence": "LIVE_DIRECT_DELEGATION_AFTER_AUTH_UID_TO_ACTIVE_ACTOR_RESOLUTION",
        "dimensions": _dims(
            "authn_identity_equivalence",
            "authz_scope_equivalence",
            "input_validation_equivalence",
            "idempotency_or_versioning_equivalence",
            "write_set_equivalence",
            "error_contract_equivalence",
            "audit_event_equivalence",
        ),
        "status": "STRUCTURAL_PARITY_7_OF_8_ROLLBACK_EVIDENCE_PENDING",
    },
    "fenix_prod_exp_update": {
        "server_target": "fenix_prod_exp_update_server",
        "evidence": "LIVE_DIRECT_DELEGATION_AFTER_AUTH_CONTEXT_RESOLUTION",
        "dimensions": _dims(
            "authn_identity_equivalence",
            "authz_scope_equivalence",
            "input_validation_equivalence",
            "idempotency_or_versioning_equivalence",
            "write_set_equivalence",
            "error_contract_equivalence",
            "audit_event_equivalence",
        ),
        "status": "STRUCTURAL_PARITY_7_OF_8_ROLLBACK_EVIDENCE_PENDING",
    },
    "fenix_prod_profile_update_user": {
        "server_target": "fenix_prod_profile_update_server",
        "evidence": "LIVE_IMPLEMENTATIONS_DIFFER_PROFILE_USER_WRITES_ACTOR_PROFILES_AND_MORE_FIELDS",
        "dimensions": _dims(),
        "status": "NOT_EQUIVALENT_BY_INSPECTION",
    },
    "fenix_prod_chat_attachment_add_user": {"server_target": None, "evidence": "NO_SERVER_EQUIVALENT_IDENTIFIED", "dimensions": _dims(), "status": "WRAPPER_REQUIRED"},
    "fenix_prod_chat_attachment_add_v2_user": {"server_target": None, "evidence": "NO_SERVER_EQUIVALENT_IDENTIFIED", "dimensions": _dims(), "status": "WRAPPER_REQUIRED"},
    "fenix_prod_chat_conversation_create_user": {"server_target": None, "evidence": "NO_SERVER_EQUIVALENT_IDENTIFIED", "dimensions": _dims(), "status": "WRAPPER_REQUIRED"},
    "fenix_prod_chat_group_create_user": {"server_target": None, "evidence": "NO_SERVER_EQUIVALENT_IDENTIFIED", "dimensions": _dims(), "status": "WRAPPER_REQUIRED"},
    "fenix_prod_chat_send_v2_user": {"server_target": None, "evidence": "NO_SERVER_EQUIVALENT_IDENTIFIED", "dimensions": _dims(), "status": "WRAPPER_REQUIRED"},
    "fenix_prod_contact_create": {"server_target": None, "evidence": "NO_SERVER_EQUIVALENT_IDENTIFIED", "dimensions": _dims(), "status": "WRAPPER_REQUIRED"},
    "fenix_prod_contact_create_v2": {"server_target": None, "evidence": "COMPOSES_USER_MUTATOR_AND_NO_SERVER_EQUIVALENT_IDENTIFIED", "dimensions": _dims(), "status": "WRAPPER_REQUIRED"},
    "fenix_prod_exp_create": {"server_target": None, "evidence": "NO_SERVER_EQUIVALENT_IDENTIFIED", "dimensions": _dims(), "status": "WRAPPER_REQUIRED"},
    "fenix_prod_inmo_followup_update_v1": {"server_target": None, "evidence": "NO_SERVER_EQUIVALENT_IDENTIFIED", "dimensions": _dims(), "status": "WRAPPER_REQUIRED"},
    "fenix_prod_notification_mark_user": {"server_target": None, "evidence": "NO_SERVER_EQUIVALENT_IDENTIFIED", "dimensions": _dims(), "status": "WRAPPER_REQUIRED"},
    "fenix_prod_profile_socials_update_user": {"server_target": None, "evidence": "NO_SERVER_EQUIVALENT_IDENTIFIED", "dimensions": _dims(), "status": "WRAPPER_REQUIRED"},
    "fenix_prod_sign_create": {"server_target": None, "evidence": "NO_SERVER_EQUIVALENT_IDENTIFIED_AND_SIGNATURE_REQUIRED", "dimensions": _dims(), "status": "WRAPPER_REQUIRED_SIGNATURE_REQUIRED"},
}


def assess() -> dict:
    complete = tuple(name for name, row in TARGETS.items() if all(row["dimensions"].values()))
    structural_7 = tuple(name for name, row in TARGETS.items() if sum(row["dimensions"].values()) == 7)
    wrapper_required = tuple(name for name, row in TARGETS.items() if row["server_target"] is None)
    return {
        "target_count": len(TARGETS),
        "parity_dimension_count": len(PARITY_DIMENSIONS),
        "fully_green_count": len(complete),
        "structural_7_of_8_count": len(structural_7),
        "structural_7_of_8": structural_7,
        "wrapper_required_count": len(wrapper_required),
        "wrapper_required": wrapper_required,
        "signature_required_preserved": TARGETS["fenix_prod_sign_create"]["status"] == "WRAPPER_REQUIRED_SIGNATURE_REQUIRED",
        "automatic_prod_mutation_allowed": False,
        "grant_revoke_allowed": False,
        "retirement_allowed": False,
        "security_green": False,
        "status": "TWO_STRUCTURAL_PARITY_PATHS_NEAR_GREEN_ROLLBACK_AND_REMAINING_WRAPPERS_PENDING",
    }
