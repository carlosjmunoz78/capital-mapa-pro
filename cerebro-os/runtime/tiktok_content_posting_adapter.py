from dataclasses import dataclass


CREATOR_INFO_PATH = "/v2/post/publish/creator_info/query/"
DIRECT_POST_VIDEO_INIT_PATH = "/v2/post/publish/video/init/"
POST_STATUS_PATH = "/v2/post/publish/status/fetch/"
REQUIRED_SCOPE = "video.publish"


@dataclass(frozen=True)
class TikTokDirectPostPlan:
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    title: str
    privacy_level: str
    video_size: int
    chunk_size: int
    total_chunk_count: int
    access_token_ref_present: bool
    creator_consent: bool
    scope_approved: bool
    user_authorized_scope: bool


def build_direct_post_plan(req: TikTokDirectPostPlan) -> dict:
    blockers = []
    for field in ("company_id", "engine_id", "environment", "version", "publication_id", "run_id", "title", "privacy_level"):
        if not str(getattr(req, field)).strip():
            blockers.append(f"MISSING_{field.upper()}")
    if req.environment != "PROD": blockers.append("ENVIRONMENT_NOT_PROD")
    if req.video_size <= 0: blockers.append("INVALID_VIDEO_SIZE")
    if req.chunk_size <= 0: blockers.append("INVALID_CHUNK_SIZE")
    if req.total_chunk_count <= 0: blockers.append("INVALID_CHUNK_COUNT")
    if not req.access_token_ref_present: blockers.append("MISSING_CREDENTIAL")
    if not req.creator_consent: blockers.append("CUSTOMER_HUMAN_REQUEST")
    if not req.scope_approved: blockers.append("PERMISSION_REQUIRED")
    if not req.user_authorized_scope: blockers.append("PERMISSION_REQUIRED")

    return {
        "status": "READY_FOR_EXPLICIT_EXECUTION" if not blockers else "BLOCKED",
        "blockers": tuple(dict.fromkeys(blockers)),
        "required_scope": REQUIRED_SCOPE,
        "creator_info_path": CREATOR_INFO_PATH,
        "direct_post_video_init_path": DIRECT_POST_VIDEO_INIT_PATH,
        "post_status_path": POST_STATUS_PATH,
        "source": "FILE_UPLOAD",
        "external_action_allowed": False,
        "secret_value_required_in_runtime_input": False,
        "requires_human": bool(blockers) or True,
        "human_reason": "SIGNATURE_REQUIRED" if not blockers else ("PERMISSION_REQUIRED" if "PERMISSION_REQUIRED" in blockers else blockers[0]),
    }
