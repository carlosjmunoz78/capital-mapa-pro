from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

def _record_hash(record: dict) -> str:
    raw = json.dumps(record, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def run() -> list[Path]:
    source_root = Path(os.environ.get(
        "CEREBRO_KNOWLEDGE_UPDATE_CANDIDATE_ROOT",
        ".cerebro-runtime/knowledge-update-candidates",
    ))
    ledger_root = Path(os.environ.get(
        "CEREBRO_KNOWLEDGE_LAB_LEDGER_ROOT",
        ".cerebro-runtime/knowledge-lab-ledger",
    ))
    ledger_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for path in sorted(source_root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("knowledge update candidate payload must be object")
        company_id = str(payload.get("company_id", "")).strip()
        if not company_id:
            raise ValueError("company_id required")

        ledger_path = ledger_root / f"{company_id}.jsonl"
        existing_hashes: set[str] = set()
        if ledger_path.exists():
            for line in ledger_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                existing = json.loads(line)
                if str(existing.get("company_id", "")) != company_id:
                    raise ValueError("cross-company ledger contamination denied")
                existing_hashes.add(str(existing.get("record_hash", "")))

        appended = 0
        with ledger_path.open("a", encoding="utf-8") as fh:
            for candidate in payload.get("candidates") or []:
                if str(candidate.get("company_id", "")) != company_id:
                    raise ValueError("cross-company candidate denied")
                if str(candidate.get("engine_id", "")) != "UPD-001":
                    raise ValueError("unexpected engine_id")
                if str(candidate.get("status", "")) != "CANDIDATE_ONLY":
                    raise ValueError("only candidate-only updates may enter LAB ledger")
                if bool(candidate.get("auto_apply_allowed", True)):
                    raise ValueError("auto-apply must remain disabled")
                if bool(candidate.get("external_mutation_allowed", True)):
                    raise ValueError("external mutation forbidden")
                if bool(candidate.get("delete_allowed", True)):
                    raise ValueError("delete forbidden")
                if not bool(candidate.get("append_only", False)):
                    raise ValueError("append-only invariant required")
                if not str(candidate.get("provenance_id", "")).strip():
                    raise ValueError("provenance_id required")
                if not str(candidate.get("source_type", "")).strip():
                    raise ValueError("source_type required")
                if float(candidate.get("confidence", 0.0)) < 0.80:
                    raise ValueError("low-confidence update cannot enter LAB ledger")

                record = {
                    "record_type": "knowledge_lab_candidate",
                    "company_id": company_id,
                    "engine_id": "KNW-001",
                    "source_engine_id": "UPD-001",
                    "environment": "LAB",
                    "knowledge_id": str(candidate.get("knowledge_id", "")),
                    "kind": str(candidate.get("kind", "KNOWLEDGE")),
                    "candidate_version": str(candidate.get("candidate_version", "")),
                    "provenance_id": str(candidate.get("provenance_id", "")),
                    "source_type": str(candidate.get("source_type", "")),
                    "source_uri": str(candidate.get("source_uri", "")),
                    "observed_at": str(candidate.get("observed_at", "")),
                    "validated_by": str(candidate.get("validated_by", "")),
                    "content_hash": str(candidate.get("content_hash", "")),
                    "evidence_hash": str(candidate.get("evidence_hash", "")),
                    "confidence": float(candidate.get("confidence", 0.0)),
                    "state": "VALIDATED_CANDIDATE",
                    "canonical": False,
                    "production_ready": False,
                    "history_preserved": True,
                    "external_mutation_allowed": False,
                    "delete_allowed": False,
                }
                record_hash = _record_hash(record)
                if record_hash in existing_hashes:
                    continue
                record["record_hash"] = record_hash
                fh.write(json.dumps(record, sort_keys=True) + "\n")
                existing_hashes.add(record_hash)
                appended += 1

        summary = ledger_root / f"{company_id}.summary.json"
        summary.write_text(json.dumps({
            "record_type": "knowledge_lab_ledger_summary",
            "company_id": company_id,
            "engine_id": "KNW-001",
            "environment": "LAB",
            "append_only": True,
            "canonical_mutation_performed": False,
            "production_ready": False,
            "external_mutation_allowed": False,
            "delete_allowed": False,
            "appended": appended,
            "ledger_path": str(ledger_path),
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        written.extend((ledger_path, summary))
    return written

if __name__ == "__main__":
    for path in run():
        print(path)
