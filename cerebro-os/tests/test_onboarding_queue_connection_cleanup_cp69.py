import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from runtime.onboarding_queue import OnboardingQueue

class CP69ConnectionCleanupTests(unittest.TestCase):
    def test_all_read_write_connections_are_closed(self):
        opened=[];closed=[]
        class Tracked(sqlite3.Connection):
            def close(self):
                closed.append(id(self))
                super().close()
        original=sqlite3.connect
        def make_connection(*args,**kwargs):
            c=original(*args,**kwargs,factory=Tracked)
            opened.append(id(c))
            return c
        with tempfile.TemporaryDirectory() as tmp, patch.object(sqlite3,'connect',side_effect=make_connection):
            p=Path(tmp)/'queue.db'
            q=OnboardingQueue(p)
            q.enqueue(request_id='r-a',company_id='fenix',version='1.0.0',payload={'topic':'synthetic'},now_epoch=1)
            q.enqueue(request_id='r-b',company_id='aion',version='1.0.0',payload={'topic':'synthetic'},now_epoch=1)
            self.assertIsNotNone(q.get('r-a'))
            self.assertEqual(len(q.by_company('fenix')),1)
            self.assertEqual(q.stats(now_epoch=2)['total'],2)
            self.assertIsNotNone(q.next_due_epoch(now_epoch=2))
            a=q.claim(now_epoch=2)
            self.assertEqual(a.company_id,'fenix')
            q.retry_or_dead_letter(request_id=a.request_id,result={'status':'RETRY'},now_epoch=5)
            self.assertEqual(q.get('r-a').status,'QUEUED')
            b=q.claim(now_epoch=7)
            self.assertEqual(b.company_id,'aion')
            q.complete(request_id=b.request_id,status='WAITING',result={'company_id':'aion'},now_epoch=7)
            q.requeue(request_id=b.request_id,payload={'company_id':'aion'},now_epoch=10)
            self.assertEqual(q.get('r-b').company_id,'aion')
            self.assertEqual(q.by_company('fenix')[0].company_id,'fenix')
            with self.assertRaises(ValueError):
                q.enqueue(request_id='r-a',company_id='fenix',version='1.0.0',payload={},now_epoch=10)
            reopened=OnboardingQueue(p)
            self.assertEqual(reopened.stats(now_epoch=10)['total'],2)
        self.assertGreaterEqual(len(opened),14)
        self.assertCountEqual(opened,closed)

    def test_connection_closes_on_sqlite_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            q=OnboardingQueue(Path(tmp)/'q.db')
            observed=[]
            class Wrapped:
                def __init__(self,conn):self.conn=conn
                def __enter__(self):self.conn.__enter__();return self
                def __exit__(self,*args):return self.conn.__exit__(*args)
                def execute(self,sql,*args):
                    if 'INSERT INTO onboarding_requests' in sql:
                        raise sqlite3.OperationalError('synthetic_sql_error')
                    return self.conn.execute(sql,*args)
                def close(self):observed.append('closed');self.conn.close()
            original=q._connect
            with patch.object(q,'_connect',side_effect=lambda:Wrapped(original())):
                with self.assertRaisesRegex(sqlite3.OperationalError,'synthetic_sql_error'):
                    q.enqueue(request_id='r',company_id='fenix',version='1.0.0',payload={},now_epoch=1)
            self.assertEqual(observed,['closed'])
            self.assertEqual(q.stats(now_epoch=2)['total'],0)

    def test_scope_and_retry_survive_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'q.db'
            a=OnboardingQueue(path)
            a.enqueue(request_id='req-fenix',company_id='fenix',version='1.0.0',payload={'company_id':'fenix'},now_epoch=1)
            a.enqueue(request_id='req-aion',company_id='aion',version='1.0.0',payload={'company_id':'aion'},now_epoch=1)
            first=a.claim(now_epoch=2)
            self.assertIsNotNone(first)
            a.retry_or_dead_letter(request_id=first.request_id,result={'company_id':first.company_id},now_epoch=3,base_backoff_seconds=5)
            b=OnboardingQueue(path)
            self.assertEqual(b.get('req-fenix').company_id,'fenix')
            self.assertEqual(b.get('req-aion').company_id,'aion')
            self.assertEqual(len(b.by_company('fenix')),1)
            self.assertEqual(len(b.by_company('aion')),1)
            self.assertEqual(b.get(first.request_id).status,'QUEUED')

if __name__=='__main__':unittest.main()