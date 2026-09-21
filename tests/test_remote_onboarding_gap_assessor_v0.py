import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

from jobs.assess_remote_onboarding_gaps import assess_remote_onboarding_gaps,assess_many
from jobs.plan_remote_onboarding_work import plan_remote_work
from identity.browser_bridge_acceptance_gate import evaluate_browser_bridge_acceptance

class RemoteOnboardingGapAssessorTests(unittest.TestCase):
    def _result(self,phase,status="WAITING",**extra):
        row={
          "company_id":"fenix","version":"1.0.0","status":status,
          "state":{"company_id":"fenix","environment":"LAB","current_phase":phase},
          "remote_prefill":{"engine_count":13,"green_engine_count":7},
        }
        row.update(extra); return row

    def _acceptance(self,**overrides):
        row={
          "record_type":"cerebro_browser_bridge_acceptance",
          "engine_id":"ACCESSBOOT-001",
          "service":"CEREBRO Browser Bridge",
          "service_version":"1.4.1",
          "environment":"LAB",
          "company_id":"fenix",
          "device_id":"desktop-test",
          "profile_id":"Default",
          "status":"GREEN",
          "checks":{
            "service_found":True,
            "service_version":True,
            "loopback_only":True,
            "paired":True,
            "lab_scope":True,
            "prod_disabled":True,
            "extension_connected":True,
            "extension_fresh":True,
            "transport_online":True,
            "raw_secret_exposed":False,
          },
          "next_gate":"REMOTE_LAB_ROUNDTRIP",
          "external_mutation_allowed":False,
          "prod_activation_allowed":False,
          "secret_value_included":False,
          "cost_eur":0.0,
        }
        row.update(overrides)
        return row

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

    def test_green_physical_acceptance_enables_only_remote_lab_roundtrip(self):
        row=self._result("MINIMUM_ACCESSES",browser_bridge_acceptance=self._acceptance())
        out=assess_remote_onboarding_gaps(row)
        self.assertEqual(out["classification"],"LOCAL_ACCESS_REMOTE_TEST_READY")
        self.assertTrue(out["remotely_actionable"])
        self.assertFalse(out["local_pc_required"])
        self.assertEqual(out["next_action"],"RUN_REMOTE_LAB_BRIDGE_ACCEPTANCE")
        plan=plan_remote_work(row)
        self.assertEqual(plan["work"]["execution_mode"],"BROWSER_BRIDGE_LAB_ACCEPTANCE")
        self.assertTrue(plan["work"]["may_use_browser_bridge"])
        self.assertEqual(plan["work"]["browser_bridge_action"],"OPEN_LOCAL_TEST_PAGE")
        self.assertFalse(plan["work"]["may_use_computer_use"])
        self.assertFalse(plan["work"]["may_mutate_prod"])

    def test_partial_acceptance_keeps_pc_gate_closed(self):
        evidence=self._acceptance(status="PARTIAL")
        evidence["checks"]=dict(evidence["checks"])
        evidence["checks"]["extension_fresh"]=False
        row=self._result("MINIMUM_ACCESSES",browser_bridge_acceptance=evidence)
        out=assess_remote_onboarding_gaps(row)
        self.assertEqual(out["classification"],"LOCAL_ACCESS_DEPENDENT")
        self.assertTrue(out["local_pc_required"])
        self.assertFalse(out["remotely_actionable"])

    def test_cross_company_acceptance_is_denied(self):
        evidence=self._acceptance(company_id="aion")
        with self.assertRaisesRegex(ValueError,"cross-company"):
            evaluate_browser_bridge_acceptance(evidence,company_id="fenix")

    def test_secret_exposure_becomes_canonical_security_incident(self):
        evidence=self._acceptance(secret_value_included=True)
        out=assess_remote_onboarding_gaps(
            self._result("MINIMUM_ACCESSES",browser_bridge_acceptance=evidence)
        )
        self.assertEqual(out["classification"],"HUMAN_REQUIRED")
        self.assertEqual(out["human_reason"],"SECURITY_INCIDENT")
        self.assertFalse(out["remotely_actionable"])

    def test_prod_or_external_mutation_flags_never_open_remote_roundtrip(self):
        for evidence in (
            self._acceptance(prod_activation_allowed=True),
            self._acceptance(external_mutation_allowed=True),
            self._acceptance(environment="PROD"),
        ):
            out=evaluate_browser_bridge_acceptance(evidence,company_id="fenix")
            self.assertFalse(out["remote_lab_roundtrip_allowed"])

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
