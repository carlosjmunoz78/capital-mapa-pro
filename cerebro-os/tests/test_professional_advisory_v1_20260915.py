import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

models = _load("advisory_models", ROOT / "advisory" / "models.py")

# Router uses a relative import; load it as a package module through sys.path.
import sys
sys.path.insert(0, str(ROOT))
from advisory.router import route_case
from advisory.models import AdvisoryCase, Territory, CANONICAL_DOMAINS


def test_exact_12_advisory_domains_and_fiscal_not_root():
    assert len(CANONICAL_DOMAINS) == 12
    assert len(set(CANONICAL_DOMAINS)) == 12
    assert CANONICAL_DOMAINS[0] == "FISCAL"
    catalog = json.loads((ROOT / "registry" / "advisory_source_catalog_20260915.json").read_text())
    assert catalog["invariants"]["domain_count"] == 12
    assert catalog["invariants"]["fiscal_is_root"] is False
    assert catalog["invariants"]["professional_advisory_is_orchestrator"] is True


def test_laboral_final_supersedes_v01():
    catalog = json.loads((ROOT / "registry" / "advisory_source_catalog_20260915.json").read_text())
    labor = next(x for x in catalog["domains"] if x["domain"] == "LABORAL")
    assert labor["canonical_source"].endswith("v1.0_FINAL.md")
    assert any(x.endswith("v0.1.md") for x in labor["supersedes"])


def test_missing_general_legal_is_explicit_not_invented_green():
    catalog = json.loads((ROOT / "registry" / "advisory_source_catalog_20260915.json").read_text())
    legal = next(x for x in catalog["domains"] if x["domain"] == "JURIDICA_GENERAL")
    assert legal["canonical_source"] is None
    assert legal["source_status"] == "MISSING_ARTIFACT"


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
    assert "INMOBILIARIA" in routed
    assert "FISCAL" in routed
    assert "CONTABLE" in routed
    assert "MERCANTIL" in routed
    assert "FINANCIERA" in routed
    assert "PATRIMONIAL" in routed


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
    assert models.CANONICAL_HUMAN_EXCEPTIONS == {
        "LEGAL_REQUIRED", "SIGNATURE_REQUIRED", "LOW_CONFIDENCE", "HIGH_RISK",
        "POLICY_CONFLICT", "SECURITY_INCIDENT", "MONEY_LIMIT", "CUSTOMER_HUMAN_REQUEST"
    }
