import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from advisory.models import CANONICAL_DOMAINS
from advisory.representative_cases import (
    REPRESENTATIVE_CASE_SPECS,
    build_representative_case,
    lab_capability_green,
    representative_suite_coverage,
    run_representative_case_suite,
)


class AdvisoryRepresentativeCasesTests(unittest.TestCase):
    def test_suite_covers_all_12_domains(self):
        self.assertEqual(representative_suite_coverage(), CANONICAL_DOMAINS)

    def test_all_representative_cases_are_green_with_audit_refs(self):
        results = run_representative_case_suite()
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertEqual(result.overall_status, "GREEN")
            self.assertTrue(result.audit_refs)
            self.assertTrue(result.routed_domains)

    def test_fixtures_are_explicitly_lab_and_not_customer_data(self):
        for spec in REPRESENTATIVE_CASE_SPECS:
            case = build_representative_case(spec)
            self.assertEqual(case.environment, "LAB")
            self.assertTrue(case.facts["representative_fixture"])
            self.assertTrue(case.facts["not_customer_data"])
            self.assertTrue(case.evidence)

    def test_engine_and_domain_evidence_are_present(self):
        for spec in REPRESENTATIVE_CASE_SPECS:
            case = build_representative_case(spec)
            engine_evidence = case.facts["engine_evidence"]
            domain_sources = case.facts["domain_source_refs"]
            self.assertTrue(engine_evidence)
            for domain in case.requested_domains:
                self.assertIn(domain, domain_sources)
                self.assertTrue(domain_sources[domain])

    def test_lab_capability_green_is_environment_scoped(self):
        self.assertTrue(lab_capability_green())


if __name__ == "__main__":
    unittest.main()
