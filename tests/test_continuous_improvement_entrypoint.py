import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ImprovementEntrypointTests(unittest.TestCase):
    def test_entrypoint_runs_and_waits_without_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = root / "companies.json"
            cfg.write_text(json.dumps([{
                "company_id":"aion","legal_name":"AION","autonomy_profile":"AUTONOMOUS_VENTURE",
                "environment":"LAB","version":"1.0.0","interval_hours":24,"enabled":True
            }]), encoding="utf-8")
            env = os.environ.copy()
            env["CEREBRO_IMPROVEMENT_STATE_ROOT"] = str(root / "state")
            env["CEREBRO_IMPROVEMENT_COMPANIES"] = str(cfg)
            env["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"] = str(root / "evidence")
            env["CEREBRO_IMPROVEMENT_NOW"] = "2026-09-19T12:00:00+00:00"
            proc = subprocess.run(
                [sys.executable, str(ROOT/"cerebro-os/jobs/continuous_improvement_entrypoint.py")],
                cwd=ROOT, env=env, text=True, capture_output=True, check=True,
            )
            out = json.loads(proc.stdout.strip().splitlines()[-1])
            self.assertEqual(out["status"], "WAITING")
            self.assertEqual(out["companies"], 1)
            self.assertEqual(out["waiting"], 1)

    def test_entrypoint_runs_green_with_complete_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = root/"companies.json"
            cfg.write_text(json.dumps([{
                "company_id":"aion","legal_name":"AION","autonomy_profile":"AUTONOMOUS_VENTURE",
                "environment":"LAB","version":"1.0.0","interval_hours":24,"enabled":True
            }]), encoding="utf-8")
            evidence = root/"evidence"; evidence.mkdir()
            stages = ("OBSERVE","MEASURE","DETECT","PROPOSE","LAB","TEST","EVALUATE","TRIBUNAL","OLD_VS_NEW","CANARY","PROMOTE_OR_ROLLBACK","LEARN")
            (evidence/"aion.json").write_text(json.dumps({s:{"status":"GREEN","evidence_ref":f"e://{s}"} for s in stages}), encoding="utf-8")
            env=os.environ.copy()
            env["CEREBRO_IMPROVEMENT_STATE_ROOT"]=str(root/"state")
            env["CEREBRO_IMPROVEMENT_COMPANIES"]=str(cfg)
            env["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(evidence)
            env["CEREBRO_IMPROVEMENT_NOW"]="2026-09-19T12:00:00+00:00"
            proc=subprocess.run([sys.executable,str(ROOT/"cerebro-os/jobs/continuous_improvement_entrypoint.py")],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
            out=json.loads(proc.stdout.strip().splitlines()[-1])
            self.assertEqual(out["status"],"GREEN")
            self.assertEqual(out["green"],1)


if __name__=="__main__":
    unittest.main()
