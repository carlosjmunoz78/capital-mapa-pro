import importlib.util
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/"audit"/"onboarding_claim_consumer_inventory_cp81.py"
spec=importlib.util.spec_from_file_location("onboarding_claim_consumer_inventory_cp81",MOD)
audit=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=audit
spec.loader.exec_module(audit)

class OnboardingConsumerContractCP81Tests(unittest.TestCase):
    def test_all_checked_out_python_consumers_fenced(self):
        report=audit.inventory(ROOT)
        self.assertGreater(report["files_scanned"],50)
        self.assertGreater(report["consumer_sites"],5)
        self.assertEqual(report["parse_errors"],[])
        self.assertEqual(report["blockers"],[],report["blockers"])
        self.assertTrue(any(x["path"]=="jobs/run_company_onboarding_worker.py"
                            and x["classification"]=="FENCED" for x in report["sites"]))
        self.assertFalse(report["external_clients_verified"])
        self.assertFalse(report["remote_execution_verified"])
        self.assertFalse(report["promotion_allowed"])

    def test_missing_claim_token_fails_closed(self):
        src="from runtime.onboarding_queue import OnboardingQueue\n" + (
            "def run(queue):\n    queue.complete(request_id='x', status='WAITING', result={}, now_epoch=1)\n"
        )
        rows=audit.inspect_source(src,"jobs/example.py")
        self.assertEqual([r["classification"] for r in rows],["MISSING_TOKEN"])

    def test_explicit_fenced_call_is_accepted(self):
        src="from runtime.onboarding_queue import OnboardingQueue\n" + (
            "def run(queue,item):\n    queue.retry_or_dead_letter(request_id='x',result={},now_epoch=1,claim_attempts=item.attempts)\n"
        )
        rows=audit.inspect_source(src,"jobs/example.py")
        self.assertEqual([r["classification"] for r in rows],["FENCED"])

    def test_expected_denial_is_not_mistaken_for_legacy_consumer(self):
        src=("from runtime.onboarding_queue import OnboardingQueue\n"
            "def test_bad(q):\n"
            "    with self.assertRaisesRegex(PermissionError, 'claim_attempts required'):\n"
            "        q.complete(request_id='x',status='WAITING',result={},now_epoch=1)\n")
        rows=audit.inspect_source(src,"tests/example.py")
        self.assertEqual([r["classification"] for r in rows],["EXPECTED_DENIAL"])

    def test_dynamic_lookup_flags_manual_review(self):
        src=("from runtime.onboarding_queue import OnboardingQueue\n"
             "f=getattr(queue,'complete')\n")
        rows=audit.inspect_source(src,"jobs/dynamic.py")
        self.assertEqual([r["classification"] for r in rows],["DYNAMIC_REVIEW"])

if __name__=="__main__":
    unittest.main()
