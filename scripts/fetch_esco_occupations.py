"""Cache the ESCO essential AND optional skills of the selected occupations to data/esco_occupation_skills.json.

    python scripts/fetch_esco_occupations.py      # needs internet (ESCO public API)

Used by build_skill_map.py to map the condensed SkillPath skill list onto occupations traceably.
"""
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_skill_map import ROOT, SELECTION, find_occupation  # noqa: E402

out = {"retrieved": dt.date.today().isoformat(), "source": "ESCO public API https://ec.europa.eu/esco/api",
       "occupations": {}}
for disc, ofo, ofo_title, min_qual, esco_label in SELECTION:
    occ = find_occupation(esco_label)
    links = occ["_links"]
    out["occupations"][ofo_title] = {
        "discipline": disc, "ofo_code": f"2021-{ofo}", "minimum_qualification": min_qual,
        "esco_occupation": occ["title"], "esco_uri": occ["uri"], "isco_code": str(occ.get("code", "")),
        "essential": sorted(s["title"] for s in links.get("hasEssentialSkill", [])),
        "optional": sorted(s["title"] for s in links.get("hasOptionalSkill", [])),
    }
    print(f"{ofo_title:28} essential {len(out['occupations'][ofo_title]['essential']):3}  optional {len(out['occupations'][ofo_title]['optional']):3}")
with open(os.path.join(ROOT, "data", "esco_occupation_skills.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
