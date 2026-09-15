import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from advisory.gateway import AdvisoryGatewayRequest, resolve_gateway_route
from advisory.models import Territory


def make_request(**overrides):
    values = {
        "company_id": "COMPANY-001",
        "engine_id": "PROFESSIONAL_ADVISORY",
        "environment": "LAB",
        "version": "1.0.0",
        "case_id": "CASE-001",
        "correlation_id": "CORR-001",
        "requested_service": "tax accounting",
        "territory": Territory(
            country="ES",
            autonomous_community="Andalucia",
            province="Cordoba",
            municipality="Cordoba",
        ),
        "facts": {"scenario": "gateway-contract-test"},
    }
    values.update(overrides)
    return AdvisoryGatewayRequest(**values)


class AdvisoryGatewayContractTests(unittest.TestCase):
    def test_required_multi_company_contract_fields_are_enforced(self):
        make_request().validate()
        for field in (
            "company_id",
            "engine_id",
            "version",
            "case_id",
            "correlation_id",
            "requested_service",
        ):
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    make_request(**{field: ""}).validate()

    def test_service_hints_route_multiple_domains(self):
        routed = resolve_gateway_route(make_request(requested_service="tax accounting finance"))
        self.assertEqual(routed, ("FISCAL", "CONTABLE", "FINANCIERA"))

    def test_cross_domain_trigger_routes_automatically(self):
        request = make_request(
            requested_service="advisory",
            facts={
                "scenario": "property acquisition",
                "advisory_triggers": ("company_buys_property",),
            },
        )
        routed = resolve_gateway_route(request)
        self.assertEqual(
            routed,
            (
                "INMOBILIARIA",
                "FISCAL",
                "CONTABLE",
                "MERCANTIL",
                "FINANCIERA",
                "PATRIMONIAL",
            ),
        )

    def test_unknown_or_unroutable_request_fails_closed(self):
        with self.assertRaises(ValueError):
            resolve_gateway_route(make_request(requested_service="unrecognized advisory request"))

    def test_explicit_unknown_domain_fails_closed(self):
        with self.assertRaises(ValueError):
            resolve_gateway_route(make_request(requested_domains=("NOT_A_DOMAIN",)))


if __name__ == "__main__":
    unittest.main()
