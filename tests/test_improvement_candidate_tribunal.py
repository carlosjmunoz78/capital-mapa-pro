import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

from jobs.generate_improvement_candidate_tribunal import generate


class CandidateTribunalTests(unittest.TestCase):
    def test_deterministic_safe_spec_gets_lab_tribunal_green(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); candidates=root/"candidates"; evidence=root/"evidence"
            candidates.mkdir(); evidence.mkdir()
            (candidates/"aion.json").write_text(json.dumps({
                "company_id":"aion",
                "candidates":[{
                    "company_id":"aion","proposal_id":"p","domain":"WEB_SEO",
                    "mode":"DETERMINISTIC_PATCH_SPEC","target":"https://example.com/",
                    "change_spec":{"operation":"SET_CANONICAL","value":"https://example.com/"},
                    "evidence_ref":"e://candidate","external_mutation_allowed":False,"cost_eur":0.0
                }]
            }),encoding="utf-8")
            (evidence/"aion.test.json").write_text(json.dumps({
                "company_id":"aion","stage":"TEST","status":"GREEN",
                "test_scope":"CANDIDATE_CONTRACT_ONLY","external_mutation_allowed":False
            }),encoding="utf-8")
            (evidence/"aion.evaluate.json").write_text(json.dumps({
                "company_id":"aion","stage":"EVALUATE","status":"GREEN",
                "evaluation_scope":"SPEC_SAFETY_ONLY","outcome_effect_verified":False,
                "external_mutation_allowed":False
            }),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_CANDIDATES_ROOT"]=str(candidates)
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(evidence)
            try: generate()
            finally: os.environ.clear(); os.environ.update(old)
            payload=json.loads((evidence/"aion.tribunal.json").read_text())
            self.assertEqual(payload["status"],"GREEN")
            self.assertEqual(payload["tribunal_scope"],"LAB_SPEC_SAFETY_ONLY")
            self.assertFalse(payload["production_approval"])
            self.assertFalse(payload["external_mutation_allowed"])
            self.assertEqual(payload["missing_gates"],[])

    def test_non_deterministic_candidate_waits(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); candidates=root/"candidates"; evidence=root/"evidence"
            candidates.mkdir(); evidence.mkdir()
            (candidates/"fenix.json").write_text(json.dumps({
                "company_id":"fenix",
                "candidates":[{
                    "company_id":"fenix","proposal_id":"p","domain":"CONTENT",
                    "mode":"RESEARCH_REQUIRED","target":"e://content",
                    "change_spec":{"operation":"RESEARCH_AND_PROPOSE"},
                    "evidence_ref":"e://candidate","external_mutation_allowed":False,"cost_eur":0.0
                }]
            }),encoding="utf-8")
            (evidence/"fenix.evaluate.json").write_text(json.dumps({
                "company_id":"fenix","stage":"EVALUATE","status":"WAITING",
                "evaluation_scope":"SPEC_SAFETY_ONLY","outcome_effect_verified":False,
                "external_mutation_allowed":False
            }),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_CANDIDATES_ROOT"]=str(candidates)
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(evidence)
            try: generate()
            finally: os.environ.clear(); os.environ.update(old)
            payload=json.loads((evidence/"fenix.tribunal.json").read_text())
            self.assertEqual(payload["status"],"WAITING")
            self.assertTrue(payload["missing_gates"])

    def test_runtime_advances_through_tribunal_then_waits_at_old_vs_new(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); evidence=root/"evidence"; evidence.mkdir()
            config=root/"companies.json"
            config.write_text(json.dumps([{
                "company_id":"aion","legal_name":"AION",
                "autonomy_profile":"AUTONOMOUS_VENTURE","environment":"LAB",
                "version":"1.0.0","interval_hours":24,"enabled":True
            }]),encoding="utf-8")
            (evidence/"aion.observations.json").write_text(json.dumps({
                "company_id":"aion","checked":True,"source":"MULTI_SOURCE",
                "evidence_ref":"e://proposal","status":"PROPOSAL_READY","confidence":1.0,
                "summary":"candidate found","facts":{}
            }),encoding="utf-8")
            for stage in ("LAB","TEST","EVALUATE","TRIBUNAL"):
                extra={}
                if stage=="TRIBUNAL":
                    extra={"production_approval":False}
                (evidence/f"aion.{stage.lower()}.json").write_text(json.dumps({
                    "company_id":"aion","stage":stage,"status":"GREEN",
                    "evidence_ref":f"e://{stage.lower()}","external_mutation_allowed":False,**extra
                }),encoding="utf-8")
            env=os.environ.copy()
            env["CEREBRO_IMPROVEMENT_STATE_ROOT"]=str(root/"state")
            env["CEREBRO_IMPROVEMENT_COMPANIES"]=str(config)
            env["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(evidence)
            env["CEREBRO_IMPROVEMENT_NOW"]="2026-09-19T12:00:00+00:00"
            proc=subprocess.run([sys.executable,str(ROOT/"cerebro-os/jobs/continuous_improvement_entrypoint.py")],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
            out=json.loads(proc.stdout.strip().splitlines()[-1])
            self.assertEqual(out["status"],"WAITING")
            self.assertEqual(out["waiting"],1)


if __name__=="__main__":
    unittest.main()
