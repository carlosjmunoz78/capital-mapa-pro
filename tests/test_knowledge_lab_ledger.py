import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

from jobs.apply_knowledge_update_candidates_lab import run

class KnowledgeLabLedgerTests(unittest.TestCase):
    def test_safe_candidate_appends_once_and_never_becomes_canonical(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=root/"src"; out=root/"out"; src.mkdir()
            candidate={
                "company_id":"aion","engine_id":"UPD-001","knowledge_id":"k1",
                "kind":"KNOWLEDGE","candidate_version":"revalidated-abc",
                "provenance_id":"prv-123","source_type":"LIVE_SOURCE",
                "source_uri":"https://example.com","observed_at":"2026-09-19",
                "validated_by":"validator-v1","content_hash":"abc","evidence_hash":"ev",
                "confidence":0.95,"status":"CANDIDATE_ONLY","append_only":True,
                "history_preserved":True,"auto_apply_allowed":False,
                "production_ready":False,"external_mutation_allowed":False,"delete_allowed":False
            }
            (src/"aion.json").write_text(json.dumps({"company_id":"aion","candidates":[candidate]}),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_KNOWLEDGE_UPDATE_CANDIDATE_ROOT"]=str(src)
            os.environ["CEREBRO_KNOWLEDGE_LAB_LEDGER_ROOT"]=str(out)
            try:
                run(); run()
            finally:
                os.environ.clear(); os.environ.update(old)
            lines=(out/"aion.jsonl").read_text().splitlines()
            self.assertEqual(len(lines),1)
            rec=json.loads(lines[0])
            self.assertEqual(rec["environment"],"LAB")
            self.assertFalse(rec["canonical"])
            self.assertFalse(rec["production_ready"])
            self.assertTrue(rec["history_preserved"])
            summary=json.loads((out/"aion.summary.json").read_text())
            self.assertFalse(summary["canonical_mutation_performed"])

    def test_low_confidence_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=root/"src"; out=root/"out"; src.mkdir()
            candidate={
                "company_id":"aion","engine_id":"UPD-001","knowledge_id":"k1",
                "provenance_id":"prv-123","source_type":"LIVE_SOURCE",
                "confidence":0.5,"status":"CANDIDATE_ONLY","append_only":True,
                "auto_apply_allowed":False,"external_mutation_allowed":False,"delete_allowed":False
            }
            (src/"aion.json").write_text(json.dumps({"company_id":"aion","candidates":[candidate]}),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_KNOWLEDGE_UPDATE_CANDIDATE_ROOT"]=str(src)
            os.environ["CEREBRO_KNOWLEDGE_LAB_LEDGER_ROOT"]=str(out)
            try:
                with self.assertRaisesRegex(ValueError,"low-confidence"):
                    run()
            finally:
                os.environ.clear(); os.environ.update(old)

    def test_cross_company_candidate_denied(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=root/"src"; out=root/"out"; src.mkdir()
            (src/"aion.json").write_text(json.dumps({
                "company_id":"aion","candidates":[{
                    "company_id":"fenix","engine_id":"UPD-001","status":"CANDIDATE_ONLY",
                    "append_only":True,"auto_apply_allowed":False,"external_mutation_allowed":False,
                    "delete_allowed":False,"provenance_id":"prv-x","source_type":"LIVE_SOURCE","confidence":1.0
                }]
            }),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_KNOWLEDGE_UPDATE_CANDIDATE_ROOT"]=str(src)
            os.environ["CEREBRO_KNOWLEDGE_LAB_LEDGER_ROOT"]=str(out)
            try:
                with self.assertRaisesRegex(ValueError,"cross-company"):
                    run()
            finally:
                os.environ.clear(); os.environ.update(old)

if __name__=="__main__":
    unittest.main()
