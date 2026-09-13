from __future__ import annotations

# LAB-only semantic replay for the five CHAT wrappers missing in PROD.
# This module performs no SQL, no provider call, no App/CRM mutation, and no grant/RLS change.

CHAT_TARGETS = {
    "fenix_prod_chat_attachment_add_user": "fenix_prod_chat_attachment_add_server",
    "fenix_prod_chat_attachment_add_v2_user": "fenix_prod_chat_attachment_add_v2_server",
    "fenix_prod_chat_conversation_create_user": "fenix_prod_chat_conversation_create_server",
    "fenix_prod_chat_group_create_user": "fenix_prod_chat_group_create_server",
    "fenix_prod_chat_send_v2_user": "fenix_prod_chat_send_v2_server",
}

ALLOWED_MIME = {
    "image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf", "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "audio/mpeg", "audio/mp4", "audio/wav", "audio/webm", "audio/ogg", "audio/opus", "audio/aac", "audio/flac",
}


def attachment_decision(*, actor_present: bool, message_owned: bool, member: bool, storage_owned: bool, size_bytes: int, mime_type: str, v2: bool) -> tuple[int, str]:
    if not actor_present:
        return 403, "identity_not_linked"
    if not message_owned or (v2 and not member):
        return 403, "message_not_owned"
    if not storage_owned:
        return 400, "invalid_storage_path"
    if size_bytes <= 0 or size_bytes > 20 * 1024 * 1024:
        return 400, "invalid_size"
    if mime_type not in ALLOWED_MIME:
        return 400, "invalid_mime"
    return 201, "attachment_created"


def conversation_decision(*, actor_present: bool, valid_members: bool, member_count: int, group: bool) -> tuple[int, str]:
    if not actor_present:
        return 403, "identity_not_linked"
    if member_count < 2:
        return 400, "select_at_least_one_person"
    if not valid_members:
        return 400, "invalid_member"
    return 201, "group_created" if group else "conversation_created_or_reused"


def send_v2_decision(*, actor_present: bool, member: bool, body: str) -> tuple[int, str]:
    if not actor_present or not member:
        return 403, "forbidden"
    clean = (body or "").strip()
    if not clean or len(clean) > 5000:
        return 400, "invalid_body"
    return 201, "message_created_or_idempotent"


REPLAY_FIXTURES = (
    ("attachment_v1_ok", attachment_decision(actor_present=True, message_owned=True, member=True, storage_owned=True, size_bytes=1024, mime_type="application/pdf", v2=False), (201, "attachment_created")),
    ("attachment_v2_member_required", attachment_decision(actor_present=True, message_owned=True, member=False, storage_owned=True, size_bytes=1024, mime_type="application/pdf", v2=True), (403, "message_not_owned")),
    ("attachment_size_limit", attachment_decision(actor_present=True, message_owned=True, member=True, storage_owned=True, size_bytes=20 * 1024 * 1024 + 1, mime_type="application/pdf", v2=False), (400, "invalid_size")),
    ("conversation_members", conversation_decision(actor_present=True, valid_members=True, member_count=2, group=False), (201, "conversation_created_or_reused")),
    ("group_invalid_member", conversation_decision(actor_present=True, valid_members=False, member_count=3, group=True), (400, "invalid_member")),
    ("send_v2_body_limit", send_v2_decision(actor_present=True, member=True, body="x" * 5001), (400, "invalid_body")),
    ("send_v2_ok", send_v2_decision(actor_present=True, member=True, body=" hola "), (201, "message_created_or_idempotent")),
)


def replay() -> dict:
    results = [(name, actual, expected, actual == expected) for name, actual, expected in REPLAY_FIXTURES]
    green = all(row[3] for row in results)
    return {
        "target_count": len(CHAT_TARGETS),
        "fixture_count": len(results),
        "all_fixture_semantics_match": green,
        "prod_mutation_allowed": False,
        "grant_change_allowed": False,
        "legacy_retirement_allowed": False,
        "lab_chat_semantic_replay_green": green,
        "rollback_path_proven": False,
        "prod_parity_green": False,
        "status": "CHAT_LAB_SEMANTIC_REPLAY_GREEN_ROLLBACK_AND_REAL_DB_REPLAY_PENDING" if green else "CHAT_LAB_SEMANTIC_REPLAY_RED",
    }
