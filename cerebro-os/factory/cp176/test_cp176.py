"""CP176: local CP131 contract integration. Synthetic independent role keys only."""
import unittest,sqlite3,tempfile,json,hmac,hashlib,secrets,time
from pathlib import Path
from remote_read_proof_cp82 import verify_authorized_private_read
def canonical(x):return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
class Contract(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.a=sqlite3.connect(str(Path(self.tmp.name)/"iam.sqlite"))
  self.f=sqlite3.connect(str(Path(self.tmp.name)/"fact.sqlite"))
  self.j=sqlite3.connect(str(Path(self.tmp.name)/"jarvis.sqlite"))
  for db in (self.a,self.f,self.j):self.addCleanup(db.close);db.execute("CREATE TABLE evidence(id TEXT PRIMARY KEY,body TEXT NOT NULL)")
  self.now=int(time.time());self.r="CP176-LOCAL-TEST-001";self.ref="policy://cp176/"+self.r
  self.jkey=secrets.token_bytes(32);self.fkey=secrets.token_bytes(32)
  s=dict(request_id=self.r,company_id="fenix",engine_id="FACT-001",environment="LAB",version="1.0.0",capability="FACT.INVENTORY.READ",read_only=True,external_mutation_allowed=False,cost_ceiling_eur=0,emitted_at_epoch=self.now,schema="cerebro.private-read.v1",principal_id="iam:jarvis-cp176-fixture",policy_receipt_ref=self.ref)
  self.jarvis=dict(s,origin="JARVIS",target="FACT-001",owner_access_verified=True,iam_policy="ALLOW_READ_ONLY")
  self.fact=dict(s,origin="FACT-001",target="JARVIS",status="COMPLETED",result_sha256=hashlib.sha256(b"synthetic inventory").hexdigest())
  self.grant=dict(s,issuer_id="iam:authority-cp176-fixture",decision="ALLOW_READ_ONLY",verified=True,active=True,revoked=False,issued_at_epoch=self.now-1,expires_at_epoch=self.now+119)
  self.put(self.a,self.ref,self.grant);self.put(self.f,self.r,self.fact);self.put(self.j,self.r,self.jarvis);self.calls=[]
 def put(self,db,key,obj):
  db.execute("INSERT INTO evidence VALUES(?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body",(key,json.dumps(obj)));db.commit()
 def get(self,db,key):
  row=db.execute("SELECT body FROM evidence WHERE id=?",(key,)).fetchone();return json.loads(row[0]) if row else None
 def gr(self,ref):self.calls.append("IAM");return self.get(self.a,ref)
 def fr(self,r):self.calls.append("FACT");return self.get(self.f,r)
 def sig(self,b,k):return hmac.new(k,canonical(b),hashlib.sha256).hexdigest()
 def run_pair(self,**kw):
  q=dict(jarvis=self.get(self.j,self.r),fact=self.fact,jarvis_signature=self.sig(self.jarvis,self.jkey),fact_signature=self.sig(self.fact,self.fkey),jarvis_key=self.jkey,fact_key=self.fkey,company_id="fenix",request_id=self.r,now_epoch=self.now,persisted_fact_reader=self.fr,trusted_grant_reader=self.gr,expected_principal=self.jarvis["principal_id"],expected_issuer=self.grant["issuer_id"],canonical_company_id="fenix")
  q.update(kw);return verify_authorized_private_read(**q)
 def test_01_live(self):
  r=self.run_pair();self.assertEqual(r["status"],"VERIFIED_AUTHORIZED_PAIR");self.assertFalse(r["promotion_allowed"]);self.assertEqual(self.calls,["IAM","FACT"])
 def test_02_revoked(self):
  self.put(self.a,self.ref,dict(self.grant,active=False,revoked=True))
  with self.assertRaisesRegex(PermissionError,"GRANT_POLICY"):self.run_pair()
  self.assertEqual(self.calls,["IAM"])
 def test_03_jarvis_bad(self):
  with self.assertRaisesRegex(PermissionError,"JARVIS receipt MAC"):self.run_pair(jarvis_signature="0"*64)
  self.assertEqual(self.calls,[])
 def test_04_fact_bad(self):
  with self.assertRaisesRegex(PermissionError,"FACT receipt MAC"):self.run_pair(fact_signature="0"*64)
  self.assertEqual(self.calls,[])
 def test_05_shared_key(self):
  with self.assertRaisesRegex(ValueError,"distinct service keys"):self.run_pair(fact_key=self.jkey)
  self.assertEqual(self.calls,[])
 def test_06_foreign(self):
  with self.assertRaises(PermissionError):self.run_pair(company_id="fenix-capital")
  self.assertEqual(self.calls,[])
 def test_07_stale(self):
  with self.assertRaises(PermissionError):self.run_pair(now_epoch=self.now+120)
  self.assertEqual(self.calls,["IAM"])
 def test_08_storage_changed(self):
  self.put(self.f,self.r,dict(self.fact,result_sha256="0"*64))
  with self.assertRaisesRegex(PermissionError,"persisted FACT receipt mismatch"):self.run_pair()
  self.assertEqual(self.calls,["IAM","FACT"])
 def test_09_wrong_issuer(self):
  self.put(self.a,self.ref,dict(self.grant,issuer_id="iam:other"))
  with self.assertRaisesRegex(PermissionError,"GRANT_SCOPE"):self.run_pair()
  self.assertEqual(self.calls,["IAM"])
 def test_10_grant_missing(self):
  self.a.execute("DELETE FROM evidence");self.a.commit()
  with self.assertRaisesRegex(PermissionError,"GRANT_NOT_FOUND"):self.run_pair()
  self.assertEqual(self.calls,["IAM"])
if __name__=="__main__":unittest.main(verbosity=2)
