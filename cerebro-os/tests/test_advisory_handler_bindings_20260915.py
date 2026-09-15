import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from advisory.capabilities import engine_dependencies
from advisory.handlers import build_lab_handlers, evidence_bound_handler
from advisory.models import AdvisoryCase, Territory
from advisory.runtime import execute_case


def make_case(domains, *, include_all_evidence=True):
    engine_evidence = {}
    domain_source_refs = {}
    for domain in domains:
        for engine_id in engine_dependencies(domain):
            engine_evidence[engine_id] = (f"evidence:{engine_id}",)
        domain_source_refs[domain] = (f"source:{domain}",)
    if not include_all_evidence and domains:
        first = engine_dependencies(domains[0])[0]
        engine_evidence.pop(first, None)
    return AdvisoryCase(
        company_id="company-test",
        case_id="case-bindings",
        environment="LAB",
        version="1.0.0",
        requested_service="explicit advisory",
        territory=Territory(country="ES", autonomous_community="Andalucia", province="Cordoba", municipality="Cordoba"),
        facts={
            "summary": "synthetic binding case",
            "engine_evidence": engine_evidence,
            "domain_source_refs": domain_source_refs,
        },
        requested_domains=tuple(domains),
    )


class AdvisoryHandlerBindingsTests(unittest.TestCase):
    def test_all_12_domains_can_execute_with_complete_lab_evidence(self):
        domains = (
            "FISCAL", "CONTABLE", "LABORAL", "MERCANTIL", "FINANCIERA",
            "INMOBILIARIA", "HIPOTECARIA", "SUBVENCIONES_AYUDAS",
            "PROTECCION_DATOS_COMPLIANCE", "EMPRESARIAL_ESTRATEGICA",
            "PATRIMONIAL", "JURIDICA_GENERAL",
        )
        case = make_case(domains)
        decision = execute_case(case, build_lab_handlers(domains), audit_refs=("audit:binding-e2e",))
        self.assertEqual(decision.overall_status, "GREEN")
        self.assertEqual(decision.domains, domains)
        self.assertEqual(len(decision.opinions), 12)
        self.assertTrue(all(op.source_refs for op in decision.opinions))

    def test_missing_engine_evidence_blocks_domain(self):
        domains = ("INMOBILIARIA",)
        case = make_case(domains, include_all_evidence=False)
        decision = execute_case(case, build_lab_handlers(domains))
        self.assertEqual(decision.overall_status, "BLOCKED")
        self.assertTrue(any(r.startswith("missing_engine_evidence:") for r in decision.opinions[0].risks))

    def test_lab_handler_blocks_non_lab_environment(self):
        case = make_case(("FISCAL",))
        object.__setattr__(case, "environment", "PREPROD")
        decision = execute_case(case, {"FISCAL": evidence_bound_handler("FISCAL")})
        self.assertEqual(decision.overall_status, "BLOCKED")


if __name__ == "__main__":
    unittest.main()
