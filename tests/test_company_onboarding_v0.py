import json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"cerebro-os"))
from jobs.company_onboarding_orchestrator import initial_state,advance,default_phase_plan,PHASES
from jobs.scan_company_digital_footprint import scan_company,_public_url
from jobs.discover_business_model import discover_business_model
from jobs.discover_company_processes import discover_processes
from jobs.audit_company_website import audit_website
from jobs.discover_company_keywords import discover_keywords

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

    def test_bmd_never_invents_and_exposes_missing_critical_facts(self):
        out=discover_business_model({
            "company_id":"fenix",
            "facts":{"products_services":["hipotecas"],"target_customers":["compradores"]},
            "evidence":[{"ref":"doc://master"}],
        })
        self.assertEqual(out["engine_id"],"BMD-001")
        self.assertEqual(out["status"],"PARTIAL")
        self.assertIn("geography",out["missing_critical_facts"])
        self.assertFalse(out["inventions_allowed"])
        self.assertFalse(out["external_mutation_allowed"])

    def test_bmd_complete_evidence_can_be_green_without_paid_ai(self):
        facts={k:[k] for k in ("products_services","target_customers","geography","channels","revenue_model","objectives","constraints")}
        out=discover_business_model({"company_id":"aion","facts":facts,"evidence":[{"ref":f"e://{i}"} for i in range(7)]})
        self.assertEqual(out["status"],"GREEN")
        self.assertGreaterEqual(out["confidence"],0.75)
        self.assertEqual(out["cost_eur"],0)

    def test_process_discovery_candidates_are_versioned_and_unresolved_owner_is_visible(self):
        out=discover_processes({
            "company_id":"fenix",
            "process_candidates":[{"name":"Lead a expediente","inputs":["lead"],"outputs":["expediente"],"evidence_refs":["e://crm"]}]
        })
        self.assertEqual(out["engine_id"],"PROC-001")
        self.assertEqual(out["status"],"PARTIAL")
        self.assertEqual(out["process_count"],1)
        self.assertIn("owner",out["processes"][0]["missing_fields"])
        self.assertTrue(out["candidate_only"])

    def test_process_discovery_is_deterministic(self):
        payload={"company_id":"aion","process_candidates":[
            {"name":"Zeta","inputs":["a"],"outputs":["b"],"owner":"ops","evidence_refs":["e://1"]},
            {"name":"Alpha","inputs":["x"],"outputs":["y"],"owner":"ops","evidence_refs":["e://2"]},
        ]}
        a=discover_processes(payload); b=discover_processes(payload)
        self.assertEqual(a["evidence_hash"],b["evidence_hash"])
        self.assertEqual([x["name"] for x in a["processes"]],["Alpha","Zeta"])

    def test_website_audit_requires_same_company_scan_evidence(self):
        scan={"company_id":"fenix","engine_id":"SCAN-001","pages":[]}
        with self.assertRaisesRegex(ValueError,"cross-company"):
            audit_website({"company_id":"aion","scan_result":scan})

    def test_website_audit_is_read_only_and_does_not_overclaim(self):
        scan={
            "company_id":"fenix","engine_id":"SCAN-001",
            "pages":[{"url":"https://example.com","final_url":"https://example.com/","checked":True,"status":"OK","http_status":200,"content_type":"text/html","content_hash":"abc","bytes":1200}]
        }
        out=audit_website({"company_id":"fenix","scan_result":scan})
        self.assertEqual(out["status"],"GREEN")
        self.assertTrue(out["read_only"])
        self.assertFalse(out["external_mutation_allowed"])
        self.assertIn("full_crawl",out["not_claimed"])

    def test_keyword_discovery_is_deterministic_first_and_zero_cost(self):
        out=discover_keywords({
            "company_id":"fenix",
            "source_texts":["Hipotecas en Cordoba para comprar vivienda. Asesoramiento hipotecario en Cordoba."],
            "seed_keywords":["asesor hipotecario","hipoteca"],
            "geographies":["Cordoba"],
        })
        self.assertEqual(out["engine_id"],"KW-001")
        self.assertEqual(out["strategy"],"DETERMINISTIC_FIRST")
        self.assertFalse(out["semantic_ai_used"])
        self.assertFalse(out["paid_ai_used"])
        self.assertEqual(out["cost_eur"],0)
        self.assertGreater(out["keyword_count"],0)
        self.assertTrue(any(x["intent"]=="LOCAL" for x in out["keywords"]))

    def test_keyword_discovery_does_not_fake_volume_or_rank(self):
        out=discover_keywords({"company_id":"aion","seed_keywords":["automation"],"source_texts":[],"geographies":[]})
        self.assertIn("no_search_volume_without_external_source",out["limitations"])
        self.assertIn("no_serp_rank_without_external_source",out["limitations"])

if __name__=="__main__": unittest.main()
