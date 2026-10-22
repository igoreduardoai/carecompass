"""Smoke test over real HTTP: python3 test_server.py"""
import json, subprocess, sys, time, urllib.request, os
p = subprocess.Popen([sys.executable, "server.py"], env={**os.environ, "PORT": "8799"}); time.sleep(1.2)
def rpc(m, params=None, i=1):
    r = urllib.request.urlopen(urllib.request.Request("http://localhost:8799/mcp", json.dumps({"jsonrpc": "2.0", "id": i, "method": m, "params": params or {}}).encode(), {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}))
    return json.loads(r.read())
ok = []
try:
    ok.append(rpc("initialize", {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}})["result"]["serverInfo"]["name"] == "carecompass-mcp")
    ok.append(len(rpc("tools/list")["result"]["tools"]) == 4)  # +caregiver_recap (v0.2)
    r = rpc("tools/call", {"name": "estimate_patient_bill", "arguments": {"plan": {"deductible_remaining": 500, "coinsurance": 0.2}, "lines": [{"description": "ER visit", "billed": 1450, "allowed": 620}, {"description": "X-ray", "billed": 380, "allowed": 95}, {"description": "ECG", "billed": 210, "allowed": 40}]}})
    ok.append(r["result"]["structuredContent"]["total"] == 551.0)
    r = rpc("tools/call", {"name": "estimate_patient_bill", "arguments": {"plan": {"deductible_remaining": 500, "coinsurance": 20, "copay": 0, "oop_remaining": 0}, "lines": [{"description": "ER visit", "billed": 620, "allowed": 620}, {"description": "X-ray", "billed": 95, "allowed": 95}, {"description": "ECG", "billed": 40, "allowed": 40}]}})
    ok.append(r["result"]["structuredContent"]["total"] == 551.0)  # LLM-style args: percent coinsurance + oop_remaining=0 placeholder
    ok.append(rpc("tools/call", {"name": "payment_plan", "arguments": {"total": 551, "months": 3}})["result"]["structuredContent"]["installments"] == [183.67, 183.67, 183.66])
    r = rpc("tools/call", {"name": "screen_care_barriers", "arguments": {"zip": "78741", "answers": {"missed_visit_due_to_transport": True, "needs_interpreter": True, "missed_appointments_last_12m": 3}}})
    ok.append(r["result"]["structuredContent"]["tier"] == "high")
    ok.append(rpc("tools/call", {"name": "nope", "arguments": {}})["result"]["isError"] is True)
finally:
    p.terminate()
print(ok, f"{sum(ok)}/{len(ok)} passed"); sys.exit(0 if all(ok) else 1)
