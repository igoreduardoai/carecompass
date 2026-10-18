"""Deterministic SDOH barrier scoring from a short patient-reported screener
(questions adapted in spirit from AHC-HRSN/PRAPARE domains; wording is our own).
Every flag cites the exact answer that triggered it, so clinicians can audit it."""
DOMAINS = {
    "transportation": {"q": "missed_visit_due_to_transport", "weight": 3,
                       "action": "Offer ride-scheduling help / non-emergency transport benefit check"},
    "cost": {"q": "skipped_care_due_to_cost", "weight": 3,
             "action": "Refer to financial counselor; check manufacturer patient-support and foundation copay programs"},
    "language": {"q": "needs_interpreter", "weight": 2,
                 "action": "Book interpreter for every visit; give instructions in preferred language"},
    "health_literacy": {"q": "difficulty_understanding_instructions", "weight": 2,
                        "action": "Teach-back; large-print, plain-language injection-schedule handout"},
    "housing": {"q": "housing_unstable", "weight": 2,
                "action": "Confirm a reliable phone/address for reminders; social work referral"},
    "caregiver": {"q": "needs_someone_to_drive_after_injection", "weight": 2,
                  "action": "Plan escort for injection days; caregiver contact on file"},
    "digital_access": {"q": "no_reliable_phone_or_internet", "weight": 1,
                       "action": "Use SMS/voice reminders instead of portal-only"},
}

def screen(answers: dict):
    flags, score = [], 0
    for name, d in DOMAINS.items():
        if answers.get(d["q"]) is True:
            flags.append({"domain": name, "evidence": f"{d['q']} = yes", "action": d["action"]})
            score += d["weight"]
    missed = int(answers.get("missed_appointments_last_12m", 0))
    if missed >= 2:
        flags.append({"domain": "adherence_risk", "evidence": f"missed_appointments_last_12m = {missed}",
                      "action": "Proactive outreach 72h before each visit; flexible scheduling"})
        score += 2
    tier = "high" if score >= 6 else "moderate" if score >= 3 else "low"
    return {"score": score, "tier": tier, "flags": flags}
