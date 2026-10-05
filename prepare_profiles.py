"""
SkillPath Phase 3 - check and complete the synthetic profile specification sheet
REIT8419 Part 3

Run this BEFORE testing. It never runs SkillPath, so acceptable recommendations
are fixed independently of the system's outputs.

USAGE
    python prepare_profiles.py profiles.csv skill_map.csv
        -> checks only, prints a report
    python prepare_profiles.py profiles.csv skill_map.csv --fill-acceptable
        -> also fills EMPTY acceptable_recommendations for core profiles using the rule
           "essential skills of the target occupation minus skills the profile already has",
           and writes profiles_ready.csv
    add --cv-dir CVs/   to check that every cv_file exists

Exit code 0 = ready to test, 1 = problems found.
"""

import argparse
import itertools
import os
import sys

import pandas as pd

REQUIRED = ["profile_id", "competency_level", "discipline", "employment_goal", "qualification", "current_skills",
            "target_occupation", "designed_to_test", "acceptable_recommendations", "is_edge_case", "cv_file"]
LEVELS = ["limited", "foundational", "moderate"]
GOALS = ["in-field", "pivot"]


def split(s):
    return [x.strip().lower() for x in str(s).split(";") if x.strip() and str(s).lower() != "nan"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("profiles")
    ap.add_argument("skill_map")
    ap.add_argument("--fill-acceptable", action="store_true")
    ap.add_argument("--cv-dir")
    a = ap.parse_args()

    p = pd.read_csv(a.profiles, dtype=str).fillna("")
    sm = pd.read_csv(a.skill_map, dtype=str).fillna("")
    problems, notes = [], []

    missing = [c for c in REQUIRED if c not in p.columns]
    if missing:
        sys.exit(f"profiles.csv is missing columns: {missing}")
    for c in ["occupation", "essential_skills", "source"]:
        if c not in sm.columns:
            problems.append(f"skill_map.csv is missing column '{c}'")
    if "[[" in sm.to_string():
        problems.append("skill_map.csv still contains [[placeholders]]")
    no_source = sm[sm.get("source", pd.Series([""] * len(sm))).str.strip() == ""]
    if len(no_source):
        problems.append(f"{len(no_source)} skill_map rows have no source citation")

    occ = {r.occupation.strip(): set(split(r.essential_skills)) for r in sm.itertuples()}
    vocab = set().union(*occ.values()) if occ else set()
    notes.append(f"skill_map: {len(occ)} occupations, {len(vocab)} distinct skills")

    if p.profile_id.duplicated().any():
        problems.append(f"Duplicate profile_id: {sorted(p[p.profile_id.duplicated()].profile_id)}")

    p["is_edge_case"] = p.is_edge_case.str.strip().str.upper()
    core = p[p.is_edge_case == "N"]
    edge = p[p.is_edge_case == "Y"]
    notes.append(f"profiles: {len(core)} core, {len(edge)} edge cases")

    # design matrix coverage
    discs = sorted(set(core.discipline))
    cells = set(zip(core.competency_level.str.lower(), core.discipline, core.employment_goal.str.lower()))
    for cell in itertools.product(LEVELS, discs, GOALS):
        if cell not in cells:
            problems.append(f"Design matrix cell not covered: {cell}")

    filled = 0
    for i, r in p.iterrows():
        pid = r.profile_id
        if "[[" in "".join(str(v) for v in r.values):
            problems.append(f"{pid}: still contains [[placeholders]]")
        skills = split(r.current_skills)
        if r.is_edge_case == "Y":
            continue
        if not skills:
            problems.append(f"{pid}: core profile has no current skills")
        unknown = [s for s in skills if s not in vocab]
        if unknown:
            problems.append(f"{pid}: skills not in SkillPath vocabulary: {unknown}")
        tgt = r.target_occupation.strip()
        if tgt not in occ:
            problems.append(f"{pid}: target_occupation '{tgt}' not in skill_map")
            continue
        acc = split(r.acceptable_recommendations)
        if not acc and a.fill_acceptable:
            rule = sorted(occ[tgt] - set(skills))
            p.at[i, "acceptable_recommendations"] = "; ".join(rule)
            acc = rule
            filled += 1
        if not acc:
            problems.append(f"{pid}: acceptable_recommendations is empty (use --fill-acceptable or fill by hand)")
        if set(acc) & set(skills):
            problems.append(f"{pid}: acceptable set includes skills the profile already has: {sorted(set(acc) & set(skills))}")
        bad = [s for s in acc if s not in vocab]
        if bad:
            problems.append(f"{pid}: acceptable skills not in vocabulary: {bad}")
        if not r.designed_to_test.strip():
            problems.append(f"{pid}: designed_to_test is empty")
        if a.cv_dir and not os.path.exists(os.path.join(a.cv_dir, r.cv_file)):
            problems.append(f"{pid}: CV file not found: {r.cv_file}")

    for _, r in edge.iterrows():
        if not r.designed_to_test.strip():
            problems.append(f"{r.profile_id}: edge case has no designed_to_test description")

    if a.fill_acceptable:
        p.to_csv("profiles_ready.csv", index=False)
        notes.append(f"Filled acceptable sets for {filled} profiles -> profiles_ready.csv "
                     "(review them, then record the date they were fixed)")

    print("\n".join(notes))
    if problems:
        print(f"\n{len(problems)} problem(s):")
        print("\n".join(" - " + x for x in problems))
        sys.exit(1)
    print("\nREADY: specification sheet passes all checks.")


if __name__ == "__main__":
    main()
