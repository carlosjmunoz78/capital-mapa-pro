import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

from jobs.assess_remote_onboarding_gaps import assess_remote_onboarding_gaps,assess_many
from jobs.plan_remote_onboarding_work import plan_remote_work

class RemoteOnboardingGapAssessorTests(unittest.TestCase):
    def _result(self,phase,status="WAITING",**extra):
        row={
          "company_id":"fenix","version":"1.0.0","status":status,
          "state":{"company_id":"fenix","environment":"LAB","current_phase":phase},
          "remote_prefill":{"engine_count":13,"green_engine_count":7},
        }
        row.update(extra); return row

    def test_remote_discovery_phase_is_actionable_without_pc(self):
        out=assess_remote_onboarding_gaps(self._result("SCAN_DIGITAL_FOOTPRINT"))
        self.assertEqual(out["classification"],"REMOTE_SAFE")
        self.assertTrue(out["remotely_actionable"])
        self.assertFalse(out["local_pc_required"])
        self.assertEqual(out["remote_prefill_remaining"],6)
        plan=plan_remote_work(self._result("SCAN_DIGITAL_FOOTPRINT"))
        self.assertEqual(plan["work"]["execution_mode"],"READ_ONLY_OR_LOCAL_DETERMINISTIC")
        self.assertFalse(plan["work"]["may_use_browser_bridge"])

    def test_minimum_access_phase_is_explicitly_local_pc_dependent(self):
        out=assess_remote_onboarding_gaps(self._result("MINIMUM_ACCESSES"))
        self.assertEqual(out["classification"],"LOCAL_ACCESS_DEPENDENT")
        self.assertFalse(out["remotely_actionable"])
        self.assertTrue(out["local_pc_required"])
        self.assertEqual(out["next_action"],"WAIT_FOR_LOCAL_ACCESS_OR_EXISTING_CLOUD_EVIDENCE")

    def test_preprod_bootstrap_can_continue_remotely_without_prod_mutation(self):
        out=plan_remote_work(self._result("BOOTSTRAP_CRM"))
        self.assertEqual(out["status"],"GREEN")
        self.assertEqual(out["work"]["execution_mode"],"PREPROD_ONLY")
        self.assertFalse(out["work"]["may_mutate_prod"])
        self.assertFalse(out["production_activation_allowed"])

    def test_prod_gate_is_never_remote_actionable(self):
        out=assess_remote_onboarding_gaps(self._result("PRODUCTION_ACTIVATION"))
        self.assertEqual(out["classification"],"PROD_GATE")
        self.assertFalse(out["remotely_actionable"])
        self.assertFalse(out["production_activation_allowed"])

    def test_human_required_reason_is_preserved(self):
        out=assess_remote_onboarding_gaps(self._result(
            "PREPROD_TESTS",status="HUMAN_REQUIRED",human_reason="HIGH_RISK"
        ))
        self.assertEqual(out["classification"],"HUMAN_REQUIRED")
        self.assertEqual(out["human_reason"],"HIGH_RISK")
        self.assertEqual(out["status"],"HUMAN_REQUIRED")

    def test_cross_company_state_is_denied(self):
        row=self._result("SCAN_DIGITAL_FOOTPRINT")
        row["state"]["company_id"]="aion"
        with self.assertRaisesRegex(ValueError,"cross-company"):
            assess_remote_onboarding_gaps(row)

    def test_batch_counts_remote_local_and_human_gaps(self):
        out=assess_many([
          self._result("SCAN_DIGITAL_FOOTPRINT"),
          {**self._result("MINIMUM_ACCESSES"),"company_id":"aion","state":{"company_id":"aion","environment":"LAB","current_phase":"MINIMUM_ACCESSES"}},
          {**self._result("PREPROD_TESTS",status="HUMAN_REQUIRED",human_reason="POLICY_CONFLICT"),"company_id":"third","state":{"company_id":"third","environment":"PREPROD","current_phase":"PREPROD_TESTS"}}
        ])
        self.assertEqual(out["remote_actionable_count"],1)
        self.assertEqual(out["local_pc_required_count"],1)
        self.assertEqual(out["human_required_count"],1)
        self.assertEqual(out["status"],"HUMAN_REQUIRED")

if __name__=="__main__":
    unittest.main()
