from __future__ import annotations


class DependencyClosure:
    def __init__(self, canonical_ids):
        self.canonical = set(canonical_ids)
        self.edges: dict[str, tuple[str, ...]] = {}

    def add(self, engine_id: str, dependencies=()):
        if engine_id not in self.canonical:
            raise ValueError(f"unknown engine_id: {engine_id}")
        deps = tuple(dict.fromkeys(dependencies))
        unknown = [dep for dep in deps if dep not in self.canonical]
        if unknown:
            raise ValueError(f"unknown dependencies: {unknown}")
        if engine_id in deps:
            raise ValueError("engine cannot depend on itself")
        old = self.edges.get(engine_id)
        self.edges[engine_id] = deps
        try:
            self._assert_acyclic()
        except Exception:
            if old is None:
                self.edges.pop(engine_id, None)
            else:
                self.edges[engine_id] = old
            raise

    def _assert_acyclic(self):
        visiting, visited = set(), set()
        def visit(node):
            if node in visiting:
                raise ValueError("dependency cycle detected")
            if node in visited:
                return
            visiting.add(node)
            for dep in self.edges.get(node, ()):
                visit(dep)
            visiting.remove(node)
            visited.add(node)
        for node in tuple(self.edges):
            visit(node)

    def order(self):
        self._assert_acyclic()
        result, visited = [], set()
        def visit(node):
            if node in visited:
                return
            for dep in self.edges.get(node, ()):
                visit(dep)
            visited.add(node)
            result.append(node)
        for node in sorted(self.edges):
            visit(node)
        return tuple(result)

    def audit(self):
        referenced = {dep for deps in self.edges.values() for dep in deps}
        registered = set(self.edges)
        return {
            "valid": True,
            "nodes_defined": len(registered),
            "dependencies_referenced": len(referenced),
            "unmapped_canonical": tuple(sorted(self.canonical - registered)),
        }
