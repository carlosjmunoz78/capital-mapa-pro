import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))
sys.path.insert(0,str(ROOT/"cerebro-os/discovery"))

import jobs.collect_public_footprint_observations as footprint
from jobs.aggregate_improvement_observations import aggregate


class PublicFootprintTests(unittest.TestCase):
    def test_detects_social_schema_robots_sitemap(self):
        html=b"""
        <html><head>
        <title>Example services Cordoba</title>
        <link rel='canonical' href='https://example.com/' />
        <script type='application/ld+json'>{"@type":"Organization"}</script>
        </head><body><h1>Example</h1>
        <a href='https://www.linkedin.com/company/example'>LinkedIn</a>
        <a href='https://www.instagram.com/example'>Instagram</a>
        </body></html>
        """
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); cfg=root/"sources.json"; evidence=root/"evidence"
            cfg.write_text(json.dumps([{
                "company_id":"fenix","enabled":True,
                "official_web_urls":["https://example.com/"]
            }]),encoding="utf-8")
            old_env=os.environ.copy(); old_fetch=footprint._fetch
            def fake(url):
                if url.endswith("robots.txt"):
                    return b"User-agent: *\nSitemap: https://example.com/sitemap.xml\n","text/plain"
                if url.endswith("sitemap_index.xml") or url.endswith("sitemap.xml"):
                    return b"<urlset></urlset>","application/xml"
                return html,"text/html"
            footprint._fetch=fake
            os.environ["CEREBRO_IMPROVEMENT_BUSINESS_SOURCES"]=str(cfg)
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(evidence)
            try:
                footprint.collect()
            finally:
                footprint._fetch=old_fetch
                os.environ.clear(); os.environ.update(old_env)
            payload=json.loads((evidence/"fenix.footprint.json").read_text())
            self.assertEqual(payload["status"],"NO_CHANGE")
            self.assertTrue(payload["facts"]["robots_ok"])
            self.assertTrue(payload["facts"]["sitemap_ok"])
            self.assertIn("LINKEDIN",payload["facts"]["social_platforms"])
            self.assertIn("INSTAGRAM",payload["facts"]["social_platforms"])

    def test_missing_social_and_schema_becomes_proposal(self):
        html=b"<html><head><title>Example services Cordoba</title><link rel='canonical' href='https://example.com/'></head><body><h1>Example</h1></body></html>"
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); cfg=root/"sources.json"; evidence=root/"evidence"
            cfg.write_text(json.dumps([{"company_id":"fenix","enabled":True,"official_web_urls":["https://example.com/"]}]))
            old_env=os.environ.copy(); old_fetch=footprint._fetch
            def fake(url):
                if url.endswith("robots.txt"):
                    return b"User-agent: *\n","text/plain"
                if "sitemap" in url:
                    return b"<urlset></urlset>","application/xml"
                return html,"text/html"
            footprint._fetch=fake
            os.environ["CEREBRO_IMPROVEMENT_BUSINESS_SOURCES"]=str(cfg)
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(evidence)
            try: footprint.collect()
            finally:
                footprint._fetch=old_fetch; os.environ.clear(); os.environ.update(old_env)
            payload=json.loads((evidence/"fenix.footprint.json").read_text())
            self.assertEqual(payload["status"],"PROPOSAL_READY")

    def test_aggregate_includes_footprint_proposal(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); cfg=root/"companies.json"
            cfg.write_text(json.dumps([{"company_id":"fenix","enabled":True}]))
            (root/"fenix.observations.json").write_text(json.dumps({
                "company_id":"fenix","checked":True,"source":"TECH","evidence_ref":"e://tech",
                "status":"NO_CHANGE","confidence":1.0,"summary":"ok"
            }))
            (root/"fenix.footprint.json").write_text(json.dumps({
                "company_id":"fenix","checked":True,"source":"FOOTPRINT","evidence_ref":"e://foot",
                "status":"PROPOSAL_READY","confidence":0.9,"summary":"issue"
            }))
            old=os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(root)
            os.environ["CEREBRO_IMPROVEMENT_COMPANIES"]=str(cfg)
            try: aggregate()
            finally: os.environ.clear(); os.environ.update(old)
            out=json.loads((root/"fenix.observations.json").read_text())
            self.assertEqual(out["status"],"PROPOSAL_READY")


if __name__=="__main__": unittest.main()
