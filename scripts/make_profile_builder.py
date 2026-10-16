"""Create profiles/profile_builder.xlsx: a workbook the RESEARCHER fills in to build the synthetic profiles,
and profiles/cv_template/CV_TEMPLATE.docx for writing the fabricated study CVs.

    python scripts/make_profile_builder.py

The workbook only provides structure from the researcher's template (profile IDs, design-matrix cells,
edge-case purposes, CV file names) and drop-down lists of SkillPath's occupation and skill names. It contains
no profile content: qualification, target occupation and skills are chosen by the researcher.
Convert it with scripts/profiles_from_builder.py.
"""

import csv
import json
import os
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_demo_cvs import write_docx  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_SKILLS = 12
SKILLS_FOR_LEVEL = {"limited": 2, "foundational": 4, "moderate": 6}
EDGE_GUIDE = {
    "SP25": "Leave all skill cells EMPTY (tests the empty-profile message).",
    "SP26": "Choose 8-12 skills from DIFFERENT categories that do not belong together (tests ranking stability).",
    "SP27": "Type 2-3 skills that are NOT in SkillPath (e.g. welding) in the skill cells; ignore the drop-down warning.",
    "SP28": "Type ALL SKILLS in skill_1: the profile then holds every SkillPath skill, so nothing is left to add.",
}

HEAD = PatternFill("solid", fgColor="1F5FAD")
YOU = PatternFill("solid", fgColor="FFF6E0")


