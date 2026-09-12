from dataclasses import dataclass


@dataclass(frozen=True)
class ImageReceiptNormalizeRequest:
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    run_id: str
    canonical_receipt_exists: bool
    source_receipt_exists: bool
    external_id: str
    page_id: str


def normalize_image_receipt(req: ImageReceiptNormalizeRequest) -> dict:
    if not all((req.company_id, req.engine_id, req.environment, req.version, req.publication_id, req.run_id)):
        raise ValueError("missing required receipt-normalizer scope")
    if req.canonical_receipt_exists:
        return {
            "status": "CANONICAL_RECEIPT_ALREADY_EXISTS",
            "external_action_allowed": False,
            "facebook_called": False,
            "notion_mutation_allowed": False,
            "requires_human": False,
        }
    if not req.source_receipt_exists or not req.external_id or not req.page_id:
        return {
            "status": "BLOCKED_SOURCE_RECEIPT_MISSING",
            "external_action_allowed": False,
            "facebook_called": False,
            "notion_mutation_allowed": False,
            "requires_human": True,
            "human_reason": "LOW_CONFIDENCE",
        }
    return {
        "status": "CANONICAL_RECEIPT_CREATED",
        "canonical_status": "FACEBOOK_ACCEPTED",
        "platform_state": "PUBLISHED",
        "external_id": req.external_id,
        "page_id": req.page_id,
        "result_hash": f"POST_ID_{req.external_id}|FORMAT_IMAGE|SOURCE_RECEIPT_OK",
        "external_action_allowed": False,
        "facebook_called": False,
        "notion_mutation_allowed": False,
        "analytics_windows_enabled": True,
        "requires_human": False,
    }
