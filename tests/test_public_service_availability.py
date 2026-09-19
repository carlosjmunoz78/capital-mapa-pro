import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

import jobs.collect_public_service_availability as availability
from jobs.aggregate_improvement_observations import aggregate


class PublicServiceAvailabilityTests(unittest.TestCase):
    def test_all_services_reachable_is_no_change(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); cfg=root/"sources.json"; evidence=root/"evidence"
            cfg.write_text(json.dumps([{
                "company_id":"fenix","enabled":True,
                "official_web_urls":["https://example.com/"],
                "app_url":"https://app.example.com/",
                "gateway_url":"https://project.supabase.co/functions/v1/gateway",
                "wordpress_rest_base":"https://example.com/wp-json/wp/v2"
            }]),encoding="utf-8")
            old_env=os.environ.copy(); old_probe=availability._probe
            def fake(url):
                if "gateway" in url:
                    return {"reachable":True,"status_code":401,"latency_ms":50.0,"body_nonempty":True}
                return {"reachable":True,"status_code":200,"latency_ms":50.0,"body_nonempty":True}
            availability._probe=fake
            os.environ["CEREBRO_IMPROVEMENT_BUSINESS_SOURCES"]=str(cfg)
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(evidence)
            try: availability.collect()
            finally:
                availability._probe=old_probe
                os.environ.clear(); os.environ.update(old_env)
            payload=json.loads((evidence/"fenix.availability.json").read_text())
            self.assertEqual(payload["status"],"NO_CHANGE")
            self.assertEqual(payload["facts"]["failures"],[])

    def test_unreachable_app_becomes_proposal(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); cfg=root/"sources.json"; evidence=root/"evidence"
            cfg.write_text(json.dumps([{
                "company_id":"fenix","enabled":True,
                "official_web_urls":["https://example.com/"],
                "app_url":"https://app.example.com/"
            }]),encoding="utf-8")
            old_env=os.environ.copy(); old_probe=availability._probe
            def fake(url):
                if "app." in url:
                    return {"reachable":False,"status_code":0,"latency_ms":1000.0,"body_nonempty":False}
                return {"reachable":True,"status_code":200,"latency_ms":50.0,"body_nonempty":True}
            availability._probe=fake
            os.environ["CEREBRO_IMPROVEMENT_BUSINESS_SOURCES"]=str(cfg)
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(evidence)
            try: availability.collect()
            finally:
                availability._probe=old_probe
                os.environ.clear(); os.environ.update(old_env)
            payload=json.loads((evidence/"fenix.availability.json").read_text())
            self.assertEqual(payload["status"],"PROPOSAL_READY")
            self.assertEqual(payload["facts"]["failures"],["app"])

    def test_optional_availability_proposal_is_aggregated(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            cfg=root/"companies.json"
            cfg.write_text(json.dumps([{"company_id":"fenix","enabled":True}]))
            pol=root/"policy.json"
            pol.write_text(json.dumps({"fenix":{"required":["technical"],"optional":["availability"]}}))
            (root/"fenix.observations.json").write_text(json.dumps({
                "company_id":"fenix","checked":True,"source":"TECH","evidence_ref":"e://tech",
                "status":"NO_CHANGE","confidence":1.0,"summary":"ok"
            }))
            (root/"fenix.availability.json").write_text(json.dumps({
                "company_id":"fenix","checked":True,"source":"PUBLIC_SERVICE_AVAILABILITY",
                "evidence_ref":"e://availability","status":"PROPOSAL_READY","confidence":0.95,"summary":"app down"
            }))
            old=os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(root)
            os.environ["CEREBRO_IMPROVEMENT_COMPANIES"]=str(cfg)
            os.environ["CEREBRO_IMPROVEMENT_SOURCE_POLICY"]=str(pol)
            try: aggregate()
            finally: os.environ.clear(); os.environ.update(old)
            out=json.loads((root/"fenix.observations.json").read_text())
            self.assertEqual(out["status"],"PROPOSAL_READY")


if __name__=="__main__": unittest.main()
