import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))

from jobs.analyze_knowledge_obsolescence import analyze_record, run


class KnowledgeObsolescenceTests(unittest.TestCase):
    def test_fresh_record_stays_active(self):
        out = analyze_record({
            "company_id":"aion","knowledge_id":"k1","environment":"LAB","version":"1.0.0",
            "kind":"KNOWLEDGE","state":"ACTIVE","verified_at":"2026-09-10T00:00:00+00:00",
            "ttl_days":90,"confidence":0.9,"source_available":True
        }, datetime(2026,9,19,tzinfo=timezone.utc))
        self.assertEqual(out["proposed_state"],"ACTIVE")
        self.assertFalse(out["delete_allowed"])
        self.assertTrue(out["history_preserved"])

    def test_expired_record_degrades_without_deletion(self):
        out = analyze_record({
            "company_id":"aion","knowledge_id":"k2","environment":"LAB","version":"1.0.0",
            "kind":"KNOWLEDGE","state":"ACTIVE","verified_at":"2026-01-01T00:00:00+00:00",
            "ttl_days":30,"confidence":0.95,"source_available":True
        }, datetime(2026,9,19,tzinfo=timezone.utc))
        self.assertEqual(out["proposed_state"],"STALE_REVIEW")
        self.assertLess(out["proposed_confidence"],0.95)
        self.assertFalse(out["automatic_forgetting_allowed"])
        self.assertFalse(out["external_mutation_allowed"])

    def test_superseded_record_preserves_history(self):
        out = analyze_record({
            "company_id":"aion","knowledge_id":"k3","environment":"LAB","version":"1.0.0",
            "kind":"KNOWLEDGE","state":"ACTIVE","verified_at":"2026-09-18T00:00:00+00:00",
            "ttl_days":90,"confidence":1.0,"superseded_by":"k4"
        }, datetime(2026,9,19,tzinfo=timezone.utc))
        self.assertEqual(out["proposed_state"],"SUPERSEDED")
        self.assertTrue(out["history_preserved"])
        self.assertFalse(out["delete_allowed"])

    def test_protected_policy_never_auto_changes(self):
        out = analyze_record({
            "company_id":"aion","knowledge_id":"p1","environment":"LAB","version":"1.0.0",
            "kind":"POLICY","state":"ACTIVE","verified_at":"2025-01-01T00:00:00+00:00",
            "ttl_days":30,"confidence":1.0
        }, datetime(2026,9,19,tzinfo=timezone.utc))
        self.assertTrue(out["human_review_required"])
        self.assertFalse(out["policy_or_permission_change_allowed"])

    def test_job_rejects_cross_company_batch(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=root/"src"; out=root/"out"; src.mkdir()
            (src/"mixed.json").write_text(json.dumps([
                {"company_id":"aion","knowledge_id":"a","environment":"LAB","version":"1.0","verified_at":"2026-09-01T00:00:00+00:00"},
                {"company_id":"fenix","knowledge_id":"b","environment":"LAB","version":"1.0","verified_at":"2026-09-01T00:00:00+00:00"}
            ]),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_KNOWLEDGE_INVENTORY_ROOT"]=str(src)
            os.environ["CEREBRO_OBSOLESCENCE_ROOT"]=str(out)
            os.environ["CEREBRO_OBSOLESCENCE_NOW"]="2026-09-19T00:00:00+00:00"
            try:
                with self.assertRaisesRegex(ValueError,"cross-company"):
                    run()
            finally:
                os.environ.clear(); os.environ.update(old)


if __name__=="__main__":
    unittest.main()
