"""Write profiles/skill_reference.xlsx: a lookup of occupations and exact skill names for building
synthetic profiles. Derived only from data/skill_map.csv and data/skill_descriptions.json; never runs
the engine (oracle isolation).

    python scripts/make_skill_reference.py
"""
import json
import os

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sm = pd.read_csv(os.path.join(ROOT, "data", "skill_map.csv")).fillna("")
desc = json.load(open(os.path.join(ROOT, "data", "skill_descriptions.json"), encoding="utf-8"))
occ = {r.occupation: [s.strip() for s in r.essential_skills.split(";") if s.strip()] for r in sm.itertuples()}
label = {k: v["label"] for k, v in desc.items()}

out = os.path.join(ROOT, "profiles", "skill_reference.xlsx")
with pd.ExcelWriter(out) as xw:
    pd.DataFrame({"How to use": [
        "Copy skill names EXACTLY as in the 'skill' column into current_skills, separated by '; '.",
        "target_occupation must be one of the occupation names on the 'Occupations' sheet, spelt exactly.",
        "Skills needed by several occupations create adjacency: they are the bridges between occupations.",
        "Do NOT test your profiles in the app or engine before fixing acceptable_recommendations (oracle isolation).",
        "Sources: DHET 2024 OIHD (occupations), ESCO (skill-occupation evidence), WEF Future of Jobs 2025 (demand), "
        "Stats SA 2024 (income). Build: scripts/build_skill_map.py.",
    ]}).to_excel(xw, sheet_name="READ ME", index=False)
    pd.DataFrame([{"category": d["category"], "skill": d["label"], "what_it_means": d["description"],
                   "how_to_show_it": d["how_to_show"], "demand_evidence": d["demand_evidence"],
                   "occupations_needing_it": len(d["needed_by_occupations"]),
                   "occupations": "; ".join(d["needed_by_occupations"])}
                  for d in sorted(desc.values(), key=lambda d: (d["category"], d["label"]))]
                 ).to_excel(xw, sheet_name="Skills", index=False)
    pd.DataFrame([{"discipline": r.discipline, "occupation": r.occupation, "ofo_code": r.ofo_code,
                   "minimum_qualification": r.minimum_qualification, "skill_count": len(occ[r.occupation]),
                   "skills": "; ".join(label.get(s.lower(), s) for s in occ[r.occupation]),
                   "income_estimate": r.income_estimate}
                  for r in sm.sort_values(["discipline", "occupation"]).itertuples()]
                 ).to_excel(xw, sheet_name="Occupations", index=False)
    for ws in xw.book.worksheets:
        for c in ws[1]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor="1F5FAD")
        for i, col in enumerate(ws.columns, 1):
            width = max(len(str(c.value or "")) for c in col)
            ws.column_dimensions[get_column_letter(i)].width = min(max(12, width + 2), 70)
        ws.freeze_panes = "A2"
        for row in ws.iter_rows(min_row=2):
            for c in row:
                c.alignment = Alignment(vertical="top", wrap_text=True)
print("wrote", out)
