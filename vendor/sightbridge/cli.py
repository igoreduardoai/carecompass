import json, sys
from .card import build
for p in json.load(open(sys.argv[1] if len(sys.argv) > 1 else "data/patients.json")):
    c = build(p); print(json.dumps({k: c[k] for k in ("patient_id","tier","score","flags","patient_message")}, indent=1)); print()
