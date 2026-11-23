"""CP81: physically exercise fencing in independent subprocesses against the same LAB SQLite file."""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runtime.onboarding_queue import OnboardingQueue

CHILD=r"""
import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from runtime.onboarding_queue import OnboardingQueue
_,root,db,op,*args=sys.argv
q=OnboardingQueue(db)
try:
    if op=="claim":
        item=q.claim(now_epoch=int(args[0]),lease_seconds=int(args[1]))
        print(json.dumps({"claimed":item is not None,"attempts":item.attempts if item else None}))
    elif op=="complete":
        q.complete(request_id=args[0],status="WAITING",result={"company_id":"fenix"},
                   now_epoch=int(args[1]),claim_attempts=int(args[2]))
        print(json.dumps({"status":"COMPLETED_BY_CURRENT_CLAIM"}))
    else:raise ValueError("invalid test operation")
except Exception as e:
    print(json.dumps({"error":type(e).__name__,"message":str(e)}))
"""

class OnboardingTwoProcessCP81(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Path(self.tmp.name)/"q.sqlite3"
        self.queue=OnboardingQueue(self.db)
        self.queue.enqueue(request_id="r1",company_id="fenix",version="1.0.0",
                           payload={"company_id":"fenix","environment":"LAB"},now_epoch=100)
    def tearDown(self):
        self.tmp.cleanup()
    def command(self,op,*args):
        return [sys.executable,"-c",CHILD,str(ROOT),str(self.db),op,*(str(x) for x in args)]
    def run_child(self,op,*args):
        p=subprocess.run(self.command(op,*args),text=True,capture_output=True,timeout=20)
        self.assertEqual(p.returncode,0,p.stderr)
        return json.loads(p.stdout.strip().splitlines()[-1])

    def test_expired_claim_reclaimed_in_second_process_fences_old_writer(self):
        a=self.run_child("claim",101,5)
        b=self.run_child("claim",107,5)
        self.assertEqual(a,{"claimed":True,"attempts":1})
        self.assertEqual(b,{"claimed":True,"attempts":2})
        old=self.run_child("complete","r1",108,a["attempts"])
        self.assertEqual(old["error"],"PermissionError")
        self.assertIn("stale",old["message"])
        self.assertEqual(self.queue.get("r1").status,"IN_PROGRESS")
        good=self.run_child("complete","r1",108,b["attempts"])
        self.assertEqual(good,{"status":"COMPLETED_BY_CURRENT_CLAIM"})
        reopened=OnboardingQueue(self.db).get("r1")
        self.assertEqual(reopened.status,"WAITING")
        self.assertEqual(reopened.attempts,2)
        self.assertEqual(reopened.last_result["company_id"],"fenix")

    def test_two_independent_processes_cannot_claim_same_unexpired_job(self):
        workers=[
            subprocess.Popen(self.command("claim",101,300),text=True,
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            for _ in range(2)
        ]
        output=[]
        for p in workers:
            out,err=p.communicate(timeout=20)
            self.assertEqual(p.returncode,0,err)
            output.append(json.loads(out.strip().splitlines()[-1]))
        self.assertEqual(sum(1 for x in output if x["claimed"]),1,output)
        self.assertEqual(self.queue.get("r1").attempts,1)
        self.assertEqual(self.queue.get("r1").status,"IN_PROGRESS")

if __name__=="__main__":
    unittest.main()
