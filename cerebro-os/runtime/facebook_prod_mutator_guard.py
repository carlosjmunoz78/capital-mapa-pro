from dataclasses import dataclass
from enum import Enum


class MutatorDecision(str, Enum):
    BLOCKED = "BLOCKED"
    READY_FOR_EXPLICIT_EXECUTION = "READY_FOR_EXPLICIT_EXECUTION"


@dataclass(frozen=True)
class FacebookProdMutator:
    scenario_id: int
    action: str
    make_module: str
    requires_t48: bool


FACEBOOK_PROD_MUTATORS = {
    9533715: FacebookProdMutator(9533715, "publish_text", "facebook-pages:CreatePost", True),
    9533724: FacebookProdMutator(9533724, "publish_link", "facebook-pages:CreatePost", True),
    9533532: FacebookProdMutator(9533532, "publish_image", "facebook-pages:UploadPhoto", True),
    9533564: FacebookProdMutator(9533564, "upload_reel", "facebook-pages:uploadAReel", False),
    9533967: FacebookProdMutator(9533967, "publish_carousel", "facebook-pages:CreatePostWithPhotos", False),
    9533972: FacebookProdMutator(9533972, "upload_video_long", "facebook-pages:UploadVideo", False),
}


@dataclass(frozen=True)
class FacebookProdExecutionEvidence:
    scenario_id: int
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    engine_enabled: bool
    override_authorized_once: bool
    override_record_matches: bool
    override_not_expired: bool
    idempotency_clear: bool
    explicit_publish_authorized: bool
    policy_green: bool
    target_runtime_live: bool
    rollback_proven: bool
    t48_approved: bool = False
    t48_version_locked: bool = False
    t48_hash_present: bool = False


@dataclass(frozen=True)
class FacebookProdExecutionDecision:
    decision: MutatorDecision
    blockers: tuple[str, ...]
    external_action_allowed: bool
    human_reason: str | None


def get_mutator(scenario_id: int) -> FacebookProdMutator:
    try:
        return FACEBOOK_PROD_MUTATORS[scenario_id]
    except KeyError as exc:
        raise ValueError("unknown Facebook PROD mutator") from exc


def assess_facebook_prod_execution(evidence: FacebookProdExecutionEvidence) -> FacebookProdExecutionDecision:
    mutator = get_mutator(evidence.scenario_id)
    blockers: list[str] = []

    for field_name in ("company_id", "engine_id", "version", "publication_id", "run_id"):
        if not str(getattr(evidence, field_name)).strip():
            blockers.append(f"MISSING_{field_name.upper()}")

    if evidence.environment != "PROD":
        blockers.append("ENVIRONMENT_NOT_PROD")
    if not evidence.engine_enabled:
        blockers.append("ENGINE_DISABLED")
    if not evidence.override_authorized_once:
        blockers.append("OVERRIDE_NOT_AUTHORIZED_ONCE")
    if not evidence.override_record_matches:
        blockers.append("OVERRIDE_RECORD_MISMATCH")
    if not evidence.override_not_expired:
        blockers.append("OVERRIDE_EXPIRED")
    if not evidence.idempotency_clear:
        blockers.append("DUPLICATE_OR_LOCK_PRESENT")
    if not evidence.explicit_publish_authorized:
        blockers.append("SIGNATURE_REQUIRED")
    if not evidence.policy_green:
        blockers.append("POLICY_CONFLICT")
    if not evidence.target_runtime_live:
        blockers.append("TARGET_RUNTIME_NOT_LIVE")
    if not evidence.rollback_proven:
        blockers.append("ROLLBACK_NOT_PROVEN")

    if mutator.requires_t48:
        if not evidence.t48_approved:
            blockers.append("T48_NOT_APPROVED")
        if not evidence.t48_version_locked:
            blockers.append("T48_VERSION_NOT_LOCKED")
        if not evidence.t48_hash_present:
            blockers.append("T48_HASH_MISSING")

    if blockers:
        human_reason = None
        if "SIGNATURE_REQUIRED" in blockers:
            human_reason = "SIGNATURE_REQUIRED"
        elif "POLICY_CONFLICT" in blockers:
            human_reason = "POLICY_CONFLICT"
        return FacebookProdExecutionDecision(
            decision=MutatorDecision.BLOCKED,
            blockers=tuple(blockers),
            external_action_allowed=False,
            human_reason=human_reason,
        )

    return FacebookProdExecutionDecision(
        decision=MutatorDecision.READY_FOR_EXPLICIT_EXECUTION,
        blockers=(),
        external_action_allowed=False,
        human_reason="SIGNATURE_REQUIRED",
    )


def mutator_ids() -> frozenset[int]:
    return frozenset(FACEBOOK_PROD_MUTATORS)
