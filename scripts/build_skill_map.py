"""Build data/skill_map.csv and data/skill_descriptions.json from published sources.

    python scripts/build_skill_map.py            # needs internet (ESCO public API)

SOURCES
  Occupations  DHET (2024) National List of Occupations in High Demand: 2024.
               Government Gazette No. 50510, Notice 2414 of 2024, 16 April 2024 (Table 2).
  Skills       ESCO - European Skills, Competences, Qualifications and Occupations
               (European Commission), public API https://ec.europa.eu/esco/api :
               the occupation's "essential skills" (hasEssentialSkill) and each skill's description.
  Income       Statistics South Africa (2024) Labour Market Dynamics in South Africa, 2024.
               Report 02-11-02 (2024), section 4.3, p. 64: median monthly earnings of employees, 2024,
               by occupation group. Matched mechanically by the ISCO major group of the ESCO occupation.

SELECTION RULE (documented in DECISIONS.md)
  From the 2024 OIHD list: OFO major groups 2-3 (professionals, technicians) with a minimum
  qualification at NQF 6-7 (diploma / bachelor's), six per discipline of the profile template.
  Each is matched to the ESCO occupation whose 4-digit ISCO unit group equals the OFO unit group;
  where no ESCO occupation shares the unit group, the closest ESCO occupation by title is used and
  flagged with isco_unit_match = N.

The output is deterministic for a given ESCO release (rows and skills sorted). The retrieval date is
written to data/skill_map_build.json.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://ec.europa.eu/esco/api"

# discipline, OFO code (2021), OFO occupation title (as gazetted), minimum qualification (as gazetted),
# ESCO occupation preferred label
SELECTION = [
    ("Commerce", "241107", "Financial Accountant", "Bachelor's Degree or Advanced Diploma (NQF Level 7)", "accountant"),
    ("Commerce", "241104", "External Auditor", "Bachelor's Degree or Advanced Diploma (NQF Level 7)", "financial auditor"),
    ("Commerce", "241103", "Tax Professional", "Bachelor's Degree or Advanced Diploma (NQF Level 7)", "tax advisor"),
    ("Commerce", "242101", "Management Consultant", "Bachelor's Degree or Advanced Diploma (NQF Level 7)", "business consultant"),
    ("Commerce", "243103", "Marketing Practitioner", "Diploma or Advanced Certificate (NQF Level 6)", "marketing assistant"),
    ("Commerce", "333905", "Supply Chain Practitioner", "Diploma or Advanced Certificate (NQF Level 6)", "supply chain assistant"),
    ("Humanities", "242202", "Policy Analyst", "Bachelor's Degree or Advanced Diploma (NQF Level 7)", "policy officer"),
    ("Humanities", "242303", "Human Resource Advisor", "Diploma or Advanced Certificate (NQF Level 6)", "human resources officer"),
    ("Humanities", "243201", "Communication Coordinator", "Diploma or Advanced Certificate (NQF Level 6)", "public relations officer"),
    ("Humanities", "262201", "Librarian", "Bachelor's Degree or Advanced Diploma (NQF Level 7)", "librarian"),
    ("Humanities", "264103", "Technical Writer", "Bachelor's Degree or Advanced Diploma (NQF Level 7)", "technical communicator"),
    ("Humanities", "264302", "Translator", "Diploma or Advanced Certificate (NQF Level 6)", "translator"),
    ("Natural Sciences", "211301", "Chemist", "Bachelor's Degree or Advanced Diploma (NQF Level 7)", "chemist"),
    ("Natural Sciences", "213102", "General Biologist", "Bachelor's Degree or Advanced Diploma (NQF Level 7)", "biologist"),
    ("Natural Sciences", "213202", "Agricultural Scientist", "Diploma or Advanced Certificate (NQF Level 6)", "agricultural scientist"),
    ("Natural Sciences", "213302", "Environmental Scientist", "Bachelor's Degree or Advanced Diploma (NQF Level 7)", "environmental scientist"),
    ("Natural Sciences", "213306", "Water Quality Analyst", "Diploma or Advanced Certificate (NQF Level 6)", "water quality analyst"),
    ("Natural Sciences", "311101", "Chemistry Technician", "Diploma or Advanced Certificate (NQF Level 6)", "chemistry technician"),
    ("IT", "251101", "ICT Systems Analyst", "Bachelor's Degree or Advanced Diploma (NQF Level 7)", "ICT system analyst"),
    ("IT", "251102", "Data Scientist", "Bachelor's Degree or Advanced Diploma (NQF Level 7)", "data scientist"),
    ("IT", "251201", "Software Developer", "Diploma or Advanced Certificate (NQF Level 6)", "software developer"),
    ("IT", "251302", "Web Developer", "Diploma or Advanced Certificate (NQF Level 6)", "web developer"),
    ("IT", "252201", "Systems Administrator", "Diploma or Advanced Certificate (NQF Level 6)", "ICT system administrator"),
    ("IT", "252901", "ICT Security Specialist", "Diploma or Advanced Certificate (NQF Level 6)", "ICT security administrator"),
]

# Stats SA (2024), Labour Market Dynamics in South Africa 2024, p. 64 (both sexes, 2024).
# ISCO major group -> (group label, median). Only groups whose both-sexes median is given as text.
INCOME_BY_ISCO_MAJOR = {
    "1": ("Managers", "R25 000"),
    "2": ("Professionals", "R25 000"),
    "3": ("Technicians", "R20 000"),
}


def get(path: str, **params) -> dict:
    url = f"{API}/{path}?" + urllib.parse.urlencode({**params, "language": "en"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception:  # transient network error: back off and retry
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError(url)


def find_occupation(label: str) -> dict:
    res = get("search", text=label, type="occupation", limit=20)["_embedded"]["results"]
    exact = [r for r in res if r["title"].lower() == label.lower()]
    if not exact:
        sys.exit(f"ESCO occupation '{label}' not found; check the label")
    return get("resource/occupation", uri=exact[0]["uri"])


def clean(label: str) -> str:
    # ';' separates skills in skill_map.csv, so it must not appear inside a skill name
    return " ".join(label.replace(";", ",").split())


def main():
    rows, skill_uris = [], {}
    for disc, ofo, ofo_title, min_qual, esco_label in SELECTION:
        occ = find_occupation(esco_label)
        isco = str(occ.get("code", ""))
        skills = {}
        for s in occ["_links"].get("hasEssentialSkill", []):
            skills[clean(s["title"])] = s["uri"]
        skill_uris.update(skills)
        group, median = INCOME_BY_ISCO_MAJOR.get(isco[:1], ("", ""))
        income = f"{median} per month (Stats SA 2024 median for {group}, all employees)" if median else ""
        rows.append({
            "occupation": ofo_title,
            "essential_skills": "; ".join(sorted(skills, key=str.lower)),
            "income_estimate": income,
            "source": (f"Occupation: DHET 2024 National List of Occupations in High Demand (OFO 2021-{ofo}). "
                       f"Skills: ESCO essential skills of '{occ['title']}' (ISCO {isco}). "
                       + ("Income: Stats SA, Labour Market Dynamics in South Africa 2024, p. 64." if income else "")).strip(),
            "discipline": disc,
            "ofo_code": f"2021-{ofo}",
            "minimum_qualification": min_qual,
            "esco_occupation": occ["title"],
            "esco_uri": occ["uri"],
            "isco_code": isco,
            "isco_unit_match": "Y" if isco[:4] == ofo[:4] else "N",
            "essential_skill_count": len(skills),
        })
        print(f"{ofo_title:28} -> {occ['title']:28} ISCO {isco:12} {len(skills):3} skills")
        time.sleep(0.2)

    rows.sort(key=lambda r: r["occupation"].lower())
    with open(os.path.join(ROOT, "data", "skill_map.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # Skill descriptions (used by the app to explain each recommended skill)
    descriptions = {}
    for i, (label, uri) in enumerate(sorted(skill_uris.items(), key=lambda kv: kv[0].lower())):
        s = get("resource/skill", uri=uri)
        desc = s.get("description", {}).get("en", {}).get("literal", "") or ""
        descriptions[label.lower()] = {"label": label, "description": " ".join(desc.split()), "esco_uri": uri}
        if i % 50 == 0:
            print(f"  skill descriptions: {i}/{len(skill_uris)}")
        time.sleep(0.1)
    with open(os.path.join(ROOT, "data", "skill_descriptions.json"), "w", encoding="utf-8") as f:
        json.dump(descriptions, f, ensure_ascii=False, indent=1, sort_keys=True)

    meta = {"retrieved": dt.date.today().isoformat(), "esco_api": API, "esco_version": "current release served by the API on the retrieval date",
            "occupations": len(rows), "distinct_skills": len(skill_uris)}
    with open(os.path.join(ROOT, "data", "skill_map_build.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
