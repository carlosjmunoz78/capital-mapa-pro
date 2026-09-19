from __future__ import annotations
import hashlib,json,os
from pathlib import Path
ENGINE_ID="SOCAUD-001"
REQUIRED_PROFILE_FIELDS=("platform","handle_or_url")

def audit_social(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    profiles=payload.get("profiles") or []
    if not company_id: raise ValueError("company_id required")
    if not isinstance(profiles,list): raise ValueError("profiles must be list")
    rows=[]
    for item in profiles:
        if not isinstance(item,dict): raise ValueError("profile must be object")
        platform=str(item.get("platform","")).strip().lower()
        handle=str(item.get("handle_or_url","")).strip()
        if not platform or not handle: raise ValueError("profile requires platform and handle_or_url")
        evidence_refs=sorted({str(x).strip() for x in (item.get("evidence_refs") or []) if str(x).strip()})
        issues=[]
        if not evidence_refs: issues.append("MISSING_EVIDENCE")
        if item.get("active") is False: issues.append("INACTIVE_PROFILE")
        if not str(item.get("bio","")).strip(): issues.append("BIO_UNKNOWN")
        if not str(item.get("last_post_at","")).strip(): issues.append("LAST_POST_UNKNOWN")
        rows.append({"platform":platform,"handle_or_url":handle,"active":item.get("active"),"bio":str(item.get("bio","")).strip(),"last_post_at":str(item.get("last_post_at","")).strip(),"evidence_refs":evidence_refs,"issues":sorted(set(issues))})
    rows=sorted(rows,key=lambda x:(x["platform"],x["handle_or_url"]))
    missing=sum(1 for r in rows if r["issues"])
    canonical=json.dumps({"company_id":company_id,"profiles":rows},sort_keys=True,separators=(",",":"))
    return {
        "record_type":"social_media_audit","company_id":company_id,"engine_id":ENGINE_ID,
        "environment":str(payload.get("environment","LAB")).upper(),"version":str(payload.get("version","1.0.0")),
        "profiles":rows,"profile_count":len(rows),"profiles_with_gaps":missing,
        "status":"GREEN" if rows and missing==0 else "PARTIAL" if rows else "WAITING",
        "read_only":True,"external_mutation_allowed":False,"posting_allowed":False,"cost_eur":0.0,
        "not_claimed":["audience_quality","reach","engagement_rate","follower_authenticity","platform_api_verification"],
        "evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_SOCAUD_REQUEST_ROOT",".cerebro-runtime/social-audit-requests"))
    out=Path(os.environ.get("CEREBRO_SOCAUD_RESULT_ROOT",".cerebro-runtime/social-audit-results")); out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        result=audit_social(json.loads(path.read_text(encoding="utf-8")))
        target=out/f'{result["company_id"]}.json'; target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); written.append(target)
    return written
if __name__=="__main__":
    for p in run(): print(p)
