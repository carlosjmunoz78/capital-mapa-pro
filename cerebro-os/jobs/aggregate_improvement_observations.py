from __future__ import annotations

import json
import os
from pathlib import Path

_PRIORITY = {
    "HUMAN_REQUIRED": 4,
    "PROPOSAL_READY": 3,
    "NO_CHANGE": 2,
    "SOURCE_ERROR": 1,
}

def _load(path: Path) -> dict | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("observation payload must be object")
    return payload


def aggregate() -> list[Path]:
    evidence_root = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_EVIDENCE_ROOT",
        ".cerebro-runtime/evidence",
    ))
    company_config = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_COMPANIES",
        "cerebro-os/config/improvement_companies.lab.json",
    ))
    companies = json.loads(company_config.read_text(encoding="utf-8"))
    written: list[Path] = []

    for config in companies:
        if not config.get("enabled", True):
            continue
        company_id = str(config["company_id"])
        sources = [
            _load(evidence_root / f"{company_id}.observations.json"),
            _load(evidence_root / f"{company_id}.business.json"),
        ]
        sources = [s for s in sources if s is not None]
        if not sources:
            continue
        for source in sources:
            if str(source.get("company_id", "")) != company_id:
                raise ValueError("cross-company observation denied")

        checked_sources = [s for s in sources if bool(s.get("checked"))]
        if not checked_sources:
            chosen = max(sources, key=lambda s: _PRIORITY.get(str(s.get("status")), 0))
            status = "SOURCE_ERROR"
            checked = False
            confidence = 0.0
        else:
            chosen = max(checked_sources, key=lambda s: _PRIORITY.get(str(s.get("status")), 0))
            status = str(chosen.get("status", "SOURCE_ERROR"))
            checked = True
            confidence = min(float(s.get("confidence", 0.0)) for s in checked_sources)

        combined = {
            "company_id": company_id,
            "checked": checked,
            "source": "MULTI_SOURCE",
            "evidence_ref": str(chosen.get("evidence_ref", f"evidence://{company_id}/missing")),
            "status": status,
            "confidence": confidence,
            "summary": " | ".join(
                f'{s.get("source")}:{s.get("status")}:{s.get("summary","")}' for s in sources
            ),
        }
        target = evidence_root / f"{company_id}.observations.json"
        target.write_text(json.dumps(combined, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        written.append(target)

    return written


if __name__ == "__main__":
    for path in aggregate():
        print(path)
