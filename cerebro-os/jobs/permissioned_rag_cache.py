from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

TOKEN_RE=re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9_\-]{2,}")
VALID_SCOPES={"GLOBAL","COMPANY"}


def _tokens(text:str)->set[str]:
    return {m.group(0).lower() for m in TOKEN_RE.finditer(text or "")}


def _doc_id(company_id:str, source_kind:str, source_id:str)->str:
    return "rag-"+hashlib.sha256("|".join([company_id,source_kind,source_id]).encode("utf-8")).hexdigest()[:24]


def build_index()->list[Path]:
    inventory_root=Path(os.environ.get("CEREBRO_KNOWLEDGE_INVENTORY_ROOT",".cerebro-runtime/knowledge-inventory"))
    ledger_root=Path(os.environ.get("CEREBRO_KNOWLEDGE_LAB_LEDGER_ROOT",".cerebro-runtime/knowledge-lab-ledger"))
    index_root=Path(os.environ.get("CEREBRO_RAG_INDEX_ROOT",".cerebro-runtime/rag-index"))
    index_root.mkdir(parents=True,exist_ok=True)
    companies=set(p.stem for p in inventory_root.glob("*.json"))
    companies.update(p.stem for p in ledger_root.glob("*.jsonl"))
    written=[]

    for company_id in sorted(companies):
        docs=[]
        inv=inventory_root/f"{company_id}.json"
        if inv.exists():
            rows=json.loads(inv.read_text(encoding="utf-8"))
            if not isinstance(rows,list): raise ValueError("knowledge inventory must be list")
            for r in rows:
                if str(r.get("company_id",""))!=company_id: raise ValueError("cross-company inventory denied")
                source_id=str(r.get("knowledge_id","")).strip()
                if not source_id: continue
                searchable=" ".join([
                    source_id,str(r.get("kind","")),str(r.get("source_type","")),
                    str(r.get("source_uri","")),str(r.get("state","")),str(r.get("content_hash",""))
                ])
                docs.append({
                    "doc_id":_doc_id(company_id,"INVENTORY",source_id),
                    "company_id":company_id,
                    "scope":"COMPANY",
                    "source_kind":"INVENTORY",
                    "source_id":source_id,
                    "text":searchable,
                    "tokens":sorted(_tokens(searchable)),
                    "provenance_id":str(r.get("provenance_id","")),
                    "confidence":float(r.get("confidence",0.0)),
                    "canonical":False,
                    "production_ready":False,
                })

        ledger=ledger_root/f"{company_id}.jsonl"
        if ledger.exists():
            for line in ledger.read_text(encoding="utf-8").splitlines():
                if not line.strip(): continue
                r=json.loads(line)
                if str(r.get("company_id",""))!=company_id: raise ValueError("cross-company ledger denied")
                source_id=str(r.get("knowledge_id","")).strip()
                searchable=" ".join([
                    source_id,str(r.get("kind","")),str(r.get("source_type","")),
                    str(r.get("source_uri","")),str(r.get("state","")),str(r.get("content_hash",""))
                ])
                docs.append({
                    "doc_id":_doc_id(company_id,"LAB_LEDGER",source_id+"|"+str(r.get("record_hash",""))),
                    "company_id":company_id,
                    "scope":"COMPANY",
                    "source_kind":"LAB_LEDGER",
                    "source_id":source_id,
                    "text":searchable,
                    "tokens":sorted(_tokens(searchable)),
                    "provenance_id":str(r.get("provenance_id","")),
                    "confidence":float(r.get("confidence",0.0)),
                    "canonical":bool(r.get("canonical",False)),
                    "production_ready":bool(r.get("production_ready",False)),
                })

        target=index_root/f"{company_id}.json"
        target.write_text(json.dumps({
            "record_type":"permissioned_rag_index",
            "engine_id":"RAG-001",
            "company_id":company_id,
            "strategy":"TEXT_TOKEN_MATCH_V0",
            "embeddings_used":False,
            "documents":docs,
            "external_mutation_allowed":False,
            "cost_eur":0.0
        },sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written


def search(query:str, *, company_id:str, allowed_company_ids:set[str], limit:int=10)->list[dict]:
    if company_id not in allowed_company_ids:
        raise PermissionError("company scope denied")
    if limit<1 or limit>100:
        raise ValueError("invalid limit")
    index_root=Path(os.environ.get("CEREBRO_RAG_INDEX_ROOT",".cerebro-runtime/rag-index"))
    path=index_root/f"{company_id}.json"
    if not path.exists(): return []
    payload=json.loads(path.read_text(encoding="utf-8"))
    if str(payload.get("company_id",""))!=company_id:
        raise ValueError("cross-company index contamination denied")
    q=_tokens(query)
    if not q: return []
    scored=[]
    for doc in payload.get("documents") or []:
        if str(doc.get("company_id",""))!=company_id:
            raise ValueError("cross-company document contamination denied")
        dt=set(doc.get("tokens") or [])
        overlap=len(q & dt)
        if overlap==0: continue
        score=overlap/max(len(q),1)
        score+=min(float(doc.get("confidence",0.0)),1.0)*0.01
        scored.append((score,doc))
    scored.sort(key=lambda x:(-x[0],str(x[1].get("doc_id",""))))
    return [{**doc,"score":round(score,6)} for score,doc in scored[:limit]]


@dataclass(frozen=True)
class CacheKey:
    company_id:str
    namespace:str
    rule_version:str
    payload_hash:str

    @classmethod
    def from_payload(cls,company_id:str,namespace:str,rule_version:str,payload:object)->"CacheKey":
        raw=json.dumps(payload,sort_keys=True,separators=(",",":"))
        return cls(company_id,namespace,rule_version,hashlib.sha256(raw.encode("utf-8")).hexdigest())

    def digest(self)->str:
        raw="|".join([self.company_id,self.namespace,self.rule_version,self.payload_hash])
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class IntelligenceCache:
    def __init__(self, root:Path|None=None):
        self.root=Path(root or os.environ.get("CEREBRO_INTELLIGENCE_CACHE_ROOT",".cerebro-runtime/intelligence-cache"))
        self.root.mkdir(parents=True,exist_ok=True)

    def _path(self,key:CacheKey)->Path:
        return self.root/key.company_id/f"{key.digest()}.json"

    def put(self,key:CacheKey,value:object,*,ttl_seconds:int,now:float|None=None)->Path:
        if ttl_seconds<1: raise ValueError("ttl_seconds must be >= 1")
        now=time.time() if now is None else float(now)
        path=self._path(key); path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({
            "engine_id":"CACHE-001",
            "company_id":key.company_id,
            "namespace":key.namespace,
            "rule_version":key.rule_version,
            "payload_hash":key.payload_hash,
            "created_at_epoch":now,
            "expires_at_epoch":now+ttl_seconds,
            "value":value,
            "external_mutation_allowed":False,
            "cost_eur":0.0
        },sort_keys=True,indent=2)+"\n",encoding="utf-8")
        return path

    def get(self,key:CacheKey,*,now:float|None=None):
        path=self._path(key)
        if not path.exists(): return None
        data=json.loads(path.read_text(encoding="utf-8"))
        if str(data.get("company_id",""))!=key.company_id:
            raise ValueError("cross-company cache contamination denied")
        now=time.time() if now is None else float(now)
        if now>=float(data.get("expires_at_epoch",0)):
            return None
        if str(data.get("rule_version",""))!=key.rule_version or str(data.get("payload_hash",""))!=key.payload_hash:
            return None
        return data.get("value")


if __name__=="__main__":
    for p in build_index():
        print(p)
