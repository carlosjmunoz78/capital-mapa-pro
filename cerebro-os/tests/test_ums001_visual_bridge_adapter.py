import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch
import unittest

BASE=Path(__file__).resolve().parents[1]/"factory"
sys.path.insert(0,str(BASE))
import universal_media_gitops_lab as mod

ID={"engine_id":"CEREBRO-NEWS-001","request_id":"UMS001-LAB-NEWS001-B2C-20261117-03","sha":"a"*40}
SHA="a"*64

def response(**overrides):
    r=dict(company_id="fenix",engine_id=ID["engine_id"],request_id=ID["request_id"],
           environment="LAB",asset_sha256=SHA,state="QA_HOLD",reuse_allowed=False,
           publish_authorized=False)
    r.update(overrides)
    return r

class VisionBridgeAdapter(unittest.TestCase):
    def test_off_no_cloudflare_called(self):
        with patch.dict("os.environ",{"UMS001_VISION_QA_API_ENABLED":"false"}),patch.object(mod,"call") as f:
            self.assertEqual(mod.maybe_review_asset(ID,SHA)["qa_bridge_state"],"DISABLED")
            f.assert_not_called()
    def test_valid_hold_stays_hold(self):
        with patch.dict("os.environ",{"UMS001_VISION_QA_API_ENABLED":"true"}),patch.object(mod,"call",return_value=response()):
            self.assertEqual(mod.maybe_review_asset(ID,SHA)["qa_bridge_state"],"QA_HOLD")
    def test_valid_candidate_never_releases(self):
        with patch.dict("os.environ",{"UMS001_VISION_QA_API_ENABLED":"true"}),patch.object(mod,"call",return_value=response(state="QA_CANDIDATE_UNCALIBRATED")):
            self.assertEqual(mod.maybe_review_asset(ID,SHA)["qa_bridge_reason"],"PENDING_INDEPENDENT_REVIEW")
    def test_defect_rejected(self):
        with patch.dict("os.environ",{"UMS001_VISION_QA_API_ENABLED":"true"}),patch.object(mod,"call",return_value=response(state="REJECTED_VISUAL",findings=["ANATOMY_DISCONNECTED_LIMBS"])):
            self.assertEqual(mod.maybe_review_asset(ID,SHA)["qa_bridge_state"],"REJECTED_VISUAL")
    def test_cannot_authorize_publication(self):
        with patch.dict("os.environ",{"UMS001_VISION_QA_API_ENABLED":"true"}),patch.object(mod,"call",return_value=response(publish_authorized=True)):
            self.assertEqual(mod.maybe_review_asset(ID,SHA)["qa_bridge_state"],"QA_HOLD")
    def test_cannot_authorize_reuse(self):
        with patch.dict("os.environ",{"UMS001_VISION_QA_API_ENABLED":"true"}),patch.object(mod,"call",return_value=response(reuse_allowed=True)):
            self.assertEqual(mod.maybe_review_asset(ID,SHA)["qa_bridge_reason"],"QA_BRIDGE_UNAVAILABLE")
    def test_hash_mismatch_blocks(self):
        with patch.dict("os.environ",{"UMS001_VISION_QA_API_ENABLED":"true"}),patch.object(mod,"call",return_value=response(asset_sha256="b"*64)):
            self.assertEqual(mod.maybe_review_asset(ID,SHA)["qa_bridge_state"],"QA_HOLD")
    def test_cross_engine_blocks(self):
        with patch.dict("os.environ",{"UMS001_VISION_QA_API_ENABLED":"true"}),patch.object(mod,"call",return_value=response(engine_id="OTHER-001")):
            self.assertEqual(mod.maybe_review_asset(ID,SHA)["qa_bridge_state"],"QA_HOLD")
    def test_service_failure_closed(self):
        with patch.dict("os.environ",{"UMS001_VISION_QA_API_ENABLED":"true"}),patch.object(mod,"call",side_effect=RuntimeError("offline")):
            self.assertEqual(mod.maybe_review_asset(ID,SHA)["qa_bridge_reason"],"QA_BRIDGE_UNAVAILABLE")
if __name__=="__main__":unittest.main()
