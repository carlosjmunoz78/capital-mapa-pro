from __future__ import annotations

import json
import os
import sqlite3
import sys
from dataclasses import asdict
from pathlib import Path

CEREBRO_OS_ROOT = Path(__file__).resolve().parents[1]
if str(CEREBRO_OS_ROOT) not in sys.path:
    sys.path.insert(0, str(CEREBRO_OS_ROOT))

from learning.meta_learning import analyze

def _load_companies(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("company config must be a list")
    return payload

def _read_audit(path: Path) -> list[dict]:
    if not path.exists():
        return []
    conn = sqlite3.connect(path)
    try:
        rows = conn.execute("SELECT payload_json FROM improvement_audit ORDER BY seq").fetchall()
        return [json.loads(row[0]) for row in rows]
    finally:
        conn.close()

def run() -> list[Path]:
    state_root = Path(os.environ.get("CEREBRO_IMPROVEMENT_STATE_ROOT", ".cerebro-runtime/improvement"))
    config_path = Path(os.environ.get("CEREBRO_IMPROVEMENT_COMPANIES", "cerebro-os/config/improvement_companies.lab.json"))
    meta_root = Path(os.environ.get("CEREBRO_META_LEARNING_ROOT", ".cerebro-runtime/meta-learning"))
    meta_root.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for cfg in _load_companies(config_path):
        company_id = str(cfg["company_id"])
        environment = str(cfg["environment"])
        version = str(cfg["version"])
        audit_path = state_root / "state" / company_id / environment / version / "audit.db"
        records = _read_audit(audit_path)
        summary = analyze(
            records,
            company_id=company_id,
            environment=environment,
            version=version,
        )
        target = meta_root / f"{company_id}.json"
        payload = asdict(summary)
        payload["record_type"] = "meta_learning_record"
        payload["source_audit_path"] = str(audit_path)
        payload["external_mutation_allowed"] = False
        payload["production_ready"] = False
        target.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        written.append(target)
    return written

if __name__ == "__main__":
    for path in run():
        print(path)
