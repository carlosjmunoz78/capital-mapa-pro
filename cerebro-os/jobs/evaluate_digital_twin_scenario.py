from __future__ import annotations

import json
import os
from pathlib import Path

ALLOWED_METRICS={"capacity_units","cost_eur","sla_minutes","error_rate","conversion_rate"}
ALLOWED_OPS={"SET","ADD","MULTIPLY"}

def _apply(value:float,op:str,amount:float)->float:
    if op=="SET": return amount
    if op=="ADD": return value+amount
    if op=="MULTIPLY": return value*amount
    raise ValueError("unsupported scenario operation")

def evaluate(snapshot:dict,scenario:dict)->dict:
    company_id=str(snapshot.get("company_id","")).strip()
    if not company_id or str(snapshot.get("engine_id",""))!="TWIN-001":
        raise ValueError("valid TWIN-001 snapshot required")
    if str(snapshot.get("environment","")).upper()=="PROD":
        raise ValueError("TWIN-001 scenario evaluation cannot target PROD")
    if bool(snapshot.get("external_mutation_allowed",True)):
        raise ValueError("twin snapshot must be side-effect free")
    if bool(snapshot.get("writes_to_prod",True)):
        raise ValueError("twin snapshot cannot write to PROD")

    if str(scenario.get("company_id","")).strip()!=company_id:
        raise ValueError("cross-company scenario denied")
    metrics=scenario.get("baseline_metrics")
    if not isinstance(metrics,dict):
        raise ValueError("baseline_metrics required")
    changes=scenario.get("changes")
    if not isinstance(changes,list):
        raise ValueError("scenario changes required")

    before={}
    after={}
    for metric,value in metrics.items():
        if metric not in ALLOWED_METRICS:
            raise ValueError("unsupported scenario metric")
        before[metric]=float(value)
        after[metric]=float(value)

    for change in changes:
        if not isinstance(change,dict):
            raise ValueError("scenario change must be object")
        metric=str(change.get("metric",""))
        op=str(change.get("operation","")).upper()
        amount=float(change.get("value",0))
        if metric not in ALLOWED_METRICS:
            raise ValueError("unsupported scenario metric")
        if op not in ALLOWED_OPS:
            raise ValueError("unsupported scenario operation")
        if metric not in after:
            raise ValueError("scenario metric missing from baseline")
        after[metric]=_apply(after[metric],op,amount)

    deltas={k:round(after[k]-before[k],6) for k in sorted(before)}
    adverse=[]
    if "cost_eur" in after and after["cost_eur"]>before["cost_eur"]:
        adverse.append("COST_INCREASE")
    if "sla_minutes" in after and after["sla_minutes"]>before["sla_minutes"]:
        adverse.append("SLA_WORSENED")
    if "error_rate" in after and after["error_rate"]>before["error_rate"]:
        adverse.append("ERROR_RATE_WORSENED")
    if "capacity_units" in after and after["capacity_units"]<before["capacity_units"]:
        adverse.append("CAPACITY_REDUCED")
    if "conversion_rate" in after and after["conversion_rate"]<before["conversion_rate"]:
        adverse.append("CONVERSION_REDUCED")

    return {
        "record_type":"digital_twin_scenario_evaluation",
        "company_id":company_id,
        "engine_id":"TWIN-001",
        "simulation_engine_id":"SIM-001",
        "snapshot_id":str(snapshot.get("snapshot_id","")),
        "environment":str(snapshot.get("environment","")),
        "scenario_id":str(scenario.get("scenario_id","")),
        "before":before,
        "after":after,
        "deltas":deltas,
        "adverse_signals":adverse,
        "status":"REVIEW" if adverse else "GREEN",
        "promotion_allowed":False,
        "production_ready":False,
        "external_mutation_allowed":False,
        "writes_to_prod":False,
        "live_traffic_exposed":False,
        "cost_eur":0.0,
    }

def run()->list[Path]:
    twin_root=Path(os.environ.get("CEREBRO_DIGITAL_TWIN_ROOT",".cerebro-runtime/digital-twin"))
    scenario_root=Path(os.environ.get("CEREBRO_TWIN_SCENARIO_ROOT",".cerebro-runtime/twin-scenarios"))
    out_root=Path(os.environ.get("CEREBRO_TWIN_SCENARIO_RESULT_ROOT",".cerebro-runtime/twin-scenario-results"))
    out_root.mkdir(parents=True,exist_ok=True)
    written=[]
    for path in sorted(scenario_root.glob("*.json")):
        scenario=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(scenario,dict):
            raise ValueError("scenario must be object")
        company_id=str(scenario.get("company_id","")).strip()
        snap_path=twin_root/f"{company_id}.snapshot.json"
        if not snap_path.exists():
            raise ValueError("digital twin snapshot missing")
        snapshot=json.loads(snap_path.read_text(encoding="utf-8"))
        result=evaluate(snapshot,scenario)
        target=out_root/f"{company_id}.{path.stem}.json"
        target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
