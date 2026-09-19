from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlparse

ENGINE_ID="WAUD-001"

def audit_website(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    scan=payload.get("scan_result") or {}
    if not company_id: raise ValueError("company_id required")
    if not isinstance(scan,dict): raise ValueError("scan_result must be object")
    if str(scan.get("company_id",""))!=company_id: raise ValueError("cross-company scan denied")
    if str(scan.get("engine_id",""))!="SCAN-001": raise ValueError("SCAN-001 evidence required")
    pages=scan.get("pages") or []
    if not isinstance(pages,list): raise ValueError("scan pages must be list")

    audited=[]
    for page in pages:
        if not isinstance(page,dict): continue
        url=str(page.get("final_url") or page.get("url") or "")
        issues=[]
        scheme=urlparse(url).scheme.lower()
        if scheme!="https": issues.append("HTTPS_MISSING")
        if not page.get("checked"): issues.append(str(page.get("status") or "NOT_CHECKED"))
        code=page.get("http_status")
        if isinstance(code,int) and code>=400: issues.append("HTTP_ERROR")
        ctype=str(page.get("content_type","")).lower()
        if page.get("checked") and "html" not in ctype: issues.append("NON_HTML_CONTENT")
        if not page.get("content_hash"): issues.append("MISSING_CONTENT_HASH")
        size=int(page.get("bytes") or 0)
        if size>1_000_000: issues.append("LARGE_HTML_PAYLOAD")
        audited.append({
            "url":url,
            "source_status":str(page.get("status","")),
            "http_status":code,
            "content_type":ctype,
            "content_hash":str(page.get("content_hash","")),
            "bytes":size,
            "issues":sorted(set(issues)),
            "issue_count":len(set(issues)),
        })

    issue_count=sum(x["issue_count"] for x in audited)
    checked=sum(1 for x in audited if x["source_status"]=="OK")
    confidence=round(checked/max(1,len(audited)),3)
    canonical=json.dumps({"company_id":company_id,"audited":audited},sort_keys=True,separators=(",",":"))
    return {
        "record_type":"website_audit",
        "company_id":company_id,
        "engine_id":ENGINE_ID,
        "environment":"LAB",
        "version":str(payload.get("version","1.0.0")),
        "source_engine_id":"SCAN-001",
        "source_evidence_hash":"sha256:"+hashlib.sha256(json.dumps(scan,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
        "pages":audited,
        "page_count":len(audited),
        "issue_count":issue_count,
        "confidence":confidence,
        "status":"GREEN" if audited and confidence==1.0 else "PARTIAL" if audited else "WAITING",
        "audit_scope":["transport","fetchability","content_type","content_hash","payload_size"],
        "not_claimed":["full_crawl","core_web_vitals","structured_data","indexation","conversion","analytics"],
        "read_only":True,
        "external_mutation_allowed":False,
        "cost_eur":0.0,
        "evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_WAUD_REQUEST_ROOT",".cerebro-runtime/website-audit-requests"))
    out=Path(os.environ.get("CEREBRO_WAUD_RESULT_ROOT",".cerebro-runtime/website-audit-results"))
    out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        result=audit_website(payload)
        target=out/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
