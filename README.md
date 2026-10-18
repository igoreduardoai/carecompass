# CareCompass MCP (Amazon "Build, Ship, Shape", Alexa+ track)
A self-hosted **MCP server** (Streamable HTTP, protocol 2025-11-25) that lets Alexa+, or any MCP client, answer two questions patients actually ask out loud:
1. *"How much do I really owe for this bill, and can I pay it over time?"*
2. *"What's keeping me from making my appointments, and who can help?"*

| Tool | What it does |
|---|---|
| `estimate_patient_bill` | Deterministic deductible/coinsurance/copay/OOP math plus a plain-English spoken answer. No LLM arithmetic. |
| `payment_plan` | Equal, interest-free installments (1–24) |
| `screen_care_barriers` | Transport/cost/language/caregiver/housing/literacy screener → actions + verified resources only |

All tools are read-only (`readOnlyHint`), take no PHI identifiers, and return a short `speech` field sized for voice.

## Simulated Alexa+ voice turn (agentic, real LLM)
`alexa_sim.py` acts as the Alexa+ side: it connects to the MCP server over Streamable HTTP (initialize → tools/list → tools/call), lets a free LLM on OpenRouter (`:free` models only) pick the tools via function calling, and speaks a short answer. A **grounding guard** checks that every dollar amount spoken comes from a tool result; if one doesn't, Alexa reads the server's deterministic `speech` instead.
```bash
python3 server.py &
export OPENROUTER_API_KEY=...    # free key; only ':free' models are ever called
python3 alexa_sim.py                         # demo: ER bill + 3-month plan
python3 alexa_sim.py "I live in 78741, no car, I care for my mom, money is tight. Who can help?"
python3 test_grounding.py
```
Real runs (Nemotron 3 Super, free) are saved in `demo/`: the bill comes out to $551.00, paid as $183.67 + $183.67 + $183.66; the barrier screen returns a high tier with transportation, cost and caregiver flags plus five resources.

## Run
```bash
python3 server.py            # http://localhost:8765/mcp
python3 test_server.py       # 6 HTTP smoke tests
```
Python stdlib only. To expose it for Alexa+ / judges: deploy to any free host (Render free tier, Fly.io, or a Cloudflare Tunnel from a laptop).

Built on two open projects by the same author: BillPilot (billing agent with 24 evals) and SightBridge (SDOH screener with 20 evals), vendored in `vendor/`.
MIT license. Synthetic data. Not medical or financial advice.
