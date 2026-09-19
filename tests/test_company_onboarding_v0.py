import json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"cerebro-os"))
from jobs.company_onboarding_orchestrator import initial_state,advance,default_phase_plan,PHASES
from jobs.scan_company_digital_footprint import scan_company,_public_url

class FakeHeaders:
    def get(self,key,default=None): return "text/html"
class FakeResponse:
    status=200
    headers=FakeHeaders()
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self,n=-1): return b"<html>Fenix</html>"
    def geturl(self): return "https://example.com/"

class CompanyOnboardingTests(unittest.TestCase):
    def test_state_machine_is_idempotent_scoped_and_fail_closed_at_prod(self):
        s=initial_state("newco")
        self.assertEqual(s["current_phase"],PHASES[0])
        p=default_phase_plan(s)
        self.assertFalse(p["allowed_external_mutation"])
        for phase in PHASES[:-1]:
            self.assertEqual(s["current_phase"],phase)
            s=advance(s,{"company_id":"newco","phase":phase,"status":"GREEN","evidence_ref":f"e://{phase}"})
        self.assertEqual(s["current_phase"],"PRODUCTION_ACTIVATION")
        s=advance(s,{"company_id":"newco","phase":"PRODUCTION_ACTIVATION","status":"GREEN","evidence_ref":"e://prod"})
        self.assertEqual(s["status"],"HUMAN_REQUIRED")
        self.assertEqual(s["human_reason"],"HIGH_RISK")
        self.assertFalse(s["production_activation_allowed"])

    def test_cross_company_phase_result_denied(self):
        s=initial_state("aion")
        with self.assertRaisesRegex(ValueError,"cross-company"):
            advance(s,{"company_id":"fenix","phase":"REGISTER_COMPANY","status":"GREEN"})

    def test_discovery_plan_is_read_only(self):
        s=initial_state("aion")
        s["current_phase"]="SCAN_DIGITAL_FOOTPRINT"
        p=default_phase_plan(s)
        self.assertEqual(p["execution_mode"],"READ_ONLY")
        self.assertFalse(p["allowed_external_mutation"])
        self.assertEqual(p["required_cost_eur"],0)

    def test_scan_public_domain_is_read_only(self):
        with patch("urllib.request.urlopen",return_value=FakeResponse()):
            out=scan_company({"company_id":"fenix","domains":["example.com"],"version":"1"})
        self.assertEqual(out["status"],"GREEN")
        self.assertEqual(out["checked_count"],1)
        self.assertFalse(out["external_mutation_allowed"])
        self.assertFalse(out["social_discovery_performed"])
        self.assertFalse(out["local_presence_discovery_performed"])

    def test_scan_blocks_local_private_targets(self):
        self.assertFalse(_public_url("http://localhost/x"))
        self.assertFalse(_public_url("http://127.0.0.1/x"))
        self.assertFalse(_public_url("http://10.0.0.1/x"))
        self.assertTrue(_public_url("https://example.com"))

if __name__=="__main__": unittest.main()
