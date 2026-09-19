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
from learning.improvement_observation_plan import ObservationEnvelope, plan_stage_results


def _load_companies(path: Path) -> tuple[ImprovementCompanyConfig, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("company config must be a list")
    return tuple(ImprovementCompanyConfig(**item) for item in payload)


def _evidence_executor_factory(evidence_root: Path):
    def factory(company_id: str):
        company_file = evidence_root / f"{company_id}.json"
        observation_file = evidence_root / f"{company_id}.observations.json"
        data = {}
        planned: dict[str, StageResult] = {}
        lab_evidence: dict = {}
        test_evidence: dict = {}
        evaluate_evidence: dict = {}
        tribunal_evidence: dict = {}
        old_vs_new_evidence: dict = {}
        if company_file.exists():
            raw = json.loads(company_file.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("evidence file must be object")
            data = raw
        elif observation_file.exists():
            raw = json.loads(observation_file.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("observation file must be object")
            if str(raw.get("company_id", "")) != company_id:
                raise ValueError("cross-company observation denied")
            planned = plan_stage_results(ObservationEnvelope(**raw))
        lab_file = evidence_root / f"{company_id}.lab.json"
        if lab_file.exists():
            raw_lab = json.loads(lab_file.read_text(encoding="utf-8"))
            if not isinstance(raw_lab, dict):
                raise ValueError("LAB evidence file must be object")
            if str(raw_lab.get("company_id", "")) != company_id:
                raise ValueError("cross-company LAB evidence denied")
            if str(raw_lab.get("stage", "")) != "LAB":
                raise ValueError("LAB evidence stage mismatch")
            if bool(raw_lab.get("external_mutation_allowed", True)):
                raise ValueError("LAB diagnostic cannot allow external mutation")
            lab_evidence = raw_lab
        test_file = evidence_root / f"{company_id}.test.json"
        if test_file.exists():
            raw_test = json.loads(test_file.read_text(encoding="utf-8"))
            if not isinstance(raw_test, dict):
                raise ValueError("TEST evidence file must be object")
            if str(raw_test.get("company_id", "")) != company_id:
                raise ValueError("cross-company TEST evidence denied")
            if str(raw_test.get("stage", "")) != "TEST":
                raise ValueError("TEST evidence stage mismatch")
            if bool(raw_test.get("external_mutation_allowed", True)):
                raise ValueError("TEST evidence cannot allow external mutation")
            test_evidence = raw_test
        evaluate_file = evidence_root / f"{company_id}.evaluate.json"
        if evaluate_file.exists():
            raw_evaluate = json.loads(evaluate_file.read_text(encoding="utf-8"))
            if not isinstance(raw_evaluate, dict):
                raise ValueError("EVALUATE evidence file must be object")
            if str(raw_evaluate.get("company_id", "")) != company_id:
                raise ValueError("cross-company EVALUATE evidence denied")
            if str(raw_evaluate.get("stage", "")) != "EVALUATE":
                raise ValueError("EVALUATE evidence stage mismatch")
            if bool(raw_evaluate.get("external_mutation_allowed", True)):
                raise ValueError("EVALUATE evidence cannot allow external mutation")
            evaluate_evidence = raw_evaluate
        tribunal_file = evidence_root / f"{company_id}.tribunal.json"
        if tribunal_file.exists():
            raw_tribunal = json.loads(tribunal_file.read_text(encoding="utf-8"))
            if not isinstance(raw_tribunal, dict):
                raise ValueError("TRIBUNAL evidence file must be object")
            if str(raw_tribunal.get("company_id", "")) != company_id:
                raise ValueError("cross-company TRIBUNAL evidence denied")
            if str(raw_tribunal.get("stage", "")) != "TRIBUNAL":
                raise ValueError("TRIBUNAL evidence stage mismatch")
            if bool(raw_tribunal.get("production_approval", True)):
                raise ValueError("LAB tribunal packet cannot approve production")
            if bool(raw_tribunal.get("external_mutation_allowed", True)):
                raise ValueError("TRIBUNAL evidence cannot allow external mutation")
            tribunal_evidence = raw_tribunal
        old_vs_new_file = evidence_root / f"{company_id}.old_vs_new.json"
        if old_vs_new_file.exists():
            raw_old_vs_new = json.loads(old_vs_new_file.read_text(encoding="utf-8"))
            if not isinstance(raw_old_vs_new, dict):
                raise ValueError("OLD_VS_NEW evidence file must be object")
            if str(raw_old_vs_new.get("company_id", "")) != company_id:
                raise ValueError("cross-company OLD_VS_NEW evidence denied")
            if str(raw_old_vs_new.get("stage", "")) != "OLD_VS_NEW":
                raise ValueError("OLD_VS_NEW evidence stage mismatch")
            if bool(raw_old_vs_new.get("live_effect_verified", True)):
                raise ValueError("structural OLD_VS_NEW cannot claim live effect")
            if bool(raw_old_vs_new.get("production_ready", True)):
                raise ValueError("structural OLD_VS_NEW cannot claim production readiness")
            if bool(raw_old_vs_new.get("external_mutation_allowed", True)):
                raise ValueError("OLD_VS_NEW evidence cannot allow external mutation")
            old_vs_new_evidence = raw_old_vs_new

        def execute(stage: str, attempt: int) -> StageResult:
            if stage == "LAB" and lab_evidence:
                return StageResult(
                    stage,
                    str(lab_evidence.get("status", "WAITING")),
                    str(lab_evidence.get("evidence_ref", f"evidence://waiting/{company_id}/LAB")),
                )
            if stage == "TEST" and test_evidence:
                return StageResult(
                    stage,
                    str(test_evidence.get("status", "WAITING")),
                    str(test_evidence.get("evidence_ref", f"evidence://waiting/{company_id}/TEST")),
                )
            if stage == "EVALUATE" and evaluate_evidence:
                return StageResult(
                    stage,
                    str(evaluate_evidence.get("status", "WAITING")),
                    str(evaluate_evidence.get("evidence_ref", f"evidence://waiting/{company_id}/EVALUATE")),
                )
            if stage == "TRIBUNAL" and tribunal_evidence:
                return StageResult(
                    stage,
                    str(tribunal_evidence.get("status", "WAITING")),
                    str(tribunal_evidence.get("evidence_ref", f"evidence://waiting/{company_id}/TRIBUNAL")),
                )
            if stage == "OLD_VS_NEW" and old_vs_new_evidence:
                return StageResult(
                    stage,
                    str(old_vs_new_evidence.get("status", "WAITING")),
                    str(old_vs_new_evidence.get("evidence_ref", f"evidence://waiting/{company_id}/OLD_VS_NEW")),
                )
            if stage in planned:
                return planned[stage]
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
