from __future__ import annotations

import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from advisory.capabilities import CAPABILITY_REGISTRY  # noqa: E402
from runtime.zero_cost_observability_sink import StructuredStdoutObservabilitySink  # noqa: E402

REQUIRED_DISABLED = {
    "CEREBRO_EXTERNAL_WRITES": "disabled",
    "CEREBRO_APP_CRM_ACCESS": "disabled",
    "CEREBRO_PROD_CREDENTIALS": "disabled",
    "CEREBRO_CUSTOMER_DATA": "disabled",
}

OBSERVABILITY_MARKER = "PERSISTENT_OBSERVABILITY_PROBE"


def fail(message: str) -> None:
    print(json.dumps({"status": "BLOCKED", "reason": message}, sort_keys=True))
    raise SystemExit(2)


def validate_common() -> dict:
    if os.getenv("CEREBRO_ENV") != "PREPROD":
        fail("CEREBRO_ENV must be PREPROD")

    for key, expected in REQUIRED_DISABLED.items():
        if os.getenv(key) != expected:
            fail(f"{key} must be {expected}")

    status_path = Path("cerebro-os/advisory/capability_status_20260915.json")
    status = json.loads(status_path.read_text(encoding="utf-8"))
    runtime = status["capability_runtime"]

    if not runtime.get("ready_for_preprod_activation"):
        fail("PREPROD activation tribunal has not passed")
    if status.get("prod_enabled"):
        fail("PROD must remain disabled")
    if status.get("autonomy_green"):
        fail("Autonomy must remain disabled")
    if status.get("app_crm_prod_touched"):
        fail("App/CRM/PROD must remain untouched")

    return status


def run_test_discovery(pattern: str, failure_reason: str) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "cerebro-os/tests",
            "-p",
            pattern,
            "-v",
        ],
        check=False,
    )
    if completed.returncode != 0:
        fail(failure_reason)


def run_ephemeral_rehearsal() -> int:
    run_test_discovery("test_*.py", "unit test suite failed inside isolated PREPROD container")

    print(
        json.dumps(
            {
                "status": "PASS",
                "environment": "PREPROD",
                "mode": "ephemeral_rehearsal",
                "network": "disabled_by_container_runtime",
                "external_writes": False,
                "app_crm_access": False,
                "prod_credentials": False,
                "customer_data": False,
            },
            sort_keys=True,
        )
    )
    return 0


def run_persistent_representative_validation() -> None:
    run_test_discovery(
        "test_advisory_representative_cases_20260915.py",
        "persistent PREPROD representative case validation failed",
    )
    print(
        json.dumps(
            {
                "marker": "PERSISTENT_REPRESENTATIVE_VALIDATION_PASS",
                "status": "PASS",
                "environment": "PREPROD",
                "mode": "persistent_candidate",
                "representative_cases": 3,
                "domain_coverage": "12/12",
                "remote_onboarding_rehearsal": "PASS",
                "remote_onboarding_rehearsal_synthetic": True,
                "external_writes": False,
                "app_crm_access": False,
                "prod_credentials": False,
                "customer_data": False,
            },
            sort_keys=True,
        ),
        flush=True,
    )


def run_remote_onboarding_rehearsal_validation() -> None:
    run_test_discovery(
        "test_remote_company_e2e_rehearsal_v0.py",
        "persistent PREPROD remote onboarding E2E rehearsal failed",
    )
    print(
        json.dumps(
            {
                "marker": "PERSISTENT_REMOTE_ONBOARDING_REHEARSAL_PASS",
                "status": "PASS",
                "environment": "PREPROD",
                "mode": "persistent_candidate",
                "synthetic_rehearsal": True,
                "browser_bridge_used": False,
                "computer_use_performed": False,
                "external_writes": False,
                "app_crm_access": False,
                "prod_credentials": False,
                "customer_data": False,
            },
            sort_keys=True,
        ),
        flush=True,
    )


def emit_persistent_observability_probe() -> None:
    """Emit synthetic PREPROD log/metric/incident coverage for Advisory dependencies.

    These envelopes are deliberately marked synthetic and PREPROD. They provide a
    platform-log persistence proof without App/CRM/Supabase writes and without
    pretending that PROD per-engine coverage is already green.
    """

    engine_ids = sorted(
        {
            engine_id
            for capability in CAPABILITY_REGISTRY.values()
            for engine_id in capability.engine_ids
        }
    )
    sink = StructuredStdoutObservabilitySink()
    for engine_id in engine_ids:
        for kind in ("log", "metric", "incident"):
            sink.emit(
                {
                    "company_id": "fenix-capital",
                    "engine_id": engine_id,
                    "environment": "PREPROD",
                    "version": "advisory-preprod-v1",
                    "kind": kind,
                    "marker": OBSERVABILITY_MARKER,
                    "synthetic": True,
                    "severity": "INFO",
                    "message": f"synthetic PREPROD observability {kind} coverage probe",
                }
            )


def run_persistent_candidate() -> int:
    run_persistent_representative_validation()
    run_remote_onboarding_rehearsal_validation()
    emit_persistent_observability_probe()
    port = int(os.getenv("PORT", "8080"))

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path not in {"/", "/health", "/ready"}:
                self.send_response(404)
                self.end_headers()
                return

            payload = json.dumps(
                {
                    "status": "PASS",
                    "environment": "PREPROD",
                    "mode": "persistent_candidate",
                    "representative_validation": "PASS",
                    "representative_cases": 3,
                    "domain_coverage": "12/12",
                    "remote_onboarding_rehearsal": "PASS",
                    "remote_onboarding_rehearsal_synthetic": True,
                    "external_writes": False,
                    "app_crm_access": False,
                    "prod_credentials": False,
                    "customer_data": False,
                },
                sort_keys=True,
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: object) -> None:
            return

    print(
        json.dumps(
            {
                "status": "READY",
                "environment": "PREPROD",
                "mode": "persistent_candidate",
                "port": port,
                "representative_validation": "PASS",
                "representative_cases": 3,
                "domain_coverage": "12/12",
                "external_writes": False,
                "app_crm_access": False,
                "prod_credentials": False,
                "customer_data": False,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
    return 0


def main() -> int:
    validate_common()
    mode = os.getenv("CEREBRO_PREPROD_MODE")
    if mode == "ephemeral_rehearsal":
        return run_ephemeral_rehearsal()
    if mode == "persistent_candidate":
        return run_persistent_candidate()
    fail("CEREBRO_PREPROD_MODE must be ephemeral_rehearsal or persistent_candidate")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
