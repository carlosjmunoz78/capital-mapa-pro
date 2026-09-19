from __future__ import annotations

import json
import os
from pathlib import Path

def run()->list[Path]:
    result_root=Path(os.environ.get(
        "CEREBRO_RED_TEAM_RESULT_ROOT",
        ".cerebro-runtime/red-team-results",
    ))
    out_root=Path(os.environ.get(
        "CEREBRO_RED_TEAM_SUMMARY_ROOT",
        ".cerebro-runtime/red-team-summary",
    ))
    out_root.mkdir(parents=True,exist_ok=True)
    grouped={}
    for path in sorted(result_root.glob("*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload,dict):
            raise ValueError("red-team result must be object")
        company_id=str(payload.get("company_id","")).strip()
        if not company_id:
            raise ValueError("company_id required")
        grouped.setdefault(company_id,[]).append(payload)
    written=[]
    for company_id,items in grouped.items():
        blocked=sum(1 for x in items if x.get("status")=="BLOCKED")
        green=sum(1 for x in items if x.get("status")=="GREEN")
        unsafe=[x for x in items if x.get("status") not in {"BLOCKED","GREEN"}]
        status="GREEN" if items and blocked==len(items) and not unsafe else "RED"
        target=out_root/f"{company_id}.json"
        target.write_text(json.dumps({
            "record_type":"red_team_daily_summary",
            "company_id":company_id,
            "engine_id":"RED-001",
            "status":status,
            "cases":len(items),
            "blocked_as_expected":blocked,
            "unexpected_green":green,
            "unsafe_results":len(unsafe),
            "external_mutation_allowed":False,
            "production_ready":False,
            "cost_eur":0.0,
        },sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for path in run(): print(path)
