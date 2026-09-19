import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"cerebro-os"))
from jobs.build_knowledge_revalidation_queue import run

class RevalidationQueueTests(unittest.TestCase):
    def test_priority_and_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=root/"src"; out=root/"out"; src.mkdir()
            (src/"aion.json").write_text(json.dumps({
                "company_id":"aion","decisions":[
                    {"company_id":"aion","knowledge_id":"k1","kind":"KNOWLEDGE","review_required":True,"human_review_required":False,"reasons":["TTL_EXPIRED"]},
                    {"company_id":"aion","knowledge_id":"p1","kind":"POLICY","review_required":True,"human_review_required":True,"reasons":["CONTRADICTORY_EVIDENCE","PROTECTED_KIND_REQUIRES_HUMAN_OR_POLICY_REVIEW"]}
                ]}),encoding="utf-8")
            old=os.environ.copy(); os.environ["CEREBRO_OBSOLESCENCE_ROOT"]=str(src); os.environ["CEREBRO_REVALIDATION_ROOT"]=str(out)
            try: run()
            finally: os.environ.clear(); os.environ.update(old)
            p=json.loads((out/"aion.json").read_text())
            self.assertEqual(p["items"][0]["knowledge_id"],"p1")
            self.assertTrue(p["items"][0]["human_review_required"])
            self.assertFalse(p["delete_allowed"]); self.assertFalse(p["external_mutation_allowed"])
            self.assertIn("evidence_hash",p["items"][0]["required_evidence"])
    def test_cross_company_denied(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=root/"src"; out=root/"out"; src.mkdir()
            (src/"x.json").write_text(json.dumps({"company_id":"aion","decisions":[{"company_id":"fenix","knowledge_id":"k","review_required":True}]}),encoding="utf-8")
            old=os.environ.copy(); os.environ["CEREBRO_OBSOLESCENCE_ROOT"]=str(src); os.environ["CEREBRO_REVALIDATION_ROOT"]=str(out)
            try:
                with self.assertRaisesRegex(ValueError,"cross-company"): run()
            finally: os.environ.clear(); os.environ.update(old)
if __name__=="__main__": unittest.main()
