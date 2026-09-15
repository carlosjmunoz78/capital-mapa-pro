import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from advisory.models import CANONICAL_DOMAINS
from advisory.preprod_rehearsal import (
    build_preprod_rehearsal_case,
    build_preprod_rehearsal_handlers,
    preprod_rehearsal_passed,
    run_preprod_rehearsal_suite,
)
from advisory.representative_cases import REPRESENTATIVE_CASE_SPECS
from advisory.runtime import execute_case


class AdvisoryPreprodRehearsalTests(unittest.TestCase):
    def test_suite_passes_in_isolated_preprod(self):
        self.assertTrue(preprod_rehearsal_passed())
        decisions = run_preprod_rehearsal_suite()
        self.assertEqual(len(decisions), 3)
        covered = {domain for d in decisions for domain in d.domains}
        self.assertEqual(covered, set(CANONICAL_DOMAINS))
        for decision in decisions:
            self.assertEqual(decision.overall_status, "GREEN")
            self.assertTrue(decision.audit_refs)

    def test_cases_disable_app_crm_prod_and_customer_data(self):
        for spec in REPRESENTATIVE_CASE_SPECS:
            case = build_preprod_rehearsal_case(spec)
            self.assertEqual(case.environment, "PREPROD")
            self.assertTrue(case.facts["isolated_runtime"])
            self.assertTrue(case.facts["external_writes_disabled"])
            self.assertTrue(case.facts["app_crm_access_disabled"])
            self.assertTrue(case.facts["prod_credentials_disabled"])
            self.assertTrue(case.facts["customer_data_disabled"])

    def test_missing_isolation_control_fails_closed(self):
        spec = REPRESENTATIVE_CASE_SPECS[0]
        case = build_preprod_rehearsal_case(spec)
        facts = dict(case.facts)
        facts["external_writes_disabled"] = False
        broken = replace(case, facts=facts)
        handlers = build_preprod_rehearsal_handlers(broken.requested_domains)
        decision = execute_case(broken, handlers)
        self.assertEqual(decision.overall_status, "BLOCKED")
        self.assertTrue(any(
            "missing_isolation_control:external_writes_disabled" in risk
            for opinion in decision.opinions
            for risk in opinion.risks
        ))

    def test_lab_case_cannot_use_preprod_handlers(self):
        spec = REPRESENTATIVE_CASE_SPECS[0]
        preprod_case = build_preprod_rehearsal_case(spec)
        lab_case = replace(preprod_case, environment="LAB")
        handlers = build_preprod_rehearsal_handlers(lab_case.requested_domains)
        decision = execute_case(lab_case, handlers)
        self.assertEqual(decision.overall_status, "BLOCKED")


if __name__ == "__main__":
    unittest.main()
