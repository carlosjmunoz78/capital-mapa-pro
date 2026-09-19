import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

from jobs.prefill_remote_onboarding import prefill_remote_safe_context,REMOTE_PREFILL_PLAN
from jobs.run_company_onboarding_executor import run_request

class RemoteOnboardingPrefillTests(unittest.TestCase):
    def context(self):
        facts={k:[k] for k in ("products_services","target_customers","geography","channels","revenue_model","objectives","constraints")}
        return {
          "company_profile":{"legal_name":"Fenix Test","evidence_ref":"doc://company"},
          "access_requirements":[{"capability":"crm","purpose":"sales","provider":"existing","required":True}],
          "existing_accounts":[],"existing_connectors":[],"session_observations":[],"domains":[],
          "business_facts":facts,"business_evidence":[{"ref":"e://bmd"}],
          "process_candidates":[{"name":"Lead intake","inputs":["lead"],"outputs":["case"],"owner":"ops","evidence_refs":["e://proc"]}],
          "source_texts":["asesoramiento hipotecario cordoba"],"seed_keywords":["hipoteca cordoba"],
          "geographies":["cordoba"],"social_profiles":[],"local_listings":[],
          "competitors":[{"name":"Comp A","domain":"a.example","signals":["same service"],"evidence_refs":["e://comp"]}],
        }

    def test_remote_prefill_continues_while_access_waits(self):
        out=run_request({"company_id":"fenix","version":"1.0.0","max_steps":20,"context":self.context()})
        self.assertEqual(out["status"],"WAITING")
        self.assertEqual(out["state"]["current_phase"],"MINIMUM_ACCESSES")
        persisted={row["engine_id"]:row for row in out["engine_results"]}
        self.assertIn("BMD-001",persisted)
        self.assertIn("KW-001",persisted)
        self.assertIn("PROC-001",persisted)
        event_ids={row["engine_id"] for row in out["remote_prefill"]["events"]}
        self.assertNotIn("ACCESSBOOT-001",event_ids)
        self.assertFalse(out["remote_prefill"]["computer_use_performed"])
        self.assertEqual(out["cost_eur"],0.0)

    def test_prefill_reuses_green_evidence(self):
        context=self.context()
        context["engine_results"]={"BMD-001":{"company_id":"fenix","engine_id":"BMD-001","status":"GREEN","evidence_hash":"sha256:existing","cost_eur":0.0}}
        out=prefill_remote_safe_context(company_id="fenix",version="1.0.0",context=context)
        event=next(x for x in out["events"] if x["engine_id"]=="BMD-001")
        self.assertEqual(event["status"],"SKIPPED_GREEN")
        self.assertEqual(out["context"]["engine_results"]["BMD-001"]["evidence_hash"],"sha256:existing")

    def test_cross_company_seed_is_denied(self):
        context=self.context()
        context["engine_results"]={"BMD-001":{"company_id":"aion","engine_id":"BMD-001","status":"GREEN"}}
        with self.assertRaisesRegex(ValueError,"cross-company prefill evidence"):
            prefill_remote_safe_context(company_id="fenix",version="1.0.0",context=context)

    def test_prefill_plan_excludes_local_access_and_preprod(self):
        ids={row[0] for row in REMOTE_PREFILL_PLAN}
        for engine_id in ("ACCESSBOOT-001","CRMBOOT-001","APPBOOT-001","AUTBOOT-001","COMP-DEP-001","COMP-ONB-001"):
            self.assertNotIn(engine_id,ids)

if __name__=="__main__":
    unittest.main()
