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
if __name__=="__main__":unittest.main()
