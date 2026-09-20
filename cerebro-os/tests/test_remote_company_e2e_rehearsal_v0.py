import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from jobs.run_remote_company_rehearsal import run_remote_company_rehearsal

class RemoteCompanyE2ERehearsalTests(unittest.TestCase):
    def _context(self):
        facts={k:[k] for k in ("products_services","target_customers","geography","channels","revenue_model","objectives","constraints")}
        return {
          "company_profile":{"legal_name":"Fenix Rehearsal","evidence_ref":"doc://company"},
          "access_requirements":[{"capability":"crm","purpose":"sales","provider":"existing","required":True}],
          "existing_accounts":[],"existing_connectors":[],"session_observations":[],"domains":[],
          "business_facts":facts,"business_evidence":[{"ref":"e://bmd"}],
          "process_candidates":[{"name":"Lead intake","inputs":["lead"],"outputs":["case"],"owner":"ops","evidence_refs":["e://proc"]}],
          "source_texts":["asesoramiento hipotecario cordoba"],"seed_keywords":["hipoteca cordoba"],
          "geographies":["cordoba"],"social_profiles":[],"local_listings":[],
          "competitors":[{"name":"Comp A","domain":"a.example","signals":["same service"],"evidence_refs":["e://comp"]}],
        }

    def test_console_queue_worker_prefill_gap_view_work_end_to_end_without_pc(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=run_remote_company_rehearsal(
                company_id="fenix",version="1.0.0",context=self._context(),
                workdir=Path(tmp),now_epoch_provider=lambda:100,
            )
        self.assertEqual(out["status"],"GREEN")
        self.assertEqual(out["queue_status"],"WAITING")
        self.assertEqual(out["current_phase"],"MINIMUM_ACCESSES")
        self.assertGreater(out["remote_prefill_green_count"],0)
        self.assertEqual(out["remote_gap_classification"],"LOCAL_ACCESS_DEPENDENT")
        self.assertTrue(out["local_pc_required"])
        self.assertFalse(out["computer_use_performed"])
        self.assertFalse(out["browser_bridge_used"])
        self.assertFalse(out["external_mutation_performed"])
        self.assertFalse(out["production_activation_allowed"])
        self.assertEqual(out["cost_eur"],0.0)
        self.assertEqual(out["console_audit_count"],1)
        self.assertEqual(out["console_history_count"],1)

    def test_cross_company_context_is_denied(self):
        context=self._context()
        context["company_id"]="aion"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,"cross-company"):
                run_remote_company_rehearsal(
                    company_id="fenix",version="1.0.0",context=context,
                    workdir=Path(tmp),now_epoch_provider=lambda:100,
                )

if __name__=="__main__":
    unittest.main()
