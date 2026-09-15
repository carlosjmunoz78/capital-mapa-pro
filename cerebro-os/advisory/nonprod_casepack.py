from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

from .representative_cases import REPRESENTATIVE_CASE_SPECS


@dataclass(frozen=True)
class CasePackEntry:
    case_id: str
    scenario: str
    requested_service: str
    domains: tuple[str, ...]
    expected_status: str = "GREEN"


CASE_PACK_VERSION = "1.0.0"
CASE_PACK_ENTRIES = tuple(
    CasePackEntry(
        case_id=str(spec["case_id"]),
        scenario=str(spec["scenario"]),
        requested_service=str(spec["requested_service"]),
        domains=tuple(str(x) for x in spec["domains"]),
    )
    for spec in REPRESENTATIVE_CASE_SPECS
)


def canonical_case_pack_payload() -> bytes:
    payload = {
        "version": CASE_PACK_VERSION,
        "environment": "LAB",
        "not_customer_data": True,
        "entries": [asdict(entry) for entry in CASE_PACK_ENTRIES],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def case_pack_sha256() -> str:
    return hashlib.sha256(canonical_case_pack_payload()).hexdigest()


def verify_case_pack(expected_sha256: str) -> bool:
    return case_pack_sha256() == expected_sha256
