from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

MAX_BYTES=2_000_000

def _now()->str:
    raw=os.environ.get("CEREBRO_REVALIDATION_NOW")
    if raw:
        return raw
    return datetime.now(timezone.utc).isoformat()

def _public_http_url(url:str)->bool:
    try:
        parsed=urlparse(url)
        if parsed.scheme not in {"http","https"} or not parsed.hostname:
            return False
        host=parsed.hostname.lower()
        if host=="localhost" or host.endswith(".localhost"):
            return False
        try:
            ip=ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
        except ValueError:
            pass
        return True
    except Exception:
        return False

def _evidence_hash(source_type:str, source_uri:str, observed_at:str, validated_by:str, content_hash:str, confidence:float)->str:
    raw="|".join([source_type,source_uri,observed_at,validated_by,content_hash,f"{confidence:.6f}"])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def _fetch(url:str)->bytes:
    req=urllib.request.Request(url,headers={"User-Agent":"CEREBRO-RSH-001/0"})
    with urllib.request.urlopen(req,timeout=15) as resp:
        data=resp.read(MAX_BYTES+1)
    if len(data)>MAX_BYTES:
        raise ValueError("source exceeds max bytes")
    return data

def run()->list[Path]:
    queue_root=Path(os.environ.get("CEREBRO_REVALIDATION_ROOT",".cerebro-runtime/revalidation"))
    out_root=Path(os.environ.get("CEREBRO_REVALIDATION_EVIDENCE_ROOT",".cerebro-runtime/revalidation-evidence"))
    summary_root=Path(os.environ.get("CEREBRO_RESEARCH_REFRESH_ROOT",".cerebro-runtime/research-refresh"))
    out_root.mkdir(parents=True,exist_ok=True)
    summary_root.mkdir(parents=True,exist_ok=True)
    written=[]
    for qpath in sorted(queue_root.glob("*.json")):
        queue=json.loads(qpath.read_text(encoding="utf-8"))
        if not isinstance(queue,dict): raise ValueError("revalidation queue must be object")
        company_id=str(queue.get("company_id","")).strip()
        if not company_id: raise ValueError("company_id required")
        company_out=out_root/company_id
        company_out.mkdir(parents=True,exist_ok=True)
        results=[]
        for item in queue.get("items") or []:
            if str(item.get("company_id",""))!=company_id:
                raise ValueError("cross-company research item denied")
            knowledge_id=str(item.get("knowledge_id","")).strip()
            source_uri=str(item.get("source_uri","")).strip()
            source_type=str(item.get("source_type","")).strip().upper()
            confidence=float(item.get("confidence",0.0))
            result={"knowledge_id":knowledge_id,"engine_id":"RSH-001","source_uri":source_uri,"source_type":source_type}
            if not source_uri or not source_type:
                result.update({"status":"WAITING_DISCOVERY","reason":"SOURCE_CONTEXT_MISSING"})
                results.append(result); continue
            if not _public_http_url(source_uri):
                result.update({"status":"BLOCKED","reason":"UNSAFE_OR_UNSUPPORTED_SOURCE_URI"})
                results.append(result); continue
            try:
                data=_fetch(source_uri)
                content_hash=hashlib.sha256(data).hexdigest()
                observed_at=_now()
                validated_by="RSH-001:HTTP_REVALIDATION_V0"
                packet={
                    "company_id":company_id,
                    "knowledge_id":knowledge_id,
                    "engine_id":"RSH-001",
                    "source_type":source_type,
                    "source_uri":source_uri,
                    "observed_at":observed_at,
                    "validated_by":validated_by,
                    "content_hash":content_hash,
                    "confidence":confidence,
                    "evidence_hash":_evidence_hash(source_type,source_uri,observed_at,validated_by,content_hash,confidence),
                    "read_only_fetch":True,
                    "external_mutation_allowed":False,
                    "auto_promote_allowed":False,
                }
                ep=company_out/f"{knowledge_id}.json"
                ep.write_text(json.dumps(packet,sort_keys=True,indent=2)+"\n",encoding="utf-8")
                written.append(ep)
                result.update({"status":"FETCHED","evidence_ref":f"file://{ep}","content_hash":content_hash})
            except Exception as exc:
                result.update({"status":"WAITING","reason":"FETCH_FAILED","error_type":type(exc).__name__})
            results.append(result)
        summary=summary_root/f"{company_id}.json"
        summary.write_text(json.dumps({
            "record_type":"knowledge_revalidation_research_refresh",
            "company_id":company_id,
            "engine_id":"RSH-001",
            "results":results,
            "external_mutation_allowed":False,
            "auto_promote_allowed":False,
            "cost_eur":0.0
        },sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(summary)
    return written

if __name__=="__main__":
    for path in run(): print(path)
