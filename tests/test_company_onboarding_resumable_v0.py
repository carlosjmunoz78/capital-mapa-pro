import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

from jobs.run_company_onboarding_executor import run_request

class ResumableCompanyOnboardingTests(unittest.TestCase):
    def _base_context(self):
        return {
          "company_profile":{"legal_name":"Fenix Test","evidence_ref":"doc://company"},
          "access_requirements":[{"capability":"crm","purpose":"sales","provider":"existing","required":True}],
          "existing_accounts":[{"company_id":"fenix","account_id":"acct-1","capabilities":["crm"]}],
          "existing_connectors":[],
          "session_observations":[],
          "domains":[],
        }

    def test_runner_persists_engine_results_for_resume(self):
        first=run_request({"company_id":"fenix","context":self._base_context(),"max_steps":10})
        self.assertEqual(first["status"],"WAITING")
        ids={row["engine_id"] for row in first["engine_results"]}
        self.assertIn("COMP-REG-001",ids)
        self.assertIn("ACCESSBOOT-001",ids)
        self.assertIn("SCAN-001",ids)
        self.assertTrue(first["automatic_resume_supported"])
        self.assertFalse(first["external_mutation_allowed"])

    def test_resume_reuses_green_results_and_reexecutes_non_green_current_phase(self):
        first=run_request({"company_id":"fenix","context":self._base_context(),"max_steps":10})
        second=run_request({"company_id":"fenix","context":self._base_context(),"max_steps":2},first)
        self.assertEqual(second["executed_handlers"][0]["engine_id"],"SCAN-001")
        self.assertEqual(second["executed_handlers"][0]["result_source"],"EXECUTED")
        self.assertEqual(second["state"]["current_phase"],"SCAN_DIGITAL_FOOTPRINT")

    def test_resume_rejects_cross_company_previous_state(self):
        first=run_request({"company_id":"fenix","context":self._base_context(),"max_steps":5})
        with self.assertRaisesRegex(ValueError,"cross-company previous"):
            run_request({"company_id":"aion","context":{}},first)

    def test_partial_registration_can_be_retried_after_context_is_fixed(self):
        first=run_request({"company_id":"fenix","context":{"company_profile":{}},"max_steps":2})
        self.assertEqual(first["state"]["current_phase"],"REGISTER_COMPANY")
        fixed=self._base_context()
        second=run_request({"company_id":"fenix","context":fixed,"max_steps":3},first)
        self.assertEqual(second["executed_handlers"][0]["engine_id"],"COMP-REG-001")
        self.assertEqual(second["executed_handlers"][0]["status"],"GREEN")
        self.assertNotEqual(second["state"]["current_phase"],"REGISTER_COMPANY")

    def test_prod_activation_never_becomes_allowed_in_runner(self):
        first=run_request({"company_id":"fenix","context":self._base_context(),"max_steps":10})
        self.assertFalse(first["production_activation_allowed"])

if __name__=="__main__":
    unittest.main()
