import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"cerebro-os"))
from jobs.bootstrap_runtime_knowledge_inventory import run

class KnowledgeInventoryBootstrapTests(unittest.TestCase):
    def test_checked_business_page_becomes_real_inventory_record(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); ev=root/"ev"; inv=root/"inv"; ev.mkdir()
            (ev/"fenix.business.json").write_text(json.dumps({
                "company_id":"fenix","checked":True,"confidence":0.95,
                "facts":{"pages":[{
                    "checked":True,"url":"https://fenixcapital.es/",
                    "evidence_ref":"https://fenixcapital.es/#sha256=abc",
                    "confidence":0.95,"facts":{"content_hash":"abc"}
                }]}
            }),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(ev)
            os.environ["CEREBRO_KNOWLEDGE_INVENTORY_ROOT"]=str(inv)
            os.environ["CEREBRO_KNOWLEDGE_NOW"]="2026-09-19T00:00:00+00:00"
            try: run()
            finally: os.environ.clear(); os.environ.update(old)
            p=json.loads((inv/"fenix.json").read_text())
            self.assertEqual(len(p),1)
            r=p[0]
            self.assertEqual(r["company_id"],"fenix")
            self.assertEqual(r["source_type"],"LIVE_SOURCE")
            self.assertEqual(r["verified_at"],"2026-09-19T00:00:00+00:00")
            self.assertTrue(r["source_available"])
            self.assertTrue(r["provenance_id"].startswith("prv-"))
            self.assertFalse(r["external_mutation_allowed"])
            self.assertFalse(r["delete_allowed"])

    def test_failed_refresh_preserves_prior_verified_at_and_marks_unavailable(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); ev=root/"ev"; inv=root/"inv"; ev.mkdir(); inv.mkdir()
            prior=[{
                "company_id":"fenix","knowledge_id":"official-web:x","environment":"LAB","version":"1.0.0",
                "kind":"PUBLIC_SOURCE_POINTER","state":"ACTIVE","provenance_id":"prv-old","source_type":"LIVE_SOURCE",
                "source_uri":"https://fenixcapital.es/","verified_at":"2026-09-10T00:00:00+00:00",
                "ttl_days":7,"confidence":0.95,"source_available":True,"content_hash":"old"
            }]
            (inv/"fenix.json").write_text(json.dumps(prior),encoding="utf-8")
            (ev/"fenix.business.json").write_text(json.dumps({
                "company_id":"fenix","checked":False,"confidence":0.0,
                "facts":{"pages":[{"checked":False,"url":"https://fenixcapital.es/","facts":{}}]}
            }),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(ev)
            os.environ["CEREBRO_KNOWLEDGE_INVENTORY_ROOT"]=str(inv)
            os.environ["CEREBRO_KNOWLEDGE_NOW"]="2026-09-19T00:00:00+00:00"
            try: run()
            finally: os.environ.clear(); os.environ.update(old)
            p=json.loads((inv/"fenix.json").read_text())[0]
            self.assertEqual(p["verified_at"],"2026-09-10T00:00:00+00:00")
            self.assertFalse(p["source_available"])

    def test_cross_company_prior_inventory_denied(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); ev=root/"ev"; inv=root/"inv"; ev.mkdir(); inv.mkdir()
            (inv/"fenix.json").write_text(json.dumps([{"company_id":"aion","source_uri":"x"}]),encoding="utf-8")
            (ev/"fenix.business.json").write_text(json.dumps({"company_id":"fenix","checked":False,"facts":{}}),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(ev)
            os.environ["CEREBRO_KNOWLEDGE_INVENTORY_ROOT"]=str(inv)
            try:
                with self.assertRaisesRegex(ValueError,"cross-company"):
                    run()
            finally: os.environ.clear(); os.environ.update(old)
if __name__=="__main__": unittest.main()
