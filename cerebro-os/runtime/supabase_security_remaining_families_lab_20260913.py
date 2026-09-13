from __future__ import annotations

# LAB/CI-only closure model for the four remaining Supabase mutator families.
# Derived from the captured OLD behavior fingerprint and wrapper preservation contracts.
# It performs no RPC execution, SQL/DDL, grant/RLS change, App/CRM mutation or retirement.

FAMILIES = {
    "notifications": {
        "mutators": ("fenix_prod_notification_mark_user",),
        "preserve": ("task_owner_or_direccion_scope", "action_allowlist", "read_dismiss_restore_semantics"),
        "old_behavior": {"insert": True, "update": True, "notification": True},
        "human_required": None,
    },
    "profile_socials": {
        "mutators": ("fenix_prod_profile_socials_update_user",),
        "preserve": ("social_field_limits", "actor_profile_upsert", "activity_log_write"),
        "old_behavior": {"insert": True, "update": True, "activity_log": True},
        "human_required": None,
    },
    "profile_update": {
        "mutators": ("fenix_prod_profile_update_user",),
        "proposed_server": "fenix_prod_profile_update_self_server",
        "preserve": ("display_name_required", "username_uniqueness", "birth_date_validation", "actor_profile_full_write_set", "activity_log_write"),
        "old_behavior": {"insert": True, "update": True, "activity_log": True},
        "existing_profile_update_server_equivalent": False,
        "human_required": None,
    },
    "signature": {
        "mutators": ("fenix_prod_sign_create",),
        "preserve": ("direccion_or_financiero_scope", "financiero_owner_scope", "active_signature_conflict", "signature_state_derivation", "signature_write_set"),
        "old_behavior": {"insert": True, "update": False, "activity_log": False},
        "human_required": "SIGNATURE_REQUIRED",
    },
}


def assess() -> dict:
    mutators = tuple(m for row in FAMILIES.values() for m in row["mutators"])
    structural_lab_green = (
        len(FAMILIES) == 4
        and len(mutators) == 4
        and len(set(mutators)) == 4
        and all(bool(row["preserve"]) for row in FAMILIES.values())
        and FAMILIES["signature"]["human_required"] == "SIGNATURE_REQUIRED"
        and FAMILIES["profile_update"]["existing_profile_update_server_equivalent"] is False
    )
    return {
        "family_count": len(FAMILIES),
        "mutator_count": len(mutators),
        "structural_lab_contract_coverage_green": structural_lab_green,
        "signature_required_preserved": FAMILIES["signature"]["human_required"] == "SIGNATURE_REQUIRED",
        "profile_non_equivalent_server_reuse_blocked": FAMILIES["profile_update"]["existing_profile_update_server_equivalent"] is False,
        "real_db_replay_proven": False,
        "rollback_proven": False,
        "prod_parity_green": False,
        "prod_mutation_allowed": False,
        "grant_or_rls_change_allowed": False,
        "legacy_retirement_allowed": False,
        "status": "REMAINING_FOUR_FAMILIES_LAB_CONTRACT_COVERAGE_GREEN_DB_REPLAY_PENDING" if structural_lab_green else "REMAINING_FOUR_FAMILIES_LAB_CONTRACT_COVERAGE_RED",
    }
