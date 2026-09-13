from __future__ import annotations

# LAB-only semantic replay for expediente creation. No SQL/provider mutation.

TARGET = "fenix_prod_exp_create"
PROPOSED_SERVER = "fenix_prod_exp_create_server"


def create_decision(*, actor_present: bool, role: str, client_name: str, owner_valid: bool = True, inmobiliaria_valid: bool = True, recent_duplicate: bool = False) -> tuple[int, str]:
    if not actor_present:
        return 403, "identity_not_linked"
    if role not in {"Direccion", "Financiero"}:
        return 403, "forbidden"
    if not (client_name or "").strip():
        return 400, "client_name_required"
    if not owner_valid:
        return 400, "invalid_owner"
    if not inmobiliaria_valid:
        return 400, "invalid_inmobiliaria"
    if recent_duplicate:
        return 200, "duplicate_prevented"
    return 201, "expediente_created"


FIXTURES = (
    (create_decision(actor_present=True, role="Direccion", client_name="Ana"), (201, "expediente_created")),
    (create_decision(actor_present=True, role="Visitador", client_name="Ana"), (403, "forbidden")),
    (create_decision(actor_present=True, role="Financiero", client_name=""), (400, "client_name_required")),
    (create_decision(actor_present=True, role="Direccion", client_name="Ana", owner_valid=False), (400, "invalid_owner")),
    (create_decision(actor_present=True, role="Direccion", client_name="Ana", inmobiliaria_valid=False), (400, "invalid_inmobiliaria")),
    (create_decision(actor_present=True, role="Financiero", client_name="Ana", recent_duplicate=True), (200, "duplicate_prevented")),
)


def replay() -> dict:
    green = all(actual == expected for actual, expected in FIXTURES)
    return {
        "target": TARGET,
        "proposed_server": PROPOSED_SERVER,
        "fixture_count": len(FIXTURES),
        "lab_semantic_replay_green": green,
        "write_set_replay_pending": True,
        "rollback_path_proven": False,
        "prod_parity_green": False,
        "prod_mutation_allowed": False,
        "grant_change_allowed": False,
        "legacy_retirement_allowed": False,
        "status": "EXPEDIENTES_CREATE_LAB_SEMANTIC_REPLAY_GREEN_DB_WRITESET_REPLAY_PENDING" if green else "EXPEDIENTES_CREATE_LAB_SEMANTIC_REPLAY_RED",
    }
