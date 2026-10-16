"""Convert the researcher's profiles/profile_builder.xlsx into profiles.csv (the harness format) and
profiles/cvs/expected_skills.csv (for scripts/cv_accuracy.py).

    python scripts/profiles_from_builder.py

acceptable_recommendations is left EMPTY on purpose: prepare_profiles.py --fill-acceptable fills it from the
target occupation, before any testing. Existing outputs are backed up, not overwritten silently.
"""

import argparse
import csv
import datetime as dt
import os
import shutil
import sys

from openpyxl import load_workbook

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELDS = ["profile_id", "competency_level", "discipline", "employment_goal", "qualification", "current_skills",
          "target_occupation", "designed_to_test", "acceptable_recommendations", "is_edge_case", "cv_file"]


def backup(path):
    if os.path.exists(path):
        b = f"{path}.{dt.datetime.now():%Y%m%d-%H%M%S}.bak"
        shutil.copy2(path, b)
        print("backed up", os.path.relpath(path, ROOT), "->", os.path.basename(b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--builder", default=os.path.join(ROOT, "profiles", "profile_builder.xlsx"))
    ap.add_argument("--out", default=os.path.join(ROOT, "profiles.csv"))
    ap.add_argument("--cv-dir", default=os.path.join(ROOT, "profiles", "cvs"))
    a = ap.parse_args()
    src = a.builder
    ws = load_workbook(src, data_only=True)["Profiles"]
    head = [c.value for c in ws[1]]
    skill_cols = [i for i, h in enumerate(head) if h and str(h).startswith("skill_")]
    import json
    desc = json.load(open(os.path.join(ROOT, "data", "skill_descriptions.json"), encoding="utf-8"))
    all_skills = sorted((d["label"] for d in desc.values()), key=str.lower)
    rows, expected, warnings = [], [], []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if not r[0]:
            continue
        v = {h: ("" if x is None else str(x).strip()) for h, x in zip(head, r)}
        skills = [str(r[i]).strip() for i in skill_cols if r[i] not in (None, "")]
        if any(x.upper() == "ALL SKILLS" for x in skills):  # saturated edge case: every SkillPath skill
            skills = all_skills
        edge = v["is_edge_case"].upper() == "Y"
        if not edge:
            want = v.get("skills_to_choose", "")
            if want and str(len(skills)) != want.split(".")[0]:
                warnings.append(f"{v['profile_id']}: {len(skills)} skills chosen, guide says {want}")
            if not v["target_occupation"]:
                warnings.append(f"{v['profile_id']}: no target_occupation")
            if not v["qualification"]:
                warnings.append(f"{v['profile_id']}: no qualification")
        rows.append({"profile_id": v["profile_id"], "competency_level": v["competency_level"],
                     "discipline": v["discipline"], "employment_goal": v["employment_goal"],
                     "qualification": v["qualification"], "current_skills": "; ".join(skills),
                     "target_occupation": "" if edge else v["target_occupation"],
                     "designed_to_test": v["designed_to_test"], "acceptable_recommendations": "",
                     "is_edge_case": "Y" if edge else "N", "cv_file": v["cv_file"]})
        expected.append({"cv_file": v["cv_file"], "competency_level": v["competency_level"],
                         "expected_skills": "; ".join(skills)})

    out = a.out
    backup(out)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    cv_dir = a.cv_dir
    os.makedirs(cv_dir, exist_ok=True)
    exp = os.path.join(cv_dir, "expected_skills.csv")
    backup(exp)
    with open(exp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["cv_file", "competency_level", "expected_skills"])
        w.writeheader()
        w.writerows(e for e in expected if e["expected_skills"])  # edge cases without skills are excluded
    print(f"wrote profiles.csv ({len(rows)} profiles) and profiles/cvs/expected_skills.csv")
    if warnings:
        print("\nCheck these before continuing:\n - " + "\n - ".join(warnings))
    print("\nNext:\n  .venv\\Scripts\\python prepare_profiles.py profiles.csv data/skill_map.csv --fill-acceptable"
          "\n  put your CV files (named as cv_file) in profiles\\cvs\\ and run:"
          "\n  .venv\\Scripts\\python scripts\\cv_accuracy.py profiles\\cvs")


if __name__ == "__main__":
    main()
