from __future__ import annotations

SNAPSHOT = {
    "project_ref": "cluhljgonannaafpmblx",
    "observed_at": "2026-09-13",
    "source": "read_only_pg_catalog",
    "schema": "public",
    "automatic_prod_mutation_allowed": False,
    "grant_or_rls_change_allowed": False,
    "retirement_allowed": False,
    "human_gate_for_security_change": "HIGH_RISK",
    "mutators": {
        "fenix_prod_chat_attachment_add_user": ("eef4ad93bf9091a0bdf0f8375c5173c7", True),
        "fenix_prod_chat_attachment_add_v2_user": ("4eaf0e9bf82cbc2640ba9557dd2074d1", True),
        "fenix_prod_chat_conversation_create_user": ("8c74dd7e87a4987b71adf14c38f423a1", True),
        "fenix_prod_chat_group_create_user": ("8c14a9cd7d49657619030f4ee8407d16", True),
        "fenix_prod_chat_send_user": ("ae1126e85008aae62b09ac6c463a93ae", True),
        "fenix_prod_chat_send_v2_user": ("03dca281f601f690beb8aeadf69cc59f", True),
        "fenix_prod_contact_create": ("9e0ef08172510a001560664cf44717d0", True),
        "fenix_prod_contact_create_v2": ("d6dae699ebe027d8f7152c8da20a6fcb", True),
        "fenix_prod_exp_create": ("2cd9b00ee05aabac723b97f7612d856a", True),
        "fenix_prod_exp_update": ("0fb72de4e342af1ce0cf7a4d70517e53", True),
        "fenix_prod_inmo_followup_update_v1": ("216100e9aea59e166eb50a9c8c939862", True),
        "fenix_prod_notification_mark_user": ("f03ffdd40e8f1832d1fc2e6e1358b77c", True),
        "fenix_prod_profile_socials_update_user": ("bbd7bce7555abc2712831e939d35eed1", True),
        "fenix_prod_profile_update_user": ("7e7ecb0acf9b5b5d17277363a115b429", True),
        "fenix_prod_sign_create": ("6b1e6b112de9d359020272dce2e95fcd", True),
    },
    "acl_contract": {
        "owner": "postgres",
        "authenticated_execute": True,
        "service_role_execute": True,
        "security_definer": True,
    },
}


def assess_snapshot() -> dict:
    names = tuple(sorted(SNAPSHOT["mutators"]))
    return {
        "mutator_count": len(names),
        "all_security_definer": all(v[1] for v in SNAPSHOT["mutators"].values()),
        "all_have_definition_fingerprint": all(len(v[0]) == 32 for v in SNAPSHOT["mutators"].values()),
        "authenticated_execute_observed": SNAPSHOT["acl_contract"]["authenticated_execute"],
        "prod_security_change_allowed": SNAPSHOT["automatic_prod_mutation_allowed"],
        "status": "LIVE_ACL_BASELINE_CAPTURED_PARITY_AND_CALLER_CLOSURE_STILL_REQUIRED",
    }
