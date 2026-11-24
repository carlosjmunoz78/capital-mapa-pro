import sqlite3, pathlib, tempfile, unittest, hashlib
SQL=(pathlib.Path(__file__).resolve().parents[1]/'factory'/'fact001_factory_candidates_lab_v1.sql').read_text()
ROW=('fenix','SUP-001','LAB','0.1.0','864066db006ecaf7f79a162f2af63e1c0a28fa98','32cbc692ed0280751ea12883c3a5664e81a9ff77',9,'OPERATOR_VERIFIED_FACTORY_ARTIFACTS')
INSERT='INSERT INTO fact001_factory_candidates_lab_v1(company_id,engine_id,environment,version,source_commit,evidence_blob,artifact_count,registration_method) VALUES(?,?,?,?,?,?,?,?)'
class Registry(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.p=pathlib.Path(self.t.name)/'lab.sqlite';self.db=sqlite3.connect(self.p);self.addCleanup(self.db.close);self.db.execute('CREATE TABLE fact001_lab_engine_instances_v1(company_id TEXT,engine_id TEXT)');self.db.execute("INSERT INTO fact001_lab_engine_instances_v1 VALUES('fenix-capital','SUP-001')");self.db.commit();self.db.executescript(SQL)
 def test_insert(self):
  self.db.execute(INSERT,ROW);self.assertEqual(self.db.execute('SELECT state,authority_verified,execution_granted,production_authorized,media_dispatch_enabled,cost_ceiling_eur FROM fact001_factory_candidates_lab_v1').fetchone(),('CANDIDATE_REGISTERED',0,0,0,0,0))
 def test_duplicate(self):
  self.db.execute(INSERT,ROW)
  with self.assertRaises(sqlite3.IntegrityError): self.db.execute(INSERT,ROW)
 def test_scope(self):
  for i,v in [(0,'aion'),(0,'fenix-capital'),(2,'PROD'),(2,'PREPROD'),(1,'--'),(1,'abc-001'),(1,'A--B')]:
   with self.subTest(i=i,v=v),self.assertRaises(sqlite3.IntegrityError): self.db.execute(INSERT,ROW[:i]+(v,)+ROW[i+1:])
 def test_grants(self):
  self.db.execute(INSERT,ROW)
  for col in ['authority_verified','execution_granted','production_authorized','media_dispatch_enabled','cost_ceiling_eur']:
   with self.subTest(col=col),self.assertRaises(sqlite3.IntegrityError): self.db.execute(f'UPDATE fact001_factory_candidates_lab_v1 SET {col}=1')
 def test_hashes(self):
  for i,v in [(4,'z'*40),(5,'bad'),(6,0),(7,'AUTONOMOUS_FACT')]:
   with self.subTest(i=i,v=v),self.assertRaises(sqlite3.IntegrityError): self.db.execute(INSERT,ROW[:i]+(v,)+ROW[i+1:])
 def test_preserve_legacy(self):
  self.db.execute(INSERT,ROW);self.assertEqual(self.db.execute('SELECT * FROM fact001_lab_engine_instances_v1').fetchall(),[('fenix-capital','SUP-001')])
 def test_restore(self):
  self.db.execute(INSERT,ROW);self.db.commit();p=self.p.with_name('restore.sqlite');b=sqlite3.connect(p);self.db.backup(b);self.assertEqual(b.execute('PRAGMA integrity_check').fetchone(),('ok',));self.assertEqual(b.execute('SELECT count(*) FROM fact001_factory_candidates_lab_v1').fetchone(),(1,));b.close()
 def test_scoped_rollback(self):
  self.db.execute(INSERT,ROW);self.db.execute("UPDATE fact001_factory_candidates_lab_v1 SET state='RETIRED' WHERE company_id=? AND engine_id=? AND environment=? AND version=? AND source_commit=? AND evidence_blob=? AND state='CANDIDATE_REGISTERED'",ROW[:6]);self.assertEqual(self.db.execute('SELECT state FROM fact001_factory_candidates_lab_v1').fetchone(),('RETIRED',));self.assertEqual(self.db.execute('SELECT count(*) FROM fact001_lab_engine_instances_v1').fetchone(),(1,))
if __name__=='__main__': unittest.main(verbosity=2)
