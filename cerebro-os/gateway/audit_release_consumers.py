"""Static source consumer map, no runtime invocation and no source contents in output."""
import ast
import json
import subprocess
from pathlib import Path

def main():
    root=Path(__file__).resolve().parents[2]
    paths=subprocess.check_output(["git","-C",str(root),"ls-files","-z","cerebro-os"],text=True).split("\0")
    symbols={"control_decision","review_control","decide_verified","ConsolePipeline","Gateway","read_catalog"}
    hits=[];unparsed=[];scanned=0
    for name in paths:
        if not name.endswith(".py"):continue
        p=root/name
        try:tree=ast.parse(p.read_text(encoding="utf-8"),filename=name)
        except (OSError,UnicodeError,SyntaxError):
            unparsed.append(name);continue
        scanned+=1
        aliases={}
        for n in ast.walk(tree):
            if isinstance(n,ast.ImportFrom):
                for a in n.names:
                    if a.name in symbols:
                        aliases[a.asname or a.name]=a.name
                        hits.append({"path":name,"line":n.lineno,"kind":"import","symbol":a.name})
            elif isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in symbols:
                hits.append({"path":name,"line":n.lineno,"kind":"definition","symbol":n.name})
        for n in ast.walk(tree):
            if isinstance(n,ast.Call):
                f=n.func
                symbol=aliases.get(f.id,f.id) if isinstance(f,ast.Name) else f.attr if isinstance(f,ast.Attribute) else None
                if symbol in symbols:
                    hits.append({"path":name,"line":n.lineno,"kind":"call","symbol":symbol})
    print(json.dumps({"schema":"cerebro.static-consumers.v1","scope":"tracked Python source under cerebro-os",
       "commit":subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip(),
       "scanned":scanned,"unparsed":unparsed,"hits":sorted(hits,key=lambda x:(x["path"],x["line"],x["kind"])),
       "limitations":"Static named calls/imports only; not proof of dynamic callers, deployment or production authorization."},sort_keys=True))
if __name__=="__main__":main()
