from __future__ import annotations


def decide(role: str, owner_ok: bool, zone_ok: bool, version_ok: bool, has_change: bool) -> tuple[int, str]:
    if role not in {"Direccion", "Visitador"}:
        return 403, "forbidden"
    if role == "Visitador" and not (owner_ok or zone_ok):
        return 403, "scope_required"
    if not version_ok:
        return 409, "version_conflict"
    if not has_change:
        return 400, "no_change"
    return 200, "ok"


def assess() -> dict:
    cases = (
        (decide("Direccion", False, False, True, True), (200, "ok")),
        (decide("Visitador", False, False, True, True), (403, "scope_required")),
        (decide("Visitador", True, False, False, True), (409, "version_conflict")),
        (decide("Visitador", False, True, True, False), (400, "no_change")),
    )
    green = all(a == b for a, b in cases)
    return {"fixture_count": len(cases), "lab_green": green, "real_db_replay": False, "rollback_proven": False}
