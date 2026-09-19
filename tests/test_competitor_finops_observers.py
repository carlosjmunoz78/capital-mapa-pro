import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))
sys.path.insert(0,str(ROOT/"cerebro-os/discovery"))

import jobs.collect_competitor_observations as competitors
from jobs.collect_finops_observations import _duration
from jobs.aggregate_improvement_observations import aggregate


class CompetitorFinopsTests(unittest.TestCase):
    def test_competitor_second_run_detects_change(self):
        url="https://example.com/competitor"
        first=b"<html><head><title>Competitor mortgage</title><link rel='canonical' href='https://example.com/competitor'></head><body><h1>Mortgage broker</h1></body></html>"
        second=b"<html><head><title>Competitor mortgage updated</title><link rel='canonical' href='https://example.com/competitor'></head><body><h1>Mortgage broker</h1></body></html>"
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); evidence=root/"e"; state=root/"s"; cfg=root/"c.json"
            cfg.write_text(json.dumps([{"company_id":"fenix","enabled":True,"competitors":[{"competitor_id":"x","url":url}]}]))
            old=os.environ.copy(); old_fetch=competitors._fetch
            os.environ["CEREBRO_IMPROVEMENT_COMPETITOR_SOURCES"]=str(cfg)
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(evidence)
            os.environ["CEREBRO_IMPROVEMENT_OBSERVATION_STATE_ROOT"]=str(state)
            try:
                competitors._fetch=lambda _:first; competitors.collect()
                competitors._fetch=lambda _:second; competitors.collect()
            finally:
                competitors._fetch=old_fetch; os.environ.clear(); os.environ.update(old)
            payload=json.loads((evidence/"fenix.competitors.json").read_text())
            self.assertEqual(payload["status"],"PROPOSAL_READY")
            self.assertEqual(payload["facts"]["changed"],1)

    def test_duration_uses_run_timestamps(self):
        run={"created_at":"2026-09-19T10:00:00Z","updated_at":"2026-09-19T10:02:30Z"}
        self.assertEqual(_duration(run),150.0)

    def test_aggregate_includes_finops_proposal(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); cfg=root/"companies.json"
            cfg.write_text(json.dumps([{"company_id":"aion","enabled":True}]))
            (root/"aion.observations.json").write_text(json.dumps({"company_id":"aion","checked":True,"source":"TECH","evidence_ref":"e://tech","status":"NO_CHANGE","confidence":1.0,"summary":"ok"}))
            (root/"aion.finops.json").write_text(json.dumps({"company_id":"aion","checked":True,"source":"FINOPS","evidence_ref":"e://fin","status":"PROPOSAL_READY","confidence":1.0,"summary":"slow"}))
            old=os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(root)
            os.environ["CEREBRO_IMPROVEMENT_COMPANIES"]=str(cfg)
            try: aggregate()
            finally: os.environ.clear(); os.environ.update(old)
            out=json.loads((root/"aion.observations.json").read_text())
            self.assertEqual(out["status"],"PROPOSAL_READY")


if __name__=="__main__": unittest.main()
