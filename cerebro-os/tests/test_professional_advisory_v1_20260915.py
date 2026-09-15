import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from advisory.models import AdvisoryCase, Territory, CANONICAL_DOMAINS, CANONICAL_HUMAN_EXCEPTIONS
from advisory.router import route_case


def test_exact_12_advisory_domains_and_fiscal_not_root():
    assert len(CANONICAL_DOMAINS) == 12
    assert len(set(CANONICAL_DOMAINS)) == 12
    catalog = json.loads((ROOT / "registry" / "advisory_source_catalog_20260915.json").read_text())
    assert catalog["invariants"]["domain_count"] == 12
    assert catalog["invariants"]["fiscal_is_root"] is False
    assert catalog["invariants"]["professional_advisory_is_orchestrator"] is True


def test_laboral_final_supersedes_v01():
    catalog = json.loads((ROOT / "registry" / "advisory_source_catalog_20260915.json").read_text())
    labor = next(x for x in catalog["domains"] if x["domain"] == "LABORAL")
    assert labor["canonical_source"].endswith("v1.0_FINAL.md")
    assert any(x.endswith("v0.1.md") for x in labor["supersedes"])


def test_general_legal_v3_is_explicit_canonical_source():
    catalog = json.loads((ROOT / "registry" / "advisory_source_catalog_20260915.json").read_text())
    legal = next(x for x in catalog["domains"] if x["domain"] == "JURIDICA_GENERAL")
    assert legal["canonical_source"] == "REPOSITORIO_PRO_ASESORIA_JURIDICA_ESPANA_FINAL_v3_2026-09-15.md"
    assert legal["source_status"] == "AVAILABLE"
    assert legal["engine_refs"] == ["LEG-001"]


def test_router_supports_multidomain_company_property_purchase():
    case = AdvisoryCase(
        company_id="FENIX",
        case_id="CASE-1",
        environment="LAB",
        version="1",
        requested_service="real_estate acquisition",
        territory=Territory(country="ES", autonomous_community="Andalucía", province="Córdoba", municipality="Córdoba"),
        facts={"advisory_triggers": ["company_buys_property"]},
    )
    routed = route_case(case)
    assert {"INMOBILIARIA", "FISCAL", "CONTABLE", "MERCANTIL", "FINANCIERA", "PATRIMONIAL"}.issubset(routed)


def test_router_rejects_unknown_explicit_domain():
    case = AdvisoryCase(
        company_id="FENIX",
        case_id="CASE-2",
        environment="LAB",
        version="1",
        requested_service="custom",
        territory=Territory(country="ES"),
        facts={"x": 1},
        requested_domains=("FAKE-001",),
    )
    try:
        route_case(case)
    except ValueError:
        pass
    else:
        raise AssertionError("unknown domain must fail closed")


def test_human_exception_taxonomy_is_exact():
    assert CANONICAL_HUMAN_EXCEPTIONS == {
        "LEGAL_REQUIRED", "SIGNATURE_REQUIRED", "LOW_CONFIDENCE", "HIGH_RISK",
        "POLICY_CONFLICT", "SECURITY_INCIDENT", "MONEY_LIMIT", "CUSTOMER_HUMAN_REQUEST"
    }
