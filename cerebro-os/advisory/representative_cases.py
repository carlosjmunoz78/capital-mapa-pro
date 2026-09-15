from __future__ import annotations

from dataclasses import dataclass

from .capabilities import engine_dependencies
from .handlers import build_lab_handlers
from .models import AdvisoryCase, CANONICAL_DOMAINS, EvidenceRef, Territory
from .runtime import execute_case


@dataclass(frozen=True)
class RepresentativeCaseResult:
    case_id: str
    routed_domains: tuple[str, ...]
    overall_status: str
    audit_refs: tuple[str, ...]


REPRESENTATIVE_CASE_SPECS = (
    {
        "case_id": "LAB-REP-PROPERTY-001",
        "requested_service": "real_estate mortgage finance tax accounting corporate wealth legal",
        "domains": (
            "INMOBILIARIA",
            "HIPOTECARIA",
            "FISCAL",
            "FINANCIERA",
            "CONTABLE",
            "MERCANTIL",
            "PATRIMONIAL",
            "JURIDICA_GENERAL",
        ),
        "scenario": "company_mortgaged_property_acquisition",
    },
    {
        "case_id": "LAB-REP-HR-GRANT-001",
        "requested_service": "employment grant privacy tax accounting",
        "domains": (
            "LABORAL",
            "SUBVENCIONES_AYUDAS",
            "PROTECCION_DATOS_COMPLIANCE",
            "FISCAL",
            "CONTABLE",
        ),
        "scenario": "hire_with_incentive_and_employee_data",
    },
    {
        "case_id": "LAB-REP-STRATEGY-001",
        "requested_service": "strategy finance grant corporate",
        "domains": (
            "EMPRESARIAL_ESTRATEGICA",
            "FINANCIERA",
            "SUBVENCIONES_AYUDAS",
            "MERCANTIL",
        ),
        "scenario": "growth_investment_with_financing_and_grants",
    },
)


def _domain_source_ref(domain: str) -> str:
    slug = domain.lower()
    return f"repo://cerebro-os/advisory/knowledge_validation_{slug}_20260915.json#validated-claims"


def build_representative_case(spec: dict[str, object]) -> AdvisoryCase:
    domains = tuple(str(x) for x in spec["domains"])
    engine_ids = tuple(dict.fromkeys(
        engine_id
        for domain in domains
        for engine_id in engine_dependencies(domain)
    ))
    case_id = str(spec["case_id"])
    engine_evidence = {
        engine_id: (f"lab-evidence://{case_id}/{engine_id}/deterministic-check",)
        for engine_id in engine_ids
    }
    domain_source_refs = {
        domain: (_domain_source_ref(domain),)
        for domain in domains
    }
    return AdvisoryCase(
        company_id="LAB-COMPANY-REPRESENTATIVE",
        case_id=case_id,
        environment="LAB",
        version="1.0.0",
        requested_service=str(spec["requested_service"]),
        territory=Territory(
            country="ES",
            autonomous_community="Andalucia",
            province="Cordoba",
            municipality="Cordoba",
        ),
        facts={
            "scenario": str(spec["scenario"]),
            "representative_fixture": True,
            "not_customer_data": True,
            "engine_evidence": engine_evidence,
            "domain_source_refs": domain_source_refs,
        },
        evidence=(
            EvidenceRef(
                source_id="LAB-REPRESENTATIVE-CASE-SUITE",
                source_version="1.0.0",
                locator=f"case:{case_id}",
                verified_at="2026-09-15",
            ),
        ),
        requested_domains=domains,
    )


def run_representative_case_suite() -> tuple[RepresentativeCaseResult, ...]:
    results: list[RepresentativeCaseResult] = []
    for spec in REPRESENTATIVE_CASE_SPECS:
        case = build_representative_case(spec)
        handlers = build_lab_handlers(case.requested_domains)
        audit_refs = (
            f"lab-audit://{case.case_id}/route",
            f"lab-audit://{case.case_id}/evidence",
            f"lab-audit://{case.case_id}/coordination",
        )
        decision = execute_case(case, handlers, audit_refs=audit_refs)
        decision.validate()
        results.append(
            RepresentativeCaseResult(
                case_id=case.case_id,
                routed_domains=decision.domains,
                overall_status=decision.overall_status,
                audit_refs=decision.audit_refs,
            )
        )
    return tuple(results)


def representative_suite_coverage() -> tuple[str, ...]:
    covered = {
        domain
        for spec in REPRESENTATIVE_CASE_SPECS
        for domain in tuple(str(x) for x in spec["domains"])
    }
    return tuple(domain for domain in CANONICAL_DOMAINS if domain in covered)


def lab_capability_green() -> bool:
    results = run_representative_case_suite()
    return (
        representative_suite_coverage() == CANONICAL_DOMAINS
        and all(result.overall_status == "GREEN" for result in results)
        and all(result.audit_refs for result in results)
    )
