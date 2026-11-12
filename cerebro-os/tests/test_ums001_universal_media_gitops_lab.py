import importlib.util
import sys
from pathlib import Path
import unittest
root=Path(__file__).resolve().parents[1]/"factory"
sys.path.insert(0,str(root))
spec=importlib.util.spec_from_file_location("media_gitops",root/"universal_media_gitops_lab.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
P="cerebro-os/media-requests/FACT-OIDC-LAB-E2E-001/UMS001-LAB-GITOPS-20261112-001.json"
def payload():
    return {"company_id":"fenix","environment":"LAB","engine_id":"FACT-OIDC-LAB-E2E-001",
    "request_id":"UMS001-LAB-GITOPS-20261112-001","capability_id":"IMAGE.SYNTHETIC",
    "rights_profile":"SYNTHETIC_ORIGINAL","publish_requested":False,
    "prompt":"Original fictional apartment in Cordoba, natural sunlight, high-quality architecture photo, no logos or text."}
class MediaTests(unittest.TestCase):
    def test_valid(self):self.assertEqual(m.validate(P,payload())["company_id"],"fenix")
    def test_no_publish(self):
        x=payload();x["publish_requested"]=True
        with self.assertRaises(ValueError):m.validate(P,x)
    def test_no_cross_tenant(self):
        x=payload();x["company_id"]="other"
        with self.assertRaises(ValueError):m.validate(P,x)
    def test_no_prod(self):
        x=payload();x["environment"]="PROD"
        with self.assertRaises(ValueError):m.validate(P,x)
    def test_no_engine_spoof(self):
        x=payload();x["engine_id"]="OTHER-001"
        with self.assertRaises(ValueError):m.validate(P,x)
    def test_no_extra_fields(self):
        x=payload();x["publish_now"]=True
        with self.assertRaises(ValueError):m.validate(P,x)
    def test_reject_bad_jpeg(self):
        with self.assertRaises(ValueError):m.dimensions(b"not a jpeg")
if __name__=="__main__":unittest.main()
