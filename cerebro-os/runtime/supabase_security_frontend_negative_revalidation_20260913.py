from __future__ import annotations

APP_REPO = "carlosjmunoz78/fenix-capital-inmo-map"
APP_MAIN_HEAD = "95106d8e792257f809033486b7025d81665ea83b"

MUTATORS = (
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

SEARCH_RESULTS = {name: 0 for name in MUTATORS}


def assess() -> dict:
    return {
        "app_repo": APP_REPO,
        "app_main_head": APP_MAIN_HEAD,
        "mutator_count": len(MUTATORS),
        "zero_indexed_match_count": sum(1 for v in SEARCH_RESULTS.values() if v == 0),
        "all_zero_indexed_matches": all(v == 0 for v in SEARCH_RESULTS.values()),
        "global_absence_proven": False,
        "safe_retirement_proven": False,
        "prod_privilege_change_allowed": False,
        "status": "NINE_MUTATORS_REVALIDATED_ZERO_INDEXED_MATCHES_FAIL_CLOSED",
    }
