from __future__ import annotations

PROCESS_FAMILIES: dict[str, tuple[str, ...]] = {
    "notifications": ("NOTIF-001",),
    "voice": ("VOICE-001",),
    "post_sale": ("POST-001",),
    "referrals": ("REF-001",),
    "reporting": ("REP-001",),
    "property_registry": ("REGP-001", "CAT-001", "NOT-001"),
    "payments_sla_blocks": ("PAY-001", "SLA-001", "BLK-001", "NBA-001"),
    "agenda_third_parties": ("AGD-001", "3RD-001"),
    "strategy_innovation": ("STR-001", "FRC-001", "CAPA-001", "OPP-001", "INN-001", "EXP-001"),
    "expansion_ventures": ("MKT-002", "EXPAND-001", "FRAN-001", "VENT-001"),
}


def all_engine_ids() -> tuple[str, ...]:
    return tuple(engine_id for sequence in PROCESS_FAMILIES.values() for engine_id in sequence)


def validate_against_canonical(canonical_ids: set[str]) -> None:
    ids = all_engine_ids()
    if len(ids) != len(set(ids)):
        raise ValueError("engine_id repeated across process families")
    unknown = sorted(set(ids) - canonical_ids)
    if unknown:
        raise ValueError(f"non-canonical engine ids: {unknown}")
