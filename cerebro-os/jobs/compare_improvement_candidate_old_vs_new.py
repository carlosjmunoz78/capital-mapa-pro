from __future__ import annotations

import json
import os
import sys
from pathlib import Path

CEREBRO_OS_ROOT = Path(__file__).resolve().parents[1]
if str(CEREBRO_OS_ROOT) not in sys.path:
    sys.path.insert(0, str(CEREBRO_OS_ROOT))


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("evidence payload must be object")
    return payload


def compare() -> list[Path]:
    candidates_root = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_CANDIDATES_ROOT",
        ".cerebro-runtime/candidates",
    ))
    evidence_root = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_EVIDENCE_ROOT",
        ".cerebro-runtime/evidence",
    ))
    evidence_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for candidate_path in sorted(candidates_root.glob("*.json")):
        payload = _load(candidate_path)
        company_id = str(payload.get("company_id", "")).strip()
        if not company_id:
            raise ValueError("candidate payload missing company_id")
        candidates = payload.get("candidates") or []

        tribunal = _load(evidence_root / f"{company_id}.tribunal.json")
        tribunal_green = (
            str(tribunal.get("company_id", "")) == company_id
            and str(tribunal.get("stage", "")) == "TRIBUNAL"
            and str(tribunal.get("status", "")) == "GREEN"
            and str(tribunal.get("tribunal_scope", "")) == "LAB_SPEC_SAFETY_ONLY"
            and not bool(tribunal.get("production_approval", True))
        )

        source_payloads = {
            "WEB_SEO": _load(evidence_root / f"{company_id}.business.json"),
            "SEO_LOCAL_SOCIAL": _load(evidence_root / f"{company_id}.footprint.json"),
        }

        structural_green = tribunal_green and bool(candidates)
        comparisons: list[dict] = []
        for item in candidates:
            domain = str(item.get("domain", ""))
            mode = str(item.get("mode", ""))
            spec = item.get("change_spec") or {}
            operation = str(spec.get("operation", ""))
            source = source_payloads.get(domain, {})
            summary = str(source.get("summary", "")).lower()
            resolves = False
            baseline_issue = ""

            if mode == "DETERMINISTIC_PATCH_SPEC" and operation == "SET_CANONICAL":
                baseline_issue = "missing_canonical"
                resolves = "missing_canonical" in summary and bool(str(spec.get("value", "")).strip())
            elif mode == "DETERMINISTIC_PATCH_SPEC" and operation == "ADD_SITEMAP_REFERENCE":
                baseline_issue = "robots_without_sitemap_reference"
                resolves = "robots_without_sitemap_reference" in summary
            else:
                resolves = False

            comparisons.append({
                "proposal_id": str(item.get("proposal_id", "")),
                "domain": domain,
                "operation": operation,
                "baseline_issue": baseline_issue,
                "structurally_resolves": resolves,
            })
            structural_green = structural_green and resolves

        status = "GREEN" if structural_green else "WAITING"
        target = evidence_root / f"{company_id}.old_vs_new.json"
        target.write_text(json.dumps({
            "company_id": company_id,
            "stage": "OLD_VS_NEW",
            "status": status,
            "evidence_ref": f"file://{candidate_path}",
            "comparison_scope": "STRUCTURAL_SPEC_ONLY",
            "live_effect_verified": False,
            "production_ready": False,
            "external_mutation_allowed": False,
            "cost_eur": 0.0,
            "comparisons": comparisons,
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        written.append(target)

    return written


if __name__ == "__main__":
    for path in compare():
        print(path)
