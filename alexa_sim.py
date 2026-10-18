"""Simulated Alexa+ voice turn against the CareCompass MCP server (real MCP over Streamable HTTP).
utterance -> LLM (OpenRouter, :free models only) picks MCP tools via function calling -> server does
the deterministic math -> LLM phrases a short spoken answer -> grounding guard: every $ amount
spoken must come from a tool result, otherwise we speak the tool's own template `speech`.
Run: python3 server.py &  then  OPENROUTER_API_KEY=... python3 alexa_sim.py "utterance" """
import json, os, re, sys, urllib.request
MCP = os.getenv("MCP_URL", "http://localhost:8765/mcp")
MODELS = os.getenv("OPENROUTER_MODELS", "nvidia/nemotron-3-super-120b-a12b:free,google/gemma-4-31b-it:free,google/gemma-4-26b-a4b-it:free").split(",")
SYSTEM = ("You are Alexa+, helping a patient by voice. Use the tools for ANY number; never do arithmetic yourself. "
          "If the user gives a bill, call estimate_patient_bill with the plan and lines they describe. "
          "Answer in <=60 spoken words, kind, no medical advice. Only say dollar amounts that appear in tool results. When barriers are screened, name the specific resources and actions the tool returned.")
DEMO = ("I got an ER bill. The visit was allowed at 620 dollars, an x-ray allowed at 95 and an ECG allowed at 40. "
        "I still have 500 dollars of deductible and 20 percent coinsurance. What do I owe, and can I split it over 3 months?")

def post(url, body, headers=None):
    r = urllib.request.urlopen(urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json", "Accept": "application/json, text/event-stream", **(headers or {})}), timeout=90)
    return json.loads(r.read() or b"null"), r.headers

class MCPClient:
    def __init__(self):
        res, h = post(MCP, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "alexa-sim", "version": "0.1"}}})
        self.h = {"Mcp-Session-Id": h.get("Mcp-Session-Id", ""), "MCP-Protocol-Version": "2025-11-25"}
        post(MCP, {"jsonrpc": "2.0", "method": "notifications/initialized"}, self.h)
        self.tools = post(MCP, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, self.h)[0]["result"]["tools"]
    def call(self, name, args):
        return post(MCP, {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": name, "arguments": args}}, self.h)[0]["result"]

def chat(messages, tools):
    last = None
    for m in MODELS:
        if not m.endswith(":free"): continue
        try:
            r, _ = post("https://openrouter.ai/api/v1/chat/completions", {"model": m, "temperature": 0, "messages": messages, "tools": tools},
                        {"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"})
            if r.get("choices"): return r["choices"][0]["message"], m
            last = r.get("error")
        except Exception as e: last = e
    raise RuntimeError(f"no free model answered: {last}")

AMT = re.compile(r"\$\s?([\d,]+(?:\.\d{1,2})?)")
def amounts(text): return {round(float(x.replace(",", "")), 2) for x in AMT.findall(text or "")}
def nums(obj):
    if isinstance(obj, bool): return set()
    if isinstance(obj, (int, float)): return {round(float(obj), 2)}
    if isinstance(obj, dict): return set().union(*(nums(v) for v in obj.values())) if obj else set()
    if isinstance(obj, list): return set().union(*(nums(v) for v in obj)) if obj else set()
    if isinstance(obj, str): return amounts(obj)
    return set()

def turn(utterance):
    mcp = MCPClient()
    tools = [{"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["inputSchema"]}} for t in mcp.tools]
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": utterance}]
    trace, grounded, fallback = [], set(), []
    for _ in range(4):
        msg, model = chat(msgs, tools)
        calls = msg.get("tool_calls") or []
        if not calls: break
        msgs.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": calls})
        for c in calls:
            args = json.loads(c["function"]["arguments"] or "{}")
            res = mcp.call(c["function"]["name"], args)
            out = res.get("structuredContent", {})
            grounded |= nums(out); fallback.append(out.get("speech", ""))
            trace.append({"tool": c["function"]["name"], "args": args, "result": out})
            msgs.append({"role": "tool", "tool_call_id": c["id"], "content": json.dumps(out)})
    speech = (msg.get("content") or "").strip()
    bad = sorted(amounts(speech) - grounded)
    if bad or not speech:
        speech = " ".join(s for s in fallback if s) or "Sorry, I couldn't work that out. Please check with your provider's billing office."
    return {"model": model, "trace": trace, "ungrounded_amounts_blocked": bad, "speech": speech}

if __name__ == "__main__":
    print(json.dumps(turn(sys.argv[1] if len(sys.argv) > 1 else DEMO), indent=1))
