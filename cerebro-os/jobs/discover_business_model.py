from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

CRITICAL_FIELDS=("products_services","target_customers","geography","channels","revenue_model","objectives","constraints")
OPTIONAL_FIELDS=("value_proposition","differentiators","pricing","partners","regulation","brand")
ENGINE_ID="BMD-001"

def _norm_list(value):
    if value is None: return []
    if isinstance(value,list):
        return [str(x).strip() for x in value if str(x).strip()]
    text=str(value).strip()
    return [text] if text else []

def discover_business_model(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    if not company_id: raise ValueError("company_id required")
    if str(payload.get("environment","LAB")).upper() not in {"LAB","PREPROD"}:
        raise ValueError("BMD-001 discovery is LAB/PREPROD only")
    supplied=payload.get("facts") or {}
    if not isinstance(supplied,dict): raise ValueError("facts must be object")
    evidence=payload.get("evidence") or []
    if not isinstance(evidence,list): raise ValueError("evidence must be list")

    facts={}
    for key in CRITICAL_FIELDS+OPTIONAL_FIELDS:
        vals=_norm_list(supplied.get(key))
        if vals: facts[key]=vals

    missing=[key for key in CRITICAL_FIELDS if key not in facts]
    critical_coverage=(len(CRITICAL_FIELDS)-len(missing))/len(CRITICAL_FIELDS)
    evidence_refs=sorted({str(x.get("ref","")).strip() for x in evidence if isinstance(x,dict) and str(x.get("ref","")).strip()})
    evidence_factor=min(1.0,len(evidence_refs)/max(1,len(facts)))
    confidence=round(critical_coverage*(0.75+0.25*evidence_factor),3)
    canonical=json.dumps({"company_id":company_id,"facts":facts,"evidence_refs":evidence_refs},sort_keys=True,separators=(",",":"))

    return {
        "record_type":"business_model_discovery",
        "company_id":company_id,
        "engine_id":ENGINE_ID,
        "environment":str(payload.get("environment","LAB")).upper(),
        "version":str(payload.get("version","1.0.0")),
        "facts":facts,
        "evidence_refs":evidence_refs,
        "missing_critical_facts":missing,
        "critical_coverage":round(critical_coverage,3),
        "confidence":confidence,
        "status":"GREEN" if not missing and confidence>=0.75 else "PARTIAL",
        "requires_human":bool(missing and payload.get("require_complete",False)),
        "human_reason":"LOW_CONFIDENCE" if missing and payload.get("require_complete",False) else "",
        "inventions_allowed":False,
        "external_mutation_allowed":False,
        "cost_eur":0.0,
        "evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def run()->list[Path]:
    source=Path(os.environ.get("CEREBRO_BMD_REQUEST_ROOT",".cerebro-runtime/bmd-requests"))
    out=Path(os.environ.get("CEREBRO_BMD_RESULT_ROOT",".cerebro-runtime/bmd-results"))
    out.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source.glob("*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        result=discover_business_model(payload)
        target=out/f'{result["company_id"]}.json'
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
