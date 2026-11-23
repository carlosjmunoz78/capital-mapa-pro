import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))
from learning.improvement_proposal_queue import ProposalQueue, ProposalRecord


def item(**kw):
    d=dict(company_id="fenix",proposal_id="p1",source_key="business",domain="WEB_SEO",environment="LAB",version="1.0.0",summary="review",evidence_ref="e://one",action="LAB_DIAGNOSTIC_ONLY",external_mutation_allowed=False,cost_limit_eur=0.0,priority="P1",status="OPEN")
    d.update(kw)
    return ProposalRecord(**d)


class ProposalReplayGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Path(self.tmp.name)/"proposals.sqlite"
        self.q=ProposalQueue(self.db)
    def tearDown(self):
        self.q.close();self.tmp.cleanup()

    def test_status_is_preserved_in_payload_after_duplicate_ingest(self):
        fp=self.q.upsert(item())
        self.q.set_status(fp,"WAITING_TEST")
        self.q.upsert(item(proposal_id="p2"))
        got=self.q.list_open()[0]
        self.assertEqual(got.status,"WAITING_TEST")
        self.assertEqual(got.proposal_id,"p2")
        state,embedded=self.q.conn.execute("SELECT status,json_extract(payload_json,'$.status') FROM proposal_queue").fetchone()
        self.assertEqual(state,embedded)

    def test_closed_proposal_remains_immutable_on_reingest(self):
        fp=self.q.upsert(item())
        self.q.set_status(fp,"CLOSED")
        before=self.q.conn.execute("SELECT * FROM proposal_queue WHERE fingerprint=?",(fp,)).fetchone()
        self.q.upsert(item(proposal_id="p2",summary="changed",priority="P0"))
        after=self.q.conn.execute("SELECT * FROM proposal_queue WHERE fingerprint=?",(fp,)).fetchone()
        self.assertEqual(after,before)
        self.assertEqual(self.q.list_open(),())

    def test_cost_increase_on_same_evidence_is_denied(self):
        # Existing budget may be reduced by a new ingest but never enlarged.
        fp=self.q.upsert(item(cost_limit_eur=0.0))
        with self.assertRaises(PermissionError):
            self.q.upsert(item(cost_limit_eur=1.0))
        self.assertEqual(self.q.conn.execute("SELECT json_extract(payload_json,'$.cost_limit_eur') FROM proposal_queue WHERE fingerprint=?",(fp,)).fetchone()[0],0.0)

    def test_nan_cost_cannot_enter_queue(self):
        with self.assertRaises(ValueError):
            self.q.upsert(item(cost_limit_eur=float('nan')))

    def test_infinite_cost_cannot_enter_queue(self):
        with self.assertRaises(ValueError):
            self.q.upsert(item(cost_limit_eur=float('inf')))

    def test_cross_company_fingerprint_isolated(self):
        self.q.upsert(item())
        self.q.upsert(item(company_id="aion",proposal_id="pA",summary="aion"))
        self.assertEqual(self.q.count(),2)
        self.assertEqual(self.q.list_open(company_id="fenix")[0].company_id,"fenix")

    def test_duplicate_insert_is_atomic_across_connections(self):
        self.q.upsert(item())
        second=ProposalQueue(self.db)
        try:
            second.upsert(item(proposal_id="p2",status="WAITING_TEST"))
            self.assertEqual(self.q.count(),1)
            self.assertEqual(self.q.list_open()[0].status,"OPEN")
        finally:
            second.close()

    def test_explicit_status_change_still_functions(self):
        fp=self.q.upsert(item())
        self.q.set_status(fp,"CLOSED")
        self.assertEqual(self.q.conn.execute("SELECT status FROM proposal_queue WHERE fingerprint=?",(fp,)).fetchone()[0],"CLOSED")

if __name__=='__main__':unittest.main()