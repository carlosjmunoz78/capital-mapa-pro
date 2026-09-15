from __future__ import annotations

import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REQUIRED_DISABLED = {
    "CEREBRO_EXTERNAL_WRITES": "disabled",
    "CEREBRO_APP_CRM_ACCESS": "disabled",
    "CEREBRO_PROD_CREDENTIALS": "disabled",
    "CEREBRO_CUSTOMER_DATA": "disabled",
}


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


def run_ephemeral_rehearsal() -> int:
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "cerebro-os/tests", "-v"],
        check=False,
    )
    if completed.returncode != 0:
        fail("unit test suite failed inside isolated PREPROD container")

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


def run_persistent_candidate() -> int:
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
                "external_writes": False,
                "app_crm_access": False,
                "prod_credentials": False,
                "customer_data": False,
            },
            sort_keys=True,
        )
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
