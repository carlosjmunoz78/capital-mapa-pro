import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from advisory.autonomy_tribunal import adjudicate_advisory_autonomy
from advisory.e2e_validation import run_e2e_validation

ADVISORY_DIR = ROOT / "advisory"


class AdvisoryBlockDTests(unittest.TestCase):
    def test_e2e_suite_covers_required_block_d_scenarios(self):
        result = run_e2e_validation()
        required = {
            "representative_12_domain_coverage",
            "representative_cases_green",
            "multidomain_execution",
            "old_vs_new_domains_match",
            "old_vs_new_status_match",
            "multi_company_isolation",
            "existing_case_recovery",
            "outdated_source_fails_closed",
            "low_confidence_gate",
            "high_risk_human_exception",
            "signature_required_human_exception",
            "legal_required_human_exception",
            "idempotency",
        }
        self.assertTrue(required.issubset(result.checks))
        self.assertEqual(result.representative_cases, 3)
        self.assertEqual(len(result.representative_domains), 12)
        self.assertTrue(result.green, result.checks)

    def test_advisory_only_tribunal_passes_preprod_candidate_without_global_promotion(self):
        e2e = run_e2e_validation()
        source_lock = json.loads(
            (ADVISORY_DIR / "source_lock_20260915.json").read_text(encoding="utf-8")
        )
        capability = json.loads(
            (ADVISORY_DIR / "capability_status_20260915.json").read_text(encoding="utf-8")
        )
        verdict = adjudicate_advisory_autonomy(
            e2e=e2e,
            source_lock_summary=source_lock["summary"],
            capability_runtime=capability["capability_runtime"],
        )
        self.assertEqual(verdict.verdict, "PASS_PREPROD_ADVISORY_AUTONOMY")
        self.assertTrue(verdict.preprod_advisory_autonomy_candidate)
        self.assertEqual(verdict.blockers, ())
        self.assertFalse(verdict.capability_green_global)
        self.assertFalse(verdict.autonomy_green)
        self.assertFalse(verdict.prod_enabled)


if __name__ == "__main__":
    unittest.main()
