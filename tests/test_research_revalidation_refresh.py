import json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"cerebro-os"))
from jobs.refresh_knowledge_revalidation_evidence import run,_public_http_url

class FakeResponse:
    def __init__(self,data): self.data=data
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self,n=-1): return self.data[:n] if n>=0 else self.data

class ResearchRefreshTests(unittest.TestCase):
    def test_public_source_fetch_builds_provenance_packet(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); q=root/"q"; ev=root/"ev"; s=root/"s"; q.mkdir()
            (q/"aion.json").write_text(json.dumps({"company_id":"aion","items":[{
                "company_id":"aion","knowledge_id":"k1","source_type":"LIVE_SOURCE",
                "source_uri":"https://example.com/rule","confidence":0.91
            }]}),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_REVALIDATION_ROOT"]=str(q); os.environ["CEREBRO_REVALIDATION_EVIDENCE_ROOT"]=str(ev); os.environ["CEREBRO_RESEARCH_REFRESH_ROOT"]=str(s); os.environ["CEREBRO_REVALIDATION_NOW"]="2026-09-19T00:00:00+00:00"
            try:
                with patch("urllib.request.urlopen",return_value=FakeResponse(b"verified content")):
                    run()
            finally: os.environ.clear(); os.environ.update(old)
            p=json.loads((ev/"aion"/"k1.json").read_text())
            self.assertEqual(p["engine_id"],"RSH-001")
            self.assertEqual(p["source_type"],"LIVE_SOURCE")
            self.assertTrue(p["evidence_hash"])
            self.assertTrue(p["read_only_fetch"])
            self.assertFalse(p["external_mutation_allowed"]); self.assertFalse(p["auto_promote_allowed"])
    def test_missing_source_context_waits_without_inventing(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); q=root/"q"; ev=root/"ev"; s=root/"s"; q.mkdir()
            (q/"aion.json").write_text(json.dumps({"company_id":"aion","items":[{"company_id":"aion","knowledge_id":"k1","source_type":"","source_uri":"","confidence":0.9}]}),encoding="utf-8")
            old=os.environ.copy(); os.environ["CEREBRO_REVALIDATION_ROOT"]=str(q); os.environ["CEREBRO_REVALIDATION_EVIDENCE_ROOT"]=str(ev); os.environ["CEREBRO_RESEARCH_REFRESH_ROOT"]=str(s)
            try: run()
            finally: os.environ.clear(); os.environ.update(old)
            p=json.loads((s/"aion.json").read_text()); self.assertEqual(p["results"][0]["status"],"WAITING_DISCOVERY")
            self.assertFalse((ev/"aion"/"k1.json").exists())
    def test_private_and_local_urls_are_denied(self):
        self.assertFalse(_public_http_url("http://127.0.0.1/x"))
        self.assertFalse(_public_http_url("http://10.0.0.1/x"))
        self.assertFalse(_public_http_url("http://localhost/x"))
        self.assertTrue(_public_http_url("https://example.com/x"))
if __name__=="__main__": unittest.main()
