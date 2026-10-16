"""Measure how well SkillPath's CV reader finds the skills a set of CVs actually contain.

    python scripts/cv_accuracy.py samples/example_study/cvs        # worked example (development check)
    python scripts/cv_accuracy.py path/to/your_cvs --out report.csv

The folder must contain the CV files and expected_skills.csv with columns
    cv_file, expected_skills            (skills separated by ';', SkillPath skill names)
written BEFORE running this script (labels must not be adjusted after seeing the output).

Reports per CV and overall (micro-averaged):
    precision = correct proposed skills / all proposed skills
    recall    = correct proposed skills / all expected skills
    F1        = harmonic mean of precision and recall
"""

import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skillpath.cv import CVSkillExtractor, extract_text  # noqa: E402
from skillpath.engine import SkillMap, default_skill_map_path, normalise  # noqa: E402


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--skill-map", default=default_skill_map_path())
    ap.add_argument("--out", help="write the per-CV report to this CSV")
    a = ap.parse_args()

    sm = SkillMap.from_csv(a.skill_map)
    labels = list(csv.DictReader(open(os.path.join(a.folder, "expected_skills.csv"), encoding="utf-8")))
    unknown = sorted({s for r in labels for s in (normalise(x) for x in r["expected_skills"].split(";")) if s}
                     - sm.vocabulary)
    if unknown:
        sys.exit(f"expected_skills.csv uses names not in the skill map: {unknown}")

    x = CVSkillExtractor.from_files(sm)
    rows, TP, FP, FN = [], 0, 0, 0
    for r in labels:
        path = os.path.join(a.folder, r["cv_file"])
        expected = {normalise(s) for s in r["expected_skills"].split(";") if s.strip()}
        found = {d.skill for d in x.extract(extract_text(open(path, "rb").read(), path))}
        tp, fp, fn = len(found & expected), len(found - expected), len(expected - found)
        TP, FP, FN = TP + tp, FP + fp, FN + fn
        p, rc, f1 = prf(tp, fp, fn)
        rows.append({"cv_file": r["cv_file"], "expected": len(expected), "proposed": len(found), "correct": tp,
                     "precision": round(p, 3), "recall": round(rc, 3), "f1": round(f1, 3),
                     "missed": "; ".join(sorted(expected - found)), "extra": "; ".join(sorted(found - expected))})
    p, rc, f1 = prf(TP, FP, FN)

    w = max(len(r["cv_file"]) for r in rows)
    print(f"{'CV':{w}}  exp prop ok  prec  rec   F1")
    for r in rows:
        print(f"{r['cv_file']:{w}}  {r['expected']:3} {r['proposed']:4} {r['correct']:2}  "
              f"{r['precision']:.2f}  {r['recall']:.2f}  {r['f1']:.2f}")
        if r["missed"]:
            print(f"{'':{w}}    missed: {r['missed']}")
        if r["extra"]:
            print(f"{'':{w}}    extra:  {r['extra']}")
    print(f"\nOVERALL ({len(rows)} CVs): precision {p:.2f}, recall {rc:.2f}, F1 {f1:.2f} "
          f"(correct {TP}, wrong {FP}, missed {FN})")
    if a.out:
        with open(a.out, "w", newline="", encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=list(rows[0]))
            wr.writeheader()
            wr.writerows(rows)
            wr.writerow({"cv_file": "OVERALL", "correct": TP, "precision": round(p, 3), "recall": round(rc, 3),
                         "f1": round(f1, 3)})


if __name__ == "__main__":
    main()
