"""Build SkillPath's skill map from published sources (condensed, measurable, high-demand skills).

    python scripts/fetch_esco_occupations.py   # 1. online: cache ESCO skills of the 24 occupations
    python scripts/build_skill_map.py          # 2. offline: build data/skill_map.csv and companions

SOURCES
  Occupations  DHET (2024) National List of Occupations in High Demand: 2024. Government Gazette
               No. 50510, Notice 2414 of 2024, 16 April 2024 (Table 2).
  Skills       data/skill_taxonomy.csv: a condensed list of concrete, measurable skills grouped in
               categories. Each skill lists the ESCO skill labels (European Commission ESCO API) that
               evidence it. An occupation REQUIRES a SkillPath skill when any of those ESCO labels is an
               essential or optional skill of the occupation in ESCO (data/esco_occupation_skills.json).
  Demand       (a) needed by DHET high-demand occupations (count in the evidence file), and
               (b) the skill's World Economic Forum cluster: Future of Jobs Report 2025, Figure 3.4
               "Skills on the rise, 2025-2030" (global rank, p. 37) and the South Africa economy
               profile (p. 196), in data/wef_skills_2025.csv.
  Income       Statistics South Africa (2024) Labour Market Dynamics in South Africa, 2024,
               Report 02-11-02, p. 64: median monthly earnings by occupation group, matched by the
               ISCO major group of the ESCO occupation.

OCCUPATION SELECTION RULE (DECISIONS.md #32)
  OIHD 2024 occupations in OFO major groups 2-3 with minimum qualification NQF 6-7, six per
  discipline of the profile template, matched to the ESCO occupation sharing the 4-digit ISCO unit
  group (else flagged isco_unit_match = N).

OUTPUTS (deterministic for the same inputs)
  data/skill_map.csv                 occupation, essential_skills, income_estimate, source, + audit columns
  data/skill_descriptions.json       per skill: category, definition, how_to_show, WEF evidence, ESCO aliases,
                                     CV keywords (common tool names, curated for CV matching only)
  data/skill_occupation_evidence.csv which ESCO label links each skill to each occupation (E/O)
  data/skill_map_build.json          build metadata and coverage
"""

from __future__ import annotations

import csv
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
INCOME_BY_ISCO_MAJOR = {"1": ("Managers", "R25 000"), "2": ("Professionals", "R25 000"), "3": ("Technicians", "R20 000")}

WEF_SOURCE = "World Economic Forum (2025) Future of Jobs Report 2025, Fig. 3.4 p. 37; South Africa profile p. 196"


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


def split(s: str) -> list[str]:
    return [x.strip() for x in s.split(";") if x.strip()]


