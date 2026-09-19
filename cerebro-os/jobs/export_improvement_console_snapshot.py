from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

CEREBRO_OS_ROOT = Path(__file__).resolve().parents[1]
if str(CEREBRO_OS_ROOT) not in sys.path:
    sys.path.insert(0, str(CEREBRO_OS_ROOT))

from console.improvement_status import export_console_source_status
from learning.improvement_proposal_queue import ProposalQueue


def run() -> Path:
    evidence_root = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_EVIDENCE_ROOT",
        ".cerebro-runtime/evidence",
    ))
    config_path = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_COMPANIES",
        "cerebro-os/config/improvement_companies.lab.json",
    ))
    output_path = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_CONSOLE_SNAPSHOT",
        ".cerebro-runtime/console/improvement-source-status.json",
    ))
    queue_path = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_PROPOSAL_QUEUE",
        ".cerebro-runtime/proposals/queue.db",
    ))
    configs_raw = json.loads(config_path.read_text(encoding="utf-8"))
    configs = tuple(config for config in configs_raw if config.get("enabled", True))
    snapshot = export_console_source_status(evidence_root, configs)
    if queue_path.exists():
        queue = ProposalQueue(queue_path)
        try:
            queue_summary = queue.summary()
        finally:
            queue.close()
    else:
        queue_summary = {"queued": 0, "companies": [], "priorities": {"P0": 0, "P1": 0, "P2": 0, "P3": 0}, "domains": {}, "top": []}
    payload = {
        **snapshot,
        "proposal_queue": queue_summary,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment": "LAB",
        "version": "1.0.0",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return output_path


if __name__ == "__main__":
    run()
