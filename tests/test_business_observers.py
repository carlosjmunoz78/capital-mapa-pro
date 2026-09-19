import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))
sys.path.insert(0, str(ROOT / "cerebro-os/discovery"))

from jobs.aggregate_improvement_observations import aggregate
from discovery.public_web_collector import parse_public_html


class BusinessObserverTests(unittest.TestCase):
    def test_public_web_parser_extracts_core_seo_facts(self):
        snap = parse_public_html("https://example.com/", """
        <html><head><title>Example Mortgage Advice Córdoba</title>
        <link rel="canonical" href="https://example.com/"/>
        <script type="application/ld+json">{"@type":"Organization"}</script>
        </head><body><h1>Mortgage advice</h1></body></html>
        """)
        self.assertEqual(snap.h1, "Mortgage advice")
        self.assertIn("Organization", snap.schema_types)

    def test_aggregate_prefers_business_proposal_over_healthy_technical(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            cfg=root/"companies.json"
            cfg.write_text(json.dumps([{
                "company_id":"fenix","legal_name":"Fenix Capital","autonomy_profile":"FENIX_SENSITIVE",
                "environment":"LAB","version":"1.0.0","interval_hours":24,"enabled":True
            }]), encoding="utf-8")
            (root/"fenix.observations.json").write_text(json.dumps({
                "company_id":"fenix","checked":True,"source":"GITHUB_ENGINE_FACTORY",
                "evidence_ref":"e://tech","status":"NO_CHANGE","confidence":1.0,"summary":"healthy"
            }), encoding="utf-8")
            (root/"fenix.business.json").write_text(json.dumps({
                "company_id":"fenix","checked":True,"source":"OFFICIAL_PUBLIC_WEB",
                "evidence_ref":"e://web","status":"PROPOSAL_READY","confidence":0.95,"summary":"content changed"
            }), encoding="utf-8")
            policy=root/"policy.json"
            policy.write_text(json.dumps({"fenix":{"required":["technical","business"],"optional":[]}}))
            old=os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(root)
            os.environ["CEREBRO_IMPROVEMENT_COMPANIES"]=str(cfg)
            os.environ["CEREBRO_IMPROVEMENT_SOURCE_POLICY"]=str(policy)
            try:
                aggregate()
            finally:
                os.environ.clear(); os.environ.update(old)
            out=json.loads((root/"fenix.observations.json").read_text())
            self.assertEqual(out["status"],"PROPOSAL_READY")
            self.assertEqual(out["source"],"MULTI_SOURCE")

    def test_cross_company_payload_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            cfg=root/"companies.json"
            cfg.write_text(json.dumps([{
                "company_id":"fenix","legal_name":"Fenix","autonomy_profile":"FENIX_SENSITIVE",
                "environment":"LAB","version":"1.0.0","interval_hours":24,"enabled":True
            }]), encoding="utf-8")
            (root/"fenix.business.json").write_text(json.dumps({
                "company_id":"other","checked":True,"source":"OFFICIAL_PUBLIC_WEB",
                "evidence_ref":"e://x","status":"NO_CHANGE","confidence":1.0,"summary":"x"
            }), encoding="utf-8")
            policy=root/"policy.json"
            policy.write_text(json.dumps({"fenix":{"required":["business"],"optional":[]}}))
            old=os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(root)
            os.environ["CEREBRO_IMPROVEMENT_COMPANIES"]=str(cfg)
            os.environ["CEREBRO_IMPROVEMENT_SOURCE_POLICY"]=str(policy)
            try:
                with self.assertRaises(ValueError):
                    aggregate()
            finally:
                os.environ.clear(); os.environ.update(old)


if __name__=="__main__":
    unittest.main()
