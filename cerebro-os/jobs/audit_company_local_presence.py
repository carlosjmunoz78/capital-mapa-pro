from __future__ import annotations
import hashlib,json,os
from pathlib import Path
ENGINE_ID="LOCALP-001"

def audit_local_presence(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    listings=payload.get("listings") or []
    if not company_id: raise ValueError("company_id required")
    if not isinstance(listings,list): raise ValueError("listings must be list")
    rows=[]
    for item in listings:
        if not isinstance(item,dict): raise ValueError("listing must be object")
        provider=str(item.get("provider","")).strip()
        name=str(item.get("name","")).strip()
        locality=str(item.get("locality","")).strip()
        if not provider or not name: raise ValueError("listing requires provider and name")
        nap={"name":name,"address":str(item.get("address","")).strip(),"phone":str(item.get("phone","")).strip()}
        evidence_refs=sorted({str(x).strip() for x in (item.get("evidence_refs") or []) if str(x).strip()})
        issues=[]
        if not nap["address"]: issues.append("ADDRESS_UNKNOWN")
        if not nap["phone"]: issues.append("PHONE_UNKNOWN")
        if not locality: issues.append("LOCALITY_UNKNOWN")
        if not evidence_refs: issues.append("MISSING_EVIDENCE")
        rows.append({"provider":provider,"name":name,"locality":locality,"nap":nap,"categories":sorted({str(x).strip() for x in (item.get("categories") or []) if str(x).strip()}),"evidence_refs":evidence_refs,"issues":sorted(set(issues))})
    rows=sorted(rows,key=lambda x:(x["provider"].lower(),x["name"].lower()))
    inconsistent=[]
    canonical_nap={(r["nap"]["name"].lower(),r["nap"]["address"].lower(),r["nap"]["phone"].lower()) for r in rows if all(r["nap"].values())}
    if len(canonical_nap)>1: inconsistent.append("NAP_INCONSISTENT")
    canonical=json.dumps({"company_id":company_id,"listings":rows},sort_keys=True,separators=(",",":"))
    return {
      "record_type":"local_presence_audit","company_id":company_id,"engine_id":ENGINE_ID,
      "environment":str(payload.get("environment","LAB")).upper(),"version":str(payload.get("version","1.0.0")),
      "listings":rows,"listing_count":len(rows),"global_issues":inconsistent,
      "status":"GREEN" if rows and not inconsistent and all(not r["issues"] for r in rows) else "PARTIAL" if rows else "WAITING",
      "read_only":True,"external_mutation_allowed":False,"cost_eur":0.0,
      "not_claimed":["google_business_verification","review_sentiment","map_pack_rank","citation_scan"],
      "evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_LOCALP_REQUEST_ROOT",".cerebro-runtime/local-presence-requests"))
    out=Path(os.environ.get("CEREBRO_LOCALP_RESULT_ROOT",".cerebro-runtime/local-presence-results")); out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        result=audit_local_presence(json.loads(path.read_text(encoding="utf-8")))
        target=out/f'{result["company_id"]}.json'; target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); written.append(target)
    return written
if __name__=="__main__":
    for p in run(): print(p)
