import pytest

from advisory.capabilities import CAPABILITY_REGISTRY, engine_dependencies, validate_registry
from advisory.models import AdvisoryCase, DomainOpinion, Territory
from advisory.runtime import execute_case


def make_case(*, service: str = "real_estate", triggers=(), requested_domains=()):
    return AdvisoryCase(
        company_id="company-test",
        case_id="case-test",
        environment="LAB",
        version="1.0.0",
        requested_service=service,
        territory=Territory(
            country="ES",
            autonomous_community="Andalucia",
            province="Cordoba",
            municipality="Cordoba",
        ),
        facts={"advisory_triggers": triggers, "summary": "test facts"},
        requested_domains=requested_domains,
    )


def green_handler(domain):
    def _handler(case, dependencies):
        assert case.environment == "LAB"
        assert dependencies == engine_dependencies(domain)
        return DomainOpinion(
            domain=domain,
            status="GREEN",
            summary=f"{domain} test opinion",
            source_refs=(f"source:{domain}",),
            next_actions=("continue",),
        )

    return _handler


def test_registry_covers_exactly_12_advisory_domains():
    validate_registry()
    assert len(CAPABILITY_REGISTRY) == 12
    assert CAPABILITY_REGISTRY["FISCAL"].engine_ids == ("TAX-001",)
    assert CAPABILITY_REGISTRY["SUBVENCIONES_AYUDAS"].dedicated_engine is False
    assert CAPABILITY_REGISTRY["PATRIMONIAL"].dedicated_engine is False


def test_cross_domain_case_runs_through_shared_runtime():
    case = make_case(
        service="real_estate purchase",
        triggers=("mortgaged_property_purchase",),
    )
    expected = ("INMOBILIARIA", "HIPOTECARIA", "FISCAL", "FINANCIERA")
    handlers = {domain: green_handler(domain) for domain in expected}

    decision = execute_case(case, handlers, audit_refs=("audit:test",))

    assert decision.domains == expected
    assert decision.overall_status == "GREEN"
    assert decision.audit_refs == ("audit:test",)
    assert tuple(op.domain for op in decision.opinions) == expected


def test_runtime_fails_closed_when_a_routed_handler_is_missing():
    case = make_case(
        service="real_estate purchase",
        triggers=("mortgaged_property_purchase",),
    )
    handlers = {
        "INMOBILIARIA": green_handler("INMOBILIARIA"),
        "FISCAL": green_handler("FISCAL"),
    }

    with pytest.raises(RuntimeError, match="missing advisory handlers"):
        execute_case(case, handlers)


def test_human_exception_propagates_without_becoming_green():
    case = make_case(service="legal", requested_domains=("JURIDICA_GENERAL",))

    def legal_handler(case, dependencies):
        return DomainOpinion(
            domain="JURIDICA_GENERAL",
            status="HUMAN_REQUIRED",
            summary="Signature by authorized human is required",
            source_refs=("source:legal",),
            human_exception="SIGNATURE_REQUIRED",
        )

    decision = execute_case(case, {"JURIDICA_GENERAL": legal_handler})
    assert decision.overall_status == "HUMAN_REQUIRED"
    assert decision.opinions[0].human_exception == "SIGNATURE_REQUIRED"


def test_handler_cannot_return_another_domain():
    case = make_case(service="tax")

    def wrong_handler(case, dependencies):
        return DomainOpinion(
            domain="CONTABLE",
            status="GREEN",
            summary="wrong domain",
            source_refs=("source:wrong",),
        )

    with pytest.raises(ValueError, match="handler domain mismatch"):
        execute_case(case, {"FISCAL": wrong_handler})
