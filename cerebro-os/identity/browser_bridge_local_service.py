from __future__ import annotations

import html
import json
import os
import socket
import sys
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

HOST="127.0.0.1"
DEFAULT_PORT=8765
FORBIDDEN_SECRET_KEYS={"password","token","api_key","secret","secret_value","raw_secret","credential_value"}

def _reject_secrets(value)->None:
    if isinstance(value,dict):
        for key,child in value.items():
            if str(key).lower() in FORBIDDEN_SECRET_KEYS:
                raise ValueError(f"raw secret field forbidden: {key}")
            _reject_secrets(child)
    elif isinstance(value,list):
        for child in value:
            _reject_secrets(child)

def default_state_path()->Path:
    root=os.environ.get("LOCALAPPDATA")
    base=Path(root) if root else Path.home()/".cerebro"
    return base/"CEREBRO"/"browser-bridge"/"state.json"

def _atomic_write_json(path:Path,payload:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(payload,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    tmp.replace(path)

def load_state(path:Path)->dict:
    if not path.exists():
        return {
          "record_type":"browser_bridge_local_state",
          "device_id":"",
          "company_id":"",
          "profile_id":"",
          "browser_family":"CHROME",
          "environment":"LAB",
          "version":"v0",
          "paired":False,
          "online":True,
          "kill_switch_enabled":True,
          "last_seen_at":0,
          "cloud_transport_configured":False,
          "cloud_transport_status":"NOT_CONFIGURED",
        }
    data=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data,dict):
        raise ValueError("bridge state must be object")
    _reject_secrets(data)
    return data

def bootstrap_device_id()->str:
    raw=f"{socket.gethostname()}:{uuid.getnode()}".lower().replace(" ","-")
    safe="".join(ch for ch in raw if ch.isalnum() or ch in "-_.:")
    return ("desktop-"+safe)[0:96]

def pair_state(*,path:Path,company_id:str,profile_id:str,browser_family:str="CHROME",environment:str="LAB",version:str="v0")->dict:
    company_id=company_id.strip()
    profile_id=profile_id.strip()
    browser_family=browser_family.strip().upper()
    environment=environment.strip().upper()
    version=version.strip()
    if not company_id or not profile_id or not browser_family or not version:
        raise ValueError("company_id/profile_id/browser_family/version required")
    if environment not in {"LAB","PREPROD"}:
        raise ValueError("local launcher V0 supports LAB/PREPROD only")
    state=load_state(path)
    state.update({
      "record_type":"browser_bridge_local_state",
      "device_id":state.get("device_id") or bootstrap_device_id(),
      "company_id":company_id,
      "profile_id":profile_id,
      "browser_family":browser_family,
      "environment":environment,
      "version":version,
      "paired":True,
      "online":True,
      "kill_switch_enabled":True,
      "last_seen_at":int(time.time()),
      "cloud_transport_configured":False,
      "cloud_transport_status":"NOT_CONFIGURED",
    })
    _reject_secrets(state)
    _atomic_write_json(path,state)
    return state

def heartbeat_state(path:Path)->dict:
    state=load_state(path)
    if not state.get("device_id"):
        state["device_id"]=bootstrap_device_id()
    state["online"]=True
    state["kill_switch_enabled"]=True
    state["last_seen_at"]=int(time.time())
    _reject_secrets(state)
    _atomic_write_json(path,state)
    return state

def safe_public_state(state:dict)->dict:
    allowed=(
      "device_id","company_id","profile_id","browser_family","environment","version",
      "paired","online","kill_switch_enabled","last_seen_at",
      "cloud_transport_configured","cloud_transport_status",
    )
    return {key:state.get(key) for key in allowed}

def render_page(state:dict,message:str="")->bytes:
    safe=safe_public_state(state)
    msg=f"<p><strong>{html.escape(message)}</strong></p>" if message else ""
    rows="".join(
      f"<tr><td>{html.escape(str(k))}</td><td>{html.escape(str(v))}</td></tr>"
      for k,v in safe.items()
    )
    body=f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>CEREBRO Browser Bridge</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{{font-family:Arial,sans-serif;background:#111;color:#eee;margin:0;padding:32px}}
main{{max-width:760px;margin:auto;background:#1c1c1c;padding:24px;border-radius:12px}}
h1{{margin-top:0}} label{{display:block;margin-top:12px}} input,select{{width:100%;padding:10px;margin-top:4px;box-sizing:border-box}}
button{{margin-top:18px;padding:12px 18px;font-weight:700}} table{{width:100%;margin-top:24px;border-collapse:collapse}}
td{{padding:7px;border-bottom:1px solid #333}} .ok{{color:#9be28f}} .warn{{color:#ffcf70}}
</style></head><body><main>
<h1>CEREBRO Browser Bridge</h1>
<p class="ok">Servicio local activo en este PC.</p>
{msg}
<form method="post" action="/pair">
<label>Empresa <input name="company_id" value="{html.escape(str(safe.get("company_id") or "fenix"))}"></label>
<label>Perfil del navegador <input name="profile_id" value="{html.escape(str(safe.get("profile_id") or "chrome-default"))}"></label>
<label>Navegador <select name="browser_family"><option>CHROME</option><option>EDGE</option></select></label>
<label>Entorno <select name="environment"><option>LAB</option><option>PREPROD</option></select></label>
<label>Versión <input name="version" value="{html.escape(str(safe.get("version") or "v0"))}"></label>
<button type="submit">Emparejar este PC</button>
</form>
<table>{rows}</table>
<p class="warn">V0 no guarda contraseñas ni tokens. El transporte cloud permanece cerrado hasta validarlo explícitamente.</p>
</main></body></html>"""
    return body.encode("utf-8")

class BridgeHandler(BaseHTTPRequestHandler):
    server_version="CEREBROBridge/0"

    @property
    def state_path(self)->Path:
        return self.server.state_path  # type: ignore[attr-defined]

    def _send(self,status:int,body:bytes,content_type:str)->None:
        self.send_response(status)
        self.send_header("Content-Type",content_type)
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("X-Frame-Options","DENY")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self)->None:  # noqa: N802
        if self.path=="/health":
            state=heartbeat_state(self.state_path)
            body=json.dumps({"status":"GREEN",**safe_public_state(state)},sort_keys=True).encode("utf-8")
            self._send(200,body,"application/json; charset=utf-8")
            return
        if self.path in {"/","/pair"}:
            state=heartbeat_state(self.state_path)
            self._send(200,render_page(state),"text/html; charset=utf-8")
            return
        self._send(404,b'{"error":"not_found"}',"application/json; charset=utf-8")

    def do_POST(self)->None:  # noqa: N802
        if self.path!="/pair":
            self._send(404,b'{"error":"not_found"}',"application/json; charset=utf-8")
            return
        try:
            length=min(int(self.headers.get("Content-Length","0") or 0),8192)
            raw=self.rfile.read(length).decode("utf-8")
            form=parse_qs(raw,keep_blank_values=True)
            state=pair_state(
              path=self.state_path,
              company_id=(form.get("company_id") or [""])[0],
              profile_id=(form.get("profile_id") or [""])[0],
              browser_family=(form.get("browser_family") or ["CHROME"])[0],
              environment=(form.get("environment") or ["LAB"])[0],
              version=(form.get("version") or ["v0"])[0],
            )
        except Exception as exc:
            state=load_state(self.state_path)
            self._send(400,render_page(state,f"No se pudo emparejar: {type(exc).__name__}"),"text/html; charset=utf-8")
            return
        self._send(200,render_page(state,"PC emparejado localmente. Mantén esta ventana abierta."),"text/html; charset=utf-8")

    def log_message(self,format:str,*args:object)->None:
        return

def serve(*,host:str=HOST,port:int=DEFAULT_PORT,state_path:Path|None=None)->None:
    if host not in {"127.0.0.1","localhost"}:
        raise ValueError("Browser Bridge V0 must bind to loopback only")
    target=state_path or default_state_path()
    heartbeat_state(target)
    server=ThreadingHTTPServer((host,port),BridgeHandler)
    server.state_path=target  # type: ignore[attr-defined]
    print(json.dumps({
      "status":"READY","service":"CEREBRO Browser Bridge","host":host,"port":port,
      "state_path":str(target),"prod_enabled":False,"raw_secret_storage":False,
    },sort_keys=True),flush=True)
    server.serve_forever()

def main()->int:
    port=int(os.environ.get("CEREBRO_BRIDGE_PORT",str(DEFAULT_PORT)))
    serve(port=port)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
