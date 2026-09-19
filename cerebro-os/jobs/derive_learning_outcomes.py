from __future__ import annotations

import json
import os
import sqlite3
from collections import defaultdict
from pathlib import Path

TERMINAL_BAD = {"BLOCKED", "HUMAN_REQUIRED", "RED"}
SENSITIVE_STAGES = {"TRIBUNAL", "PROMOTE_OR_ROLLBACK", "CANARY"}


def _read_cycles(path: Path) -> list[dict]:
    if not path.exists():
        return []
    conn = sqlite3.connect(path)
    try:
        rows = conn.execute(
            "SELECT seq,payload_json,record_hash FROM improvement_audit ORDER BY seq"
        ).fetchall()
    finally:
        conn.close()
    out = []
    for seq, payload_json, record_hash in rows:
        payload = json.loads(payload_json)
        payload["seq"] = int(seq)
        payload["record_hash"] = str(record_hash)
        out.append(payload)
    return out


def _compare(records: list[dict]) -> dict:
    by_cycle: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        by_cycle[str(rec.get("cycle_id", ""))].append(rec)
    cycles = sorted(
        by_cycle.items(),
        key=lambda kv: max(int(r.get("seq", 0)) for r in kv[1]),
    )
    summaries = []
    for cycle_id, items in cycles:
        latest_by_stage = {}
        for item in sorted(items, key=lambda r: int(r.get("seq", 0))):
            latest_by_stage[str(item.get("stage", ""))] = item
        summaries.append({
            "cycle_id": cycle_id,
            "stages": {
                stage: {
                    "status": str(item.get("status", "")),
                    "evidence_ref": str(item.get("evidence_ref", "")),
                    "record_hash": str(item.get("record_hash", "")),
                }
                for stage, item in sorted(latest_by_stage.items())
                if stage
            },
        })

    comparisons = []
    if len(summaries) >= 2:
        previous = summaries[-2]
        latest = summaries[-1]
        stages = sorted(set(previous["stages"]) | set(latest["stages"]))
        for stage in stages:
            old = previous["stages"].get(stage, {})
            new = latest["stages"].get(stage, {})
            old_status = str(old.get("status", "MISSING"))
            new_status = str(new.get("status", "MISSING"))
            if old_status == new_status:
                trend = "UNCHANGED"
            elif old_status in TERMINAL_BAD and new_status == "GREEN":
                trend = "IMPROVED"
            elif old_status == "GREEN" and new_status in TERMINAL_BAD:
                trend = "REGRESSED"
            else:
                trend = "CHANGED"
            comparisons.append({
                "stage": stage,
                "old_status": old_status,
                "new_status": new_status,
                "trend": trend,
                "old_record_hash": str(old.get("record_hash", "")),
                "new_record_hash": str(new.get("record_hash", "")),
            })
    return {"cycles": summaries, "comparisons": comparisons}


def _candidate_rules(company_id: str, environment: str, version: str, analysis: dict) -> list[dict]:
    candidates = []
    for comp in analysis["comparisons"]:
        stage = comp["stage"]
        trend = comp["trend"]
        new_status = comp["new_status"]
        if trend == "REGRESSED" or (trend == "UNCHANGED" and new_status in TERMINAL_BAD):
            action = "INVESTIGATE_RECURRING_STAGE_FAILURE"
            if stage in SENSITIVE_STAGES:
                action = "REVIEW_SENSITIVE_STAGE_EVIDENCE"
            candidates.append({
                "company_id": company_id,
                "engine_id": "LRN-001",
                "environment": environment,
                "version": version,
                "stage": stage,
                "candidate_action": action,
                "status": "CANDIDATE_ONLY",
                "basis": comp,
                "required_validation": [
                    "independent_evaluation",
                    "tribunal",
                    "old_vs_new",
                    "rollback",
                ],
                "policy_change_allowed": False,
                "permission_change_allowed": False,
                "judge_change_allowed": False,
                "threshold_reduction_allowed": False,
                "auto_promote_allowed": False,
                "external_mutation_allowed": False,
                "production_ready": False,
                "cost_eur": 0.0,
            })
        elif trend == "IMPROVED":
            candidates.append({
                "company_id": company_id,
                "engine_id": "LRN-001",
                "environment": environment,
                "version": version,
                "stage": stage,
                "candidate_action": "PRESERVE_SUCCESSFUL_PATTERN",
                "status": "CANDIDATE_ONLY",
                "basis": comp,
                "required_validation": ["independent_evaluation", "tribunal"],
                "policy_change_allowed": False,
                "permission_change_allowed": False,
                "judge_change_allowed": False,
                "threshold_reduction_allowed": False,
                "auto_promote_allowed": False,
                "external_mutation_allowed": False,
                "production_ready": False,
                "cost_eur": 0.0,
            })
    return candidates


def run() -> list[Path]:
    state_root = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_STATE_ROOT",
        ".cerebro-runtime/improvement",
    ))
    cfg_path = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_COMPANIES",
        "cerebro-os/config/improvement_companies.lab.json",
    ))
    out_root = Path(os.environ.get(
        "CEREBRO_LEARNING_OUTCOME_ROOT",
        ".cerebro-runtime/learning-outcomes",
    ))
    out_root.mkdir(parents=True, exist_ok=True)
    configs = json.loads(cfg_path.read_text(encoding="utf-8"))
    written = []

    for cfg in configs:
        if not cfg.get("enabled", True):
            continue
        company_id = str(cfg["company_id"])
        environment = str(cfg["environment"])
        version = str(cfg["version"])
        audit_path = state_root / "state" / company_id / environment / version / "audit.db"
        records = _read_cycles(audit_path)
        for rec in records:
            if str(rec.get("company_id", "")) != company_id:
                raise ValueError("cross-company learning audit denied")
            if str(rec.get("environment", "")) != environment:
                raise ValueError("cross-environment learning audit denied")

        analysis = _compare(records)
        candidates = _candidate_rules(company_id, environment, version, analysis)
        target = out_root / f"{company_id}.json"
        target.write_text(json.dumps({
            "record_type": "learning_outcome_record",
            "company_id": company_id,
            "engine_id": "LRN-001",
            "environment": environment,
            "version": version,
            "source_audit_path": str(audit_path),
            "cycles_observed": len(analysis["cycles"]),
            "comparisons": analysis["comparisons"],
            "rule_candidates": candidates,
            "status": "CANDIDATES_READY" if candidates else "INSUFFICIENT_OR_STABLE_EVIDENCE",
            "auto_promote_allowed": False,
            "policy_change_allowed": False,
            "permission_change_allowed": False,
            "judge_change_allowed": False,
            "threshold_reduction_allowed": False,
            "external_mutation_allowed": False,
            "production_ready": False,
            "cost_eur": 0.0,
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        written.append(target)
    return written


if __name__ == "__main__":
    for path in run():
        print(path)
