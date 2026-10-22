"""Session-state test: caregiver_recap only repeats numbers the tools computed in the same Mcp-Session-Id."""
import json, threading, urllib.request
from http.server import HTTPServer
import server
srv = HTTPServer(("127.0.0.1", 0), server.H); port = srv.server_port
threading.Thread(target=srv.serve_forever, daemon=True).start()
def post(msg, sid=None):
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if sid: h["Mcp-Session-Id"] = sid
    r = urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/mcp", json.dumps(msg).encode(), h))
    return r.headers.get("Mcp-Session-Id"), json.loads(r.read())
sid, _ = post({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
assert sid
_, r = post({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "payment_plan", "arguments": {"total": 551, "months": 3}}}, sid)
_, r = post({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "caregiver_recap", "arguments": {"caregiver_name": "Ana"}}}, sid)
sp = r["result"]["structuredContent"]["speech"]; assert "3 interest-free payments of about $183.67" in sp and "Ana" in sp, sp
sid2, _ = post({"jsonrpc": "2.0", "id": 4, "method": "initialize", "params": {}})
_, r = post({"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "caregiver_recap", "arguments": {}}}, sid2)
assert r["result"]["structuredContent"]["items"] == 0  # no leakage across sessions
print("recap tests: 2/2 pass")
