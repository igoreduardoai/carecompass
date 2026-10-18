"""Clinician-facing 'barrier card' + optional free-LLM patient message, with guardrails."""
import os, json, re, urllib.request
from .screen import screen
from .resources import match, DIR

BANNED = re.compile(r"\b(non-?compliant|lazy|refuses|won't comply|unreliable patient)\b", re.I)  # stigmatizing language
ADVICE = re.compile(r"\b(stop|skip|delay) (your )?(injection|treatment|drops)\b", re.I)

def _llm(prompt):
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GROQ_API_KEY")
    if not key: return None
    try:
        if os.getenv("GEMINI_API_KEY"):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
            body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0}}
            r = json.loads(urllib.request.urlopen(urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"}), timeout=30).read())
            return r["candidates"][0]["content"]["parts"][0]["text"]
        body = {"model": "llama-3.1-8b-instant", "temperature": 0, "messages": [{"role": "user", "content": prompt}]}
        r = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", json.dumps(body).encode(),
                       {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}), timeout=30).read())
        return r["choices"][0]["message"]["content"]
    except Exception:
        return None

def check_message(text, allowed_resource_names):
    v = []
    if BANNED.search(text): v.append("stigmatizing_language")
    if ADVICE.search(text): v.append("treatment_advice")
    if re.search(r"\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}", text):
        phones = {r.get("phone") for r in DIR if r.get("phone")}
        for p in re.findall(r"\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}", text):
            if p not in phones: v.append(f"unknown_phone:{p}")
    return v

def build(patient: dict):
    s = screen(patient["answers"])
    res = match(s["flags"], patient["zip"])
    template = ("We want to make it easier for you to keep your eye appointments. "
                + " ".join(f"We can help with {f['domain'].replace('_', ' ')}." for f in s["flags"][:3])
                + (" Resources: " + "; ".join(f"{r['name']}" + (f" ({r['phone']})" if r.get('phone') else "") for r in res[:3]) + "." if res else "")
                + " Please keep your next visit: your care team is here to help.")
    msg, src = template, "template"
    llm = _llm(f"Rewrite kindly at a 6th-grade reading level, in {patient.get('language','English')}, max 80 words, keep names/phones exactly, add nothing new:\n{template}")
    if llm and not check_message(llm, [r["name"] for r in res]):
        msg, src = llm, "llm"
    return {"patient_id": patient["id"], "tier": s["tier"], "score": s["score"], "flags": s["flags"],
            "resources": res, "patient_message": msg, "message_source": src,
            "note": "Decision support only. Clinician reviews before any outreach."}
