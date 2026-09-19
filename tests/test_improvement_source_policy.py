import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

from jobs.aggregate_improvement_observations import aggregate


class SourcePolicyTests(unittest.TestCase):
    def _run(self, root: Path, policy: dict):
        cfg=root/"companies.json"
        cfg.write_text(json.dumps([{"company_id":"fenix","enabled":True}]),encoding="utf-8")
        pol=root/"policy.json"
        pol.write_text(json.dumps(policy),encoding="utf-8")
        old=os.environ.copy()
        os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(root)
        os.environ["CEREBRO_IMPROVEMENT_COMPANIES"]=str(cfg)
        os.environ["CEREBRO_IMPROVEMENT_SOURCE_POLICY"]=str(pol)
        try:
            aggregate()
        finally:
            os.environ.clear(); os.environ.update(old)
        return json.loads((root/"fenix.observations.json").read_text(encoding="utf-8"))

    def test_required_source_error_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"fenix.observations.json").write_text(json.dumps({
                "company_id":"fenix","checked":True,"source":"TECH",
                "evidence_ref":"e://tech","status":"NO_CHANGE","confidence":1.0,"summary":"ok"
            }))
            (root/"fenix.business.json").write_text(json.dumps({
                "company_id":"fenix","checked":False,"source":"WEB",
                "evidence_ref":"e://web-error","status":"SOURCE_ERROR","confidence":0.0,"summary":"down"
            }))
            out=self._run(root,{"fenix":{"required":["technical","business"],"optional":[]}})
            self.assertEqual(out["status"],"SOURCE_ERROR")
            self.assertFalse(out["checked"])
            self.assertEqual(out["facts"]["failed_required_sources"],["business"])

    def test_optional_source_error_does_not_mask_green_required_sources(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"fenix.observations.json").write_text(json.dumps({
                "company_id":"fenix","checked":True,"source":"TECH",
                "evidence_ref":"e://tech","status":"NO_CHANGE","confidence":1.0,"summary":"ok"
            }))
            (root/"fenix.finops.json").write_text(json.dumps({
                "company_id":"fenix","checked":False,"source":"FINOPS",
                "evidence_ref":"e://fin-error","status":"SOURCE_ERROR","confidence":0.0,"summary":"down"
            }))
            out=self._run(root,{"fenix":{"required":["technical"],"optional":["finops"]}})
            self.assertEqual(out["status"],"NO_CHANGE")
            self.assertTrue(out["checked"])
            self.assertEqual(out["facts"]["failed_optional_sources"],["finops"])

    def test_missing_required_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"fenix.observations.json").write_text(json.dumps({
                "company_id":"fenix","checked":True,"source":"TECH",
                "evidence_ref":"e://tech","status":"NO_CHANGE","confidence":1.0,"summary":"ok"
            }))
            out=self._run(root,{"fenix":{"required":["technical","footprint"],"optional":[]}})
            self.assertEqual(out["status"],"SOURCE_ERROR")
            self.assertEqual(out["facts"]["missing_required_sources"],["footprint"])


if __name__=="__main__": unittest.main()
