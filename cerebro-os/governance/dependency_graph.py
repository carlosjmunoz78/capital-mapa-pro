from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class DependencyGraph:
    edges: Dict[str, List[str]] = field(default_factory=dict)

    def add(self, engine_id: str, dependencies: List[str]):
        if engine_id in dependencies:
            raise ValueError("engine cannot depend on itself")
        self.edges[engine_id] = sorted(set(dependencies))
        self._assert_acyclic()

    def _assert_acyclic(self):
        visiting, visited = set(), set()
        def visit(node):
            if node in visiting:
                raise ValueError("dependency cycle detected")
            if node in visited:
                return
            visiting.add(node)
            for dep in self.edges.get(node, []):
                visit(dep)
            visiting.remove(node)
            visited.add(node)
        for node in list(self.edges):
            visit(node)

    def order(self):
        result, seen = [], set()
        def visit(node):
            if node in seen: return
            for dep in self.edges.get(node, []): visit(dep)
            seen.add(node); result.append(node)
        for node in sorted(self.edges): visit(node)
        return result
