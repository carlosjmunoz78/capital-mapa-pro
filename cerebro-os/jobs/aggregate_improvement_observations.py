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

_SOURCE_FILES = {
    "technical": "{company_id}.observations.json",
    "business": "{company_id}.business.json",
    "competitors": "{company_id}.competitors.json",
    "finops": "{company_id}.finops.json",
    "content": "{company_id}.content.json",
    "footprint": "{company_id}.footprint.json",
}


def _load(path: Path) -> dict | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("observation payload must be object")
    return payload


def _policy(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("source policy must be object")
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
    source_policy_path = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_SOURCE_POLICY",
        "cerebro-os/config/improvement_source_policy.lab.json",
    ))
    companies = json.loads(company_config.read_text(encoding="utf-8"))
    source_policy = _policy(source_policy_path)
    written: list[Path] = []

    for config in companies:
        if not config.get("enabled", True):
            continue
        company_id = str(config["company_id"])
        company_policy = source_policy.get(company_id) or {"required": ["technical"], "optional": []}
        required = tuple(str(x) for x in company_policy.get("required", []))
        optional = tuple(str(x) for x in company_policy.get("optional", []))
        unknown = set(required + optional) - set(_SOURCE_FILES)
        if unknown:
            raise ValueError(f"unknown source policy keys: {sorted(unknown)}")
        if set(required).intersection(optional):
            raise ValueError("source cannot be both required and optional")

        source_map: dict[str, dict | None] = {
            key: _load(evidence_root / template.format(company_id=company_id))
            for key, template in _SOURCE_FILES.items()
            if key in required or key in optional
        }
        present = {key: value for key, value in source_map.items() if value is not None}
        for source in present.values():
            if str(source.get("company_id", "")) != company_id:
                raise ValueError("cross-company observation denied")

        missing_required = [key for key in required if source_map.get(key) is None]
        failed_required = [
            key for key in required
            if source_map.get(key) is not None and (
                not bool(source_map[key].get("checked"))
                or str(source_map[key].get("status")) == "SOURCE_ERROR"
            )
        ]
        failed_optional = [
            key for key in optional
            if source_map.get(key) is not None and (
                not bool(source_map[key].get("checked"))
                or str(source_map[key].get("status")) == "SOURCE_ERROR"
            )
        ]

        required_ok = not missing_required and not failed_required
        checked_sources = [
            source for key, source in present.items()
            if bool(source.get("checked")) and str(source.get("status")) != "SOURCE_ERROR"
        ]

        if not required_ok:
            status = "SOURCE_ERROR"
            checked = False
            confidence = 0.0
            chosen = next(
                (present[key] for key in failed_required if key in present),
                next(iter(present.values()), {
                    "evidence_ref": f"evidence://{company_id}/required-source-missing",
                    "summary": "required source missing",
                    "source": "MULTI_SOURCE",
                }),
            )
        elif checked_sources:
            chosen = max(checked_sources, key=lambda s: _PRIORITY.get(str(s.get("status")), 0))
            status = str(chosen.get("status", "SOURCE_ERROR"))
            checked = True
            confidence = min(float(s.get("confidence", 0.0)) for s in checked_sources)
        else:
            chosen = {
                "evidence_ref": f"evidence://{company_id}/no-checked-source",
                "summary": "no checked source",
                "source": "MULTI_SOURCE",
            }
            status = "SOURCE_ERROR"
            checked = False
            confidence = 0.0

        combined = {
            "company_id": company_id,
            "checked": checked,
            "source": "MULTI_SOURCE",
            "evidence_ref": str(chosen.get("evidence_ref", f"evidence://{company_id}/missing")),
            "status": status,
            "confidence": confidence,
            "summary": " | ".join(
                f'{key}:{source.get("source")}:{source.get("status")}:{source.get("summary","")}'
                for key, source in present.items()
            ),
            "facts": {
                "required_sources": list(required),
                "optional_sources": list(optional),
                "missing_required_sources": missing_required,
                "failed_required_sources": failed_required,
                "failed_optional_sources": failed_optional,
                "source_status": {
                    key: {
                        "present": source_map.get(key) is not None,
                        "checked": bool(source_map[key].get("checked")) if source_map.get(key) else False,
                        "status": str(source_map[key].get("status")) if source_map.get(key) else "MISSING",
                    }
                    for key in required + optional
                },
            },
        }
        target = evidence_root / f"{company_id}.observations.json"
        target.write_text(json.dumps(combined, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        written.append(target)

    return written


if __name__ == "__main__":
    for path in aggregate():
        print(path)
