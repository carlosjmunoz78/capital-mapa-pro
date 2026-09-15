from __future__ import annotations

import json
import os
import subprocess
import sys
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


def main() -> int:
    if os.getenv("CEREBRO_ENV") != "PREPROD":
        fail("CEREBRO_ENV must be PREPROD")
    if os.getenv("CEREBRO_PREPROD_MODE") != "ephemeral_rehearsal":
        fail("CEREBRO_PREPROD_MODE must be ephemeral_rehearsal")

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


if __name__ == "__main__":
    raise SystemExit(main())
