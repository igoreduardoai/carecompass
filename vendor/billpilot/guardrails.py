"""Safety checks applied to every LLM output before a patient sees it."""
import re

MEDICAL_ADVICE = re.compile(r"\b(you should (stop|start|take)|dosage|diagnos(e|is) you|skip (your )?(treatment|medication))\b", re.I)
PHI = [re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),          # SSN
       re.compile(r"\b\d{9,}\b"),                     # long member/account ids
       re.compile(r"\b(DOB|date of birth)\b", re.I)]
MONEY = re.compile(r"\$\s?([\d,]+\.\d{2})")

def check(text: str, facts: dict):
    """Return list of violations. facts = numbers the text is allowed to cite."""
    v = []
    if MEDICAL_ADVICE.search(text): v.append("medical_advice")
    if any(p.search(text) for p in PHI): v.append("phi_leak")
    allowed = {f"{x:,.2f}" for x in facts.get("amounts", [])}
    for m in MONEY.findall(text):
        if m not in allowed: v.append(f"unsupported_amount:{m}")
    if facts.get("must_mention_total") and f"{facts['total']:,.2f}" not in text:
        v.append("missing_total")
    return v
