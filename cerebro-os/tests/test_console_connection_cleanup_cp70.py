import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'console'))
from persistent_store import ConsoleStore

class ConsoleConnectionCP70(unittest.TestCase):
    def row(self,req='req-1'):
        return {'request_id':req,'user_id':'actor','company_id':'fenix',
                'environment':'LAB','version':'1.0.0', 'engine_id':'FACT-001',
                'result':'GREEN','action':'SCAFFOLD','evidence_ref':'synthetic'}

    def test_all_console_connections_closed_even_with_errors(self):
        seen=[];closed=[]
        class Tracked(sqlite3.Connection):
            def close(self):
                closed.append(id(self));super().close()
        underlying=sqlite3.connect
        def track(*args,**kw):
            c=underlying(*args,**kw,factory=Tracked)
            seen.append(id(c));return c
        with tempfile.TemporaryDirectory() as d, patch.object(sqlite3,'connect',side_effect=track):
            store=ConsoleStore(Path(d)/'c.db')
            store.record(self.row(),now_epoch=100)
            store.record(self.row(),now_epoch=101)
            self.assertEqual(len(store.audit_by_company('fenix')),1)
            self.assertEqual(len(store.history_by_company('fenix')),1)
            self.assertEqual(store.counts(),{'audit':1,'history':1})
            with self.assertRaises(PermissionError):
                store.record({**self.row(),'company_id':'aion'},now_epoch=102)
            with self.assertRaises(ValueError):
                store.record({**self.row('req-2'),'accessToken':'synthetic'},now_epoch=103)
            self.assertEqual(store.counts(),{'audit':1,'history':1})
        self.assertGreaterEqual(len(seen),7)
        self.assertCountEqual(seen,closed)

    def test_cross_process_reopen_does_not_change_audit_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'console.sqlite'
            first=ConsoleStore(path);first.record(self.row(),now_epoch=100)
            second=ConsoleStore(path)
            self.assertEqual(second.counts(),{'audit':1,'history':1})
            self.assertEqual(second.audit_by_company('fenix')[0]['result'],'GREEN')
            self.assertEqual(second.history_by_company('aion'),())

if __name__=='__main__':unittest.main()