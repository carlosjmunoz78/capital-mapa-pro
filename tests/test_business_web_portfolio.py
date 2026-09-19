import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))
sys.path.insert(0, str(ROOT / "cerebro-os/discovery"))

import jobs.collect_business_observations as observer


class BusinessWebPortfolioTests(unittest.TestCase):
    def test_multi_page_collection_is_bounded_and_persistent(self):
        pages = {
            "https://example.com/": b"<html><head><title>Example mortgage services</title><link rel='canonical' href='https://example.com/'></head><body><h1>Mortgage services</h1></body></html>",
            "https://example.com/about/": b"<html><head><title>About example mortgage team</title><link rel='canonical' href='https://example.com/about/'></head><body><h1>About our team</h1></body></html>",
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = root / "sources.json"
            cfg.write_text(json.dumps([{
                "company_id": "fenix",
                "official_web_urls": list(pages),
                "enabled": True,
            }]), encoding="utf-8")
            evidence = root / "evidence"
            state = root / "state"
            old_env = os.environ.copy()
            old_fetch = observer._fetch
            observer._fetch = lambda url: pages[url]
            os.environ["CEREBRO_IMPROVEMENT_BUSINESS_SOURCES"] = str(cfg)
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"] = str(evidence)
            os.environ["CEREBRO_IMPROVEMENT_OBSERVATION_STATE_ROOT"] = str(state)
            try:
                written = observer.collect()
            finally:
                observer._fetch = old_fetch
                os.environ.clear()
                os.environ.update(old_env)
            self.assertEqual(len(written), 1)
            payload = json.loads(written[0].read_text(encoding="utf-8"))
            self.assertEqual(payload["facts"]["pages_configured"], 2)
            self.assertEqual(payload["facts"]["pages_checked"], 2)
            self.assertEqual(payload["facts"]["source_errors"], 0)
            self.assertEqual(len(list(state.glob("fenix.official-web.*.json"))), 2)

    def test_second_run_detects_content_change_as_proposal(self):
        url = "https://example.com/"
        first = b"<html><head><title>Example mortgage services</title><link rel='canonical' href='https://example.com/'></head><body><h1>Mortgage services</h1></body></html>"
        second = b"<html><head><title>Example mortgage services updated</title><link rel='canonical' href='https://example.com/'></head><body><h1>Mortgage services</h1></body></html>"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = root / "sources.json"
            cfg.write_text(json.dumps([{"company_id":"fenix","official_web_urls":[url],"enabled":True}]), encoding="utf-8")
            evidence = root / "evidence"
            state = root / "state"
            old_env = os.environ.copy()
            old_fetch = observer._fetch
            os.environ["CEREBRO_IMPROVEMENT_BUSINESS_SOURCES"] = str(cfg)
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"] = str(evidence)
            os.environ["CEREBRO_IMPROVEMENT_OBSERVATION_STATE_ROOT"] = str(state)
            try:
                observer._fetch = lambda _: first
                observer.collect()
                observer._fetch = lambda _: second
                observer.collect()
            finally:
                observer._fetch = old_fetch
                os.environ.clear()
                os.environ.update(old_env)
            payload = json.loads((evidence / "fenix.business.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "PROPOSAL_READY")
            self.assertEqual(payload["facts"]["proposal_pages"], 1)


if __name__ == "__main__":
    unittest.main()
