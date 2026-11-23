"""CP81: static inventory/gate for OnboardingQueue completion and retry callers.

Scope: checked-out repository Python sources. Does not certify external clients,
reflection, network calls, container executions or Cloudflare deployment.
"""
from __future__ import annotations
import ast
import json
from pathlib import Path

MUTATIONS=frozenset({"complete","retry_or_dead_letter"})
CONSOLE_WRAPPER=Path("tests/test_console_live_runtime_v0.py")

def _receiver_text(node:ast.AST)->str:
    try:
        return ast.unparse(node)
    except Exception:
        return type(node).__name__

def _negative_claim_test(parents:tuple[ast.AST,...])->bool:
    for outer in reversed(parents):
        if not isinstance(outer,(ast.With,ast.AsyncWith)):
            continue
        for item in outer.items:
            x=item.context_expr
            if not isinstance(x,ast.Call) or not isinstance(x.func,ast.Attribute):
                continue
            if x.func.attr not in {"assertRaises","assertRaisesRegex"}:
                continue
            if not x.args or not isinstance(x.args[0],ast.Name) or x.args[0].id!="PermissionError":
                continue
            if len(x.args)>1 and isinstance(x.args[1],ast.Constant) and isinstance(x.args[1].value,str):
                if "claim_attempts required" in x.args[1].value:
                    return True
    return False

def _imports_queue(tree:ast.AST)->bool:
    for x in ast.walk(tree):
        if isinstance(x,ast.ImportFrom) and x.module in {
            "runtime.onboarding_queue","cerebro_os.runtime.onboarding_queue"
        }:
            if any(y.name=="OnboardingQueue" for y in x.names):
                return True
        elif isinstance(x,ast.Import):
            if any("onboarding_queue" in y.name for y in x.names):
                return True
    return False

def inspect_source(source:str,relpath:str)->list[dict]:
    tree=ast.parse(source,filename=relpath)
    relevant=_imports_queue(tree) or relpath==str(CONSOLE_WRAPPER)
    findings=[]
    def walk(node:ast.AST,parents:tuple[ast.AST,...]=()):
        if isinstance(node,ast.Call):
            if (isinstance(node.func,ast.Attribute)
                    and node.func.attr in MUTATIONS
                    and (relevant or node.func.attr=="retry_or_dead_letter")):
                has_token=any(k.arg=="claim_attempts" for k in node.keywords)
                expected=not has_token and _negative_claim_test(parents)
                findings.append({
                    "path":relpath,"line":node.lineno,
                    "method":node.func.attr,"receiver":_receiver_text(node.func.value),
                    "has_claim_attempts":has_token,
                    "classification":"EXPECTED_DENIAL" if expected else (
                        "FENCED" if has_token else "MISSING_TOKEN"
                    ),
                })
            if (relevant and isinstance(node.func,ast.Name)
                    and node.func.id=="getattr" and len(node.args)>=2
                    and isinstance(node.args[1],ast.Constant)
                    and node.args[1].value in MUTATIONS):
                findings.append({
                    "path":relpath,"line":node.lineno,"method":str(node.args[1].value),
                    "receiver":_receiver_text(node.args[0]),
                    "has_claim_attempts":False,"classification":"DYNAMIC_REVIEW",
                })
        for child in ast.iter_child_nodes(node):
            walk(child,parents+(node,))
    walk(tree)
    return findings

def inventory(root:str|Path)->dict:
    root=Path(root).resolve()
    findings=[]
    parse_errors=[]
    files=0
    for p in sorted(root.rglob("*.py")):
        if any(s in {".git",".venv","venv","node_modules","__pycache__"} for s in p.parts):
            continue
        files+=1
        rel=p.relative_to(root).as_posix()
        try:
            findings.extend(inspect_source(p.read_text(encoding="utf-8"),rel))
        except (OSError,SyntaxError,UnicodeError) as err:
            parse_errors.append({"path":rel,"error_type":type(err).__name__})
    blockers=[x for x in findings if x["classification"] in {"MISSING_TOKEN","DYNAMIC_REVIEW"}]
    return {
        "record_type":"onboarding_claim_consumer_inventory_cp81",
        "environment":"LAB",
        "scope":"repository_python_static_only",
        "files_scanned":files,
        "consumer_sites":len(findings),
        "fenced":sum(x["classification"]=="FENCED" for x in findings),
        "expected_denials":sum(x["classification"]=="EXPECTED_DENIAL" for x in findings),
        "blockers":blockers,
        "parse_errors":parse_errors,
        "sites":findings,
        "external_clients_verified":False,
        "remote_execution_verified":False,
        "promotion_allowed":False,
    }

if __name__=="__main__":
    print(json.dumps(inventory(Path(__file__).resolve().parents[1]),sort_keys=True,indent=2))
