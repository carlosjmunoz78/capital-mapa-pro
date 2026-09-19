import hashlib,json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"cerebro-os"))
from jobs.verify_knowledge_revalidation_evidence import run as verify_run
from jobs.build_knowledge_update_candidates import run as update_run

def eh(st,src,obs,val,ch,conf):
    return hashlib.sha256("|".join([st,src,obs,val,ch,f"{conf:.6f}"]).encode()).hexdigest()

class ProvenanceUpdaterTests(unittest.TestCase):
    def _env(self,root):
        os.environ["CEREBRO_REVALIDATION_ROOT"]=str(root/"queue")
        os.environ["CEREBRO_REVALIDATION_EVIDENCE_ROOT"]=str(root/"evidence")
        os.environ["CEREBRO_PROVENANCE_VALIDATION_ROOT"]=str(root/"prov")
        os.environ["CEREBRO_KNOWLEDGE_UPDATE_CANDIDATE_ROOT"]=str(root/"upd")
    def test_green_provenance_builds_candidate_only_update(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/"queue").mkdir(); (root/"evidence"/"aion").mkdir(parents=True)
            (root/"queue"/"aion.json").write_text(json.dumps({"company_id":"aion","items":[{"company_id":"aion","knowledge_id":"k1","kind":"KNOWLEDGE","human_review_required":False}]}),encoding="utf-8")
            st="LIVE_SOURCE"; src="https://example.com/source"; obs="2026-09-19T00:00:00+00:00"; val="validator-v1"; ch="abc123"; conf=0.93
            (root/"evidence"/"aion"/"k1.json").write_text(json.dumps({"company_id":"aion","knowledge_id":"k1","source_type":st,"source_uri":src,"observed_at":obs,"validated_by":val,"content_hash":ch,"confidence":conf,"evidence_hash":eh(st,src,obs,val,ch,conf)}),encoding="utf-8")
            old=os.environ.copy(); self._env(root)
            try:
                verify_run(); update_run()
            finally: os.environ.clear(); os.environ.update(old)
            p=json.loads((root/"upd"/"aion.json").read_text())
            self.assertEqual(len(p["candidates"]),1); c=p["candidates"][0]
            self.assertEqual(c["engine_id"],"UPD-001")
            self.assertEqual(c["source_type"],"LIVE_SOURCE")
            self.assertTrue(c["provenance_id"].startswith("prv-"))
            self.assertEqual(c["status"],"CANDIDATE_ONLY")
            self.assertTrue(c["append_only"]); self.assertTrue(c["history_preserved"])
            self.assertFalse(c["auto_apply_allowed"]); self.assertFalse(c["external_mutation_allowed"]); self.assertFalse(c["delete_allowed"])
    def test_bad_hash_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/"queue").mkdir(); (root/"evidence"/"aion").mkdir(parents=True)
            (root/"queue"/"aion.json").write_text(json.dumps({"company_id":"aion","items":[{"company_id":"aion","knowledge_id":"k1","kind":"KNOWLEDGE"}]}),encoding="utf-8")
            (root/"evidence"/"aion"/"k1.json").write_text(json.dumps({"company_id":"aion","knowledge_id":"k1","source_uri":"x","observed_at":"2026-09-19","validated_by":"v","content_hash":"h","confidence":0.9,"evidence_hash":"bad"}),encoding="utf-8")
            old=os.environ.copy(); self._env(root)
            try: verify_run(); update_run()
            finally: os.environ.clear(); os.environ.update(old)
            prov=json.loads((root/"prov"/"aion.json").read_text()); self.assertEqual(prov["results"][0]["status"],"BLOCKED")
            upd=json.loads((root/"upd"/"aion.json").read_text()); self.assertEqual(upd["candidates"],[])
    def test_policy_never_becomes_auto_update_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/"queue").mkdir(); (root/"evidence"/"aion").mkdir(parents=True)
            (root/"queue"/"aion.json").write_text(json.dumps({"company_id":"aion","items":[{"company_id":"aion","knowledge_id":"p1","kind":"POLICY","human_review_required":True}]}),encoding="utf-8")
            st="STABLE_KNOWLEDGE"; src="x"; obs="2026-09-19"; val="v"; ch="h"; conf=1.0
            (root/"evidence"/"aion"/"p1.json").write_text(json.dumps({"company_id":"aion","knowledge_id":"p1","source_type":st,"source_uri":src,"observed_at":obs,"validated_by":val,"content_hash":ch,"confidence":conf,"evidence_hash":eh(st,src,obs,val,ch,conf)}),encoding="utf-8")
            old=os.environ.copy(); self._env(root)
            try: verify_run(); update_run()
            finally: os.environ.clear(); os.environ.update(old)
            prov=json.loads((root/"prov"/"aion.json").read_text()); self.assertEqual(prov["results"][0]["status"],"HUMAN_REQUIRED")
            upd=json.loads((root/"upd"/"aion.json").read_text()); self.assertEqual(upd["candidates"],[])
if __name__=="__main__": unittest.main()
