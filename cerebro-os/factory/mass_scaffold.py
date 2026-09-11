from __future__ import annotations

from pathlib import Path
import importlib.util


class EngineSpec:
    def __init__(self, engine_id: str, name: str, company_scope: str = "multi"):
        self.engine_id = engine_id
        self.name = name
        self.company_scope = company_scope


class MassScaffoldPlan:
    def __init__(self, engine_specs):
        self.engine_specs = list(engine_specs)

    def validate(self):
        ids = [s.engine_id for s in self.engine_specs]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate engine_id")
        if not all(ids):
            raise ValueError("empty engine_id")
        return True

    def output_paths(self, root: str = "generated-engines"):
        self.validate()
        return [str(Path(root) / spec.engine_id) for spec in self.engine_specs]


def _load_factory():
    path = Path(__file__).with_name("factory.py")
    spec = importlib.util.spec_from_file_location("cerebro_factory_module", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("factory module could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generate_all(root: Path, engine_ids: list[str] | tuple[str, ...]) -> list[Path]:
    if len(engine_ids) != len(set(engine_ids)):
        raise ValueError("duplicate engine_id")
    factory = _load_factory()
    created: list[Path] = []
    for engine_id in engine_ids:
        created.append(factory.scaffold(root, engine_id, engine_id))
    return created
