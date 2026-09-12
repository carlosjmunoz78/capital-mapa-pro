from __future__ import annotations

from dataclasses import dataclass

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class CarouselPhoto:
    asset_id: str
    url: str
    position: int
    qa_approved: bool

    def validate(self) -> None:
        if not self.asset_id.strip() or not self.url.strip():
            raise ValueError("carousel photo missing identity")
        if self.position < 1:
            raise ValueError("carousel photo position must be positive")


@dataclass(frozen=True)
class CarouselPreflightRequest:
    company_id: str
    engine_id: str
    environment: str
    version: str
    publication_id: str
    production_order_id: str
    programming_id: str
    run_id: str
    copy_reviewed: bool
    qa_approved: bool
    real_publish_authorized: bool
    photos: tuple[CarouselPhoto, ...]

    def validate(self) -> None:
        required = (
            self.company_id,
            self.engine_id,
            self.environment,
            self.version,
            self.publication_id,
            self.production_order_id,
            self.programming_id,
            self.run_id,
        )
        if any(not str(value).strip() for value in required):
            raise ValueError("carousel preflight missing required fields")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        for photo in self.photos:
            photo.validate()


def evaluate_carousel_preflight(req: CarouselPreflightRequest) -> dict:
    """Reproduces Make 9533987 gate without calling Facebook."""
    req.validate()
    count = len(req.photos)
    contract_valid = (
        1 < count < 31
        and req.copy_reviewed
        and req.qa_approved
        and not req.real_publish_authorized
    )
    photos_qa_ok = all(photo.qa_approved for photo in req.photos)
    positions = [photo.position for photo in req.photos]
    unique_positions = len(set(positions)) == len(positions)

    if contract_valid and photos_qa_ok and unique_positions:
        status = "DIRECT_CONTRACT_VALIDATED"
        requires_human = False
    else:
        status = "BLOCKED_PREFLIGHT"
        requires_human = True

    return {
        "company_id": req.company_id,
        "engine_id": req.engine_id,
        "environment": req.environment,
        "version": req.version,
        "publication_id": req.publication_id,
        "production_order_id": req.production_order_id,
        "programming_id": req.programming_id,
        "run_id": req.run_id,
        "status": status,
        "network": "Facebook",
        "operation_type": "carousel_preflight",
        "platform_state": "FACEBOOK_NOT_CALLED",
        "photo_count": count,
        "requires_human": requires_human,
        "external_action_allowed": False,
        "contract_valid": contract_valid,
        "photos_qa_ok": photos_qa_ok,
        "positions_unique": unique_positions,
    }