def main():
    cache = json.load(open(os.path.join(ROOT, "data", "esco_occupation_skills.json"), encoding="utf-8"))
    occs = cache["occupations"]
    taxonomy = list(csv.DictReader(open(os.path.join(ROOT, "data", "skill_taxonomy.csv"), encoding="utf-8")))
    wef = {r["wef_skill"]: r for r in csv.DictReader(open(os.path.join(ROOT, "data", "wef_skills_2025.csv"), encoding="utf-8"))}

    all_labels = {l for o in occs.values() for l in o["essential"] + o["optional"]}
    problems = []
    for t in taxonomy:
        if ";" in t["skill"]:
            problems.append(f"skill name contains ';': {t['skill']}")
        if t["wef_skill"] not in wef:
            problems.append(f"{t['skill']}: unknown WEF skill '{t['wef_skill']}'")
        for lab in split(t["esco_labels"]):
            if lab not in all_labels:
                problems.append(f"{t['skill']}: ESCO label not used by any selected occupation: '{lab}'")
    if problems:
        print("\n".join(problems))
        sys.exit("Fix data/skill_taxonomy.csv")

    evidence, occ_skills = [], {name: set() for name in occs}
    for t in taxonomy:
        labels = set(split(t["esco_labels"]))
        for name, o in occs.items():
            ess = sorted(labels & set(o["essential"]))
            opt = sorted(labels & set(o["optional"]))
            if ess or opt:
                occ_skills[name].add(t["skill"])
                evidence.append({"skill": t["skill"], "occupation": name,
                                 "esco_essential_labels": "; ".join(ess), "esco_optional_labels": "; ".join(opt)})

    rows = []
    for name, o in sorted(occs.items(), key=lambda kv: kv[0].lower()):
        isco = o["isco_code"]
        group, median = INCOME_BY_ISCO_MAJOR.get(isco[:1], ("", ""))
        income = f"{median} per month (Stats SA 2024 median for {group}, all employees)" if median else ""
        rows.append({
            "occupation": name,
            "essential_skills": "; ".join(sorted(occ_skills[name], key=str.lower)),
            "income_estimate": income,
            "source": (f"Occupation: DHET 2024 National List of Occupations in High Demand (OFO {o['ofo_code']}). "
                       f"Skills: SkillPath skills evidenced by ESCO essential/optional skills of '{o['esco_occupation']}' "
                       f"(ISCO {isco}); demand: WEF Future of Jobs 2025. "
                       + ("Income: Stats SA, Labour Market Dynamics in South Africa 2024, p. 64." if income else "")).strip(),
            "discipline": o["discipline"], "ofo_code": o["ofo_code"], "minimum_qualification": o["minimum_qualification"],
            "esco_occupation": o["esco_occupation"], "esco_uri": o["esco_uri"], "isco_code": isco,
            "isco_unit_match": "Y" if isco[:4] == o["ofo_code"][5:9] else "N",
            "skill_count": len(occ_skills[name]),
        })

    with open(os.path.join(ROOT, "data", "skill_map.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(ROOT, "data", "skill_occupation_evidence.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(evidence[0]))
        w.writeheader()
        w.writerows(sorted(evidence, key=lambda e: (e["skill"].lower(), e["occupation"].lower())))

    needed_by = {t["skill"]: sorted(n for n, s in occ_skills.items() if t["skill"] in s) for t in taxonomy}
    descriptions = {}
    for t in taxonomy:
        wr = wef[t["wef_skill"]]
        za = []
        if wr["za_core_skill_2025_pct"]:
            za.append(f"{wr['za_core_skill_2025_pct']}% of South African employers rate it a core skill in 2025")
        if wr["za_increasing_use_2030_pct"]:
            za.append(f"{wr['za_increasing_use_2030_pct']}% expect its use to increase by 2030")
        demand = (f"WEF skill '{t['wef_skill']}': ranked {wr['global_rank_skills_on_the_rise']} of 26 skills on the "
                  f"rise globally, 2025-2030" + (f"; {'; '.join(za)}" if za else "") + ".")
        descriptions[" ".join(t["skill"].lower().split())] = {
            "label": t["skill"], "category": t["category"], "description": t["definition"],
            "how_to_show": t["how_to_show"], "wef_skill": t["wef_skill"],
            "wef_global_rank": int(wr["global_rank_skills_on_the_rise"]), "demand_evidence": demand,
            "demand_source": WEF_SOURCE, "needed_by_occupations": needed_by[t["skill"]],
            "esco_aliases": split(t["esco_labels"]), "keywords": split(t.get("keywords", "")), "esco_uri": "",
        }
    with open(os.path.join(ROOT, "data", "skill_descriptions.json"), "w", encoding="utf-8") as f:
        json.dump(descriptions, f, ensure_ascii=False, indent=1, sort_keys=True)

    unused = [s for s, v in needed_by.items() if not v]
    meta = {"esco_retrieved": cache["retrieved"], "occupations": len(rows), "skills": len(taxonomy),
            "skills_used_by_no_occupation": unused,
            "skills_per_occupation": {r["occupation"]: r["skill_count"] for r in rows},
            "shared_skills": sum(1 for v in needed_by.values() if len(v) > 1)}
    with open(os.path.join(ROOT, "data", "skill_map_build.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
