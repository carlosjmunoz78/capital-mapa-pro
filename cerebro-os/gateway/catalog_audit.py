"""Offline audit adapter for FACT.CATALOG.READ, using the existing ConsoleStore.

No authentication, membership issuance, live routes, recovery of historical data,
or promotion. Caller identity and policy must come from an authorized runtime.
Only for a separately provisioned catalog rehearsal store.
"""
import json
import re
import sqlite3
from pathlib import Path
from contextlib import closing
from console.persistent_store import ConsoleStore
from gateway import catalog_read as catalog

def persist_catalog_audit(store, *, request_id, user_id, now_epoch, row, grant_ref=None):
    """Return True only after both existing store records match exact metadata."""
    if type(store) is not ConsoleStore:
        return False
    if any(type(x) is not str or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}",x)
           for x in (request_id,user_id)):
        return False
    if type(now_epoch) is not int or now_epoch<0:
        return False
    if type(row) is not dict or set(row)!={"company_id","engine_id","environment","version",
            "capability","status","source_sha256","result_sha256"}:
        return False
    if any(row.get(k)!=v for k,v in {"company_id":catalog.COMPANY,"engine_id":catalog.ENGINE,
            "environment":catalog.ENV,"version":catalog.VERSION,"capability":catalog.CAPABILITY,
            "status":"CATALOG_READ","source_sha256":catalog.SOURCE_SHA256}.items()):
        return False
    if type(row["result_sha256"]) is not str or not re.fullmatch(r"[0-9a-f]{64}",row["result_sha256"]):
        return False
    audit={**row,"request_id":request_id,"user_id":user_id,"action":catalog.CAPABILITY,
           "result":row["status"],"evidence_ref":"sha256:"+row["result_sha256"]}
    if grant_ref is not None:
        if type(grant_ref) is not str or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", grant_ref):
            return False
        audit["grant_ref"] = grant_ref
    try:
        path=Path(store.path).resolve(strict=True)
        if not path.is_file():
            return False
        store.record(audit,now_epoch=now_epoch)
        # ConsoleStore's legacy replay is scope-idempotent, not payload-idempotent.
        # Verify full metadata and history before releasing the result.
        with closing(sqlite3.connect(path.as_uri()+"?mode=ro",uri=True,timeout=2)) as db:
            db.execute("BEGIN")
            a=db.execute("SELECT company_id,user_id,engine_id,action,result,evidence_ref,environment,version,timestamp_epoch,metadata_json FROM console_audit WHERE request_id=?",(request_id,)).fetchone()
            h=db.execute("SELECT company_id,engine_id,status,evidence_ref,environment,version,timestamp_epoch FROM console_history WHERE request_id=?",(request_id,)).fetchone()
            expected=(catalog.COMPANY,user_id,catalog.ENGINE,catalog.CAPABILITY,"CATALOG_READ",audit["evidence_ref"],catalog.ENV,catalog.VERSION)
            return bool(a and h and a[:8]==expected and type(a[8]) is int and 0<=a[8]<=now_epoch
                and json.loads(a[9])==audit and h==(catalog.COMPANY,catalog.ENGINE,
                "CATALOG_READ",audit["evidence_ref"],catalog.ENV,catalog.VERSION,a[8]))
    except (OSError,ValueError,TypeError,PermissionError,sqlite3.Error):
        return False

def read_with_audit(request, *, store, request_id, user_id, now_epoch, policy_check):
    # Not an identity verifier; no request-derived policy default.
    return catalog.read_catalog(request,policy_check=policy_check,
        audit_sink=lambda row:persist_catalog_audit(store,request_id=request_id,
            user_id=user_id,now_epoch=now_epoch,row=row))
