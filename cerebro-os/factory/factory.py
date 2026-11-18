from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

HUMAN_EXCEPTION_CODES = [
    "LEGAL_REQUIRED",
    "SIGNATURE_REQUIRED",
    "LOW_CONFIDENCE",
    "HIGH_RISK",
    "POLICY_CONFLICT",
    "SECURITY_INCIDENT",
    "MONEY_LIMIT",
    "CUSTOMER_HUMAN_REQUEST",
]

ENGINE_ID_RE = re.compile(r"^(?=.{3,64}$)(?=.*[A-Z])[A-Z0-9]+(?:-[A-Z0-9]+)*$")
# Canonical registry includes 3RD-001: permit digits first, but reject punctuation-only IDs.


def validate_engine_id(engine_id: str) -> str:
    engine_id = engine_id.strip().upper()
    if not ENGINE_ID_RE.match(engine_id):
        raise ValueError("engine_id must use A-Z, 0-9 and hyphen only")
    return engine_id


def build_manifest(engine_id: str, name: str) -> dict:
    engine_id = validate_engine_id(engine_id)
    return {
        "engine_id": engine_id,
        "name": name.strip() or engine_id,
        "company_scope": "GLOBAL_OR_SCOPED",
        "environment": "LAB",
        "version": "0.1.0",
        "status": "DEFINED_NOT_BUILT",
        "owner": "UNASSIGNED",
        "inputs": [],
        "outputs": [],
        "permissions": [],
        "policies": ["deny_cross_company_by_default", "deterministic_before_ai", "zero_new_cost_by_default"],
        "events_in": [],
        "events_out": [],
        "tests": ["unit", "contract", "integration"],
        "evaluation": ["policy_gate", "tribunal_gate"],
        "observability": ["request_id", "company_id", "engine_id", "version", "environment", "result", "duration_ms", "cost_eur"],
        "cost_budget": {"target_additional_eur": 0},
        "backup": {"required": True, "verified": False},
        "rollback": {"required": True, "verified": False},
        "rebuild": {"required": True, "verified": False},
        "dependencies": [],
        "autonomy_level": "MANUAL_WITH_APPROVAL",
        "media_gateway": {
            "provider_engine_id": "UMS-001",
            "connection": "CEREBRO_GATEWAY_UNIVERSAL",
            "provisioner": "FACT-001",
            "enrollment": "AUTOMATIC_ON_ENGINE_CREATE_WHEN_FACTORY_IAM_READY",
            "enrollment_status": "PENDING_FACTORY_IAM",
            "capabilities": ["IMAGE.SYNTHETIC"],
            "uses_per_engine_worker": False,
            "uses_per_engine_subscription": False,
            "publish_authorized": False,
            "paid_execution_enabled": False,
            "version": "1.0.0"
        },
        "human_exception_codes": HUMAN_EXCEPTION_CODES,
    }


def scaffold(root: Path, engine_id: str, name: str, company_id: str | None = None) -> Path:
    """Create a fully staged engine without exposing partially built directories.

    Existing target is never modified. The temporary stage is cleaned on hook
    failure. A per-engine exclusive lock prevents concurrent FACT writers.
    Signed enrollment is allowed only *after* committing the complete scaffold.
    """
    engine_id = validate_engine_id(engine_id)
    parent = root / "engines"
    parent.mkdir(parents=True, exist_ok=True)
    target = parent / engine_id
    if target.exists():
        raise FileExistsError(f"engine already exists: {engine_id}")

    lock = parent / f".{engine_id}.factory.lock"
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    stage: Path | None = None
    try:
        if target.exists():
            raise FileExistsError(f"engine already exists: {engine_id}")
        stage = Path(tempfile.mkdtemp(prefix=f".{engine_id}.build-", dir=parent))
        for relative in [
            "config", "contracts", "policies", "events", "jobs", "api",
            "tests", "evaluation", "observability", "ops", "docs", "training",
        ]:
            (stage / relative).mkdir(parents=True, exist_ok=True)
        manifest = build_manifest(engine_id, name)
        (stage / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        # Retain the existing hooks, but do not let IAM transport send from a
        # partial engine. Stage an outbox and PENDING receipt with no secrets.
        import importlib.util
        media_hook = Path(__file__).with_name("universal_media_hook.py")
        spec = importlib.util.spec_from_file_location("cerebro_universal_media_hook", media_hook)
        if spec is None or spec.loader is None:
            raise RuntimeError("universal media hook unavailable")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.write_universal_media_scaffold(stage, manifest)

        enrollment_hook = Path(__file__).with_name("universal_media_enrollment.py")
        enroll_spec = importlib.util.spec_from_file_location(
            "cerebro_factory_media_enrollment", enrollment_hook
        )
        if enroll_spec is None or enroll_spec.loader is None:
            raise RuntimeError("universal media enrollment hook unavailable")
        enroll_module = importlib.util.module_from_spec(enroll_spec)
        enroll_spec.loader.exec_module(enroll_module)
        safe_scope = {"CEREBRO_COMPANY_ID": os.environ.get("CEREBRO_COMPANY_ID", "")}
        enroll_module.enroll_factory_engine(
            stage, manifest, company_id=company_id, environ=safe_scope
        )
        (stage / "docs" / "README.md").write_text(
            f"# {engine_id} · {manifest['name']}\n\nEstado inicial: DEFINED_NOT_BUILT.\n",
            encoding="utf-8",
        )
        for item, title in [
            ("backup", "Backup"), ("rollback", "Rollback"), ("rebuild", "Rebuild")
        ]:
            (stage / "ops" / f"{item}.md").write_text(
                f"# {title}\n\nPendiente de implementación y prueba.\n", encoding="utf-8"
            )

        # FACT writers hold this lock, so the existing target cannot be
        # replaced by a concurrent FACT call. Fail closed on an external write.
        if target.exists():
            raise FileExistsError(f"engine already exists: {engine_id}")
        stage.rename(target)
        stage = None

        # Real signed enrollment is never attempted while staging. If the
        # trusted runtime has ALL four required environment references, it may
        # now send a signed event. Missing IAM leaves a durable PENDING outbox.
        required = (
            "CEREBRO_FACT_ENROLL_EVENT_KEY", "CEREBRO_CLOUDFLARE_API_TOKEN",
            "CEREBRO_CLOUDFLARE_ACCOUNT_ID", "CEREBRO_FACT_ENROLL_QUEUE_ID",
        )
        if all(os.environ.get(k) for k in required):
            try:
                enroll_module.enroll_factory_engine(target, manifest, company_id=company_id)
            except Exception:
                # A committed scaffold stays intact; PENDING receipt/outbox
                # remains available for authorized recovery. No auto-retry.
                pass
        return target
    finally:
        try:
            if stage is not None and stage.exists():
                shutil.rmtree(stage)
        finally:
            lock.unlink(missing_ok=True)


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("usage: python factory.py ENGINE_ID 'Engine Name' [ROOT] [COMPANY_ID]", file=sys.stderr)
        return 2
    engine_id, name = argv[1], argv[2]
    root = Path(argv[3]) if len(argv) > 3 else Path(__file__).resolve().parents[1]
    company_id = argv[4] if len(argv) > 4 else None
    target = scaffold(root, engine_id, name, company_id=company_id)
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
