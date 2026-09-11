from __future__ import annotations


class CapabilityActivationPlanner:
    def __init__(self, canonical_ids):
        self.canonical = set(canonical_ids)
        self.rules: list[dict] = []

    def add_rule(self, *, name: str, predicate, required=(), optional=()):
        if not name:
            raise ValueError("rule name required")
        required = tuple(dict.fromkeys(required))
        optional = tuple(dict.fromkeys(optional))
        unknown = [engine_id for engine_id in required + optional if engine_id not in self.canonical]
        if unknown:
            raise ValueError(f"unknown engine ids: {unknown}")
        overlap = set(required) & set(optional)
        if overlap:
            raise ValueError(f"engine cannot be required and optional in same rule: {sorted(overlap)}")
        self.rules.append({
            "name": name,
            "predicate": predicate,
            "required": required,
            "optional": optional,
        })

    def plan(self, company_profile: dict) -> dict:
        required: set[str] = set()
        optional: set[str] = set()
        matched: list[str] = []
        for rule in self.rules:
            if rule["predicate"](company_profile):
                matched.append(rule["name"])
                required.update(rule["required"])
                optional.update(rule["optional"])
        optional -= required
        return {
            "required": tuple(sorted(required)),
            "optional": tuple(sorted(optional)),
            "matched_rules": tuple(matched),
        }
