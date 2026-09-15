import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from advisory.gateway import (
    AdvisoryGatewayRequest,
    execute_gateway_request,
    resolve_gateway_route,
)
from advisory.models import DomainOpinion, Territory


def make_request(**overrides):
    values = {
        "company_id": "COMPANY-001",
        "component_id": "PROFESSIONAL_ADVISORY",
        "engine_id": "TAX-001",
        "environment": "LAB",
        "version": "1.0.0",
        "case_id": "CASE-001",
        "correlation_id": "CORR-001",
        "actor": {"actor_id": "ACTOR-001", "actor_type": "SYSTEM"},
        "context": {"source": "test"},
        "permissions": ("advisory:execute",),
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
            "component_id",
            "engine_id",
            "version",
            "case_id",
            "correlation_id",
            "requested_service",
        ):
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    make_request(**{field: ""}).validate()

    def test_actor_and_execute_permission_are_fail_closed(self):
        with self.assertRaises(ValueError):
            make_request(actor={}).validate()
        with self.assertRaises(PermissionError):
            make_request(permissions=()).validate()

    def test_orchestrator_identity_is_separate_from_engine_identity(self):
        make_request(component_id="PROFESSIONAL_ADVISORY", engine_id="TAX-001").validate()
        with self.assertRaises(ValueError):
            make_request(engine_id="PROFESSIONAL_ADVISORY").validate()
        with self.assertRaises(ValueError):
            make_request(component_id="NOT_ADVISORY").validate()

    def test_service_hints_route_multiple_domains(self):
        routed = resolve_gateway_route(make_request(requested_service="tax accounting finance"))
        self.assertEqual(routed, ("FISCAL", "CONTABLE", "FINANCIERA"))

    def test_cross_domain_trigger_routes_automatically(self):
        request = make_request(
            engine_id="TAX-001",
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

    def test_unknown_engine_id_fails_closed(self):
        with self.assertRaises(ValueError):
            resolve_gateway_route(make_request(engine_id="NOT-A-CANONICAL-ID"))

    def test_specific_engine_must_match_routed_domain(self):
        routed = resolve_gateway_route(
            make_request(engine_id="TAX-001", requested_service="tax")
        )
        self.assertEqual(routed, ("FISCAL",))
        with self.assertRaises(ValueError):
            resolve_gateway_route(
                make_request(engine_id="TAX-001", requested_service="employment")
            )

    def test_gateway_executes_runtime_and_returns_traceable_response(self):
        request = make_request(requested_service="tax")

        def fiscal_handler(case, dependencies):
            self.assertIn("TAX-001", dependencies)
            return DomainOpinion(
                domain="FISCAL",
                status="GREEN",
                summary="validated",
                source_refs=("SRC-001",),
            )

        response = execute_gateway_request(request, {"FISCAL": fiscal_handler})
        self.assertEqual(response.company_id, request.company_id)
        self.assertEqual(response.case_id, request.case_id)
        self.assertEqual(response.correlation_id, request.correlation_id)
        self.assertEqual(response.decision.domains, ("FISCAL",))
        self.assertIn(
            "gateway://COMPANY-001/CASE-001/CORR-001",
            response.decision.audit_refs,
        )


if __name__ == "__main__":
    unittest.main()
