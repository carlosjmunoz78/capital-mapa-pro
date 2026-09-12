from __future__ import annotations

from hashlib import sha256
from typing import Any

from own_social_signal import OwnSocialSignal

SCENARIO_PLATFORM = {
    9597297: "FACEBOOK",
    9595955: "INSTAGRAM",
    9597307: "LINKEDIN",
    9597372: "LINKEDIN",
    9597332: "YOUTUBE",
}

SCENARIO_SIGNAL_TYPE = {
    9597297: "COMMENT",
    9595955: "COMMENT",
    9597307: "COMMENT",
    9597372: "ENGAGEMENT",
    9597332: "COMMENT",
}

SCENARIO_ENGINE_ID = {
    9597297: "OPP-001",
    9595955: "OPP-001",
    9597307: "OPP-001",
    9597372: "MKT-002",
    9597332: "OPP-001",
}

REQUIRED_PAYLOAD_FIELDS = {
    "observed_at",
    "external_id",
    "source_account_id",
    "source_content_id",
    "value",
    "evidence_ref",
}


def _require_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if value is None or not str(value).strip():
        raise ValueError(f"missing required RADAR field: {key}")
    return str(value).strip()


def _content_hash(*parts: str) -> str:
    canonical = "\x1f".join(parts)
    return sha256(canonical.encode("utf-8")).hexdigest()


def adapt_make_radar_signal(
    *,
    scenario_id: int,
    company_id: str,
    environment: str,
    version: str,
    payload: dict[str, Any],
    cost_units: float = 0.0,
    confidence: float = 1.0,
) -> OwnSocialSignal:
    if scenario_id not in SCENARIO_PLATFORM:
        raise ValueError("unsupported Make RADAR scenario")
    if not isinstance(payload, dict):
        raise ValueError("RADAR payload must be a mapping")
    if not str(company_id).strip() or not str(version).strip():
        raise ValueError("company_id and version are required")

    values = {key: _require_text(payload, key) for key in REQUIRED_PAYLOAD_FIELDS}
    content_hash = _content_hash(
        str(scenario_id),
        values["external_id"],
        values["source_account_id"],
        values["source_content_id"],
        values["value"],
    )

    signal = OwnSocialSignal(
        company_id=str(company_id).strip(),
        engine_id=SCENARIO_ENGINE_ID[scenario_id],
        environment=str(environment).strip(),
        version=str(version).strip(),
        platform=SCENARIO_PLATFORM[scenario_id],
        signal_type=SCENARIO_SIGNAL_TYPE[scenario_id],
        observed_at=values["observed_at"],
        external_id=values["external_id"],
        source_account_id=values["source_account_id"],
        source_content_id=values["source_content_id"],
        value=values["value"],
        content_hash=content_hash,
        evidence_ref=values["evidence_ref"],
        confidence=float(confidence),
        cost_units=float(cost_units),
    )
    signal.validate()
    return signal
