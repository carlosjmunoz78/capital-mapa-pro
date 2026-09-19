from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

CEREBRO_OS_ROOT = Path(__file__).resolve().parents[1]
if str(CEREBRO_OS_ROOT) not in sys.path:
    sys.path.insert(0, str(CEREBRO_OS_ROOT))

from jobs.improvement_operations_registry import ImprovementCompanyConfig, ImprovementOperationsRegistry
from jobs.improvement_shared_worker import SharedImprovementWorker, WorkerPaths
from learning.continuous_improvement_runtime import StageResult


def _load_companies(path: Path) -> tuple[ImprovementCompanyConfig, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("company config must be a list")
    return tuple(ImprovementCompanyConfig(**item) for item in payload)


def _evidence_executor_factory(evidence_root: Path):
    def factory(company_id: str):
        company_file = evidence_root / f"{company_id}.json"
        data = {}
        if company_file.exists():
            raw = json.loads(company_file.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("evidence file must be object")
            data = raw

        def execute(stage: str, attempt: int) -> StageResult:
            item = data.get(stage)
            if not isinstance(item, dict):
                return StageResult(stage, "WAITING", f"evidence://waiting/{company_id}/{stage}")
            status = str(item.get("status", "WAITING"))
            evidence_ref = str(item.get("evidence_ref", f"evidence://waiting/{company_id}/{stage}"))
            human_reason = item.get("human_reason")
            return StageResult(stage, status, evidence_ref, human_reason)
        return execute
    return factory


def run() -> dict:
    root = Path(os.environ.get("CEREBRO_IMPROVEMENT_STATE_ROOT", ".cerebro-runtime/improvement"))
    config_path = Path(os.environ.get("CEREBRO_IMPROVEMENT_COMPANIES", "cerebro-os/config/improvement_companies.lab.json"))
    evidence_root = Path(os.environ.get("CEREBRO_IMPROVEMENT_EVIDENCE_ROOT", ".cerebro-runtime/evidence"))
    now_raw = os.environ.get("CEREBRO_IMPROVEMENT_NOW")
    now = datetime.fromisoformat(now_raw) if now_raw else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    root.mkdir(parents=True, exist_ok=True)
    registry = ImprovementOperationsRegistry(root / "registry.db")
    try:
        for config in _load_companies(config_path):
            registry.upsert(config)
        worker = SharedImprovementWorker(registry, WorkerPaths(root / "state"))
        result, supervisor = worker.run(now, _evidence_executor_factory(evidence_root))
        output = {
            "status": supervisor["status"],
            "companies": supervisor["companies"],
            "green": supervisor["green"],
            "waiting": supervisor["waiting"],
            "blocked": supervisor["blocked"],
            "human_required": supervisor["human_required"],
            "not_due": supervisor["not_due"],
            "attention_company_ids": supervisor["attention_company_ids"],
        }
        print(json.dumps(output, sort_keys=True))
        return output
    finally:
        registry.close()


if __name__ == "__main__":
    result = run()
    # WAITING is a valid scheduled state. BLOCKED/HUMAN_REQUIRED are surfaced
    # by the JSON result and should be monitored, not silently converted to GREEN.
