"""Resource matching against a local, curated directory (data/resources.json).
Only resources in the directory can be suggested: no invented phone numbers or programs."""
import json
from pathlib import Path
DIR = json.loads((Path(__file__).parent.parent / "data" / "resources.json").read_text())

def match(flags, zip_code: str):
    out = []
    domains = {f["domain"] for f in flags}
    for r in DIR:
        if domains & set(r["domains"]) and (r["zip_prefixes"] == ["*"] or any(zip_code.startswith(z) for z in r["zip_prefixes"])):
            out.append(r)
    return out
