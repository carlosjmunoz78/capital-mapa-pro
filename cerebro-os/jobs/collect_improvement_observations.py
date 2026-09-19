from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path


def _github_json(url: str, token: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "cerebro-improvement-observer",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def collect() -> list[Path]:
    repo = os.environ["GITHUB_REPOSITORY"]
    token = os.environ["GITHUB_TOKEN"]
    config_path = Path(os.environ.get("CEREBRO_IMPROVEMENT_COMPANIES", "cerebro-os/config/improvement_companies.lab.json"))
    output_root = Path(os.environ.get("CEREBRO_IMPROVEMENT_EVIDENCE_ROOT", ".cerebro-runtime/evidence"))
    output_root.mkdir(parents=True, exist_ok=True)
    companies = json.loads(config_path.read_text(encoding="utf-8"))

    api = f"https://api.github.com/repos/{repo}/actions/workflows/cerebro-engine-factory-v0.yml/runs?branch=cerebro-engine-factory-v0&per_page=1"
    try:
        payload = _github_json(api, token)
        runs = payload.get("workflow_runs") or []
        latest = runs[0] if runs else None
        if latest is None:
            status = "SOURCE_ERROR"
            evidence = f"github://{repo}/engine-factory/no-run"
            summary = "No Engine Factory workflow run found"
        elif latest.get("status") != "completed":
            status = "SOURCE_ERROR"
            evidence = str(latest.get("html_url") or f"github://{repo}/engine-factory/in-progress")
            summary = "Latest Engine Factory run is not completed"
        elif latest.get("conclusion") == "success":
            status = "NO_CHANGE"
            evidence = str(latest.get("html_url") or f"github://{repo}/engine-factory/success")
            summary = "Canonical Engine Factory health is green"
        else:
            status = "PROPOSAL_READY"
            evidence = str(latest.get("html_url") or f"github://{repo}/engine-factory/failure")
            summary = f"Canonical Engine Factory health requires investigation: {latest.get('conclusion')}"
    except Exception as exc:
        status = "SOURCE_ERROR"
        evidence = f"github://{repo}/engine-factory/api-error"
        summary = f"GitHub observation failed: {type(exc).__name__}"

    written = []
    for company in companies:
        if not company.get("enabled", True):
            continue
        company_id = str(company["company_id"])
        path = output_root / f"{company_id}.observations.json"
        path.write_text(json.dumps({
            "company_id": company_id,
            "checked": status != "SOURCE_ERROR",
            "source": "GITHUB_ENGINE_FACTORY",
            "evidence_ref": evidence,
            "status": status,
            "confidence": 1.0 if status != "SOURCE_ERROR" else 0.0,
            "summary": summary,
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        written.append(path)
    return written


if __name__ == "__main__":
    for path in collect():
        print(path)
