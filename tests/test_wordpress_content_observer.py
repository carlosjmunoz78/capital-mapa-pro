import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

import jobs.collect_wordpress_content_observations as content


class WordPressContentObserverTests(unittest.TestCase):
    def test_public_content_observation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            cfg=root/"sources.json"
            cfg.write_text(json.dumps([{
                "company_id":"fenix","enabled":True,
                "wordpress_rest_base":"https://example.com/wp-json/wp/v2"
            }]),encoding="utf-8")
            evidence=root/"evidence"; state=root/"state"
            old_env=os.environ.copy(); old_fetch=content._fetch_json
            def fake(url):
                if "/posts?" in url:
                    return [{"id":1,"modified":"2026-09-19T12:00:00","link":"https://example.com/p","slug":"p","status":"publish"}]
                return [{"id":2,"modified":"2026-09-18T12:00:00","link":"https://example.com/about","slug":"about","status":"publish"}]
            content._fetch_json=fake
            os.environ["CEREBRO_IMPROVEMENT_BUSINESS_SOURCES"]=str(cfg)
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(evidence)
            os.environ["CEREBRO_IMPROVEMENT_OBSERVATION_STATE_ROOT"]=str(state)
            try:
                content.collect()
            finally:
                content._fetch_json=old_fetch
                os.environ.clear(); os.environ.update(old_env)
            payload=json.loads((evidence/"fenix.content.json").read_text())
            self.assertTrue(payload["checked"])
            self.assertEqual(payload["status"],"NO_CHANGE")
            self.assertEqual(len(payload["facts"]["posts"]),1)
            self.assertEqual(len(payload["facts"]["pages"]),1)

    def test_empty_public_content_becomes_proposal(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            cfg=root/"sources.json"
            cfg.write_text(json.dumps([{
                "company_id":"fenix","enabled":True,
                "wordpress_rest_base":"https://example.com/wp-json/wp/v2"
            }]),encoding="utf-8")
            evidence=root/"evidence"
            old_env=os.environ.copy(); old_fetch=content._fetch_json
            content._fetch_json=lambda url:[]
            os.environ["CEREBRO_IMPROVEMENT_BUSINESS_SOURCES"]=str(cfg)
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"]=str(evidence)
            os.environ["CEREBRO_IMPROVEMENT_OBSERVATION_STATE_ROOT"]=str(root/"state")
            try:
                content.collect()
            finally:
                content._fetch_json=old_fetch
                os.environ.clear(); os.environ.update(old_env)
            payload=json.loads((evidence/"fenix.content.json").read_text())
            self.assertEqual(payload["status"],"PROPOSAL_READY")


if __name__=="__main__": unittest.main()
