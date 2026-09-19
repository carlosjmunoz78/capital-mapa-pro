from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

CEREBRO_OS_ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_ROOT = CEREBRO_OS_ROOT / "discovery"
for candidate in (CEREBRO_OS_ROOT, DISCOVERY_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from discovery.public_web_collector import parse_public_html


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent":"CEREBRO-CompetitorObserver/1.0 (+public-read-only)"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.read(2_000_001)


def collect() -> list[Path]:
    config_path = Path(os.environ.get("CEREBRO_IMPROVEMENT_COMPETITOR_SOURCES","cerebro-os/config/improvement_competitor_sources.lab.json"))
    evidence_root = Path(os.environ.get("CEREBRO_IMPROVEMENT_EVIDENCE_ROOT",".cerebro-runtime/evidence"))
    state_root = Path(os.environ.get("CEREBRO_IMPROVEMENT_OBSERVATION_STATE_ROOT",".cerebro-runtime/observations"))
    evidence_root.mkdir(parents=True, exist_ok=True)
    state_root.mkdir(parents=True, exist_ok=True)
    configs = json.loads(config_path.read_text(encoding="utf-8"))
    written=[]

    for config in configs:
        if not config.get("enabled", True):
            continue
        company_id=str(config["company_id"])
        results=[]
        for item in config.get("competitors", []):
            competitor_id=str(item["competitor_id"])
            url=str(item["url"])
            try:
                snapshot=parse_public_html(url,_fetch(url))
                state_key=hashlib.sha256(f"{competitor_id}\0{url}".encode()).hexdigest()[:16]
                state_path=state_root/f"{company_id}.competitor.{state_key}.json"
                previous=json.loads(state_path.read_text()) if state_path.exists() else None
                current={"content_hash":snapshot.content_hash,"title":snapshot.title,"h1":snapshot.h1,"canonical":snapshot.canonical}
                changed=bool(previous and previous.get("content_hash") != snapshot.content_hash)
                status="PROPOSAL_READY" if changed else "NO_CHANGE"
                evidence=f"{snapshot.url}#sha256={snapshot.content_hash}"
                results.append({
                    "checked":True,"competitor_id":competitor_id,"url":snapshot.url,
                    "status":status,"confidence":0.90,"evidence_ref":evidence,
                    "summary":"competitor public page changed" if changed else "competitor public page baseline/unchanged",
                    "facts":current,
                })
                state_path.write_text(json.dumps(current,sort_keys=True,indent=2)+"\n",encoding="utf-8")
            except Exception as exc:
                results.append({
                    "checked":False,"competitor_id":competitor_id,"url":url,
                    "status":"SOURCE_ERROR","confidence":0.0,"evidence_ref":f"{url}#collector-error",
                    "summary":f"competitor observation failed: {type(exc).__name__}","facts":{},
                })
        checked=[x for x in results if x["checked"]]
        changed=[x for x in checked if x["status"]=="PROPOSAL_READY"]
        if checked:
            chosen=changed[0] if changed else checked[0]
            status="PROPOSAL_READY" if changed else "NO_CHANGE"
            confidence=min(float(x["confidence"]) for x in checked)
        elif results:
            chosen=results[0]; status="SOURCE_ERROR"; confidence=0.0
        else:
            continue
        payload={
            "company_id":company_id,"checked":bool(checked),"source":"PUBLIC_COMPETITOR_WEB",
            "evidence_ref":chosen["evidence_ref"],"status":status,"confidence":confidence,
            "summary":" | ".join(f'{x["competitor_id"]}:{x["status"]}:{x["summary"]}' for x in results),
            "facts":{"competitors_configured":len(results),"competitors_checked":len(checked),"changed":len(changed),"items":results},
        }
        target=evidence_root/f"{company_id}.competitors.json"
        target.write_text(json.dumps(payload,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written


if __name__=="__main__":
    for path in collect():
        print(path)
