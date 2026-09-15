from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED = ("AW", "AV", "BH")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_ids(value: Any) -> set[str]:
    ids: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"case_id", "id", "caseId"} and isinstance(item, str) and item.startswith("FISC-G"):
                ids.add(item)
            ids.update(_collect_ids(item))
    elif isinstance(value, list):
        for item in value:
            ids.update(_collect_ids(item))
    return ids


def validate_aw(data: Any) -> tuple[bool, str]:
    ids = _collect_ids(data)
    if len(ids) != 77:
        return False, f"AW must expose exactly 77 unique FISC-G case IDs; found {len(ids)}"
    expected = {f"FISC-G{i:03d}" for i in range(1, 78)}
    if ids != expected:
        return False, "AW case IDs are not exactly FISC-G001..FISC-G077"
    return True, "AW validated: 77 unique explicit case IDs"


def validate_bh(data: Any) -> tuple[bool, str]:
    ids = _collect_ids(data)
    if len(ids) != 21:
        return False, f"BH must expose exactly 21 unique pending FISC-G case IDs; found {len(ids)}"
    if not ids.issubset({f"FISC-G{i:03d}" for i in range(1, 78)}):
        return False, "BH contains case IDs outside the AW canonical range"
    return True, "BH validated: 21 unique pending IDs"


def validate_av(data: Any) -> tuple[bool, str]:
    text = json.dumps(data, ensure_ascii=False).lower()
    required_signals = ("provenance", "placeholder")
    missing = [signal for signal in required_signals if signal not in text]
    if missing:
        return False, f"AV provenance audit missing required signals: {', '.join(missing)}"
    return True, "AV validated as provenance/placeholder audit artifact"


def build_bound_lock(paths: dict[str, Path]) -> dict[str, Any]:
    missing = [key for key in REQUIRED if key not in paths or not paths[key].is_file()]
    if missing:
        raise ValueError(f"missing required artifact files: {', '.join(missing)}")

    validators = {"AW": validate_aw, "AV": validate_av, "BH": validate_bh}
    notes: dict[str, str] = {}
    for artifact_id in REQUIRED:
        try:
            data = load_json(paths[artifact_id])
        except Exception as exc:
            raise ValueError(f"{artifact_id} is not valid UTF-8 JSON: {exc}") from exc
        ok, reason = validators[artifact_id](data)
        if not ok:
            raise ValueError(reason)
        notes[artifact_id] = reason

    aw_ids = _collect_ids(load_json(paths["AW"]))
    bh_ids = _collect_ids(load_json(paths["BH"]))
    if not bh_ids.issubset(aw_ids):
        raise ValueError("BH pending IDs are not a subset of AW canonical IDs")

    return {
        "schema_version": "0.2.0",
        "engine_id": "TAX-001",
        "environment": "LAB",
        "status": "BOUND",
        "required_artifacts": list(REQUIRED),
        "artifacts": {
            artifact_id: {
                "sha256": sha256_file(paths[artifact_id]),
                "source_ref": str(paths[artifact_id]),
                "validation": notes[artifact_id],
            }
            for artifact_id in REQUIRED
        },
        "integrity": {
            "aw_case_count": len(aw_ids),
            "bh_pending_count": len(bh_ids),
            "bh_subset_of_aw": True,
        },
        "policy": {
            "fail_closed_when_unbound": True,
            "hash_algorithm": "sha256",
            "allow_placeholders": False,
            "manual_hash_inference_forbidden": True,
            "write_only_after_validation": True,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail-closed TAX-001 AW/AV/BH artifact binder")
    parser.add_argument("--aw", required=True, type=Path)
    parser.add_argument("--av", required=True, type=Path)
    parser.add_argument("--bh", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        lock = build_bound_lock({"AW": args.aw, "AV": args.av, "BH": args.bh})
    except ValueError as exc:
        print(f"FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "BOUND", "out": str(args.out), "integrity": lock["integrity"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
