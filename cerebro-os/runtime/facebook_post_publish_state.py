from dataclasses import dataclass


@dataclass(frozen=True)
class PostPublishInput:
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    receipt_confirmed: bool
    notion_return_ok: bool
    override_consumed: bool
    idempotency_committed: bool
    platform_state: str


def evaluate_post_publish(inp: PostPublishInput) -> dict:
    required = [inp.company_id, inp.engine_id, inp.environment, inp.version, inp.publication_id, inp.run_id]
    if not all(required):
        return _blocked(inp, "LOW_CONFIDENCE", "MISSING_REQUIRED_SCOPE")
    if inp.environment != "PROD":
        return _blocked(inp, "POLICY_CONFLICT", "POST_PUBLISH_OUTSIDE_PROD")

    published = inp.platform_state == "PUBLISHED" and inp.receipt_confirmed
    if not published:
        return {
            **_base(inp),
            "state": "PLATFORM_CONFIRMATION_PENDING",
            "notion_state": "PENDING",
            "idempotency_state": "PENDING_PLATFORM_CONFIRMATION",
            "override_state": "PENDING_OR_CONSUMED_BY_UPLOAD",
            "analytics_windows_ready": False,
            "retry_publish_allowed": False,
            "human_required": False,
            "human_reason": None,
        }

    if not inp.notion_return_ok:
        return {
            **_base(inp),
            "state": "NOTION_RETURN_PENDING",
            "notion_state": "PENDING_RETURN",
            "idempotency_state": "HOLD_UNTIL_NOTION_RETURN",
            "override_state": "CONSUMED" if inp.override_consumed else "MUST_CONSUME",
            "analytics_windows_ready": False,
            "retry_publish_allowed": False,
            "human_required": False,
            "human_reason": None,
        }

    if not inp.override_consumed:
        return {
            **_base(inp),
            "state": "OVERRIDE_CONSUMPTION_PENDING",
            "notion_state": "PUBLICADA",
            "idempotency_state": "HOLD_UNTIL_OVERRIDE_CONSUMED",
            "override_state": "MUST_CONSUME",
            "analytics_windows_ready": False,
            "retry_publish_allowed": False,
            "human_required": True,
            "human_reason": "POLICY_CONFLICT",
        }

    if not inp.idempotency_committed:
        return {
            **_base(inp),
            "state": "IDEMPOTENCY_COMMIT_PENDING",
            "notion_state": "PUBLICADA",
            "idempotency_state": "MUST_COMMIT",
            "override_state": "CONSUMED",
            "analytics_windows_ready": False,
            "retry_publish_allowed": False,
            "human_required": False,
            "human_reason": None,
        }

    return {
        **_base(inp),
        "state": "POST_PUBLISH_COMMITTED",
        "notion_state": "PUBLICADA",
        "idempotency_state": "COMMITTED",
        "override_state": "CONSUMED",
        "analytics_windows_ready": True,
        "retry_publish_allowed": False,
        "human_required": False,
        "human_reason": None,
    }


def _base(inp: PostPublishInput) -> dict:
    return {
        "company_id": inp.company_id,
        "engine_id": inp.engine_id,
        "environment": inp.environment,
        "version": inp.version,
        "publication_id": inp.publication_id,
        "run_id": inp.run_id,
        "external_action_allowed": False,
        "facebook_mutation_allowed": False,
        "notion_mutation_allowed": False,
    }


def _blocked(inp: PostPublishInput, reason: str, state: str) -> dict:
    return {
        **_base(inp),
        "state": state,
        "notion_state": "BLOCKED",
        "idempotency_state": "BLOCKED",
        "override_state": "BLOCKED",
        "analytics_windows_ready": False,
        "retry_publish_allowed": False,
        "human_required": True,
        "human_reason": reason,
    }
