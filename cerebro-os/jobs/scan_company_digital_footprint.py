from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import socket
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

MAX_BYTES=1_500_000

def _public_url(url:str)->bool:
    try:
        p=urlparse(url)
        if p.scheme not in {"http","https"} or not p.hostname: return False
        host=p.hostname.lower()
        if host=="localhost" or host.endswith(".localhost"): return False
        try:
            ip=ipaddress.ip_address(host)
            return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast)
        except ValueError:
            return True
    except Exception:
        return False

def _fetch(url:str)->dict:
    if not _public_url(url):
        return {"url":url,"checked":False,"status":"BLOCKED_UNSAFE_URL"}
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"CEREBRO-SCAN-001/0"})
        with urllib.request.urlopen(req,timeout=15) as r:
            data=r.read(MAX_BYTES+1)
            final=str(r.geturl())
            ctype=str(r.headers.get("content-type",""))
            code=int(getattr(r,"status",200))
        if len(data)>MAX_BYTES:
            return {"url":url,"checked":False,"status":"TOO_LARGE"}
        return {
            "url":url,"final_url":final,"checked":True,"status":"OK","http_status":code,
            "content_type":ctype,"content_hash":hashlib.sha256(data).hexdigest(),
            "bytes":len(data),
        }
    except Exception as exc:
        return {"url":url,"checked":False,"status":"FETCH_FAILED","error_type":type(exc).__name__}

def scan_company(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    domains=payload.get("domains") or []
    if not company_id or not isinstance(domains,list):
        raise ValueError("company_id and domains required")
    pages=[]
    for domain in domains:
        d=str(domain).strip()
        if not d: continue
        if "://" not in d: d="https://"+d
        pages.append(_fetch(d))
    checked=sum(1 for x in pages if x["checked"])
    return {
        "record_type":"digital_footprint_scan",
        "company_id":company_id,
        "engine_id":"SCAN-001",
        "environment":"LAB",
        "version":str(payload.get("version","1.0.0")),
        "domains_requested":[str(x) for x in domains],
        "pages":pages,
        "checked_count":checked,
        "status":"GREEN" if pages and checked==len(pages) else "PARTIAL" if checked else "WAITING",
        "discovery_scope":["official_domains"],
        "social_discovery_performed":False,
        "local_presence_discovery_performed":False,
        "external_mutation_allowed":False,
        "production_ready":False,
        "cost_eur":0.0,
    }

def run()->list[Path]:
    source_root=Path(os.environ.get("CEREBRO_COMPANY_SCAN_REQUEST_ROOT",".cerebro-runtime/company-scan-requests"))
    out_root=Path(os.environ.get("CEREBRO_COMPANY_SCAN_RESULT_ROOT",".cerebro-runtime/company-scan-results"))
    out_root.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source_root.glob("*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload,dict): raise ValueError("scan request must be object")
        result=scan_company(payload)
        target=out_root/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
