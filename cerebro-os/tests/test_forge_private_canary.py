import importlib.util
import pathlib
import unittest
from unittest.mock import patch
p=pathlib.Path(__file__).resolve().parents[1]/"preprod/private_canary.py"
spec=importlib.util.spec_from_file_location("private_canary",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class TestForgeCanary(unittest.TestCase):
    def q(self):
        return {"name":m.QPATH,"state":"PAUSED","rateLimits":{"maxConcurrentDispatches":1,"maxDispatchesPerSecond":1},"retryConfig":{"maxAttempts":1},"stackdriverLoggingConfig":{"samplingRatio":1}}
    def s(self):
        return {"metadata":{"name":m.SERVICE,"annotations":{"run.googleapis.com/ingress":"internal"}},"status":{"url":"https://forge-test.run.app","traffic":[{"revisionName":"old","percent":100}]}}
    def test_queue_boundary(self):
        m.validate_queue(self.q())
        for key,value in [("state","RUNNING"),("name","foreign")]:
            q=self.q();q[key]=value
            with self.assertRaises(RuntimeError):m.validate_queue(q)
        q=self.q();q["retryConfig"]["maxAttempts"]=2
        with self.assertRaises(RuntimeError):m.validate_queue(q)
    def test_old_and_tag(self):
        s=self.s();self.assertEqual(m.validate_service(s,"old"),("https://forge-test.run.app",None))
        s["status"]["traffic"].append({"revisionName":"new","tag":m.TAG,"url":"https://"+m.TAG+"---forge-test.run.app"})
        self.assertEqual(m.validate_service(s,"old","new")[1],"https://"+m.TAG+"---forge-test.run.app")
        s["status"]["traffic"][1]["url"]="https://unrelated.run.app"
        with self.assertRaises(RuntimeError):m.validate_service(s,"old","new")
    def test_public_or_traffic_denied(self):
        s=self.s();s["metadata"]["annotations"]["run.googleapis.com/ingress"]="all"
        with self.assertRaises(RuntimeError):m.validate_service(s)
        s=self.s();s["status"]["traffic"][0]["percent"]=99
        with self.assertRaises(RuntimeError):m.validate_service(s)
    def test_receipt(self):
        target="https://forge-test.run.app"
        q=[{"jsonPayload":{"attemptResponseLog":{"status":"OK","dispatchCount":"1","targetAddress":"GET "+target+"/ready"}}}]
        r=[{"httpRequest":{"status":200,"requestUrl":target+"/ready"}}]
        with patch.object(m,"logs",side_effect=[q,r]):self.assertTrue(m.accepted("task","rev","now",target))
        with patch.object(m,"logs",return_value=[]):self.assertFalse(m.accepted("task","rev","now",target))
        with patch.object(m,"logs",side_effect=[q,[{"httpRequest":{"status":403,"requestUrl":target+"/ready"}}]]):
            with self.assertRaises(RuntimeError):m.accepted("task","rev","now",target)
        with patch.object(m,"logs",return_value=q+q):
            with self.assertRaises(RuntimeError):m.accepted("task","rev","now",target)
    def test_serving_canary_no_traffic_change(self):
        import os, tempfile
        from contextlib import ExitStack
        s=self.s(); revision=m.SERVICE+"-00266-xnc"
        s["status"]["traffic"][0]["revisionName"]=revision
        tid="forge-20261124-1"; name=m.QPATH+"/tasks/"+tid
        with tempfile.TemporaryDirectory() as d, ExitStack() as stack:
            oldcwd=os.getcwd(); os.chdir(d); stack.callback(os.chdir,oldcwd)
            stack.enter_context(patch.dict(os.environ,{"FORGE_OLD_REVISION":revision,"FORGE_EXPECTED_REVISION":revision,"FORGE_CANARY_ID":tid,"GITHUB_ENV":d+"/env"}))
            stack.enter_context(patch.object(m,"preflight"))
            stack.enter_context(patch.object(m,"service",return_value=s))
            stack.enter_context(patch.object(m,"queue",return_value=self.q()))
            stack.enter_context(patch.object(m,"tasks",side_effect=[[],[{"name":name}],[],[]]))
            cloud=stack.enter_context(patch.object(m,"gcloud",side_effect=[{"name":name},None,None]))
            receipt=stack.enter_context(patch.object(m,"accepted",return_value=True))
            m.invoke(serving=True)
            self.assertEqual([c.args[:2] for c in cloud.call_args_list],[("tasks","create-http-task"),("tasks","queues"),("tasks","queues")])
            self.assertEqual(receipt.call_args.args[3],s["status"]["url"])
            self.assertIn("PRIVATE_CANARY_PASS",pathlib.Path("forge-evidence/private-canary.json").read_text())
    def test_serving_revision_mismatch(self):
        import os
        with patch.object(m,"preflight"), patch.dict(os.environ,{"FORGE_OLD_REVISION":"old","FORGE_EXPECTED_REVISION":"old","FORGE_CANARY_ID":"forge-20261124-1"}):
            with self.assertRaisesRegex(RuntimeError,"CANARY_SCOPE_DENIED"):m.invoke(serving=True)
if __name__=="__main__":unittest.main()
