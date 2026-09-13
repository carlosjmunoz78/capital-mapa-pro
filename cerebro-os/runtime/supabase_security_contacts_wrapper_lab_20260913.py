from __future__ import annotations

# LAB-only semantic replay for CONTACTS wrappers. No SQL or provider mutation.

CONTACT_TARGETS = {
    "fenix_prod_contact_create": "fenix_prod_contact_create_server",
    "fenix_prod_contact_create_v2": "fenix_prod_contact_create_v2_server",
}

CLIENT_TYPES = {
    "cliente_hipoteca_particular", "cliente_hipoteca_inmobiliaria", "cliente_deuda_refinanciacion",
    "cliente_herencia", "cliente_obra_nueva",
}


def create_decision(*, actor_present: bool, role: str, contact_type: str, name: str, entity_id: str | None = None, duplicate: bool = False, entity_visible: bool = True) -> tuple[int, str]:
    if not actor_present:
        return 403, "identity_not_linked"
    if not (name or "").strip():
        return 400, "name_required"
    if contact_type in CLIENT_TYPES:
        if role not in {"Direccion", "Financiero"}:
            return 403, "forbidden"
        if duplicate:
            return 409, "duplicate_contact"
        return 201, "Clientes"
    if contact_type == "trabajador_inmobiliaria":
        if role not in {"Direccion", "Visitador"}:
            return 403, "forbidden"
        if not (entity_id or "").strip():
            return 400, "entity_required"
        if not entity_visible:
            return 403, "entity_not_found_or_forbidden"
        if duplicate:
            return 409, "duplicate_contact"
        return 201, "Contactos inmobiliaria"
    if contact_type == "contacto_bancario":
        if role != "Direccion":
            return 403, "forbidden"
        if entity_id and not entity_visible:
            return 400, "entity_not_found"
        if duplicate:
            return 409, "duplicate_contact"
        return 201, "Contactos bancarios"
    return 422, "contact_type_not_supported_in_prod"


def normalize_v2(primary_email: str | None, primary_phone: str | None, emails: tuple[str, ...], phones: tuple[str, ...]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    out_emails = list(emails)
    if primary_email and primary_email.strip() and primary_email.strip().lower() not in {x.strip().lower() for x in out_emails}:
        out_emails.insert(0, primary_email.strip())
    digits = lambda s: "".join(ch for ch in s if ch.isdigit())
    out_phones = list(phones)
    if primary_phone and primary_phone.strip() and digits(primary_phone) not in {digits(x) for x in out_phones}:
        out_phones.insert(0, primary_phone.strip())
    return tuple(out_emails), tuple(out_phones)


FIXTURES = (
    (create_decision(actor_present=True, role="Financiero", contact_type="cliente_hipoteca_particular", name="Ana"), (201, "Clientes")),
    (create_decision(actor_present=True, role="Visitador", contact_type="cliente_hipoteca_particular", name="Ana"), (403, "forbidden")),
    (create_decision(actor_present=True, role="Visitador", contact_type="trabajador_inmobiliaria", name="Luis", entity_id="i1", entity_visible=True), (201, "Contactos inmobiliaria")),
    (create_decision(actor_present=True, role="Direccion", contact_type="contacto_bancario", name="Eva", duplicate=True), (409, "duplicate_contact")),
    (create_decision(actor_present=True, role="Direccion", contact_type="otro", name="X"), (422, "contact_type_not_supported_in_prod")),
)


def replay() -> dict:
    green = all(actual == expected for actual, expected in FIXTURES)
    emails, phones = normalize_v2("A@B.com", "+34 600 100 200", ("a@b.com",), ("600100200",))
    normalization_green = emails == ("a@b.com",) and phones == ("600100200",)
    return {
        "target_count": len(CONTACT_TARGETS),
        "fixture_count": len(FIXTURES),
        "v1_semantic_replay_green": green,
        "v2_normalization_replay_green": normalization_green,
        "lab_contacts_semantic_replay_green": green and normalization_green,
        "rollback_path_proven": False,
        "prod_parity_green": False,
        "prod_mutation_allowed": False,
        "grant_change_allowed": False,
        "legacy_retirement_allowed": False,
        "status": "CONTACTS_LAB_SEMANTIC_REPLAY_GREEN_REAL_DB_REPLAY_PENDING" if green and normalization_green else "CONTACTS_LAB_SEMANTIC_REPLAY_RED",
    }
