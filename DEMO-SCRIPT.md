# Demo (≤3 min) — v2, 2026-10-19 (adds caregiver_recap)
Label every terminal scene "Simulated Alexa+ experience" (allowed by the rules).
0:00 Hook: "Alexa, I got an ER bill. What do I actually owe?" LLMs are fluent, bad at money; CareCompass computes every number and remembers the session for a family caregiver.
0:20 Architecture: simulated Alexa+ → MCP Streamable HTTP (2025-11-25) → 4 read-only tools (estimate_patient_bill, payment_plan, screen_care_barriers, caregiver_recap) → grounding guard.
0:45 Live run: `python3 server.py` + `python3 alexa_sim.py` → estimate_patient_bill → $551.00 → payment_plan → 183.67 / 183.67 / 183.66 → spoken answer.
1:15 Grounding guard: `test_grounding.py` → "$560.00" draft BLOCKED → deterministic speech used. Real bug fixed (percent coinsurance, oop_remaining=0 placeholder).
1:40 Care barriers: "No car, I care for my mom, money is tight" → tier HIGH, flags transportation/cost/caregiver/adherence_risk, 5 resources; strict schema.
2:00 **Session memory — caregiver_recap**: same Mcp-Session-Id, "Alexa, send my daughter Ana a recap" → reads back only stored results: $551.00, 3 interest-free payments of about $183.67, barriers, next step. New session → 0 items (no leakage). `test_recap.py` 2/2.
2:40 Open source (MIT): tests 7/7 server + 2/2 recap + 3/3 grounding. Close: "Every number you hear was computed, not guessed."
Render: `python3 make_video.py video-spec.json out.mp4` (PIL frames + edge-tts en-US-AndrewNeural + ffmpeg, 1280x720).
