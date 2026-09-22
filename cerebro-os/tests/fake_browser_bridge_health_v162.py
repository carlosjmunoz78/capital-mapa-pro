"""Offline CI fixture only: localhost /health for Windows installer runtime test."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
class H(BaseHTTPRequestHandler):
 def do_GET(self):
  if self.path != "/health":
   self.send_error(404);return
  payload={"status":"GREEN","service":"CEREBRO Browser Bridge","service_version":"1.4.1",
           "company_id":"fenix","environment":"LAB","version":"v0","paired":True,
           "kill_switch_enabled":True,"extension_status":"NOT_CONNECTED",
           "cloud_transport_status":"NOT_CONFIGURED"}
  body=json.dumps(payload).encode()
  self.send_response(200)
  self.send_header("Content-Type","application/json")
  self.send_header("Content-Length",str(len(body)))
  self.end_headers();self.wfile.write(body)
 def log_message(self,*args): pass
ThreadingHTTPServer(("127.0.0.1",8765),H).serve_forever()
