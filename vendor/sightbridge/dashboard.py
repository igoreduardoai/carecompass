"""Clinic-level view: which barriers drive missed anti-VEGF visits (synthetic panel)."""
import json, collections
from .screen import screen
def summarize(patients):
    c, tiers = collections.Counter(), collections.Counter()
    for p in patients:
        s = screen(p["answers"]); tiers[s["tier"]] += 1
        for f in s["flags"]: c[f["domain"]] += 1
    return {"n": len(patients), "tiers": dict(tiers), "barriers": c.most_common()}
if __name__ == "__main__":
    print(json.dumps(summarize(json.load(open("data/patients.json"))), indent=1))
