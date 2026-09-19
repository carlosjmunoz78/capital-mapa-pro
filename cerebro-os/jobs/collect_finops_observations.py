from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime
from pathlib import Path
from statistics import median


def _github_json(url: str, token: str) -> dict:
    req=urllib.request.Request(url,headers={
        "Authorization":f"Bearer {token}",
        "Accept":"application/vnd.github+json",
        "X-GitHub-Api-Version":"2022-11-28",
        "User-Agent":"cerebro-finops-observer",
    })
    with urllib.request.urlopen(req,timeout=20) as response:
        return json.load(response)


def _duration(run: dict) -> float | None:
    if not run.get("created_at") or not run.get("updated_at"):
        return None
    start=datetime.fromisoformat(str(run["created_at"]).replace("Z","+00:00"))
    end=datetime.fromisoformat(str(run["updated_at"]).replace("Z","+00:00"))
    return max(0.0,(end-start).total_seconds())


def collect() -> list[Path]:
    repo=os.environ["GITHUB_REPOSITORY"]
    token=os.environ["GITHUB_TOKEN"]
    evidence_root=Path(os.environ.get("CEREBRO_IMPROVEMENT_EVIDENCE_ROOT",".cerebro-runtime/evidence"))
    company_config=Path(os.environ.get("CEREBRO_IMPROVEMENT_COMPANIES","cerebro-os/config/improvement_companies.lab.json"))
    evidence_root.mkdir(parents=True,exist_ok=True)
    companies=json.loads(company_config.read_text(encoding="utf-8"))
    url=f"https://api.github.com/repos/{repo}/actions/workflows/cerebro-engine-factory-v0.yml/runs?branch=cerebro-engine-factory-v0&per_page=10"
    written=[]
    try:
        runs=(_github_json(url,token).get("workflow_runs") or [])
        completed=[r for r in runs if r.get("status")=="completed"]
        durations=[d for d in (_duration(r) for r in completed) if d is not None]
        if not completed or not durations:
            raise ValueError("no completed duration evidence")
        latest=durations[0]
        history=durations[1:] or durations
        baseline=median(history)
        threshold=max(baseline*2.0,baseline+60.0)
        status="PROPOSAL_READY" if latest > threshold else "NO_CHANGE"
        evidence=str(completed[0].get("html_url") or f"github://{repo}/engine-factory")
        summary=f"latest_duration_seconds={latest:.1f}; baseline_median_seconds={baseline:.1f}; threshold_seconds={threshold:.1f}"
        checked=True; confidence=1.0
    except Exception as exc:
        latest=baseline=threshold=0.0
        status="SOURCE_ERROR"; evidence=f"github://{repo}/finops-error"; summary=f"finops observation failed: {type(exc).__name__}"
        checked=False; confidence=0.0

    for company in companies:
        if not company.get("enabled",True):
            continue
        company_id=str(company["company_id"])
        payload={
            "company_id":company_id,"checked":checked,"source":"GITHUB_ACTIONS_FINOPS",
            "evidence_ref":evidence,"status":status,"confidence":confidence,"summary":summary,
            "facts":{"latest_duration_seconds":latest,"baseline_median_seconds":baseline,"threshold_seconds":threshold,"estimated_additional_cost_eur":0.0},
        }
        target=evidence_root/f"{company_id}.finops.json"
        target.write_text(json.dumps(payload,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written


if __name__=="__main__":
    for path in collect():
        print(path)
