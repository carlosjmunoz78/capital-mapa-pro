import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

from jobs.company_onboarding_orchestrator import initial_state,PHASE_ENGINE_MAP
from jobs.company_onboarding_executor import EngineHandler,OnboardingHandlerRegistry,execute_onboarding_superloop

class CompanyOnboardingExecutorTests(unittest.TestCase):
    def _green_handler(self,eid):
        def handler(payload):
            return {
              "company_id":payload["company_id"],"engine_id":eid,"status":"GREEN",
              "evidence_hash":f"sha256:{eid}","external_mutation_performed":False,"cost_eur":0.0,
            }
        return handler

    def test_executes_consecutive_safe_handlers_without_manual_ok(self):
        reg=OnboardingHandlerRegistry()
        reg.register(EngineHandler("COMP-REG-001",self._green_handler("COMP-REG-001"),("LOCAL_DETERMINISTIC",)))
        reg.register(EngineHandler("ACCESSBOOT-001",self._green_handler("ACCESSBOOT-001"),("LOCAL_DETERMINISTIC",)))
        out=execute_onboarding_superloop(initial_state("fenix"),registry=reg,max_steps=10)
        self.assertEqual(out["status"],"WAITING")
        self.assertEqual(out["executor_stop_reason"],"HANDLER_MISSING")
        self.assertEqual(out["missing_handler_engine_id"],"SCAN-001")
        self.assertEqual(out["state"]["current_phase"],"SCAN_DIGITAL_FOOTPRINT")
        self.assertEqual(len(out["executed_handlers"]),2)

    def test_partial_handler_stops_same_phase(self):
        reg=OnboardingHandlerRegistry()
        reg.register(EngineHandler("COMP-REG-001",self._green_handler("COMP-REG-001"),("LOCAL_DETERMINISTIC",)))
        reg.register(EngineHandler(
            "ACCESSBOOT-001",
            lambda p:{"company_id":p["company_id"],"engine_id":"ACCESSBOOT-001","status":"PARTIAL","evidence_hash":"sha256:a","cost_eur":0.0},
            ("LOCAL_DETERMINISTIC",)
        ))
        out=execute_onboarding_superloop(initial_state("fenix"),registry=reg,max_steps=10)
        self.assertEqual(out["status"],"WAITING")
        self.assertEqual(out["executor_stop_reason"],"ENGINE_NOT_GREEN")
        self.assertEqual(out["state"]["current_phase"],"MINIMUM_ACCESSES")

    def test_mode_mismatch_fails_closed(self):
        reg=OnboardingHandlerRegistry()
        reg.register(EngineHandler("COMP-REG-001",self._green_handler("COMP-REG-001"),("READ_ONLY",)))
        out=execute_onboarding_superloop(initial_state("fenix"),registry=reg,max_steps=5)
        self.assertEqual(out["status"],"BLOCKED")
        self.assertEqual(out["executor_stop_reason"],"HANDLER_MODE_MISMATCH")

    def test_external_mutation_report_is_rejected(self):
        reg=OnboardingHandlerRegistry()
        reg.register(EngineHandler(
            "COMP-REG-001",
            lambda p:{"company_id":"fenix","engine_id":"COMP-REG-001","status":"GREEN","external_mutation_performed":True,"cost_eur":0},
            ("LOCAL_DETERMINISTIC",)
        ))
        with self.assertRaisesRegex(ValueError,"external mutation"):
            execute_onboarding_superloop(initial_state("fenix"),registry=reg,max_steps=5)

    def test_cross_company_handler_result_is_rejected(self):
        reg=OnboardingHandlerRegistry()
        reg.register(EngineHandler(
            "COMP-REG-001",
            lambda p:{"company_id":"aion","engine_id":"COMP-REG-001","status":"GREEN","cost_eur":0},
            ("LOCAL_DETERMINISTIC",)
        ))
        with self.assertRaisesRegex(ValueError,"cross-company"):
            execute_onboarding_superloop(initial_state("fenix"),registry=reg,max_steps=5)

    def test_all_safe_handlers_reach_final_prod_gate_and_stop_high_risk(self):
        reg=OnboardingHandlerRegistry()
        seen=set()
        for phase,eid in PHASE_ENGINE_MAP.items():
            if eid in seen:
                continue
            seen.add(eid)
            if phase=="PRODUCTION_ACTIVATION":
                modes=("GATE_ONLY",)
            elif phase in {
                "SCAN_DIGITAL_FOOTPRINT","DISCOVER_BUSINESS_MODEL","DISCOVER_PROCESSES",
                "AUDIT_WEBSITE","DISCOVER_KEYWORDS","AUDIT_SOCIAL_MEDIA","AUDIT_LOCAL_PRESENCE","MAP_COMPETITORS"
            }:
                modes=("READ_ONLY",)
            elif phase in {
                "BOOTSTRAP_CRM","BOOTSTRAP_APP","BOOTSTRAP_AUTOMATIONS","BOOTSTRAP_TRAINING",
                "CREATE_SUPERVISOR_SCOPE","CREATE_BACKUP_REBUILD_PACK","PREPROD_TESTS"
            }:
                modes=("PREPROD_ONLY",)
            else:
                modes=("LOCAL_DETERMINISTIC",)
            reg.register(EngineHandler(eid,self._green_handler(eid),modes))
        out=execute_onboarding_superloop(initial_state("fenix"),registry=reg,max_steps=50)
        self.assertEqual(out["status"],"HUMAN_REQUIRED")
        self.assertEqual(out["human_reason"],"HIGH_RISK")
        self.assertFalse(out["state"]["production_activation_allowed"])
        self.assertEqual(out["executed_handlers"][-1]["engine_id"],"COMP-ONB-001")

if __name__=="__main__":
    unittest.main()
