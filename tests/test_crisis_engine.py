import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"cerebro-os"))
from jobs.plan_crisis_response import classify,derive_from_incidents,run

class CrisisEngineTests(unittest.TestCase):
    def test_security_crisis_is_human_required_and_no_external_send(self):
        out=classify({"company_id":"fenix","environment":"LAB","version":"1","crisis_type":"DATA_LEAK"})
        self.assertEqual(out["status"],"HUMAN_REQUIRED")
        self.assertEqual(out["human_reason"],"SECURITY_INCIDENT")
        self.assertFalse(out["external_mutation_allowed"])
        self.assertFalse(out["external_communication_sent"])
        self.assertTrue(all(not a["external_execution_allowed"] for a in out["actions"]))
        self.assertTrue(all(not a["communication_send_allowed"] for a in out["actions"]))

    def test_legal_crisis_routes_to_legal_required(self):
        out=classify({"company_id":"fenix","environment":"LAB","version":"1","crisis_type":"LEGAL_INCIDENT"})
        self.assertEqual(out["human_reason"],"LEGAL_REQUIRED")

    def test_low_severity_plan_is_prepared_but_not_executed(self):
        out=classify({"company_id":"aion","environment":"LAB","version":"1","crisis_type":"WEB_DOWN","severity":"MEDIUM"})
        self.assertEqual(out["status"],"PLAN_READY")
        self.assertIsNone(out["human_reason"])
        self.assertFalse(out["external_mutation_allowed"])

    def test_incident_derivation_maps_security_and_mass_failure(self):
        plans=derive_from_incidents({
            "company_id":"aion","environment":"LAB","version":"1",
            "incidents":[
                {"company_id":"aion","incident_type":"SECURITY_REGRESSION","severity":"CRITICAL"},
                {"company_id":"aion","incident_type":"CRITICAL_PROCESS_NON_CONFORMITY","severity":"CRITICAL"}
            ]
        })
        self.assertEqual({p["crisis_type"] for p in plans},{"DATA_LEAK","MASS_FAILURE"})
        self.assertTrue(all(p["status"]=="HUMAN_REQUIRED" for p in plans))

    def test_cross_company_incident_denied(self):
        with self.assertRaisesRegex(ValueError,"cross-company"):
            derive_from_incidents({"company_id":"aion","incidents":[{"company_id":"fenix","incident_type":"SECURITY_REGRESSION","severity":"CRITICAL"}]})

if __name__=="__main__": unittest.main()
