"""
SkillPath Phase 3 - controlled synthetic testing harness
REIT8419 Part 3 (approved procedure: Annexure Q and Ethics Waiver, 2026)

WHAT THIS DOES
    Feeds each researcher-built synthetic graduate profile into SkillPath in a
    controlled sequence, under BOTH the income-visible (A) and income-neutral (B)
    versions of the recommendation logic, and records what the system returns.
    No real person is involved. No external dataset is used.

    For every profile and version it runs five fixed test scripts:
      baseline   - first recommendation and pathway for the profile
      steady     - the profile passes every module (tests milestone staging)
      struggle   - the profile fails twice, then passes (tests adaptive revision)
      gap        - the profile is inactive for several days (tests nudge rule)
      repeat     - baseline run again (tests consistency / determinism)

INPUTS
    profiles.csv     your profile specification sheet (templates/profile_specifications_TEMPLATE.csv)
    skill_map.csv    SkillPath's own occupation-skill reference table
                     (templates/skill_map_TEMPLATE.csv)

USAGE
    python run_synthetic_tests.py profiles.csv skill_map.csv --app-version 0.9.2

OUTPUT
    test_output_log.csv   one row per recorded system response (raw data for the supervisor)

CONNECTING YOUR REAL APP  (important)
    --engine reference  uses the ReferenceEngine stand-in below (for trial runs only).
    --engine skillpath  imports SkillPathEngine from skillpath_adapter.py, which the
                        SkillPath codebase must provide (see CLAUDE_CODE_PROMPT.md).
    The study's data must come from --engine skillpath.

    ADAPTER CONTRACT (skillpath_adapter.SkillPathEngine)
        __init__(skill_map: pandas.DataFrame)
        recommend(profile: dict, version: "A" | "B") -> dict with keys
            recommended_skill (str, "" if none), alternatives (list[str]),
            explanation (str), income_displayed (str, "" if none),
            pathway (list[tuple[module_id: str, difficulty: int]])
        progress(state: dict, passed: bool) -> dict with keys
            milestone (str, "" if none), revised (bool), next_difficulty (int)
            state starts as {"passes": 0, "fails": 0, "difficulty": <first module difficulty>}
            and may be mutated / extended by the adapter
        should_nudge(days_inactive: int) -> bool

ORACLE ISOLATION
    The engine only ever receives the fields in ENGINE_FIELDS. The target occupation,
    acceptable recommendations and test notes are never passed to SkillPath, so its
    outputs cannot be influenced by the expected answers.

    Manual testing through the app is also possible: fill test_output_log.csv by
    hand using templates/test_output_log_TEMPLATE.csv; the analysis script reads either.
"""

import argparse
import csv
from datetime import datetime

import pandas as pd

LOGIC_VERSIONS = {"A": "income-visible", "B": "income-neutral"}
ENGINE_FIELDS = ["profile_id", "competency_level", "qualification", "discipline", "current_skills"]
STEADY_MODULES = 6
GAP_DAYS = 4


def split(s):
    return [x.strip() for x in str(s).split(";") if x.strip() and str(s).lower() != "nan"]


