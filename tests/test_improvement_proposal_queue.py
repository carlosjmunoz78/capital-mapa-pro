import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

from learning.improvement_proposal_queue import ProposalQueue, ProposalRecord
from jobs.ingest_improvement_proposals import ingest


class ProposalQueueTests(unittest.TestCase):
    def test_queue_deduplicates_same_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            q=ProposalQueue(Path(td)/"q.db")
            r=ProposalRecord("fenix","p1","business","WEB_SEO","LAB","1.0.0","x","e://same","LAB_DIAGNOSTIC_ONLY",False,0.0,"P1","WAITING_TEST")
            fp1=q.upsert(r)
            fp2=q.upsert(ProposalRecord(**{**r.__dict__,"proposal_id":"p2"}))
            self.assertEqual(fp1,fp2)
            self.assertEqual(q.count(),1)
            q.close()

    def test_priority_order_is_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            q=ProposalQueue(Path(td)/"q.db")
            q.upsert(ProposalRecord("a","p2","x","CONTENT","LAB","1.0.0","c","e://2","LAB_DIAGNOSTIC_ONLY",False,0.0,"P2","WAITING_TEST"))
            q.upsert(ProposalRecord("a","p0","x","SERVICE_HEALTH","LAB","1.0.0","s","e://0","LAB_DIAGNOSTIC_ONLY",False,0.0,"P0","WAITING_TEST"))
            self.assertEqual(tuple(x.priority for x in q.list_open()),("P0","P2"))
            q.close()

    def test_external_mutation_fails_closed(self):
        with self.assertRaises(ValueError):
            ProposalRecord("a","p","x","WEB_SEO","LAB","1.0.0","s","e://x","LAB_DIAGNOSTIC_ONLY",True,0.0).validate()

    def test_ingest_generated_files(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); proposals=root/"proposals"; proposals.mkdir()
            (proposals/"fenix.json").write_text(json.dumps({
                "company_id":"fenix",
                "proposals":[{
                    "company_id":"fenix","proposal_id":"fenix:business:1","source_key":"business",
                    "domain":"WEB_SEO","environment":"LAB","version":"1.0.0",
                    "summary":"seo issue","evidence_ref":"e://seo","action":"LAB_DIAGNOSTIC_ONLY",
                    "external_mutation_allowed":False,"cost_limit_eur":0.0
                }]
            }),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_PROPOSALS_ROOT"]=str(proposals)
            os.environ["CEREBRO_IMPROVEMENT_PROPOSAL_QUEUE"]=str(root/"queue.db")
            try:
                out=ingest()
            finally:
                os.environ.clear(); os.environ.update(old)
            self.assertEqual(out["inserted"],1)
            self.assertEqual(out["queued"],1)
            self.assertEqual(out["priorities"]["P1"],1)


if __name__=="__main__": unittest.main()
