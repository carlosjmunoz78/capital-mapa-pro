from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

CEREBRO_OS_ROOT = Path(__file__).resolve().parents[1]
if str(CEREBRO_OS_ROOT) not in sys.path:
    sys.path.insert(0, str(CEREBRO_OS_ROOT))

from learning.improvement_proposal_queue import ProposalQueue, ProposalRecord


@dataclass(frozen=True)
class CandidatePlan:
    company_id: str
    proposal_id: str
    domain: str
    mode: str
    target: str
    change_spec: dict
    evidence_ref: str
    external_mutation_allowed: bool = False
    cost_eur: float = 0.0

    def validate(self) -> None:
        if self.mode not in {
            "DETERMINISTIC_PATCH_SPEC",
            "RESEARCH_REQUIRED",
            "INCIDENT_DIAGNOSTIC",
            "OPTIMIZATION_ANALYSIS",
        }:
            raise ValueError("invalid candidate mode")
        if self.external_mutation_allowed:
            raise ValueError("candidate V0 cannot mutate external systems")
        if self.cost_eur < 0:
            raise ValueError("candidate cost cannot be negative")
        if not all((self.company_id.strip(), self.proposal_id.strip(), self.domain.strip(), self.evidence_ref.strip())):
            raise ValueError("candidate identity required")


def _classify(item: ProposalRecord) -> CandidatePlan:
    summary = item.summary.lower()
    evidence_url = item.evidence_ref.split("#", 1)[0]

    if item.domain == "WEB_SEO" and "missing_canonical" in summary:
        mode = "DETERMINISTIC_PATCH_SPEC"
        target = evidence_url
        spec = {"operation": "SET_CANONICAL", "value": evidence_url}
    elif item.domain == "SEO_LOCAL_SOCIAL" and "robots_without_sitemap_reference" in summary:
        mode = "DETERMINISTIC_PATCH_SPEC"
        target = evidence_url
        spec = {"operation": "ADD_SITEMAP_REFERENCE", "value": "DISCOVER_FROM_EXISTING_SITEMAP"}
    elif item.domain in {"SERVICE_HEALTH", "PLATFORM_HEALTH"}:
        mode = "INCIDENT_DIAGNOSTIC"
        target = evidence_url
        spec = {"operation": "READ_ONLY_DIAGNOSTIC", "source_domain": item.domain}
    elif item.domain == "FINOPS":
        mode = "OPTIMIZATION_ANALYSIS"
        target = evidence_url
        spec = {"operation": "ANALYZE_RUNTIME_REGRESSION"}
    else:
        mode = "RESEARCH_REQUIRED"
        target = evidence_url
        spec = {"operation": "RESEARCH_AND_PROPOSE", "source_domain": item.domain}

    candidate = CandidatePlan(
        company_id=item.company_id,
        proposal_id=item.proposal_id,
        domain=item.domain,
        mode=mode,
        target=target,
        change_spec=spec,
        evidence_ref=item.evidence_ref,
    )
    candidate.validate()
    return candidate


def generate() -> list[Path]:
    queue_path = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_PROPOSAL_QUEUE",
        ".cerebro-runtime/proposals/queue.db",
    ))
    candidates_root = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_CANDIDATES_ROOT",
        ".cerebro-runtime/candidates",
    ))
    evidence_root = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_EVIDENCE_ROOT",
        ".cerebro-runtime/evidence",
    ))
    candidates_root.mkdir(parents=True, exist_ok=True)
    evidence_root.mkdir(parents=True, exist_ok=True)
    if not queue_path.exists():
        return []

    queue = ProposalQueue(queue_path)
    written: list[Path] = []
    try:
        by_company: dict[str, list[CandidatePlan]] = {}
        for item in queue.next_by_company():
            by_company.setdefault(item.company_id, []).append(_classify(item))

        for company_id, candidates in sorted(by_company.items()):
            candidate_path = candidates_root / f"{company_id}.json"
            candidate_path.write_text(json.dumps({
                "company_id": company_id,
                "candidates": [asdict(item) for item in candidates],
            }, sort_keys=True, indent=2) + "\n", encoding="utf-8")

            contract_ok = True
            failures: list[str] = []
            for item in candidates:
                try:
                    item.validate()
                    if item.mode == "DETERMINISTIC_PATCH_SPEC" and not item.change_spec.get("operation"):
                        raise ValueError("deterministic candidate requires operation")
                except Exception as exc:
                    contract_ok = False
                    failures.append(f"{item.proposal_id}:{type(exc).__name__}")

            test_path = evidence_root / f"{company_id}.test.json"
            test_path.write_text(json.dumps({
                "company_id": company_id,
                "stage": "TEST",
                "status": "GREEN" if contract_ok else "BLOCKED",
                "evidence_ref": f"file://{candidate_path}",
                "summary": f"{len(candidates)} candidate contract test(s); failures={len(failures)}",
                "test_scope": "CANDIDATE_CONTRACT_ONLY",
                "external_mutation_allowed": False,
                "cost_eur": 0.0,
                "failures": failures,
            }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            written.extend((candidate_path, test_path))
        return written
    finally:
        queue.close()


if __name__ == "__main__":
    for path in generate():
        print(path)
