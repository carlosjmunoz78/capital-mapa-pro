from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

CANONICAL_STAGES = (
    "OBSERVE", "MEASURE", "DETECT", "PROPOSE", "LAB", "TEST",
    "EVALUATE", "TRIBUNAL", "OLD_VS_NEW", "CANARY",
    "PROMOTE_OR_ROLLBACK", "LEARN",
)

@dataclass(frozen=True)
class MetaLearningSummary:
    company_id: str
    environment: str
    version: str
    cycle_count: int
    bottleneck_stage: str | None
    bottleneck_score: int
    decision: str
    hypothesis: str
    prior_strategy_version: str
    candidate_strategy_version: str
    auto_apply_allowed: bool
    anti_gaming: dict
    metrics: dict

def _stage_index(stage: str) -> int:
    try:
        return CANONICAL_STAGES.index(stage)
    except ValueError:
        return len(CANONICAL_STAGES)

def analyze(
    records: Iterable[dict],
    *,
    company_id: str,
    environment: str,
    version: str,
    prior_strategy_version: str = "meta-v0",
    minimum_cycles: int = 3,
) -> MetaLearningSummary:
    cycles = set()
    stage_stats: dict[str, dict[str, float]] = {}

    for raw in records:
        if str(raw.get("company_id", "")) != company_id:
            continue
        if str(raw.get("environment", "")) != environment:
            continue
        if str(raw.get("version", "")) != version:
            continue
        cycle_id = str(raw.get("cycle_id", "")).strip()
        if cycle_id:
            cycles.add(cycle_id)
        stage = str(raw.get("stage", ""))
        if stage not in CANONICAL_STAGES:
            continue
        bucket = stage_stats.setdefault(stage, {
            "green": 0.0, "waiting": 0.0, "blocked": 0.0,
            "human_required": 0.0, "cost_eur": 0.0,
        })
        status = str(raw.get("status", "")).upper()
        if status == "GREEN":
            bucket["green"] += 1
        elif status == "WAITING":
            bucket["waiting"] += 1
        elif status == "BLOCKED":
            bucket["blocked"] += 1
        elif status == "HUMAN_REQUIRED":
            bucket["human_required"] += 1
        bucket["cost_eur"] += float(raw.get("cost_eur", 0.0) or 0.0)

    scored = []
    for stage, stats in stage_stats.items():
        score = int(stats["waiting"] + 3 * stats["blocked"] + 4 * stats["human_required"])
        if score > 0:
            scored.append((score, _stage_index(stage), stage))
    scored.sort(key=lambda item: (-item[0], item[1], item[2]))

    cycle_count = len(cycles)
    bottleneck_stage = scored[0][2] if scored else None
    bottleneck_score = scored[0][0] if scored else 0

    if cycle_count < minimum_cycles:
        decision = "MORE_EVIDENCE"
        hypothesis = "Collect more independent cycles before changing the learning strategy."
    elif bottleneck_stage is None:
        decision = "NO_CHANGE"
        hypothesis = "No repeated learning-pipeline bottleneck is demonstrated."
    else:
        decision = "PROPOSE_META_EXPERIMENT"
        hypothesis = (
            f"Reduce validated friction at {bottleneck_stage} without weakening tests, "
            "judge independence, security, permissions, budget limits or promotion gates."
        )

    proposal_green = stage_stats.get("PROPOSE", {}).get("green", 0.0)
    learn_green = stage_stats.get("LEARN", {}).get("green", 0.0)
    learning_yield = (learn_green / proposal_green) if proposal_green else None

    return MetaLearningSummary(
        company_id=company_id,
        environment=environment,
        version=version,
        cycle_count=cycle_count,
        bottleneck_stage=bottleneck_stage,
        bottleneck_score=bottleneck_score,
        decision=decision,
        hypothesis=hypothesis,
        prior_strategy_version=prior_strategy_version,
        candidate_strategy_version=f"{prior_strategy_version}-candidate-1",
        auto_apply_allowed=False,
        anti_gaming={
            "judge_modification_allowed": False,
            "policy_weakening_allowed": False,
            "permission_escalation_allowed": False,
            "holdout_leakage_allowed": False,
            "threshold_reduction_requires_independent_gate": True,
        },
        metrics={
            "learning_yield": learning_yield,
            "waiting_total": int(sum(s["waiting"] for s in stage_stats.values())),
            "blocked_total": int(sum(s["blocked"] for s in stage_stats.values())),
            "human_required_total": int(sum(s["human_required"] for s in stage_stats.values())),
            "cost_eur": float(sum(s["cost_eur"] for s in stage_stats.values())),
            "stage_stats": stage_stats,
        },
    )
