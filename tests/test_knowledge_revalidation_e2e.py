import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

from jobs.analyze_knowledge_obsolescence import run as obs_run
from jobs.build_knowledge_revalidation_queue import run as queue_run
from jobs.refresh_knowledge_revalidation_evidence import run as research_run
from jobs.verify_knowledge_revalidation_evidence import run as provenance_run
from jobs.build_knowledge_update_candidates import run as updater_run
from jobs.apply_knowledge_update_candidates_lab import run as ledger_run

class FakeResponse:
    def __init__(self,data): self.data=data
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self,n=-1): return self.data[:n] if n>=0 else self.data

class KnowledgeRevalidationE2ETests(unittest.TestCase):
    def test_stale_public_source_flows_end_to_end_without_prod_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            inv=root/"inventory"; obs=root/"obs"; q=root/"queue"; ev=root/"evidence"
            rr=root/"research"; prov=root/"prov"; upd=root/"upd"; ledger=root/"ledger"
            inv.mkdir()
            (inv/"fenix.json").write_text(json.dumps([{
                "company_id":"fenix",
                "knowledge_id":"official-web:test",
                "environment":"LAB",
                "version":"1.0.0",
                "kind":"PUBLIC_SOURCE_POINTER",
                "state":"ACTIVE",
                "provenance_id":"prv-old",
                "source_type":"LIVE_SOURCE",
                "source_uri":"https://example.com/knowledge",
                "verified_at":"2026-09-10T00:00:00+00:00",
                "ttl_days":7,
                "confidence":0.95,
                "source_available":True,
                "contradictory_evidence":False,
                "superseded_by":"",
                "content_hash":"old",
                "external_mutation_allowed":False,
                "delete_allowed":False
            }]),encoding="utf-8")
            old=os.environ.copy()
            os.environ.update({
                "CEREBRO_KNOWLEDGE_INVENTORY_ROOT":str(inv),
                "CEREBRO_OBSOLESCENCE_ROOT":str(obs),
                "CEREBRO_REVALIDATION_ROOT":str(q),
                "CEREBRO_REVALIDATION_EVIDENCE_ROOT":str(ev),
                "CEREBRO_RESEARCH_REFRESH_ROOT":str(rr),
                "CEREBRO_PROVENANCE_VALIDATION_ROOT":str(prov),
                "CEREBRO_KNOWLEDGE_UPDATE_CANDIDATE_ROOT":str(upd),
                "CEREBRO_KNOWLEDGE_LAB_LEDGER_ROOT":str(ledger),
                "CEREBRO_OBSOLESCENCE_NOW":"2026-09-19T00:00:00+00:00",
                "CEREBRO_REVALIDATION_NOW":"2026-09-19T00:00:00+00:00",
            })
            try:
                obs_run()
                queue_run()
                with patch("urllib.request.urlopen",return_value=FakeResponse(b"new verified public content")):
                    research_run()
                provenance_run()
                updater_run()
                ledger_run()
            finally:
                os.environ.clear(); os.environ.update(old)

            ob=json.loads((obs/"fenix.json").read_text())
            self.assertEqual(ob["decisions"][0]["proposed_state"],"STALE_REVIEW")
            queue=json.loads((q/"fenix.json").read_text())
            self.assertEqual(len(queue["items"]),1)
            refresh=json.loads((rr/"fenix.json").read_text())
            self.assertEqual(refresh["results"][0]["status"],"FETCHED")
            pv=json.loads((prov/"fenix.json").read_text())
            self.assertEqual(pv["results"][0]["status"],"GREEN")
            updates=json.loads((upd/"fenix.json").read_text())
            self.assertEqual(len(updates["candidates"]),1)
            self.assertEqual(updates["candidates"][0]["status"],"CANDIDATE_ONLY")
            rows=(ledger/"fenix.jsonl").read_text().splitlines()
            self.assertEqual(len(rows),1)
            record=json.loads(rows[0])
            self.assertEqual(record["environment"],"LAB")
            self.assertEqual(record["state"],"VALIDATED_CANDIDATE")
            self.assertFalse(record["canonical"])
            self.assertFalse(record["production_ready"])
            self.assertFalse(record["external_mutation_allowed"])
            self.assertFalse(record["delete_allowed"])
            self.assertTrue(record["provenance_id"].startswith("prv-"))

    def test_deeply_stale_source_stays_human_required(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            inv=root/"inventory"; obs=root/"obs"; q=root/"queue"; ev=root/"evidence"
            rr=root/"research"; prov=root/"prov"; upd=root/"upd"; ledger=root/"ledger"
            inv.mkdir()
            (inv/"fenix.json").write_text(json.dumps([{
                "company_id":"fenix",
                "knowledge_id":"official-web:very-old",
                "environment":"LAB",
                "version":"1.0.0",
                "kind":"PUBLIC_SOURCE_POINTER",
                "state":"ACTIVE",
                "provenance_id":"prv-old",
                "source_type":"LIVE_SOURCE",
                "source_uri":"https://example.com/very-old",
                "verified_at":"2026-01-01T00:00:00+00:00",
                "ttl_days":7,
                "confidence":0.95,
                "source_available":True,
                "contradictory_evidence":False,
                "superseded_by":"",
                "content_hash":"old",
                "external_mutation_allowed":False,
                "delete_allowed":False
            }]),encoding="utf-8")
            old=os.environ.copy()
            os.environ.update({
                "CEREBRO_KNOWLEDGE_INVENTORY_ROOT":str(inv),
                "CEREBRO_OBSOLESCENCE_ROOT":str(obs),
                "CEREBRO_REVALIDATION_ROOT":str(q),
                "CEREBRO_REVALIDATION_EVIDENCE_ROOT":str(ev),
                "CEREBRO_RESEARCH_REFRESH_ROOT":str(rr),
                "CEREBRO_PROVENANCE_VALIDATION_ROOT":str(prov),
                "CEREBRO_KNOWLEDGE_UPDATE_CANDIDATE_ROOT":str(upd),
                "CEREBRO_KNOWLEDGE_LAB_LEDGER_ROOT":str(ledger),
                "CEREBRO_OBSOLESCENCE_NOW":"2026-09-19T00:00:00+00:00",
                "CEREBRO_REVALIDATION_NOW":"2026-09-19T00:00:00+00:00",
            })
            try:
                obs_run()
                queue_run()
                with patch("urllib.request.urlopen",return_value=FakeResponse(b"new verified public content")):
                    research_run()
                provenance_run()
                updater_run()
            finally:
                os.environ.clear(); os.environ.update(old)

            pv=json.loads((prov/"fenix.json").read_text())
            self.assertEqual(pv["results"][0]["status"],"HUMAN_REQUIRED")
            self.assertEqual(pv["results"][0]["reasons"],["LOW_CONFIDENCE"])
            updates=json.loads((upd/"fenix.json").read_text())
            self.assertEqual(updates["candidates"],[])

if __name__=="__main__":
    unittest.main()
