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
from jobs.audit_company_social import audit_social
from jobs.audit_company_local_presence import audit_local_presence
from jobs.map_company_competitors import map_competitors
from jobs.bootstrap_company_knowledge import bootstrap_company_knowledge
from jobs.bootstrap_company_seo import bootstrap_seo
from jobs.bootstrap_company_social import bootstrap_social
from jobs.bootstrap_company_marketing import bootstrap_marketing
from jobs.activate_company_engine_matrix import activate_matrix
from jobs.bootstrap_company_crm import bootstrap_crm
from jobs.bootstrap_company_app import bootstrap_app
from jobs.bootstrap_company_automations import bootstrap_automations
from jobs.bootstrap_company_training import bootstrap_training
from jobs.create_company_supervisor_scope import create_supervisor_scope
from jobs.create_company_backup_rebuild_pack import create_backup_rebuild_pack
from jobs.evaluate_company_preprod_readiness import evaluate_preprod_readiness
from jobs.evaluate_company_production_activation import evaluate_production_activation

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

    def test_social_audit_is_read_only_and_exposes_unknowns(self):
        out=audit_social({"company_id":"fenix","profiles":[{"platform":"instagram","handle_or_url":"@fenix","evidence_refs":["e://ig"]}]})
        self.assertEqual(out["engine_id"],"SOCAUD-001")
        self.assertTrue(out["read_only"])
        self.assertFalse(out["posting_allowed"])
        self.assertEqual(out["status"],"PARTIAL")

    def test_local_presence_audit_detects_nap_inconsistency(self):
        out=audit_local_presence({"company_id":"fenix","listings":[
            {"provider":"google","name":"Fenix","address":"A","phone":"1","locality":"Cordoba","evidence_refs":["e://1"]},
            {"provider":"bing","name":"Fenix","address":"B","phone":"1","locality":"Cordoba","evidence_refs":["e://2"]},
        ]})
        self.assertIn("NAP_INCONSISTENT",out["global_issues"])
        self.assertFalse(out["external_mutation_allowed"])

    def test_competitor_map_never_claims_market_share_or_rank(self):
        out=map_competitors({"company_id":"aion","competitors":[{"name":"Comp A","domain":"a.example","signals":["same service"],"evidence_refs":["e://a"]}]})
        self.assertEqual(out["engine_id"],"COMPET-001")
        self.assertFalse(out["ranking_claimed"])
        self.assertFalse(out["market_share_claimed"])
        self.assertEqual(out["status"],"GREEN")

    def test_kboot_requires_provenance_and_is_candidate_only(self):
        source=discover_keywords({"company_id":"fenix","seed_keywords":["hipoteca"],"source_texts":["hipoteca cordoba"],"geographies":["cordoba"]})
        out=bootstrap_company_knowledge({"company_id":"fenix","inputs":[source]})
        self.assertEqual(out["engine_id"],"KBOOT-001")
        self.assertEqual(out["status"],"GREEN")
        self.assertFalse(out["direct_knowledge_promotion_allowed"])
        self.assertIn("PRV-001",out["required_downstream_gates"])

    def test_kboot_cross_company_is_denied(self):
        source=discover_keywords({"company_id":"fenix","seed_keywords":["hipoteca"],"source_texts":[],"geographies":[]})
        with self.assertRaisesRegex(ValueError,"cross-company"):
            bootstrap_company_knowledge({"company_id":"aion","inputs":[source]})

    def test_seoboot_requires_waud_and_kw_and_never_publishes(self):
        waud={"company_id":"fenix","engine_id":"WAUD-001","status":"GREEN","issue_count":1}
        kw={"company_id":"fenix","engine_id":"KW-001","status":"GREEN","keywords":[{"keyword":"hipoteca cordoba","intent":"LOCAL"}]}
        out=bootstrap_seo({"company_id":"fenix","inputs":[waud,kw]})
        self.assertEqual(out["engine_id"],"SEOBOOT-001")
        self.assertEqual(out["status"],"GREEN")
        self.assertFalse(out["publication_allowed"])
        self.assertFalse(out["external_mutation_allowed"])

    def test_socboot_is_plan_only(self):
        soc={"company_id":"fenix","engine_id":"SOCAUD-001","status":"GREEN","profiles":[{"platform":"instagram","handle_or_url":"@fenix"}]}
        bmd={"company_id":"fenix","engine_id":"BMD-001","status":"GREEN","facts":{"products_services":["hipotecas"]}}
        out=bootstrap_social({"company_id":"fenix","inputs":[soc,bmd]})
        self.assertEqual(out["status"],"GREEN")
        self.assertFalse(out["publication_allowed"])
        self.assertFalse(out["paid_distribution_allowed"])

    def test_mktboot_budget_defaults_to_zero(self):
        bmd={"company_id":"aion","engine_id":"BMD-001","status":"GREEN","facts":{"target_customers":["pymes"]}}
        kw={"company_id":"aion","engine_id":"KW-001","status":"GREEN","keywords":[{"keyword":"automatizacion pymes","intent":"DISCOVERY"}]}
        out=bootstrap_marketing({"company_id":"aion","inputs":[bmd,kw]})
        self.assertEqual(out["status"],"GREEN")
        self.assertEqual(out["default_budget_eur"],0.0)
        self.assertFalse(out["paid_campaigns_allowed"])

    def test_engact_blocks_missing_required_evidence_and_never_activates_prod(self):
        out=activate_matrix({"company_id":"fenix","engine_evidence":[]})
        self.assertEqual(out["engine_id"],"ENGACT-001")
        self.assertEqual(out["status"],"PARTIAL")
        self.assertFalse(out["prod_activation_allowed"])
        self.assertGreater(len(out["blocked_required_engines"]),0)

    def test_engact_denies_cross_company_evidence(self):
        with self.assertRaisesRegex(ValueError,"cross-company"):
            activate_matrix({"company_id":"aion","engine_evidence":[{"company_id":"fenix","engine_id":"KW-001","status":"GREEN"}]})

    def test_crmboot_requires_existing_contract_inventory_before_any_migration(self):
        out=bootstrap_crm({"company_id":"fenix","existing_contract_refs":[],"entities":["lead"],"pipeline":["new"]})
        self.assertEqual(out["status"],"BLOCKED")
        self.assertEqual(out["reason"],"EXISTING_CONTRACT_INVENTORY_REQUIRED")
        self.assertFalse(out["migration_allowed"])
        self.assertFalse(out["prod_write_allowed"])

    def test_crmboot_wraps_existing_first_when_inventory_exists(self):
        out=bootstrap_crm({"company_id":"fenix","existing_contract_refs":["contract://crm-v1"],"entities":["lead","customer"],"pipeline":["new","won"]})
        self.assertEqual(out["status"],"GREEN")
        self.assertEqual(out["strategy"],"WRAP_EXISTING_FIRST")
        self.assertFalse(out["migration_allowed"])

    def test_appboot_is_preprod_only_and_preserves_existing_contracts(self):
        out=bootstrap_app({"company_id":"aion","existing_contract_refs":["contract://app-v1"],"roles":["admin"],"modules":["home"]})
        self.assertEqual(out["environment"],"PREPROD")
        self.assertEqual(out["status"],"GREEN")
        self.assertFalse(out["prod_deploy_allowed"])
        self.assertFalse(out["external_mutation_allowed"])

    def test_appboot_blocks_without_contract_inventory(self):
        out=bootstrap_app({"company_id":"aion","existing_contract_refs":[],"roles":[],"modules":[]})
        self.assertEqual(out["status"],"BLOCKED")
        self.assertEqual(out["reason"],"EXISTING_APP_CONTRACT_INVENTORY_REQUIRED")

    def test_autboot_creates_preprod_candidates_only(self):
        out=bootstrap_automations({"company_id":"fenix","existing_automation_refs":["make://existing"],"workflow_candidates":[{"trigger":"lead.created","action":"prepare_followup","external_side_effect":False}]})
        self.assertEqual(out["status"],"GREEN")
        self.assertFalse(out["prod_execution_allowed"])
        self.assertEqual(out["workflow_candidates"][0]["promotion_status"],"PREPROD_CANDIDATE")

    def test_training_bootstrap_cannot_train_on_prod_or_promote_directly(self):
        out=bootstrap_training({"company_id":"fenix","knowledge_sources":["kb://1"],"evaluation_cases":[{"input":"x","expected":"y"}]})
        self.assertEqual(out["status"],"GREEN")
        self.assertFalse(out["train_on_prod_data_allowed"])
        self.assertFalse(out["direct_prod_promotion_allowed"])

    def test_company_supervisor_scope_requires_scoped_green_evidence(self):
        required=("COMP-REG-001","COMP-ONB-001")
        evidence=[
            {"company_id":"fenix","engine_id":"COMP-REG-001","status":"GREEN","environment":"PREPROD","version":"1.0.0","evidence_hash":"sha256:a"},
            {"company_id":"fenix","engine_id":"COMP-ONB-001","status":"GREEN","environment":"PREPROD","version":"1.0.0","evidence_hash":"sha256:b"},
        ]
        out=create_supervisor_scope({"company_id":"fenix","environment":"PREPROD","version":"1.0.0","required_engines":required,"engine_evidence":evidence})
        self.assertEqual(out["engine_id"],"COMP-HLT-001")
        self.assertEqual(out["status"],"GREEN")
        self.assertFalse(out["prod_actions_allowed"])
        self.assertFalse(out["self_heal_prod_allowed"])

    def test_company_supervisor_scope_denies_cross_company_evidence(self):
        with self.assertRaisesRegex(ValueError,"cross-company"):
            create_supervisor_scope({"company_id":"aion","engine_evidence":[{"company_id":"fenix","engine_id":"COMP-REG-001","status":"GREEN"}]})

    def test_company_backup_rebuild_pack_requires_restore_rehearsal(self):
        backup={"company_id":"fenix","status":"GREEN","rehearsal":{"status":"GREEN"},"live_restore_performed":False}
        rebuild={"company_id":"fenix","status":"GREEN","environment":"PREPROD","rebuild_performed":True}
        out=create_backup_rebuild_pack({"company_id":"fenix","backup_evidence":backup,"rebuild_evidence":rebuild})
        self.assertEqual(out["engine_id"],"COMP-BKP-001")
        self.assertEqual(out["status"],"GREEN")
        self.assertFalse(out["live_restore_allowed"])
        self.assertFalse(out["prod_rebuild_allowed"])

    def test_preprod_readiness_is_fail_closed_and_never_authorizes_prod(self):
        evidence=[{"company_id":"fenix","engine_id":eid,"status":"GREEN"} for eid in ("COMP-HLT-001","COMP-BKP-001","QA-001","QAB-001","REG-001","TENANT-001","EVA-001","JDG-001","TWIN-001","RED-001","BCP-001","OBSERV-001","DR-001","RBLD-001")]
        out=evaluate_preprod_readiness({"company_id":"fenix","engine_evidence":evidence})
        self.assertTrue(out["preprod_ready"])
        self.assertEqual(out["status"],"GREEN")
        self.assertFalse(out["production_activation_allowed"])
        self.assertFalse(out["canary_live_traffic_allowed"])
        self.assertEqual(out["human_required_if_prod_requested"],"HIGH_RISK")
        self.assertIn("TWIN-001",out["required_evidence"])
        self.assertIn("RED-001",out["required_evidence"])
        self.assertIn("BCP-001",out["required_evidence"])

    def test_preprod_readiness_blocks_missing_gates(self):
        out=evaluate_preprod_readiness({"company_id":"aion","engine_evidence":[]})
        self.assertEqual(out["status"],"BLOCKED")
        self.assertFalse(out["preprod_ready"])
        self.assertGreater(len(out["missing_evidence"]),0)

    def test_production_activation_gate_blocks_when_preprod_is_not_green(self):
        readiness={"company_id":"fenix","engine_id":"COMP-DEP-001","status":"BLOCKED","preprod_ready":False,"evidence_hash":"sha256:x"}
        out=evaluate_production_activation({"company_id":"fenix","preprod_readiness":readiness})
        self.assertEqual(out["status"],"BLOCKED")
        self.assertFalse(out["production_activation_allowed"])
        self.assertFalse(out["live_traffic_allowed"])

    def test_production_activation_gate_emits_canonical_high_risk_exception(self):
        readiness={"company_id":"fenix","engine_id":"COMP-DEP-001","status":"GREEN","preprod_ready":True,"evidence_hash":"sha256:x"}
        out=evaluate_production_activation({"company_id":"fenix","preprod_readiness":readiness})
        self.assertEqual(out["status"],"HUMAN_REQUIRED")
        self.assertEqual(out["human_reason"],"HIGH_RISK")
        self.assertFalse(out["production_activation_allowed"])
        self.assertFalse(out["external_mutation_allowed"])

    def test_production_activation_gate_denies_cross_company_readiness(self):
        readiness={"company_id":"fenix","engine_id":"COMP-DEP-001","status":"GREEN","preprod_ready":True}
        with self.assertRaisesRegex(ValueError,"cross-company"):
            evaluate_production_activation({"company_id":"aion","preprod_readiness":readiness})

if __name__=="__main__": unittest.main()
