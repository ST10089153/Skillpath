"""Write profiles/skill_reference.xlsx: a lookup of occupations and exact skill names for building
synthetic profiles. Derived only from data/skill_map.csv; never runs the engine (oracle isolation).

    python scripts/make_skill_reference.py
"""
import collections
import os

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sm = pd.read_csv(os.path.join(ROOT, "data", "skill_map.csv")).fillna("")
occ = {r.occupation: [s.strip().lower() for s in r.essential_skills.split(";") if s.strip()] for r in sm.itertuples()}
needed_by = collections.defaultdict(list)
for o, skills in occ.items():
    for s in skills:
        needed_by[s].append(o)

out = os.path.join(ROOT, "profiles", "skill_reference.xlsx")
with pd.ExcelWriter(out) as xw:
    pd.DataFrame({"How to use": [
        "Copy skill names EXACTLY (lower case is fine) into current_skills, separated by '; '.",
        "target_occupation must be one of the occupation names on the 'Occupations' sheet, spelt exactly.",
        "Shared skills (needed by 2+ occupations) are what create adjacency between occupations.",
        "Do NOT test your profiles in the app or engine before fixing acceptable_recommendations (oracle isolation).",
        "Source: data/skill_map.csv (DHET 2024 OIHD + ESCO essential skills + Stats SA 2024).",
    ]}).to_excel(xw, sheet_name="READ ME", index=False)
    pd.DataFrame([{"discipline": r.discipline, "occupation": r.occupation, "ofo_code": r.ofo_code,
                   "minimum_qualification": r.minimum_qualification, "skill_count": len(occ[r.occupation]),
                   "income_estimate": r.income_estimate}
                  for r in sm.sort_values(["discipline", "occupation"]).itertuples()]
                 ).to_excel(xw, sheet_name="Occupations", index=False)
    for disc in sorted(sm.discipline.unique()):
        rows = []
        for o in sorted(sm[sm.discipline == disc].occupation):
            for s in sorted(occ[o]):
                others = [x for x in needed_by[s] if x != o]
                rows.append({"occupation": o, "skill": s, "shared_with": "; ".join(sorted(others))})
        pd.DataFrame(rows).to_excel(xw, sheet_name=disc[:31], index=False)
    pd.DataFrame([{"skill": s, "occupations_needing_it": len(v), "occupations": "; ".join(sorted(v))}
                  for s, v in sorted(needed_by.items(), key=lambda kv: (-len(kv[1]), kv[0]))]
                 ).to_excel(xw, sheet_name="All skills", index=False)
    for ws in xw.book.worksheets:
        for c in ws[1]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor="1F5FAD")
        for i, col in enumerate(ws.columns, 1):
            width = max(len(str(c.value or "")) for c in col)
            ws.column_dimensions[get_column_letter(i)].width = min(max(12, width + 2), 90)
        ws.freeze_panes = "A2"
        for row in ws.iter_rows(min_row=2):
            for c in row:
                c.alignment = Alignment(vertical="top", wrap_text=True)
print("wrote", out)
