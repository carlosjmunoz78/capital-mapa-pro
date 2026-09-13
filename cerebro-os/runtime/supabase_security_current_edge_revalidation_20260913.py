from __future__ import annotations

# Read-only revalidation against current live PROD Edge Function versions on 2026-09-13.
# No Edge Function was deployed or mutated. The target surface is the 15 authenticated
# SECURITY DEFINER mutators tracked by the security closure work.

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

CURRENT_EDGE = {
    "fenix-app-gateway": {
        "version": 16,
        "sha256": "8c57b7372791e5557e767cded1dcf2fdc7a940a9f53fccfa247dddd30ffffb1f",
        "target_mutator_reference_observed": False,
        "observed_server_wrappers": ("fenix_prod_sign_schedule_server", "fenix_prod_sign_confirm_server", "fenix_prod_sign_close_server"),
    },
    "fenix-profile-api": {
        "version": 1,
        "sha256": "ba3ad3bb90d80b08d9daf48b0d891966a1d47f70dc8da7f1fe6309803f08f300",
        "target_mutator_reference_observed": False,
        "observed_server_wrappers": ("fenix_prod_profile_get_server", "fenix_prod_profile_update_server"),
    },
    "fenix-b2b-actions": {
        "version": 9,
        "sha256": "51b7a83f9c6c1f16bc2b25240d836e0804b3480ccb995d52cec7c9cb48405116",
        "target_mutator_reference_observed": False,
        "observed_server_wrappers": (),
        "notes": "B2B writes use scoped Notion paths and session context; no tracked target mutator name observed.",
    },
}


def assess_current_edge_revalidation() -> dict:
    rows = tuple(CURRENT_EDGE.values())
    return {
        "surface_count": len(rows),
        "all_current_versions_pinned": all(int(r["version"]) > 0 and len(r["sha256"]) == 64 for r in rows),
        "tracked_target_mutator_count": len(TARGET_MUTATORS),
        "direct_target_reference_count": sum(bool(r["target_mutator_reference_observed"]) for r in rows),
        "all_three_clear_of_direct_target_names": all(not r["target_mutator_reference_observed"] for r in rows),
        "prod_mutation_performed": False,
        "retirement_allowed": False,
        "security_green": False,
        "status": "THREE_CURRENT_PROD_EDGE_SURFACES_REVALIDATED_OTHER_CALLERS_AND_PARITY_PENDING",
    }
