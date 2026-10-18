"""CareCompass MCP: a self-hosted MCP server (Streamable HTTP, JSON responses) for the Alexa+ track.
Tools: estimate_patient_bill, payment_plan, screen_care_barriers.
Reuses BillPilot (deterministic billing + guardrails) and SightBridge (SDOH screener).
Run: python3 server.py  -> POST http://localhost:8765/mcp"""
import json, sys, uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
ROOT = Path(__file__).resolve().parent / "vendor"
sys.path.insert(0, str(ROOT))
from billpilot.billing import Plan, Line, compute, payment_plan          # noqa
from billpilot.agent import template_explanation                        # noqa
import os
from sightbridge.card import build as barrier_card                       # noqa

PROTOCOL = "2025-11-25"
TOOLS = [
 {"name": "estimate_patient_bill", "description": "Compute exactly what a patient owes for a claim (deductible, coinsurance, copay, OOP max) and explain it in plain English. Math is deterministic; never estimated by an LLM.",
  "inputSchema": {"type": "object", "required": ["plan", "lines"], "properties": {
     "plan": {"type": "object", "properties": {"deductible_remaining": {"type": "number"}, "coinsurance": {"type": "number"}, "copay": {"type": "number"}, "oop_remaining": {"type": "number"}}},
     "lines": {"type": "array", "items": {"type": "object", "properties": {"code": {"type": "string"}, "description": {"type": "string"}, "billed": {"type": "number"}, "allowed": {"type": "number"}, "covered": {"type": "boolean"}}}}}},
  "annotations": {"readOnlyHint": True}},
 {"name": "payment_plan", "description": "Split a balance into 1-24 equal interest-free monthly payments.",
  "inputSchema": {"type": "object", "required": ["total", "months"], "properties": {"total": {"type": "number"}, "months": {"type": "integer", "minimum": 1, "maximum": 24}}},
  "annotations": {"readOnlyHint": True}},
 {"name": "screen_care_barriers", "description": "Turn yes/no answers about transport, cost, language, caregiving, housing, literacy and phone access into flagged barriers, concrete actions and verified resources. Decision support only.",
  "inputSchema": {"type": "object", "required": ["zip", "answers"], "properties": {"zip": {"type": "string"}, "language": {"type": "string"}, "answers": {"type": "object", "additionalProperties": False, "properties": {
        "missed_visit_due_to_transport": {"type": "boolean"}, "skipped_care_due_to_cost": {"type": "boolean"},
        "needs_interpreter": {"type": "boolean"}, "difficulty_understanding_instructions": {"type": "boolean"},
        "housing_unstable": {"type": "boolean"}, "needs_someone_to_drive_after_injection": {"type": "boolean", "description": "true if caregiving duties or lack of an escort get in the way"},
        "no_reliable_phone_or_internet": {"type": "boolean"}, "missed_appointments_last_12m": {"type": "integer"}}}}},
  "annotations": {"readOnlyHint": True}},
]

def call(name, a):
    if name == "estimate_patient_bill":
        calc = compute([Line(**{"code": "", "description": "service", "covered": True, **l}) for l in a["lines"]], Plan(**{"deductible_remaining": 0, "coinsurance": 0, "copay": 0, "oop_remaining": 1e9, **a["plan"]}))
        return {"total": calc["total"], "lines": calc["lines"], "speech": template_explanation(calc)}
    if name == "payment_plan":
        p = payment_plan(float(a["total"]), int(a["months"]))
        return {"installments": p, "speech": f"That's {len(p)} payments of about ${p[0]:,.2f}, with no interest."}
    if name == "screen_care_barriers":
        c = barrier_card({"id": "voice-session", "zip": a["zip"], "language": a.get("language", "English"), "answers": a["answers"]})
        unknown = sorted(set(a["answers"]) - set(TOOLS[2]["inputSchema"]["properties"]["answers"]["properties"]))
        return {"unknown_answer_keys": unknown, "tier": c["tier"], "flags": [f["domain"] for f in c["flags"]], "actions": [f["action"] for f in c["flags"]], "resources": [r["name"] for r in c["resources"]], "speech": c["patient_message"], "note": c["note"]}
    raise KeyError(name)

def handle(msg):
    m, i = msg.get("method"), msg.get("id")
    if i is None: return None  # notification
    if m == "initialize":
        res = {"protocolVersion": PROTOCOL, "capabilities": {"tools": {}}, "serverInfo": {"name": "carecompass-mcp", "version": "0.1.0"}}
    elif m == "tools/list": res = {"tools": TOOLS}
    elif m == "tools/call":
        try:
            out = call(msg["params"]["name"], msg["params"].get("arguments", {}))
            res = {"content": [{"type": "text", "text": out.get("speech", "")}], "structuredContent": out, "isError": False}
        except Exception as e:
            res = {"content": [{"type": "text", "text": f"Error: {type(e).__name__}: {e}"}], "isError": True}
    elif m == "ping": res = {}
    else: return {"jsonrpc": "2.0", "id": i, "error": {"code": -32601, "message": "Method not found"}}
    return {"jsonrpc": "2.0", "id": i, "result": res}

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/mcp": self.send_error(404); return
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        out = [r for r in map(handle, body) if r] if isinstance(body, list) else handle(body)
        if out is None or out == []:
            self.send_response(202); self.end_headers(); return
        data = json.dumps(out).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        if isinstance(body, dict) and body.get("method") == "initialize": self.send_header("Mcp-Session-Id", str(uuid.uuid4()))
        self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_GET(self): self.send_response(405); self.end_headers()
    def log_message(self, *a): pass

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8765")); print(f"CareCompass MCP on http://0.0.0.0:{port}/mcp")
    HTTPServer(("0.0.0.0", port), H).serve_forever()
