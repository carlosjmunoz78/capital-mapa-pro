from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

def _now()->str:
    raw=os.environ.get("CEREBRO_KNOWLEDGE_NOW")
    if raw:
        return raw
    return datetime.now(timezone.utc).isoformat()

def _knowledge_id(url:str)->str:
    return "official-web:"+hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]

def _provenance_id(company_id:str,url:str,content_hash:str)->str:
    raw="|".join([company_id,"LIVE_SOURCE",url,content_hash])
    return "prv-"+hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]

def run()->list[Path]:
    evidence_root=Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_EVIDENCE_ROOT",
        ".cerebro-runtime/evidence",
    ))
    inventory_root=Path(os.environ.get(
        "CEREBRO_KNOWLEDGE_INVENTORY_ROOT",
        ".cerebro-runtime/knowledge-inventory",
    ))
    inventory_root.mkdir(parents=True,exist_ok=True)
    ttl_days=int(os.environ.get("CEREBRO_PUBLIC_SOURCE_TTL_DAYS","7"))
    if ttl_days<1:
        raise ValueError("TTL must be >= 1")
    written=[]

    for path in sorted(evidence_root.glob("*.business.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload,dict):
            raise ValueError("business evidence must be object")
        company_id=str(payload.get("company_id","")).strip()
        if not company_id:
            raise ValueError("company_id required")

        target=inventory_root/f"{company_id}.json"
        previous={}
        if target.exists():
            prior=json.loads(target.read_text(encoding="utf-8"))
            if not isinstance(prior,list):
                raise ValueError("knowledge inventory must be list")
            for item in prior:
                if str(item.get("company_id",""))!=company_id:
                    raise ValueError("cross-company inventory contamination denied")
                previous[str(item.get("source_uri",""))]=item

        pages=((payload.get("facts") or {}).get("pages") or [])
        next_by_url=dict(previous)
        observed_urls=set()
        for page in pages:
            url=str(page.get("url","")).strip()
            if not url:
                continue
            observed_urls.add(url)
            checked=bool(page.get("checked",False))
            old=previous.get(url,{})
            if checked:
                facts=page.get("facts") or {}
                content_hash=str(facts.get("content_hash","")).strip()
                if not content_hash:
                    raise ValueError("checked official page missing content_hash")
                next_by_url[url]={
                    "company_id":company_id,
                    "knowledge_id":_knowledge_id(url),
                    "environment":"LAB",
                    "version":"1.0.0",
                    "kind":"PUBLIC_SOURCE_POINTER",
                    "state":"ACTIVE",
                    "provenance_id":_provenance_id(company_id,url,content_hash),
                    "source_type":"LIVE_SOURCE",
                    "source_uri":url,
                    "verified_at":_now(),
                    "ttl_days":ttl_days,
                    "confidence":float(page.get("confidence",payload.get("confidence",0.0))),
                    "source_available":True,
                    "contradictory_evidence":False,
                    "superseded_by":"",
                    "content_hash":content_hash,
                    "evidence_ref":str(page.get("evidence_ref","")),
                    "external_mutation_allowed":False,
                    "delete_allowed":False,
                }
            elif old:
                stale=dict(old)
                stale["source_available"]=False
                next_by_url[url]=stale

        if not pages and not bool(payload.get("checked",False)):
            for url,old in list(next_by_url.items()):
                stale=dict(old)
                stale["source_available"]=False
                next_by_url[url]=stale

        target.write_text(json.dumps(
            sorted(next_by_url.values(),key=lambda x:str(x.get("knowledge_id",""))),
            sort_keys=True,indent=2
        )+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for path in run(): print(path)
