from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path


_SOURCE_FILES = {
    "business": "{company_id}.business.json",
    "competitors": "{company_id}.competitors.json",
    "finops": "{company_id}.finops.json",
    "content": "{company_id}.content.json",
    "footprint": "{company_id}.footprint.json",
    "availability": "{company_id}.availability.json",
    "technical": "{company_id}.observations.json",
}

_DOMAIN = {
    "business": "WEB_SEO",
    "competitors": "MARKET_INTELLIGENCE",
    "finops": "FINOPS",
    "content": "CONTENT",
    "footprint": "SEO_LOCAL_SOCIAL",
    "availability": "SERVICE_HEALTH",
    "technical": "PLATFORM_HEALTH",
}


@dataclass(frozen=True)
class LabProposal:
    company_id: str
    proposal_id: str
    source_key: str
    domain: str
    environment: str
    version: str
    summary: str
    evidence_ref: str
    action: str
    external_mutation_allowed: bool = False
    cost_limit_eur: float = 0.0


def _read(path: Path) -> dict | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("source evidence must be object")
    return payload


def generate() -> list[Path]:
    evidence_root = Path(os.environ.get("CEREBRO_IMPROVEMENT_EVIDENCE_ROOT", ".cerebro-runtime/evidence"))
    proposals_root = Path(os.environ.get("CEREBRO_IMPROVEMENT_PROPOSALS_ROOT", ".cerebro-runtime/proposals"))
    config_path = Path(os.environ.get("CEREBRO_IMPROVEMENT_COMPANIES", "cerebro-os/config/improvement_companies.lab.json"))
    proposals_root.mkdir(parents=True, exist_ok=True)
    configs = json.loads(config_path.read_text(encoding="utf-8"))
    written: list[Path] = []

    for config in configs:
        if not config.get("enabled", True):
            continue
        company_id = str(config["company_id"])
        proposals: list[LabProposal] = []
        for key, template in _SOURCE_FILES.items():
            payload = _read(evidence_root / template.format(company_id=company_id))
            if not payload or str(payload.get("company_id", "")) != company_id:
                continue
            if str(payload.get("status")) != "PROPOSAL_READY":
                continue
            proposal_id = f"{company_id}:{key}:{datetime.now(timezone.utc).strftime('%Y%m%d')}"
            proposals.append(LabProposal(
                company_id=company_id,
                proposal_id=proposal_id,
                source_key=key,
                domain=_DOMAIN[key],
                environment=str(config.get("environment", "LAB")),
                version=str(config.get("version", "1.0.0")),
                summary=str(payload.get("summary", "")).strip() or f"{key} source requires LAB diagnostic",
                evidence_ref=str(payload.get("evidence_ref", "")).strip() or f"evidence://{company_id}/{key}",
                action="LAB_DIAGNOSTIC_ONLY",
            ))

        target = proposals_root / f"{company_id}.json"
        target.write_text(json.dumps({
            "company_id": company_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "proposals": [asdict(item) for item in proposals],
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        written.append(target)
    return written


def build_lab_evidence() -> list[Path]:
    proposals_root = Path(os.environ.get("CEREBRO_IMPROVEMENT_PROPOSALS_ROOT", ".cerebro-runtime/proposals"))
    evidence_root = Path(os.environ.get("CEREBRO_IMPROVEMENT_EVIDENCE_ROOT", ".cerebro-runtime/evidence"))
    evidence_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for path in sorted(proposals_root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        company_id = str(payload.get("company_id", ""))
        proposals = payload.get("proposals") or []
        if not company_id:
            raise ValueError("proposal file missing company_id")
        if not proposals:
            continue
        target = evidence_root / f"{company_id}.lab.json"
        target.write_text(json.dumps({
            "company_id": company_id,
            "stage": "LAB",
            "status": "GREEN",
            "evidence_ref": f"file://{target}",
            "summary": f"{len(proposals)} deterministic LAB diagnostic proposal(s) prepared",
            "external_mutation_allowed": False,
            "cost_eur": 0.0,
            "proposals": proposals,
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        written.append(target)
    return written


if __name__ == "__main__":
    for path in generate():
        print(path)
    for path in build_lab_evidence():
        print(path)
