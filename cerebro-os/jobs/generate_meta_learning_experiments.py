from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

CEREBRO_OS_ROOT = Path(__file__).resolve().parents[1]
if str(CEREBRO_OS_ROOT) not in sys.path:
    sys.path.insert(0, str(CEREBRO_OS_ROOT))

from learning.meta_experiment import build

def run() -> list[Path]:
    meta_root = Path(os.environ.get("CEREBRO_META_LEARNING_ROOT", ".cerebro-runtime/meta-learning"))
    out_root = Path(os.environ.get("CEREBRO_META_EXPERIMENT_ROOT", ".cerebro-runtime/meta-experiments"))
    out_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for path in sorted(meta_root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("meta-learning record must be object")
        experiment = build(payload)
        if experiment is None:
            continue
        target = out_root / f"{experiment.company_id}.json"
        body = asdict(experiment)
        body["record_type"] = "meta_experiment_spec"
        body["status"] = "CANDIDATE_ONLY"
        body["production_ready"] = False
        body["evidence_required"] = [
            "baseline_meta_metrics",
            "candidate_meta_metrics",
            "independent_holdout",
            "tests",
            "evaluation",
            "tribunal",
            "rollback",
        ]
        target.write_text(json.dumps(body, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        written.append(target)
    return written

if __name__ == "__main__":
    for path in run():
        print(path)