def main():
    sm = list(csv.DictReader(open(os.path.join(ROOT, "data", "skill_map.csv"), encoding="utf-8")))
    desc = json.load(open(os.path.join(ROOT, "data", "skill_descriptions.json"), encoding="utf-8"))
    labels = sorted((d["label"] for d in desc.values()), key=str.lower)
    occupations = sorted((r["occupation"] for r in sm), key=str.lower)
    template = list(csv.DictReader(open(os.path.join(ROOT, "templates", "profile_specifications_TEMPLATE.csv"),
                                        encoding="utf-8")))

    wb = Workbook()
    guide = wb.active
    guide.title = "Guide"
    steps = [
        "PROFILE BUILDER - the researcher completes the yellow cells. Nothing here is study data until you fill it in.",
        "",
        "1. For each core profile (SP01-SP24) fill: qualification, target_occupation (drop-down) and the skills (drop-downs).",
        "2. Number of skills: limited = 2, foundational = 4, moderate = 6 (shown in column 'skills_to_choose').",
        "3. in-field = target occupation in the SAME discipline (see 'Occupations' sheet); pivot = a DIFFERENT discipline.",
        "4. Pick skills a graduate of that qualification and level would realistically have. For pivots, include at least",
        "   one skill the target occupation also needs, so a realistic route exists.",
        "5. Do not choose a skill the target occupation needs if it is the obvious 'next' skill you expect - leave the",
        "   acceptable set to prepare_profiles.py (target skills minus current skills).",
        "6. Edge cases SP25-SP28: follow the instruction in 'edge_case_instruction'.",
        "7. Write each CV (cv_file) from profiles/cv_template/CV_TEMPLATE.docx so it shows EXACTLY the skills on its row.",
        "8. Do NOT try profiles in the app or engine before acceptable sets are fixed (oracle isolation).",
        "9. Save, then run:  .venv\\Scripts\\python scripts\\profiles_from_builder.py",
        "",
        "Saturated edge case (SP28): SkillPath compares a profile with its up-to-3 nearest occupations. It is",
        "'saturated' only if it already holds every skill of ALL of those occupations. Because most skills are shared",
        "between occupations, type ALL SKILLS in skill_1 (the converter expands it to every SkillPath skill).",
    ]
    for i, s in enumerate(steps, 1):
        guide.cell(i, 1, s)
    guide.column_dimensions["A"].width = 120
    guide["A1"].font = Font(bold=True, size=13)

    lists = wb.create_sheet("Lists")
    for i, o in enumerate(occupations, 1):
        lists.cell(i, 1, o)
    for i, s in enumerate(labels, 1):
        lists.cell(i, 2, s)
    lists.sheet_state = "hidden"

    ws = wb.create_sheet("Profiles", 0)
    cols = (["profile_id", "competency_level", "discipline", "employment_goal", "is_edge_case", "cv_file",
             "designed_to_test", "skills_to_choose", "edge_case_instruction", "qualification", "target_occupation"]
            + [f"skill_{i}" for i in range(1, MAX_SKILLS + 1)] + ["researcher_notes"])
    ws.append(cols)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = HEAD
        c.alignment = Alignment(wrap_text=True, vertical="top")
    for t in template:
        pid = t["profile_id"]
        edge = t["is_edge_case"].strip().upper() == "Y"
        level = t["competency_level"].strip().lower()
        ws.append([pid, level, t["discipline"], t["employment_goal"], "Y" if edge else "N", t["cv_file"],
                   t["designed_to_test"], "" if edge else SKILLS_FOR_LEVEL.get(level, ""),
                   EDGE_GUIDE.get(pid, ""), "", ""] + [""] * MAX_SKILLS + [""])
    n = ws.max_row
    first_you = cols.index("qualification") + 1
    last_skill = cols.index(f"skill_{MAX_SKILLS}") + 1
    for r in range(2, n + 1):
        for c in range(first_you, last_skill + 1):
            ws.cell(r, c).fill = YOU
        for c in range(1, len(cols) + 1):
            ws.cell(r, c).alignment = Alignment(wrap_text=True, vertical="top")

    occ_dv = DataValidation(type="list", formula1=f"=Lists!$A$1:$A${len(occupations)}", allow_blank=True,
                            showErrorMessage=True, errorTitle="Not a SkillPath occupation",
                            error="Choose an occupation from the list.")
    skill_dv = DataValidation(type="list", formula1=f"=Lists!$B$1:$B${len(labels)}", allow_blank=True,
                              showErrorMessage=True, errorStyle="warning", errorTitle="Not a SkillPath skill",
                              error="This is not in SkillPath's skill list. OK only for edge case SP27.")
    ws.add_data_validation(occ_dv)
    ws.add_data_validation(skill_dv)
    tcol = get_column_letter(cols.index("target_occupation") + 1)
    occ_dv.add(f"{tcol}2:{tcol}{n}")
    skill_dv.add(f"{get_column_letter(cols.index('skill_1') + 1)}2:{get_column_letter(last_skill)}{n}")

    widths = {"profile_id": 9, "competency_level": 13, "discipline": 15, "employment_goal": 11, "is_edge_case": 8,
              "cv_file": 13, "designed_to_test": 40, "skills_to_choose": 9, "edge_case_instruction": 40,
              "qualification": 26, "target_occupation": 26, "researcher_notes": 30}
    for i, c in enumerate(cols, 1):
        ws.column_dimensions[get_column_letter(i)].width = widths.get(c, 30)
    ws.freeze_panes = "B2"

    occ_ws = wb.create_sheet("Occupations", 1)
    occ_ws.append(["discipline", "occupation", "minimum_qualification", "skills (SkillPath names)"])
    for c in occ_ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = HEAD
    for r in sorted(sm, key=lambda r: (r["discipline"], r["occupation"])):
        skills = [desc.get(s.strip().lower(), {}).get("label", s.strip()) for s in r["essential_skills"].split(";")
                  if s.strip()]
        occ_ws.append([r["discipline"], r["occupation"], r["minimum_qualification"], "; ".join(skills)])
    for col, w in zip("ABCD", (16, 26, 34, 110)):
        occ_ws.column_dimensions[col].width = w
    for row in occ_ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")

    out = os.path.join(ROOT, "profiles", "profile_builder.xlsx")
    if os.path.exists(out):
        sys.exit(f"{out} already exists; it may contain your work. Rename or delete it first to regenerate.")
    wb.save(out)
    print("wrote", out)

    tpl_dir = os.path.join(ROOT, "profiles", "cv_template")
    os.makedirs(tpl_dir, exist_ok=True)
    write_docx(os.path.join(tpl_dir, "CV_TEMPLATE.docx"), [
        "Synthetic test profile created by the researcher. Not a real person. [Profile SPxx]",
        "",
        "[FICTITIOUS FULL NAME]",
        "[Town, Province] | [fictitious email, e.g. name@example.com] | [fictitious number]",
        "",
        "PERSONAL SUMMARY",
        "[2-3 sentences: qualification, what kind of role you are looking for, one strength.]",
        "",
        "EDUCATION",
        "[Qualification (NQF level)], [Institution], [Year]",
        "[Matric / National Senior Certificate, Year - optional: relevant subjects]",
        "",
        "EXPERIENCE AND PROJECTS",
        "[Role or project], [Fictitious organisation (fictional)], [Dates]",
        "- [Action verb + task + tool, showing ONE of the profile's skills]",
        "- [Action verb + task + tool, showing another skill]",
        "[limited: 1 internship/project | foundational: part-time job + projects | moderate: 1-2 years' work]",
        "",
        "SKILLS",
        "[Only the skills on this profile's row, in everyday words - e.g. 'Excel (pivot tables), Sage Pastel']",
        "",
        "REFERENCES",
        "Available on request.",
    ])
    print("wrote", os.path.join(tpl_dir, "CV_TEMPLATE.docx"))


if __name__ == "__main__":
    main()
