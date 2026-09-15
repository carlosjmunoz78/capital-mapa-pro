from __future__ import annotations

from .models import AdvisoryCase, CANONICAL_DOMAINS

SERVICE_ROUTE_HINTS = {
    "tax": ("FISCAL",),
    "accounting": ("CONTABLE",),
    "employment": ("LABORAL",),
    "corporate": ("MERCANTIL",),
    "finance": ("FINANCIERA",),
    "real_estate": ("INMOBILIARIA",),
    "mortgage": ("HIPOTECARIA",),
    "grant": ("SUBVENCIONES_AYUDAS",),
    "privacy": ("PROTECCION_DATOS_COMPLIANCE",),
    "strategy": ("EMPRESARIAL_ESTRATEGICA",),
    "wealth": ("PATRIMONIAL",),
    "legal": ("JURIDICA_GENERAL",),
}

CROSS_DOMAIN_TRIGGERS = {
    "company_buys_property": ("INMOBILIARIA", "FISCAL", "CONTABLE", "MERCANTIL", "FINANCIERA", "PATRIMONIAL"),
    "mortgaged_property_purchase": ("INMOBILIARIA", "HIPOTECARIA", "FISCAL", "FINANCIERA"),
    "hire_with_incentive": ("LABORAL", "SUBVENCIONES_AYUDAS", "FISCAL", "CONTABLE"),
    "inheritance": ("PATRIMONIAL", "FISCAL", "JURIDICA_GENERAL", "INMOBILIARIA"),
    "donation": ("PATRIMONIAL", "FISCAL", "JURIDICA_GENERAL"),
    "company_restructuring": ("MERCANTIL", "FISCAL", "CONTABLE", "FINANCIERA", "EMPRESARIAL_ESTRATEGICA"),
    "employee_personal_data": ("LABORAL", "PROTECCION_DATOS_COMPLIANCE"),
}


def route_case(case: AdvisoryCase) -> tuple[str, ...]:
    case.validate()
    selected: list[str] = []

    def add(domain: str) -> None:
        if domain not in CANONICAL_DOMAINS:
            raise ValueError(f"unknown domain: {domain}")
        if domain not in selected:
            selected.append(domain)

    for domain in case.requested_domains:
        add(domain)

    service = case.requested_service.strip().lower()
    for token, domains in SERVICE_ROUTE_HINTS.items():
        if token in service:
            for domain in domains:
                add(domain)

    triggers = case.facts.get("advisory_triggers", ())
    if isinstance(triggers, str):
        triggers = (triggers,)
    for trigger in triggers:
        for domain in CROSS_DOMAIN_TRIGGERS.get(str(trigger), ()):
            add(domain)

    if not selected:
        raise ValueError("cannot route advisory case without explicit domain or recognized trigger")
    return tuple(selected)
