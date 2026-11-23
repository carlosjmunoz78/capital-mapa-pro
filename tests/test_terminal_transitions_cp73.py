import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))
from learning.improvement_proposal_queue import ProposalQueue,ProposalRecord


def proposal(company="fenix", status="OPEN"):
    return ProposalRecord(company,"p","source","WEB_SEO","LAB","1.0.0","summary","e://1","LAB_DIAGNOSTIC_ONLY",False,0.0,"P1",status)


class TerminalTransitionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.db=Path(self.temp.name)/"q.db"
        self.queue=ProposalQueue(self.db)
    def tearDown(self):
        self.queue.close();self.temp.cleanup()

    def test_closed_cannot_reopen(self):
        fp=self.queue.upsert(proposal());self.queue.set_status(fp,"CLOSED")
        with self.assertRaises(PermissionError):self.queue.set_status(fp,"OPEN")
        self.assertEqual(self.queue.conn.execute("SELECT status FROM proposal_queue").fetchone()[0],"CLOSED")

    def test_human_required_cannot_reopen(self):
        fp=self.queue.upsert(proposal());self.queue.set_status(fp,"HUMAN_REQUIRED")
        with self.assertRaises(PermissionError):self.queue.set_status(fp,"WAITING_TEST")
        self.assertEqual(self.queue.conn.execute("SELECT status FROM proposal_queue").fetchone()[0],"HUMAN_REQUIRED")

    def test_blocked_cannot_reopen(self):
        fp=self.queue.upsert(proposal());self.queue.set_status(fp,"BLOCKED")
        with self.assertRaises(PermissionError):self.queue.set_status(fp,"WAITING_TEST")
        self.assertEqual(self.queue.conn.execute("SELECT status FROM proposal_queue").fetchone()[0],"BLOCKED")

    def test_waiting_test_cannot_rollback_to_open(self):
        fp=self.queue.upsert(proposal());self.queue.set_status(fp,"WAITING_TEST")
        with self.assertRaises(PermissionError):self.queue.set_status(fp,"OPEN")
        self.assertEqual(self.queue.list_open()[0].status,"WAITING_TEST")

    def test_explicit_progress_to_closed_allowed(self):
        fp=self.queue.upsert(proposal())
        self.queue.set_status(fp,"WAITING_TEST")
        self.queue.set_status(fp,"CLOSED")
        self.assertEqual(self.queue.list_open(),())

    def test_terminal_idempotent_repeat(self):
        fp=self.queue.upsert(proposal());self.queue.set_status(fp,"CLOSED")
        self.queue.set_status(fp,"CLOSED")
        self.assertEqual(self.queue.conn.execute("SELECT status,json_extract(payload_json,'$.status') FROM proposal_queue").fetchone(),("CLOSED","CLOSED"))

    def test_concurrent_connection_cannot_reopen(self):
        fp=self.queue.upsert(proposal());self.queue.set_status(fp,"HUMAN_REQUIRED")
        other=ProposalQueue(self.db)
        try:
            with self.assertRaises(PermissionError):other.set_status(fp,"OPEN")
        finally:other.close()
        self.assertEqual(self.queue.conn.execute("SELECT status FROM proposal_queue").fetchone()[0],"HUMAN_REQUIRED")

    def test_legacy_json_drift_repaired_by_explicit_status(self):
        fp=self.queue.upsert(proposal())
        self.queue.conn.execute("UPDATE proposal_queue SET status='WAITING_TEST',payload_json=json_set(payload_json,'$.status','OPEN')")
        self.queue.conn.commit()
        self.queue.set_status(fp,"CLOSED")
        self.assertEqual(self.queue.conn.execute("SELECT status,json_extract(payload_json,'$.status') FROM proposal_queue").fetchone(),("CLOSED","CLOSED"))

    def test_company_isolation_of_separate_keys(self):
        a=self.queue.upsert(proposal("fenix"));b=self.queue.upsert(proposal("aion"))
        self.queue.set_status(a,"CLOSED")
        self.assertEqual(self.queue.list_open(company_id="aion")[0].company_id,"aion")
        self.assertEqual(self.queue.conn.execute("SELECT status FROM proposal_queue WHERE fingerprint=?",(b,)).fetchone()[0],"OPEN")

if __name__=='__main__':unittest.main()