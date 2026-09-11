from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class EngineSpec:
    engine_id: str
    name: str
    company_scope: str = "multi"

class MassScaffoldPlan:
    def __init__(self, engine_specs):
        self.engine_specs=list(engine_specs)
    def validate(self):
        ids=[s.engine_id for s in self.engine_specs]
        if len(ids)!=len(set(ids)): raise ValueError("duplicate engine_id")
        if not all(ids): raise ValueError("empty engine_id")
        return True
    def output_paths(self, root: str="generated-engines"):
        self.validate()
        return [str(Path(root)/spec.engine_id) for spec in self.engine_specs]
