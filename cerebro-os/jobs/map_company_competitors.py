from __future__ import annotations
import hashlib,json,os
from pathlib import Path
ENGINE_ID="COMPET-001"

def map_competitors(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    candidates=payload.get("competitors") or []
    if not company_id: raise ValueError("company_id required")
    if not isinstance(candidates,list): raise ValueError("competitors must be list")
    rows=[]
    for item in candidates:
        if not isinstance(item,dict): raise ValueError("competitor must be object")
        name=str(item.get("name","")).strip()
        if not name: raise ValueError("competitor name required")
        refs=sorted({str(x).strip() for x in (item.get("evidence_refs") or []) if str(x).strip()})
        signals=sorted({str(x).strip() for x in (item.get("signals") or []) if str(x).strip()})
        confidence=round(min(1.0,0.4+0.15*len(refs)+0.1*len(signals)),3)
        rows.append({"name":name,"domain":str(item.get("domain","")).strip(),"geography":str(item.get("geography","")).strip(),"signals":signals,"evidence_refs":refs,"confidence":confidence,"status":"CANDIDATE"})
    rows=sorted(rows,key=lambda x:(-x["confidence"],x["name"].lower()))
    canonical=json.dumps({"company_id":company_id,"competitors":rows},sort_keys=True,separators=(",",":"))
    return {
      "record_type":"competitor_map","company_id":company_id,"engine_id":ENGINE_ID,
      "environment":str(payload.get("environment","LAB")).upper(),"version":str(payload.get("version","1.0.0")),
      "competitors":rows,"competitor_count":len(rows),
      "status":"GREEN" if rows and all(x["evidence_refs"] for x in rows) else "PARTIAL" if rows else "WAITING",
      "read_only":True,"external_mutation_allowed":False,"cost_eur":0.0,
      "ranking_claimed":False,"market_share_claimed":False,
      "evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_COMPET_REQUEST_ROOT",".cerebro-runtime/competitor-map-requests"))
    out=Path(os.environ.get("CEREBRO_COMPET_RESULT_ROOT",".cerebro-runtime/competitor-map-results")); out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        result=map_competitors(json.loads(path.read_text(encoding="utf-8")))
        target=out/f'{result["company_id"]}.json'; target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); written.append(target)
    return written
if __name__=="__main__":
    for p in run(): print(p)
