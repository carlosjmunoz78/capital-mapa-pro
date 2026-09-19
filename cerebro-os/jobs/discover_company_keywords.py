from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from collections import Counter
from pathlib import Path

ENGINE_ID="KW-001"
STOPWORDS={"a","al","algo","ante","con","como","de","del","desde","el","ella","en","es","esta","este","la","las","lo","los","o","para","por","que","se","sin","su","sus","un","una","y","ya","the","and","for","with","from","this","that"}

def _fold(text:str)->str:
    text=unicodedata.normalize("NFKD",text)
    text="".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+"," ",text.lower()).strip()

def _tokens(text:str)->list[str]:
    return [x for x in _fold(text).split() if len(x)>2 and x not in STOPWORDS and not x.isdigit()]

def _texts(payload:dict)->list[str]:
    source=payload.get("source_texts") or []
    if not isinstance(source,list): raise ValueError("source_texts must be list")
    return [str(x).strip() for x in source if str(x).strip()]

def discover_keywords(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    if not company_id: raise ValueError("company_id required")
    texts=_texts(payload)
    seeds=[_fold(str(x)) for x in (payload.get("seed_keywords") or []) if _fold(str(x))]
    geos=[_fold(str(x)) for x in (payload.get("geographies") or []) if _fold(str(x))]
    if not isinstance(payload.get("seed_keywords") or [],list): raise ValueError("seed_keywords must be list")
    if not isinstance(payload.get("geographies") or [],list): raise ValueError("geographies must be list")

    unigram=Counter()
    bigram=Counter()
    for text in texts:
        t=_tokens(text)
        unigram.update(t)
        bigram.update(" ".join(t[i:i+2]) for i in range(len(t)-1))

    candidates={}
    for term,count in unigram.items():
        if count>=1: candidates[term]=candidates.get(term,0)+count
    for term,count in bigram.items():
        if count>=1: candidates[term]=candidates.get(term,0)+count*2
    for seed in seeds:
        candidates[seed]=candidates.get(seed,0)+10
        for geo in geos:
            candidates[f"{seed} {geo}"]=candidates.get(f"{seed} {geo}",0)+12

    rows=[]
    for term,score in sorted(candidates.items(),key=lambda kv:(-kv[1],kv[0]))[:100]:
        intent="LOCAL" if any(geo and geo in term for geo in geos) else "DISCOVERY"
        rows.append({"keyword":term,"score":score,"intent":intent,"source":"DETERMINISTIC"})
    canonical=json.dumps({"company_id":company_id,"keywords":rows},sort_keys=True,separators=(",",":"))
    confidence=0.9 if seeds and texts else 0.75 if seeds or texts else 0.0

    return {
        "record_type":"keyword_discovery",
        "company_id":company_id,
        "engine_id":ENGINE_ID,
        "environment":str(payload.get("environment","LAB")).upper(),
        "version":str(payload.get("version","1.0.0")),
        "keywords":rows,
        "keyword_count":len(rows),
        "confidence":confidence,
        "status":"GREEN" if rows else "WAITING",
        "strategy":"DETERMINISTIC_FIRST",
        "semantic_ai_used":False,
        "paid_ai_used":False,
        "external_mutation_allowed":False,
        "cost_eur":0.0,
        "limitations":["no_search_volume_without_external_source","no_serp_rank_without_external_source","no_competitor_gap_without_competitor_evidence"],
        "evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_KW_REQUEST_ROOT",".cerebro-runtime/keyword-discovery-requests"))
    out=Path(os.environ.get("CEREBRO_KW_RESULT_ROOT",".cerebro-runtime/keyword-discovery-results"))
    out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        result=discover_keywords(payload)
        target=out/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
