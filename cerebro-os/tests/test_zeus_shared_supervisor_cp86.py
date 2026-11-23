import pathlib
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class ZeusSharedSupervisorCP86(unittest.TestCase):
    def test_node_supervisor_contract_and_idempotency(self):
        if not shutil.which("node"):
            self.skipTest("Node runtime not installed")
        test_file=ROOT/"supervisor"/"zeus_shared_lab_worker.test.mjs"
        p=subprocess.run(["node","--test","--test-reporter=tap",str(test_file)],capture_output=True,text=True,timeout=50)
        self.assertEqual(p.returncode,0,p.stdout+"\n"+p.stderr)
        self.assertIn("# fail 0",p.stdout)
        self.assertIn("# tests 12",p.stdout)
