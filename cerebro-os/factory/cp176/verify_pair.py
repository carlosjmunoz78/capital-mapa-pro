import sys,json,sqlite3,pathlib
from remote_read_proof_cp82 import verify_authorized_private_read
v=json.load(sys.stdin);d=pathlib.Path(v["dir"])
def read(name,key):
 with sqlite3.connect(d/name) as c:
  r=c.execute("SELECT body FROM evidence WHERE id=?",(key,)).fetchone()
  return json.loads(r[0]) if r else None
j=v["jarvis"];f=v["fact"]
assert read("jarvis.sqlite",v["rid"])==j
out=verify_authorized_private_read(jarvis=j["body"],fact=f["body"],jarvis_signature=j["mac"],fact_signature=f["mac"],jarvis_key=bytes.fromhex(v["jkey"]),fact_key=bytes.fromhex(v["fkey"]),company_id="fenix",request_id=v["rid"],now_epoch=v["now"],persisted_fact_reader=lambda rid:read("fact.sqlite",rid)["body"],trusted_grant_reader=lambda ref:read("iam.sqlite",ref),expected_principal=v["principal"],expected_issuer=v["issuer"],canonical_company_id="fenix")
print(json.dumps(out))
