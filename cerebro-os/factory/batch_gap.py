from __future__ import annotations


def build_batch_gap_queue(*, canonical_ids, present_by_engine: dict[str, set[str]], standard_requirements) -> tuple[dict, ...]:
    canonical = tuple(canonical_ids)
    required = tuple(standard_requirements)
    required_set = set(required)
    queue = []
    for engine_id in canonical:
        present = set(present_by_engine.get(engine_id, set()))
        unknown = present - required_set
        if unknown:
            raise ValueError(f"unknown requirement markers for {engine_id}: {sorted(unknown)}")
        missing = tuple(item for item in required if item not in present)
        if missing:
            queue.append({
                "engine_id": engine_id,
                "missing": missing,
                "missing_count": len(missing),
            })
    return tuple(sorted(queue, key=lambda row: (-row["missing_count"], row["engine_id"])))


def completed_count(*, canonical_ids, queue) -> int:
    return len(tuple(canonical_ids)) - len(tuple(queue))
