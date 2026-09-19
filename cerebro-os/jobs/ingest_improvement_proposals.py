from __future__ import annotations

import json
import os
import sys
from pathlib import Path

CEREBRO_OS_ROOT = Path(__file__).resolve().parents[1]
if str(CEREBRO_OS_ROOT) not in sys.path:
    sys.path.insert(0, str(CEREBRO_OS_ROOT))

from learning.improvement_proposal_queue import ProposalQueue, ProposalRecord

_PRIORITY_BY_DOMAIN = {
    "SERVICE_HEALTH": "P0",
    "PLATFORM_HEALTH": "P0",
    "FINOPS": "P1",
    "WEB_SEO": "P1",
    "SEO_LOCAL_SOCIAL": "P1",
    "MARKET_INTELLIGENCE": "P2",
    "CONTENT": "P2",
}


def ingest() -> dict:
    proposals_root = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_PROPOSALS_ROOT", ".cerebro-runtime/proposals"
    ))
    queue_path = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_PROPOSAL_QUEUE", ".cerebro-runtime/proposals/queue.db"
    ))
    queue = ProposalQueue(queue_path)
    inserted = 0
    try:
        for path in sorted(proposals_root.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            company_id = str(payload.get("company_id", ""))
            for item in payload.get("proposals") or []:
                if str(item.get("company_id", "")) != company_id:
                    raise ValueError("cross-company proposal denied")
                domain = str(item["domain"])
                record = ProposalRecord(
                    company_id=company_id,
                    proposal_id=str(item["proposal_id"]),
                    source_key=str(item["source_key"]),
                    domain=domain,
                    environment=str(item["environment"]),
                    version=str(item["version"]),
                    summary=str(item["summary"]),
                    evidence_ref=str(item["evidence_ref"]),
                    action=str(item["action"]),
                    external_mutation_allowed=bool(item.get("external_mutation_allowed", False)),
                    cost_limit_eur=float(item.get("cost_limit_eur", 0.0)),
                    priority=_PRIORITY_BY_DOMAIN.get(domain, "P2"),
                    status="WAITING_TEST",
                )
                before = queue.count()
                queue.upsert(record)
                if queue.count() > before:
                    inserted += 1
        open_items = queue.list_open()
        output = {
            "inserted": inserted,
            "queued": len(open_items),
            "companies": sorted({item.company_id for item in open_items}),
            "priorities": {
                p: sum(1 for item in open_items if item.priority == p)
                for p in ("P0","P1","P2","P3")
            },
        }
        print(json.dumps(output, sort_keys=True))
        return output
    finally:
        queue.close()


if __name__ == "__main__":
    ingest()
