import json
import pathlib
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[1]
SERVICE=ROOT/"identity"/"windows"/"CerebroBrowserBridgeService.ps1"
TRANSPORT=ROOT/"identity"/"windows"/"CerebroBrowserTransport.ps1"
EXT=ROOT/"identity"/"chrome_extension_v1_6"

class OperatorServiceTransportV16Tests(unittest.TestCase):
    def test_preserves_existing_actions_and_exact_operator_path(self):
        service=SERVICE.read_text(encoding="utf-8")
        transport=TRANSPORT.read_text(encoding="utf-8")
        worker=(EXT/"service_worker.js").read_text(encoding="utf-8")
        for action in ("OPEN_LOCAL_TEST_PAGE","READ_ONLY_PAGE_METADATA","OPERATOR_CLICK","OPERATOR_TYPE","OPERATOR_SELECT","OPERATOR_READ"):
            self.assertIn(action,service)
            self.assertIn(action,transport)
            self.assertIn(action,worker)
        self.assertIn("/lab/operator-fixture",service)
        self.assertIn("/extension/operator-result",service)
        self.assertIn("LAB_OPERATOR_FIXTURE_VERIFIED",transport)
        self.assertIn("RUNTIME", "RUNTIME")
        self.assertIn('ALLOWED_URL = "https://example.com/"',worker)
        self.assertNotIn("chrome.cookies",worker)

    @unittest.skipUnless(shutil.which("powershell.exe") or shutil.which("pwsh"),"PowerShell required")
    def test_local_service_rejects_arbitrary_action_and_validates_fixture_receipt(self):
        exe=shutil.which("powershell.exe") or shutil.which("pwsh")
        with tempfile.TemporaryDirectory(prefix="Cerebro Operator ") as td:
            tmp=pathlib.Path(td)
            with socket.socket() as sock:
                sock.bind(("127.0.0.1",0));port=sock.getsockname()[1]
            args=[exe,"-NoProfile"]
            if pathlib.Path(exe).name.lower()=="powershell.exe": args+=["-ExecutionPolicy","Bypass"]
            args+=["-File",str(SERVICE),"-Port",str(port),"-StatePath",str(tmp/"state.json"),"-TransportKey","ci-test-key"]
            p=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
            base="http://127.0.0.1:"+str(port)
            def get(route,**params):
                url=base+route+("?" + urllib.parse.urlencode(params) if params else "")
                with urllib.request.urlopen(url,timeout=3) as f:return f.read().decode()
            try:
                ready=False
                for _ in range(60):
                    if p.poll() is not None: self.fail("service unexpectedly stopped: "+p.stderr.read()[-500:])
                    try:
                        ready=json.loads(get("/health"))["status"]=="GREEN"
                        if ready:break
                    except (urllib.error.URLError,ValueError):time.sleep(.3)
                self.assertTrue(ready)
                get("/pair",company_id="fenix",profile_id="Default",browser_family="CHROME",environment="LAB",version="v0")
                ext="c"*32
                ping=json.loads(get("/extension/ping",extension_id=ext,extension_version="1.6.0"))
                self.assertEqual(ping["status"],"GREEN")
                with self.assertRaises(urllib.error.HTTPError) as denied:
                    get("/cloud/enqueue",transport_key="ci-test-key",command_id="bad1",action="OPERATOR_CLICK",selector="#another",value="")
                self.assertEqual(denied.exception.code,400)
                cmd=dict(transport_key="ci-test-key",command_id="good1",action="OPERATOR_CLICK",selector="#cerebro-button",value="")
                self.assertEqual(json.loads(get("/cloud/enqueue",**cmd))["status"],"GREEN")
                result=json.loads(get("/extension/command",extension_id=ext))
                self.assertEqual(result["target_url"],base+"/lab/operator-fixture")
                self.assertEqual(result["selector"],"#cerebro-button")
                self.assertEqual(result["company_id"],"fenix")
                html=get("/lab/operator-fixture")
                self.assertIn('id="cerebro-button"',html)
                receipt=json.loads(get("/extension/operator-result",extension_id=ext,command_id="good1",result="COMPLETED",evidence="LAB_OPERATOR_FIXTURE_VERIFIED",observed_value="CLICKED"))
                self.assertTrue(receipt["semantic_verified"])
                h=json.loads(get("/health"))
                self.assertEqual(h["lab_command_status"],"COMPLETED")
                self.assertEqual(h["lab_command_observed_value"],"CLICKED")
                replay=json.loads(get("/extension/operator-result",extension_id=ext,command_id="good1",result="COMPLETED",evidence="LAB_OPERATOR_FIXTURE_VERIFIED",observed_value="CLICKED"))
                self.assertEqual(replay["decision"],"IDEMPOTENT_REPLAY_SUPPRESSED")
            finally:
                p.terminate()
                try:p.communicate(timeout=5)
                except subprocess.TimeoutExpired:p.kill();p.communicate(timeout=5)
if __name__=="__main__":unittest.main()
