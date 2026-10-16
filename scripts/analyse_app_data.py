"""Analyse SkillPath operational (app-usage) data: the event log exported by the API.

    python scripts/analyse_app_data.py runs/APPSIM<...>          # a simulated-user run
    python scripts/analyse_app_data.py path/to/export_folder     # any folder with events.csv (+ simulated_users.csv)

Computes the operational evaluation measures defined in the research proposal (section 3.6), per logic
version (A income-visible, B income-neutral) and, when simulated_users.csv is present, per persona:

  Assessment completion       users with assessment_complete / users with onboarding_complete   (proposal: >= 60%)
  Pathway adoption            users who adopted or swapped / users with pathway_recommended     (proposal: >= 50%)
  Re-engagement after revision revisions followed by a session_start within 48 h / revisions   (proposal: >= 70%)
  Multi-milestone completion  users with >= 2 milestones / users who adopted or swapped         (proposal: >= 40%)
  14-day retention            users with a session_start >= 14 days after onboarding / all users (A vs B)
  plus swap and defer rates, nudges sent and opened, and days to first milestone.

Writes into the folder: app_metrics.xlsx, APP_DATA_RESULTS.md, fig_app_metrics.png.
For simulated users the values follow from the scripted personas; they describe system behaviour and logging,
not human engagement.
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

THRESHOLDS = {"Assessment completion": 0.60, "Pathway adoption": 0.50,
              "Re-engagement within 48 h after revision": 0.70, "Multi-milestone completion": 0.40}


def rate(n, d):
    return n / d if d else float("nan")


def metrics(ev: pd.DataFrame, users: list) -> dict:
    e = ev[ev.user_id.isin(users)]
    has = lambda t: set(e.loc[e.event_type == t, "user_id"])
    onboard, assess = has("onboarding_complete"), has("assessment_complete")
    recd = has("pathway_recommended")
    adopted, swapped, deferred = has("pathway_adopted"), has("pathway_swapped"), has("pathway_deferred")
    took = adopted | swapped
    ms = e[e.event_type == "milestone_reached"].groupby("user_id").size()
    multi = {u for u, n in ms.items() if n >= 2}
    rev = e[e.event_type == "roadmap_revised"]
    sess = e[e.event_type == "session_start"]
    back = 0
    for _, r in rev.iterrows():
        later = sess[(sess.user_id == r.user_id) & (sess.ts > r.ts) & (sess.ts <= r.ts + pd.Timedelta(hours=48))]
        back += int(len(later) > 0)
    start = e[e.event_type == "onboarding_complete"].groupby("user_id").ts.min()
    retained = {u for u, g in sess.groupby("user_id") if u in start and (g.ts.max() - start[u]) >= pd.Timedelta(days=14)}
    first_ms = e[e.event_type == "milestone_reached"].groupby("user_id").ts.min()
    days_ms = [(first_ms[u] - start[u]).total_seconds() / 86400 for u in first_ms.index if u in start]
    sent, opened = (e.event_type == "notification_sent").sum(), (e.event_type == "notification_opened").sum()
    return {
        "Users": len(users),
        "Assessment completion": (len(assess & onboard), len(onboard)),
        "Pathway adoption": (len(took & recd), len(recd)),
        "Re-engagement within 48 h after revision": (back, len(rev)),
        "Multi-milestone completion": (len(multi & took), len(took)),
        "14-day retention": (len(retained), len(users)),
        "Swap rate": (len(swapped & recd), len(recd)),
        "Defer rate": (len(deferred & recd), len(recd)),
        "Nudges opened": (int(opened), int(sent)),
        "Mean days to first milestone": round(sum(days_ms) / len(days_ms), 2) if days_ms else float("nan"),
    }


def flatten(name, m):
    rows = []
    for k, v in m.items():
        if isinstance(v, tuple):
            rows.append({"Group": name, "Measure": k, "Numerator": v[0], "Denominator": v[1], "Result": rate(*v),
                         "Proposal threshold": THRESHOLDS.get(k, float("nan"))})
        else:
            rows.append({"Group": name, "Measure": k, "Numerator": "", "Denominator": "", "Result": v,
                         "Proposal threshold": float("nan")})
    return rows


def md_table(df):
    df = df.fillna("")
    out = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(f"{v:.1%}" if isinstance(v, float) and c in ("Result", "Proposal threshold")
                                     and v == v and v <= 1 else (f"{v:.2f}" if isinstance(v, float) else str(v))
                                     for c, v in zip(df.columns, r)) + " |")
    return "\n".join(out)


def main():
    folder = sys.argv[1]
    ev = pd.read_csv(os.path.join(folder, "events.csv"), dtype=str).fillna("")
    ev["ts"] = pd.to_datetime(ev.timestamp, utc=True, format="ISO8601")
    sim_path = os.path.join(folder, "simulated_users.csv")
    sims = pd.read_csv(sim_path, dtype=str).fillna("") if os.path.exists(sim_path) else None
    all_users = sorted(set(ev.user_id))
    arm = ev.drop_duplicates("user_id").set_index("user_id").arm

    rows = flatten("All users", metrics(ev, all_users))
    for a in sorted(arm.unique()):
        rows += flatten(f"Arm {a}", metrics(ev, [u for u in all_users if arm[u] == a]))
    persona_rows = []
    if sims is not None:
        for p in sims.persona.unique():
            persona_rows += flatten(p, metrics(ev, list(sims.loc[sims.persona == p, "user_id"])))
    res, per = pd.DataFrame(rows), pd.DataFrame(persona_rows)
    counts = ev.groupby(["event_type", "arm"]).size().unstack(fill_value=0)

    with pd.ExcelWriter(os.path.join(folder, "app_metrics.xlsx")) as xw:
        pd.DataFrame({"Note": ["SkillPath operational data. For simulated users, values follow from scripted personas "
                               "and describe system behaviour and logging, not human engagement."]}
                     ).to_excel(xw, sheet_name="READ ME", index=False)
        res.to_excel(xw, sheet_name="Measures by arm", index=False)
        if len(per):
            per.to_excel(xw, sheet_name="Measures by persona", index=False)
        counts.to_excel(xw, sheet_name="Event counts")

    core = res[res.Measure.isin(THRESHOLDS) & res.Group.str.startswith("Arm")]
    if len(core):
        piv = core.pivot(index="Measure", columns="Group", values="Result").reindex(list(THRESHOLDS))
        ax = piv.mul(100).plot.barh(figsize=(9, 4.5), color=["#E39B2D", "#2E5C8A"][:len(piv.columns)])
        for i, m in enumerate(piv.index):
            ax.plot([THRESHOLDS[m] * 100] * 2, [i - 0.4, i + 0.4], color="#C0392B", lw=2)
        ax.set_xlim(0, 105); ax.set_xlabel("% (red line = proposal threshold)"); ax.invert_yaxis()
        ax.set_title("SkillPath operational measures by logic version")
        plt.tight_layout(); plt.savefig(os.path.join(folder, "fig_app_metrics.png"), dpi=200); plt.close()

    lines = ["# SkillPath operational (app-usage) data results", "",
             f"Source: `{os.path.basename(os.path.normpath(folder))}`. {len(all_users)} users, {len(ev)} events.", ""]
    if sims is not None:
        lines += ["**Simulated users.** Behaviour followed researcher-defined personas and was identical in both "
                  "logic versions, so these results show how SkillPath behaves and records each kind of user. They "
                  "are not evidence of human engagement or motivation.", ""]
    lines += ["## Table A1: Operational measures by logic version", "",
              md_table(res[res.Group.str.startswith(("All", "Arm"))]), ""]
    if len(per):
        lines += ["## Table A2: Operational measures by persona", "",
                  md_table(per[per.Measure.isin(list(THRESHOLDS) + ["14-day retention", "Nudges opened"])]), ""]
    lines += ["## Table A3: Event counts by logic version", "", md_table(counts.reset_index()), ""]
    open(os.path.join(folder, "APP_DATA_RESULTS.md"), "w", encoding="utf-8").write("\n".join(lines))
    print(res[res.Group.str.startswith(("All", "Arm"))].to_string(index=False))
    print(f"\nWrote app_metrics.xlsx, APP_DATA_RESULTS.md, fig_app_metrics.png in {folder}")


if __name__ == "__main__":
    main()
