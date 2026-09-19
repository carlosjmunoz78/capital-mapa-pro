import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

from jobs.company_onboarding_orchestrator import initial_state,PHASES,PHASE_ENGINE_MAP
from jobs.company_onboarding_superloop import run_superloop

class CompanyOnboardingSuperloopTests(unittest.TestCase):
    def test_groups_consecutive_green_phases_until_next_engine_is_missing(self):
        state=initial_state("fenix")
        results=[
            {"company_id":"fenix","engine_id":"COMP-REG-001","status":"GREEN","evidence_hash":"sha256:reg"},
            {"company_id":"fenix","engine_id":"ACCESSBOOT-001","status":"GREEN","evidence_hash":"sha256:access"},
        ]
        out=run_superloop(state,results)
        self.assertEqual(out["status"],"WAITING")
        self.assertEqual(out["stop_reason"],"ENGINE_RESULT_MISSING")
        self.assertEqual(out["missing_engine_id"],"SCAN-001")
        self.assertEqual(out["state"]["current_phase"],"SCAN_DIGITAL_FOOTPRINT")
        self.assertEqual(len(out["processed_steps"]),2)
        self.assertEqual(out["next_execution_plan"]["target_engine_id"],"SCAN-001")

    def test_partial_or_degraded_engine_does_not_advance_phase(self):
        state=initial_state("fenix")
        results=[
            {"company_id":"fenix","engine_id":"COMP-REG-001","status":"GREEN","evidence_hash":"sha256:reg"},
            {"company_id":"fenix","engine_id":"ACCESSBOOT-001","status":"PARTIAL","evidence_hash":"sha256:access"},
        ]
        out=run_superloop(state,results)
        self.assertEqual(out["status"],"WAITING")
        self.assertEqual(out["stop_reason"],"ENGINE_NOT_GREEN")
        self.assertEqual(out["waiting_engine_id"],"ACCESSBOOT-001")
        self.assertEqual(out["state"]["current_phase"],"MINIMUM_ACCESSES")

    def test_blocked_engine_stops_without_advancing(self):
        state=initial_state("fenix")
        results=[
            {"company_id":"fenix","engine_id":"COMP-REG-001","status":"BLOCKED","reason":"registry unavailable"},
        ]
        out=run_superloop(state,results)
        self.assertEqual(out["status"],"BLOCKED")
        self.assertEqual(out["stop_reason"],"ENGINE_BLOCKED")
        self.assertEqual(out["state"]["current_phase"],"REGISTER_COMPANY")
        self.assertFalse(out["external_mutation_allowed"])

    def test_human_required_reason_is_preserved(self):
        state=initial_state("fenix")
        results=[
            {"company_id":"fenix","engine_id":"COMP-REG-001","status":"HUMAN_REQUIRED","human_reason":"LEGAL_REQUIRED"},
        ]
        out=run_superloop(state,results)
        self.assertEqual(out["status"],"HUMAN_REQUIRED")
        self.assertEqual(out["human_reason"],"LEGAL_REQUIRED")
        self.assertEqual(out["stop_reason"],"HUMAN_REQUIRED")

    def test_all_green_evidence_reaches_prod_gate_and_still_fails_closed_high_risk(self):
        state=initial_state("fenix")
        results=[]
        seen=set()
        for phase in PHASES:
            eid=PHASE_ENGINE_MAP[phase]
            if eid in seen:
                continue
            seen.add(eid)
            results.append({"company_id":"fenix","engine_id":eid,"status":"GREEN","evidence_hash":f"sha256:{eid}"})
        out=run_superloop(state,results,max_steps=50)
        self.assertEqual(out["status"],"HUMAN_REQUIRED")
        self.assertEqual(out["human_reason"],"HIGH_RISK")
        self.assertFalse(out["state"]["production_activation_allowed"])
        self.assertEqual(out["processed_steps"][-1]["phase"],"PRODUCTION_ACTIVATION")

    def test_cross_company_result_is_denied(self):
        state=initial_state("fenix")
        with self.assertRaisesRegex(ValueError,"cross-company"):
            run_superloop(state,[{"company_id":"aion","engine_id":"COMP-REG-001","status":"GREEN"}])

if __name__=="__main__":
    unittest.main()
