from __future__ import annotations

# LAB-only implementation plan for the 13 missing/non-equivalent server wrappers.
# This module deliberately contains no SQL DDL and performs no database mutation.
# It converts the already-captured contracts into an executable, fail-closed work plan.

from dataclasses import dataclass


@dataclass(frozen=True)
class WrapperLabPlan:
    legacy_rpc: str
    proposed_server: str
    family: str
    requires_actor_context: bool = True
    requires_old_vs_new_replay: bool = True
    requires_error_contract_replay: bool = True
    requires_write_set_assertion: bool = True
    requires_rollback_fixture: bool = True
    human_required: str | None = None


PLANS = (
    WrapperLabPlan("fenix_prod_chat_attachment_add_user", "fenix_prod_chat_attachment_add_server", "chat"),
    WrapperLabPlan("fenix_prod_chat_attachment_add_v2_user", "fenix_prod_chat_attachment_add_v2_server", "chat"),
    WrapperLabPlan("fenix_prod_chat_conversation_create_user", "fenix_prod_chat_conversation_create_server", "chat"),
    WrapperLabPlan("fenix_prod_chat_group_create_user", "fenix_prod_chat_group_create_server", "chat"),
    WrapperLabPlan("fenix_prod_chat_send_v2_user", "fenix_prod_chat_send_v2_server", "chat"),
    WrapperLabPlan("fenix_prod_contact_create", "fenix_prod_contact_create_server", "contacts"),
    WrapperLabPlan("fenix_prod_contact_create_v2", "fenix_prod_contact_create_v2_server", "contacts"),
    WrapperLabPlan("fenix_prod_exp_create", "fenix_prod_exp_create_server", "expedientes"),
    WrapperLabPlan("fenix_prod_inmo_followup_update_v1", "fenix_prod_inmo_followup_update_v1_server", "inmobiliarias"),
    WrapperLabPlan("fenix_prod_notification_mark_user", "fenix_prod_notification_mark_server", "notifications"),
    WrapperLabPlan("fenix_prod_profile_socials_update_user", "fenix_prod_profile_socials_update_server", "profiles"),
    WrapperLabPlan("fenix_prod_profile_update_user", "fenix_prod_profile_update_self_server", "profiles"),
    WrapperLabPlan("fenix_prod_sign_create", "fenix_prod_sign_create_server", "signatures", human_required="SIGNATURE_REQUIRED"),
)


def build_lab_queue() -> tuple[dict, ...]:
    queue = []
    for index, plan in enumerate(PLANS, start=1):
        queue.append({
            "order": index,
            "legacy_rpc": plan.legacy_rpc,
            "proposed_server": plan.proposed_server,
            "family": plan.family,
            "required_checks": (
                "auth_context_fixture",
                "authorization_scope_fixture",
                "input_validation_fixture",
                "idempotency_or_version_fixture",
                "write_set_fixture",
                "error_contract_fixture",
                "audit_event_fixture",
                "rollback_fixture",
                "old_vs_new_replay",
            ),
            "human_required": plan.human_required,
            "prod_apply_allowed": False,
            "prod_grant_change_allowed": False,
            "legacy_retirement_allowed": False,
        })
    return tuple(queue)


def assess() -> dict:
    queue = build_lab_queue()
    unique_legacy = {row["legacy_rpc"] for row in queue}
    unique_server = {row["proposed_server"] for row in queue}
    return {
        "plan_count": len(queue),
        "unique_legacy_count": len(unique_legacy),
        "unique_server_count": len(unique_server),
        "all_have_nine_required_checks": all(len(row["required_checks"]) == 9 for row in queue),
        "signature_required_preserved": any(row["human_required"] == "SIGNATURE_REQUIRED" for row in queue),
        "prod_apply_allowed": False,
        "prod_grant_change_allowed": False,
        "legacy_retirement_allowed": False,
        "lab_implementation_green": False,
        "next_gate": "IMPLEMENT_13_WRAPPERS_IN_ISOLATED_LAB_OR_NON_PROD_AND_REPLAY_OLD_VS_NEW",
        "status": "LAB_PLAN_READY_IMPLEMENTATION_PENDING",
    }
