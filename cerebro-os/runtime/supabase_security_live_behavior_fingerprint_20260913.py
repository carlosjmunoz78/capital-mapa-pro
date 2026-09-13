from __future__ import annotations

# Read-only behavioral fingerprint captured from live PROD function definitions on 2026-09-13.
# This is OLD-contract evidence only. It performs no RPC execution, DDL, grant/RLS change,
# App/CRM mutation, provider mutation or retirement.

FINGERPRINT = {
    "fenix_prod_chat_attachment_add_user": {"auth_uid": True, "insert": True, "update": False, "delete": False, "jsonb": True, "expected_version": False, "idempotency": False, "activity_log": False, "notification": False},
    "fenix_prod_chat_attachment_add_v2_user": {"auth_uid": True, "insert": True, "update": False, "delete": False, "jsonb": True, "expected_version": False, "idempotency": False, "activity_log": False, "notification": False},
    "fenix_prod_chat_conversation_create_user": {"auth_uid": True, "insert": True, "update": False, "delete": False, "jsonb": True, "expected_version": False, "idempotency": False, "activity_log": False, "notification": False},
    "fenix_prod_chat_group_create_user": {"auth_uid": True, "insert": True, "update": False, "delete": False, "jsonb": True, "expected_version": False, "idempotency": False, "activity_log": False, "notification": False},
    "fenix_prod_chat_send_user": {"auth_uid": True, "insert": False, "update": False, "delete": False, "jsonb": True, "expected_version": False, "idempotency": True, "activity_log": False, "notification": False},
    "fenix_prod_chat_send_v2_user": {"auth_uid": True, "insert": True, "update": True, "delete": False, "jsonb": True, "expected_version": False, "idempotency": True, "activity_log": False, "notification": False},
    "fenix_prod_contact_create": {"auth_uid": True, "insert": True, "update": False, "delete": False, "jsonb": True, "expected_version": False, "idempotency": False, "activity_log": False, "notification": False},
    "fenix_prod_contact_create_v2": {"auth_uid": True, "insert": False, "update": True, "delete": False, "jsonb": True, "expected_version": False, "idempotency": False, "activity_log": False, "notification": False},
    "fenix_prod_exp_create": {"auth_uid": True, "insert": True, "update": False, "delete": False, "jsonb": True, "expected_version": False, "idempotency": False, "activity_log": False, "notification": False},
    "fenix_prod_exp_update": {"auth_uid": True, "insert": False, "update": False, "delete": False, "jsonb": True, "expected_version": True, "idempotency": False, "activity_log": False, "notification": False},
    "fenix_prod_inmo_followup_update_v1": {"auth_uid": True, "insert": False, "update": True, "delete": False, "jsonb": True, "expected_version": True, "idempotency": False, "activity_log": False, "notification": False},
    "fenix_prod_notification_mark_user": {"auth_uid": True, "insert": True, "update": True, "delete": False, "jsonb": True, "expected_version": False, "idempotency": False, "activity_log": False, "notification": True},
    "fenix_prod_profile_socials_update_user": {"auth_uid": True, "insert": True, "update": True, "delete": False, "jsonb": True, "expected_version": False, "idempotency": False, "activity_log": True, "notification": False},
    "fenix_prod_profile_update_user": {"auth_uid": True, "insert": True, "update": True, "delete": False, "jsonb": True, "expected_version": False, "idempotency": False, "activity_log": True, "notification": False},
    "fenix_prod_sign_create": {"auth_uid": True, "insert": True, "update": False, "delete": False, "jsonb": True, "expected_version": False, "idempotency": False, "activity_log": False, "notification": False},
}


def assess_behavior_fingerprint() -> dict:
    rows = tuple(FINGERPRINT.values())
    return {
        "rpc_count": len(rows),
        "all_use_auth_uid": all(r["auth_uid"] for r in rows),
        "all_build_jsonb": all(r["jsonb"] for r in rows),
        "any_delete_observed": any(r["delete"] for r in rows),
        "expected_version_mutators": tuple(sorted(k for k, r in FINGERPRINT.items() if r["expected_version"])),
        "idempotent_mutators": tuple(sorted(k for k, r in FINGERPRINT.items() if r["idempotency"])),
        "activity_log_mutators": tuple(sorted(k for k, r in FINGERPRINT.items() if r["activity_log"])),
        "notification_mutators": tuple(sorted(k for k, r in FINGERPRINT.items() if r["notification"])),
        "old_behavior_baseline_ready": len(rows) == 15,
        "prod_mutation_performed": False,
        "security_green": False,
        "status": "LIVE_BEHAVIOR_FINGERPRINT_GREEN_PARITY_EXECUTION_PENDING",
    }