class ReferenceEngine:
    """Stand-in for SkillPath. Replace the method bodies with calls to your app."""

    MODULES_PER_MILESTONE = 3   # design setting (DD5)
    FAILS_BEFORE_REVISION = 2   # design setting (DD3)
    INACTIVE_DAYS_NUDGE = 2     # design setting (DD7)

    def __init__(self, skill_map):
        self.occ = {r.occupation: set(s.lower() for s in split(r.essential_skills)) for r in skill_map.itertuples()}
        self.income = {r.occupation: r.income_estimate for r in skill_map.itertuples()
                       if "income_estimate" in skill_map.columns and pd.notna(r.income_estimate)}

    @staticmethod
    def _jac(a, b):
        return len(a & b) / len(a | b) if a | b else 0.0

    def recommend(self, profile, version):
        """Return dict: recommended_skill, alternatives (list), explanation, income_displayed (str or ''),
        pathway (list of (module_id, difficulty))."""
        current = set(s.lower() for s in split(profile["current_skills"]))
        if not current:
            return {"recommended_skill": "", "alternatives": [], "income_displayed": "", "pathway": [],
                    "explanation": "Profile has no recorded skills; user asked to complete the skills profile first."}
        near = sorted(self.occ.items(), key=lambda kv: self._jac(current, kv[1]), reverse=True)[:3]
        before = sum(self._jac(current, s) for _, s in near) / len(near)
        scored = []
        for skill in set().union(*[s for _, s in near]) - current:
            after = sum(self._jac(current | {skill}, s) for _, s in near) / len(near)
            scored.append((after - before, skill))
        scored.sort(reverse=True)
        if not scored:
            return {"recommended_skill": "", "alternatives": [], "income_displayed": "", "pathway": [],
                    "explanation": "Profile already covers all skills of the nearest occupations."}
        top = scored[0][1]
        level = {"limited": 0, "foundational": 1, "moderate": 2}.get(str(profile.get("competency_level", "")).lower(), 1)
        pathway = [(f"{top[:20]}_m{i + 1}", level + 1 + i // 2) for i in range(STEADY_MODULES)]
        income = ""
        if version == "A":
            occ_name = near[0][0]
            if occ_name in self.income:
                income = f"Estimated {self.income[occ_name]} (literature-derived estimate, not financial advice)"
        return {"recommended_skill": top, "alternatives": [s for _, s in scored[1:4]], "income_displayed": income,
                "pathway": pathway,
                "explanation": f"'{top}' is the smallest step that brings you closer to: " + ", ".join(o for o, _ in near)}

    def progress(self, state, passed):
        """Advance one module. Return dict: milestone (str or ''), revised (bool), next_difficulty (int)."""
        out = {"milestone": "", "revised": False}
        if passed:
            state["passes"] += 1
            state["fails"] = 0
            if state["passes"] % self.MODULES_PER_MILESTONE == 0:
                out["milestone"] = f"MS{state['passes'] // self.MODULES_PER_MILESTONE}"
            state["difficulty"] += 1 if state["passes"] % 2 == 0 else 0
        else:
            state["fails"] += 1
            if state["fails"] >= self.FAILS_BEFORE_REVISION:
                state["difficulty"] = max(0, state["difficulty"] - 1)
                state["fails"] = 0
                out["revised"] = True
        out["next_difficulty"] = state["difficulty"]
        return out

    def should_nudge(self, days_inactive):
        return days_inactive >= self.INACTIVE_DAYS_NUDGE


FIELDS = ["run_id", "timestamp", "app_version", "logic_version", "profile_id", "scenario", "step", "input_action",
          "recommended_skill", "alternatives", "explanation_present", "explanation_text", "income_displayed",
          "pathway_modules", "module_difficulties", "roadmap_revised", "milestone_awarded",
          "notification_triggered", "error", "notes"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("profiles")
    ap.add_argument("skill_map")
    ap.add_argument("--app-version", required=True, help="SkillPath build/commit being tested")
    ap.add_argument("--out", default="test_output_log.csv")
    ap.add_argument("--engine", choices=["reference", "skillpath"], default="skillpath")
    a = ap.parse_args()

    profiles = pd.read_csv(a.profiles).fillna("")
    skill_map = pd.read_csv(a.skill_map)
    if a.engine == "skillpath":
        from skillpath_adapter import SkillPathEngine
        engine = SkillPathEngine(skill_map)
    else:
        print("WARNING: using the ReferenceEngine stand-in. Do not report these results as SkillPath's.")
        engine = ReferenceEngine(skill_map)
    run_id = datetime.now().strftime("RUN%Y%m%d%H%M%S")
    rows = []

    def rec(version, pid, scenario, step, action, **kw):
        r = {k: "" for k in FIELDS}
        r.update(run_id=run_id, timestamp=datetime.now().isoformat(timespec="seconds"), app_version=a.app_version,
                 logic_version=version, profile_id=pid, scenario=scenario, step=step, input_action=action)
        r.update(kw)
        rows.append(r)

    def rec_recommendation(version, pid, scenario, res):
        rec(version, pid, scenario, 0, "submit profile",
            recommended_skill=res["recommended_skill"], alternatives=";".join(res["alternatives"]),
            explanation_present="Y" if res["explanation"] else "N", explanation_text=res["explanation"],
            income_displayed=res["income_displayed"],
            pathway_modules=";".join(m for m, _ in res["pathway"]),
            module_difficulties=";".join(str(d) for _, d in res["pathway"]))

    for _, p in profiles.iterrows():
        pid = p["profile_id"]
        engine_input = {k: p[k] for k in ENGINE_FIELDS if k in p}
        for v in LOGIC_VERSIONS:
            try:
                res = engine.recommend(dict(engine_input), v)
                rec_recommendation(v, pid, "baseline", res)
                rec_recommendation(v, pid, "repeat", engine.recommend(dict(engine_input), v))
                if not res["pathway"]:
                    continue
                start = res["pathway"][0][1]
                st = {"passes": 0, "fails": 0, "difficulty": start}
                for i in range(STEADY_MODULES):
                    o = engine.progress(st, True)
                    rec(v, pid, "steady", i + 1, "pass module", milestone_awarded=o["milestone"],
                        roadmap_revised="Y" if o["revised"] else "N", module_difficulties=str(o["next_difficulty"]))
                st = {"passes": 0, "fails": 0, "difficulty": start}
                for i, passed in enumerate([False, False, True]):
                    o = engine.progress(st, passed)
                    rec(v, pid, "struggle", i + 1, "pass module" if passed else "fail module",
                        milestone_awarded=o["milestone"], roadmap_revised="Y" if o["revised"] else "N",
                        module_difficulties=str(o["next_difficulty"]), notes=f"start difficulty {start}")
                for d in range(1, GAP_DAYS + 1):
                    rec(v, pid, "gap", d, f"inactive day {d}",
                        notification_triggered="Y" if engine.should_nudge(d) else "N")
            except Exception as e:  # robustness: record the failure instead of stopping
                rec(v, pid, "error", 0, "submit profile", error=f"{type(e).__name__}: {e}")

    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"Engine: {a.engine}")
    print(f"{run_id}: {len(profiles)} profiles x {len(LOGIC_VERSIONS)} versions -> {len(rows)} logged responses in {a.out}")


if __name__ == "__main__":
    main()
