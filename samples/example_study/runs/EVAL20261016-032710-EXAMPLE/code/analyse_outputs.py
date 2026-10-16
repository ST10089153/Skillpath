"""
SkillPath Phase 3 - analysis of controlled synthetic testing outputs
REIT8419 Part 3

Reads the profile specification sheet and the test output log, and evaluates
SkillPath against Hevner et al.'s (2004) DSR criteria of utility, quality and
efficacy, plus the paired income-visible (A) vs income-neutral (B) comparison.

All results describe SYSTEM OUTPUTS for researcher-built synthetic profiles.
They are not observations of real people.

USAGE
    pip install pandas matplotlib openpyxl --break-system-packages
    python analyse_outputs.py profiles.csv test_output_log.csv

OUTPUT (folder ./results)
    results.xlsx        Tables for Section 5 of Part 3
    fig_criteria.png    Criteria results against thresholds
    fig_match.png       Expected-recommendation match by competency level and discipline
    analysis_log.txt    Counts and exclusions
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

# ---------------------------------------------------------------------------
# Acceptance thresholds. Set these BEFORE testing (Weeks 11 to 13), get
# supervisor sign-off, and do not change them after seeing results.
# ---------------------------------------------------------------------------
THRESHOLDS = {
    "U1 Recommendation coverage": 1.00,          # [[confirm]]
    "U2 Expected-recommendation match": 0.70,    # [[confirm]]
    "Q1 Adaptive revision correctness": 1.00,    # [[confirm]]
    "Q2 Output consistency on repeat": 1.00,     # [[confirm]]
    "Q3 Explanation completeness": 1.00,         # [[confirm]]
    "Q4 Edge-case robustness": 0.90,             # [[confirm]]
    "Q5 Nudge rule correctness": 1.00,           # [[confirm]]
    "E1 Multi-milestone staging": 0.90,          # [[confirm]]
    "E2 Graduated difficulty (ZPD) sequencing": 0.90,  # [[confirm]]
}
CRITERION = {"U": "Utility", "Q": "Quality", "E": "Efficacy"}
NUDGE_DAY = 2          # SkillPath design rule (DD7)
MIN_DIFFICULTY = 1     # lowest difficulty level; a revision at the floor cannot lower it further
PRIMARY_VERSION = "B"  # income-neutral logic = core recommender, used for U/Q/E criteria
OUT = "results"
log = []


def say(m):
    print(m)
    log.append(m)


def split(s):
    return [x.strip().lower() for x in str(s).split(";") if x.strip() and str(s).lower() != "nan"]


def yes(s):
    return str(s).strip().upper() == "Y"


def ratio(n, d):
    return n / d if d else float("nan")


def main():
    if len(sys.argv) < 3:
        sys.exit("Usage: python analyse_outputs.py profiles.csv test_output_log.csv")
    os.makedirs(OUT, exist_ok=True)
    spec = pd.read_csv(sys.argv[1]).fillna("")
    lg = pd.read_csv(sys.argv[2]).fillna("")
    lg["profile_id"] = lg["profile_id"].astype(str)
    spec["profile_id"] = spec["profile_id"].astype(str)
    edge = set(spec.loc[spec.is_edge_case.astype(str).str.upper() == "Y", "profile_id"])
    core = set(spec.profile_id) - edge
    say(f"Profiles: {len(spec)} ({len(core)} core, {len(edge)} edge cases). Logged responses: {len(lg)}")
    say(f"App versions tested: {', '.join(sorted(set(lg.app_version.astype(str))))}")

    unknown = set(lg.profile_id) - set(spec.profile_id)
    if unknown:
        say(f"WARNING: log contains profiles not in the spec sheet: {sorted(unknown)}")

    base = lg[lg.scenario == "baseline"]
    rep = lg[lg.scenario == "repeat"]
    bP = base[base.logic_version == PRIMARY_VERSION].set_index("profile_id")
    rows = []

    def add(code, name, num, den, note=""):
        rows.append({"Criterion": CRITERION[code[0]], "Metric": f"{code} {name}", "Numerator": num,
                     "Denominator": den, "Result": ratio(num, den), "Note": note})

    # ---------- Utility ----------
    cov = [p for p in core if p in bP.index and bP.loc[p, "recommended_skill"] != "" and bP.loc[p, "pathway_modules"] != ""]
    add("U1", "Recommendation coverage", len(cov), len([p for p in core if p in bP.index]))

    match_rows = []
    for _, s in spec[spec.profile_id.isin(core)].iterrows():
        ok_set = set(split(s.acceptable_recommendations))
        if not ok_set or s.profile_id not in bP.index:
            continue
        hit = str(bP.loc[s.profile_id, "recommended_skill"]).strip().lower() in ok_set
        match_rows.append({"profile_id": s.profile_id, "competency_level": s.competency_level,
                           "discipline": s.discipline, "employment_goal": s.employment_goal, "match": hit})
    mt = pd.DataFrame(match_rows)
    add("U2", "Expected-recommendation match", int(mt.match.sum()) if len(mt) else 0, len(mt),
        "Acceptable sets defined in spec sheet before testing")

    # ---------- Quality ----------
    q1_ok = q1_n = 0
    st = lg[(lg.scenario == "struggle") & (lg.logic_version == PRIMARY_VERSION)]
    for pid, g in st.groupby("profile_id"):
        g = g.sort_values("step")
        start = str(bP.loc[pid, "module_difficulties"]).split(";")[0] if pid in bP.index else ""
        second = g[g.step.astype(int) == 2]
        if second.empty or start == "":
            continue
        q1_n += 1
        revised = yes(second.iloc[0].roadmap_revised)
        lowered = int(float(second.iloc[0].module_difficulties)) < int(float(start)) or int(float(start)) <= MIN_DIFFICULTY
        first_not = not yes(g[g.step.astype(int) == 1].iloc[0].roadmap_revised)
        q1_ok += int(revised and lowered and first_not)
    add("Q1", "Adaptive revision correctness", q1_ok, q1_n, "Revision only after 2nd failure, with lower difficulty")

    cols = ["recommended_skill", "alternatives", "pathway_modules", "income_displayed"]
    b2 = base.set_index(["profile_id", "logic_version"])[cols]
    r2 = rep.set_index(["profile_id", "logic_version"])[cols]
    both = b2.index.intersection(r2.index)
    same = sum((b2.loc[i] == r2.loc[i]).all() for i in both)
    add("Q2", "Output consistency on repeat", int(same), len(both), "Both versions")

    withrec = base[base.recommended_skill != ""]
    add("Q3", "Explanation completeness", int(withrec.explanation_present.map(yes).sum()), len(withrec), "Both versions")

    e = lg[lg.profile_id.isin(edge) & lg.scenario.isin(["baseline", "error"])]
    ok = 0
    groups = list(e.groupby(["profile_id", "logic_version"]))
    for _, g in groups:
        no_err = (g.error == "").all()
        graceful = ((g.recommended_skill != "") | (g.explanation_text != "")).any()
        ok += int(no_err and graceful)
    add("Q4", "Edge-case robustness", ok, len(groups), "No error and a valid recommendation or clear fallback message")

    gp = lg[(lg.scenario == "gap") & (lg.logic_version == PRIMARY_VERSION)]
    q5_ok = 0
    gpg = list(gp.groupby("profile_id"))
    for _, g in gpg:
        trig = g[g.notification_triggered.map(yes)].step.astype(int)
        q5_ok += int(len(trig) > 0 and trig.min() == NUDGE_DAY)
    add("Q5", "Nudge rule correctness", q5_ok, len(gpg), f"First nudge on inactive day {NUDGE_DAY}")

    # ---------- Efficacy ----------
    sd = lg[(lg.scenario == "steady") & (lg.logic_version == PRIMARY_VERSION)]
    sdg = list(sd.groupby("profile_id"))
    e1 = sum(int((g.milestone_awarded != "").sum() >= 2) for _, g in sdg)
    add("E1", "Multi-milestone staging", e1, len(sdg), "Two or more milestones across the steady-progress script")

    e2_ok = e2_n = 0
    for pid, r in bP.iterrows():
        d = [int(float(x)) for x in str(r.module_difficulties).split(";") if x.strip() != ""]
        if len(d) < 2:
            continue
        e2_n += 1
        e2_ok += int(all(0 <= b - a <= 1 for a, b in zip(d, d[1:])))
    add("E2", "Graduated difficulty (ZPD) sequencing", e2_ok, e2_n, "Each step rises by at most one level")

    res = pd.DataFrame(rows)
    res["Threshold"] = res.Metric.map(THRESHOLDS)
    res["Met?"] = res.apply(lambda r: "n/a" if pd.isna(r.Result) else ("Yes" if r.Result >= r.Threshold else "No"), axis=1)

    # ---------- Paired A/B comparison ----------
    bA = base[base.logic_version == "A"].set_index("profile_id")
    paired = [p for p in core if p in bA.index and p in bP.index]
    ab_rows = []
    for p in paired:
        altA, altB = set(split(bA.loc[p, "alternatives"])), set(split(bP.loc[p, "alternatives"]))
        ab_rows.append({"profile_id": p,
                        "same_primary": bA.loc[p, "recommended_skill"] == bP.loc[p, "recommended_skill"],
                        "alt_overlap": len(altA & altB) / len(altA | altB) if altA | altB else 1.0,
                        "income_in_A": bA.loc[p, "income_displayed"] != "",
                        "income_labelled_estimate": "estimate" in str(bA.loc[p, "income_displayed"]).lower(),
                        "income_in_B": bP.loc[p, "income_displayed"] != ""})
    ab = pd.DataFrame(ab_rows)
    if len(ab):
        shown = ab[ab.income_in_A]
        ab_summary = pd.DataFrame([
            {"Comparison": "Primary recommendation identical in A and B", "Result": ab.same_primary.mean(), "n": len(ab)},
            {"Comparison": "Mean overlap of alternative recommendations", "Result": ab.alt_overlap.mean(), "n": len(ab)},
            {"Comparison": "A: income information displayed", "Result": ab.income_in_A.mean(), "n": len(ab)},
            {"Comparison": "A: displayed income labelled as an estimate", "Result": shown.income_labelled_estimate.mean() if len(shown) else float("nan"), "n": len(shown)},
            {"Comparison": "B: income information leaked (should be 0)", "Result": ab.income_in_B.mean(), "n": len(ab)},
        ])
    else:
        ab_summary = pd.DataFrame()

    # ---------- Breakdown ----------
    if len(mt):
        by_level = mt.groupby("competency_level").match.agg(["sum", "count", "mean"]).rename(columns={"sum": "matched", "count": "profiles", "mean": "rate"})
        by_disc = mt.groupby("discipline").match.agg(["sum", "count", "mean"]).rename(columns={"sum": "matched", "count": "profiles", "mean": "rate"})
        by_goal = mt.groupby("employment_goal").match.agg(["sum", "count", "mean"]).rename(columns={"sum": "matched", "count": "profiles", "mean": "rate"})
    else:
        by_level = by_disc = by_goal = pd.DataFrame()

    with pd.ExcelWriter(f"{OUT}/results.xlsx") as xw:
        pd.DataFrame({"Note": ["Results describe SkillPath outputs for researcher-built synthetic profiles. No real persons involved."]}).to_excel(xw, sheet_name="READ ME", index=False)
        res.to_excel(xw, sheet_name="DSR criteria", index=False)
        ab_summary.to_excel(xw, sheet_name="AB paired summary", index=False)
        ab.to_excel(xw, sheet_name="AB per profile", index=False)
        mt.to_excel(xw, sheet_name="U2 per profile", index=False)
        by_level.to_excel(xw, sheet_name="U2 by competency")
        by_disc.to_excel(xw, sheet_name="U2 by discipline")
        by_goal.to_excel(xw, sheet_name="U2 by goal")

    fig, ax = plt.subplots(figsize=(9, 5))
    colors = {"Utility": "#2E5C8A", "Quality": "#5B8DB8", "Efficacy": "#E39B2D"}
    ax.barh(res.Metric, res.Result * 100, color=[colors[c] for c in res.Criterion])
    for i, t in enumerate(res.Threshold):
        ax.plot([t * 100] * 2, [i - 0.4, i + 0.4], color="#C0392B", lw=2)
    ax.invert_yaxis(); ax.set_xlim(0, 105); ax.set_xlabel("% (red line = threshold)")
    ax.set_title("SkillPath DSR evaluation: synthetic profile testing")
    plt.tight_layout(); plt.savefig(f"{OUT}/fig_criteria.png", dpi=200); plt.close()

    if len(mt):
        fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
        for ax, (title, t) in zip(axes, [("By competency level", by_level), ("By discipline", by_disc)]):
            ax.bar(t.index.astype(str), t.rate * 100, color="#2E5C8A")
            ax.axhline(THRESHOLDS["U2 Expected-recommendation match"] * 100, color="#C0392B", lw=1.5)
            ax.set_title(title); ax.set_ylim(0, 105); ax.tick_params(axis="x", rotation=25)
        axes[0].set_ylabel("% matching expected recommendation")
        plt.tight_layout(); plt.savefig(f"{OUT}/fig_match.png", dpi=200); plt.close()

    with open(f"{OUT}/analysis_log.txt", "w") as f:
        f.write("\n".join(log))
    pd.set_option("display.width", 200)
    print("\n", res.to_string(index=False), "\n\n", ab_summary.to_string(index=False))
    print(f"\nOutputs written to ./{OUT}/")


if __name__ == "__main__":
    main()
