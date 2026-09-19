import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

from jobs.company_onboarding_orchestrator import initial_state,PHASE_ENGINE_MAP
from jobs.company_onboarding_executor import execute_onboarding_superloop
from jobs.company_onboarding_default_handlers import build_default_onboarding_registry

class CompanyOnboardingDefaultHandlersTests(unittest.TestCase):
    def test_registry_has_concrete_binding_for_every_onboarding_engine(self):
        reg=build_default_onboarding_registry()
        for engine_id in set(PHASE_ENGINE_MAP.values()):
            self.assertIsNotNone(reg.get(engine_id),engine_id)

    def test_real_default_handlers_execute_registration_and_access_then_stop_on_empty_scan(self):
        reg=build_default_onboarding_registry()
        context={
          "company_profile":{"legal_name":"Fenix Test","evidence_ref":"doc://company"},
          "access_requirements":[{"capability":"crm","purpose":"sales","provider":"existing","required":True}],
          "existing_accounts":[{"company_id":"fenix","account_id":"acct-1","capabilities":["crm"]}],
          "existing_connectors":[],
          "session_observations":[],
          "domains":[],
        }
        out=execute_onboarding_superloop(initial_state("fenix"),registry=reg,context=context,max_steps=10)
        self.assertEqual(out["status"],"WAITING")
        self.assertEqual(out["executor_stop_reason"],"ENGINE_NOT_GREEN")
        self.assertEqual(out["state"]["current_phase"],"SCAN_DIGITAL_FOOTPRINT")
        self.assertEqual([x["engine_id"] for x in out["executed_handlers"]],["COMP-REG-001","ACCESSBOOT-001","SCAN-001"])

    def test_registration_does_not_invent_missing_legal_identity(self):
        reg=build_default_onboarding_registry()
        context={"company_profile":{}}
        out=execute_onboarding_superloop(initial_state("fenix"),registry=reg,context=context,max_steps=5)
        self.assertEqual(out["status"],"WAITING")
        self.assertEqual(out["executor_stop_reason"],"ENGINE_NOT_GREEN")
        self.assertEqual(out["executed_handlers"][0]["engine_id"],"COMP-REG-001")
        self.assertEqual(out["executed_handlers"][0]["status"],"PARTIAL")

    def test_outputs_are_carried_forward_for_dependent_handler(self):
        reg=build_default_onboarding_registry()
        context={
          "company_profile":{"legal_name":"Fenix Test","evidence_ref":"doc://company"},
          "access_requirements":[],
          "existing_accounts":[],
          "existing_connectors":[],
          "session_observations":[],
          "domains":[],
        }
        out=execute_onboarding_superloop(initial_state("fenix"),registry=reg,context=context,max_steps=10)
        # Registration is real evidence and access bootstrap is evaluated from context.
        self.assertEqual(out["executed_handlers"][0]["status"],"GREEN")
        self.assertEqual(out["executed_handlers"][1]["engine_id"],"ACCESSBOOT-001")
        self.assertEqual(out["executed_handlers"][1]["status"],"GREEN")

    def test_default_registry_never_declares_external_mutation_or_paid_handler(self):
        reg=build_default_onboarding_registry()
        for engine_id in set(PHASE_ENGINE_MAP.values()):
            handler=reg.get(engine_id)
            self.assertFalse(handler.external_mutation_allowed)
            self.assertEqual(handler.cost_eur,0.0)

if __name__=="__main__":
    unittest.main()
