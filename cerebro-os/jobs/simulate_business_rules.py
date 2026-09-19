from __future__ import annotations

import json
import operator
import os
from pathlib import Path

ALLOWED_DATASETS={"SYNTHETIC","ANONYMIZED","LAB_RECORDED"}
OPS={
    "EQ":operator.eq,
    "NE":operator.ne,
    "GT":operator.gt,
    "GE":operator.ge,
    "LT":operator.lt,
    "LE":operator.le,
}


def _evaluate_rule(event:dict, spec:dict)->str:
    field=str(spec.get("field","")).strip()
    op=str(spec.get("operator","")).strip().upper()
    if not field or op not in OPS:
        raise ValueError("unsupported simulation rule")
    if field not in event:
        return str(spec.get("else_action","NO_MATCH"))
    left=event[field]
    right=spec.get("value")
    matched=OPS[op](left,right)
    return str(spec.get("then_action","MATCH")) if matched else str(spec.get("else_action","NO_MATCH"))


def simulate(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    engine_id=str(payload.get("engine_id","")).strip()
    environment=str(payload.get("environment","LAB")).strip().upper()
    version=str(payload.get("version","1.0.0")).strip()
    dataset_kind=str(payload.get("dataset_kind","")).strip().upper()
    if not all((company_id,engine_id,environment,version,dataset_kind)):
        raise ValueError("complete simulation scope required")
    if environment=="PROD":
        raise ValueError("SIM-001 never executes against PROD")
    if dataset_kind not in ALLOWED_DATASETS:
        raise ValueError("unsupported or unsafe simulation dataset")
    if bool(payload.get("contains_live_secrets",False)):
        raise ValueError("simulation dataset cannot contain live secrets")

    events=payload.get("events")
    if not isinstance(events,list) or not events:
        raise ValueError("simulation events required")
    old_spec=payload.get("old_rule")
    new_spec=payload.get("new_rule")
    if not isinstance(old_spec,dict) or not isinstance(new_spec,dict):
        raise ValueError("old_rule and new_rule required")

    rows=[]
    changed=0
    for idx,event in enumerate(events):
        if not isinstance(event,dict):
            raise ValueError("simulation event must be object")
        old_action=_evaluate_rule(event,old_spec)
        new_action=_evaluate_rule(event,new_spec)
        different=old_action!=new_action
        changed+=1 if different else 0
        rows.append({
            "event_index":idx,
            "old_action":old_action,
            "new_action":new_action,
            "changed":different,
        })

    return {
        "record_type":"business_rule_simulation",
        "company_id":company_id,
        "engine_id":"SIM-001",
        "target_engine_id":engine_id,
        "environment":environment,
        "version":version,
        "dataset_kind":dataset_kind,
        "events_replayed":len(events),
        "changed_outcomes":changed,
        "change_rate":round(changed/len(events),6),
        "old_rule":old_spec,
        "new_rule":new_spec,
        "rows":rows,
        "status":"SIMULATION_COMPLETE",
        "live_traffic_exposed":False,
        "external_mutation_allowed":False,
        "production_ready":False,
        "promotion_allowed":False,
        "cost_eur":0.0,
    }


def run()->list[Path]:
    source_root=Path(os.environ.get(
        "CEREBRO_SIMULATION_CASE_ROOT",
        ".cerebro-runtime/simulation-cases",
    ))
    out_root=Path(os.environ.get(
        "CEREBRO_SIMULATION_RESULT_ROOT",
        ".cerebro-runtime/simulation-results",
    ))
    out_root.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(source_root.glob("*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload,dict):
            raise ValueError("simulation case must be object")
        result=simulate(payload)
        company_id=result["company_id"]
        target=out_root/f"{company_id}.{path.stem}.json"
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written


if __name__=="__main__":
    for path in run(): print(path)
