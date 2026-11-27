"""Independent read-only acceptance verifier. Not a live Supervisor or Tribunal.
It validates the actual result and durable evidence, never creates or signs them.
"""
import hashlib,json,sqlite3,re
from pathlib import Path
from contextlib import closing
from gateway import catalog_read as c
from registry.canonical_loader import load_canonical_registry

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def verify_execution(*, store_path, request_id, actor_id, result, now_epoch, grant_ref=None):
    def reject(reason):
        return {"status":"BLOCKED","reason":reason,"deployment_authorized":False}
    try:
        if any(type(v) is not str or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}",v)
               for v in (request_id,actor_id)) or type(now_epoch) is not int or now_epoch<0:
            return reject("IDENTITY_OR_CLOCK_INVALID")
        blob=c.SOURCE.read_bytes()
        if hashlib.sha256(blob).hexdigest()!=c.SOURCE_SHA256:
            return reject("CATALOG_DRIFT")
        catalog=load_canonical_registry(c.SOURCE)
        if c.SOURCE.read_bytes()!=blob or catalog!=json.loads(blob):
            return reject("CATALOG_DRIFT")
        expected=dict(status="CATALOG_READ",company_id=c.COMPANY,engine_id=c.ENGINE,
            environment=c.ENV,version=c.VERSION,capability=c.CAPABILITY,
            catalog_scope="GLOBAL_LOGICAL_DEFINITIONS",source_schema=catalog["schema_version"],
            source_sha256=c.SOURCE_SHA256,engine_ids=tuple(catalog["engine_ids"]),count=177,
            operational_instances_certified=False,external_mutation_allowed=False,deployment_authorized=False)
        if type(result) is not dict or digest(result)!=digest(expected):
            return reject("RESULT_MISMATCH")
        h=digest(expected)
        ref="sha256:"+h
        meta=dict(company_id=c.COMPANY,engine_id=c.ENGINE,environment=c.ENV,version=c.VERSION,
            capability=c.CAPABILITY,status="CATALOG_READ",source_sha256=c.SOURCE_SHA256,
            result_sha256=h,request_id=request_id,user_id=actor_id,action=c.CAPABILITY,
            result="CATALOG_READ",evidence_ref=ref)
        if grant_ref is not None:
            if type(grant_ref) is not str or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", grant_ref):
                return reject("GRANT_REFERENCE_INVALID")
            meta["grant_ref"] = grant_ref
        path=Path(store_path).resolve(strict=True)
        with closing(sqlite3.connect(path.as_uri()+"?mode=ro",uri=True,timeout=2)) as db:
            db.execute("PRAGMA query_only=ON")
            db.execute("PRAGMA trusted_schema=OFF")
            db.execute("BEGIN")
            a=db.execute("SELECT company_id,user_id,engine_id,action,result,evidence_ref,environment,version,timestamp_epoch,metadata_json FROM console_audit WHERE request_id=?",(request_id,)).fetchall()
            b=db.execute("SELECT company_id,engine_id,status,evidence_ref,environment,version,timestamp_epoch FROM console_history WHERE request_id=?",(request_id,)).fetchall()
            if len(a)!=1 or len(b)!=1:
                return reject("EVIDENCE_MISSING")
            a,b=a[0],b[0]
            if (a[:8]!=(c.COMPANY,actor_id,c.ENGINE,c.CAPABILITY,"CATALOG_READ",ref,c.ENV,c.VERSION)
                or type(a[8]) is not int or not 0<=a[8]<=now_epoch or json.loads(a[9])!=meta
                or b!=(c.COMPANY,c.ENGINE,"CATALOG_READ",ref,c.ENV,c.VERSION,a[8])):
                return reject("EVIDENCE_MISMATCH")
        return {"status":"ACCEPTANCE_READBACK_VERIFIED","environment":"PREPROD",
            "result_sha256":h,"request_id":request_id,"deployment_authorized":False}
    except Exception:
        return reject("EVIDENCE_UNAVAILABLE")
