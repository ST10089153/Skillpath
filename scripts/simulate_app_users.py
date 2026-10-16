"""Generate SkillPath operational (app-usage) data with scripted SIMULATED USERS.

    python scripts/simulate_app_users.py samples/example_study/profiles_EXAMPLE.csv --label EXAMPLE
    python scripts/simulate_app_users.py profiles.csv --label final

Each simulated user = one synthetic profile x one behaviour persona x one logic version (A income-visible,
B income-neutral). Users drive the REAL SkillPath API (in-process, simulated clock) exactly as the app does:
consent and onboarding, skills profile, recommendation, accept / swap / defer, module results, daily nudge
checks, session start and end. Every event is written by the API to its SQLite events table and exported.

WHAT THIS DATA IS: SkillPath's recorded responses to researcher-defined behaviour scripts. Behaviour is
scripted and identical in both arms (it never reacts to income), so the data shows how the system behaves
and logs for each kind of user. It is NOT evidence of how real people engage or are motivated.

Output: runs/APPSIM<date-time>-<label>/
    app_data.db, events.csv, users.csv, pathways.csv   raw operational data (API export)
    simulated_users.csv                                 who was simulated (profile, persona, arm, user_id)
    personas.json                                       the behaviour scripts used
    manifest.json                                       build, date, inputs, SHA-256 checksums
Then run scripts/analyse_app_data.py on the folder.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import os
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient  # noqa: E402

from api.main import create_app  # noqa: E402

BASE = dt.datetime(2026, 10, 19, tzinfo=dt.timezone.utc)  # simulated day 0 (a Monday)
HORIZON_DAYS = 21                                        # observe 3 weeks (covers 14-day retention)
TOKEN = "simulation-admin"

# Behaviour personas. Each step happens on a simulated day. "via_nudge" marks a return prompted by a nudge.
# Grounding: steady progress and staged milestones (Bandura, 1997); struggle and revision (Vygotsky, 1978);
# drifting and triggers (Fogg, 2003); autonomy over the pathway (Deci and Ryan, 2000); attrition in online
# learning (Jordan, 2015); informal, part-time learners outside institutional timetables (Du Plooy et al., 2024).
PERSONAS = {
    "steady": {
        "description": "Accepts the recommendation and completes one module a day until the pathway is done.",
        "decision": "accept",
        "days": [{"day": d, "modules": [True]} for d in range(6)],
    },
    "struggler": {
        "description": "Accepts; struggles twice in a row on module 2 (roadmap revision), returns next day and finishes.",
        "decision": "accept",
        "days": [{"day": 0, "modules": [True]}, {"day": 1, "modules": [False, False]},
                 {"day": 2, "modules": [True, True]}, {"day": 3, "modules": [True, True]},
                 {"day": 4, "modules": [True]}],
    },
    "drifter": {
        "description": "Accepts; completes 2 modules, goes quiet, returns when nudged and completes the pathway.",
        "decision": "accept",
        "days": [{"day": 0, "modules": [True]}, {"day": 1, "modules": [True]},
                 {"day": 3, "modules": [True, True], "via_nudge": True}, {"day": 4, "modules": [True, True]}],
    },
    "explorer": {
        "description": "Looks at alternatives and swaps to the first one; completes 4 modules, then stops.",
        "decision": "swap",
        "days": [{"day": 0, "modules": [True, True]}, {"day": 2, "modules": [True, True]}],
    },
    "deferrer": {
        "description": "Chooses 'Not now'; returns when nudged two days later, accepts and completes 3 modules.",
        "decision": "defer",
        "days": [{"day": 2, "accept": True, "modules": [True, True, True], "via_nudge": True}],
    },
    "part_time": {
        "description": "Accepts and completes one module every three days (busy part-time learner), finishing on day 15.",
        "decision": "accept",
        "days": [{"day": d, "modules": [True]} for d in (0, 3, 6, 9, 12, 15)],
    },
    "dropout": {
        "description": "Accepts and completes 1 module, then never returns (nudges are sent but not opened).",
        "decision": "accept",
        "days": [{"day": 0, "modules": [True]}],
    },
}


class Clock:
    def __init__(self):
        self.t = BASE

    def __call__(self):
        return self.t

    def at(self, day: int, hour: int, minute: int = 0):
        self.t = BASE + dt.timedelta(days=day, hours=hour, minutes=minute)


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def simulate_user(c: TestClient, clock: Clock, profile: dict, persona_name: str, arm: str) -> dict:
    persona = PERSONAS[persona_name]
    clock.at(0, 9)
    uid = c.post(f"/users?arm={arm}", json={"consent": True, "age_confirmed": True}).json()["user_id"]
    ev = lambda t, item="": c.post(f"/users/{uid}/events", json={"event_type": t, "item_id": item})
    ev("session_start")
    clock.at(0, 9, 2)
    ev("assessment_started")
    level = profile["competency_level"] if profile["competency_level"] in ("limited", "foundational", "moderate") \
        else "foundational"
    skills = [s.strip() for s in profile["current_skills"].split(";") if s.strip()]
    clock.at(0, 9, 8)
    c.post(f"/users/{uid}/profile", json={"skills": skills, "competency_level": level})
    clock.at(0, 9, 10)
    rec = c.get(f"/users/{uid}/recommendation").json()
    has_rec = bool(rec.get("recommended_skill"))
    outcome = {"user_id": uid, "recommended": has_rec, "decision": "", "modules_passed": 0}
    if has_rec:
        decision = persona["decision"]
        if decision == "swap" and not rec["alternatives"]:
            decision = "accept"
        clock.at(0, 9, 12)
        if decision == "accept":
            c.post(f"/users/{uid}/pathway/accept")
        elif decision == "swap":
            c.post(f"/users/{uid}/pathway/swap", json={"skill": rec["alternatives"][0]})
        else:
            c.post(f"/users/{uid}/pathway/defer")
        outcome["decision"] = decision

    plan = {d["day"]: d for d in persona["days"]}
    for day in range(0, HORIZON_DAYS + 1):
        if day > 0:  # daily nudge check before the user's day starts (the app's server-side trigger)
            clock.at(day, 8)
            c.get(f"/users/{uid}/nudge")
        step = plan.get(day)
        if step is None or not has_rec:
            if day == 0:
                clock.at(0, 11)
                ev("session_end")
            continue
        if day > 0:
            clock.at(day, 8, 30)
            if step.get("via_nudge"):
                ev("notification_opened")
            ev("session_start")
        if step.get("accept"):
            c.post(f"/users/{uid}/pathway/accept")
            outcome["decision"] += "+accept"
        for k, passed in enumerate(step.get("modules", [])):
            clock.at(day, 9 if day > 0 else 10, 10 * (k + 1))
            cur = c.get(f"/users/{uid}/progress").json().get("current_module")
            if not cur:
                break
            c.post(f"/users/{uid}/modules/{cur['module_id']}/result", json={"passed": passed})
            outcome["modules_passed"] += int(passed)
        clock.at(day, 11)
        ev("session_end")
    return outcome


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("profiles")
    ap.add_argument("--label", default="")
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "runs"))
    ap.add_argument("--skill-map", default=os.path.join(ROOT, "data", "skill_map.csv"))
    a = ap.parse_args()

    started = dt.datetime.now()
    run_id = "APPSIM" + started.strftime("%Y%m%d-%H%M%S") + (f"-{a.label}" if a.label else "")
    out = os.path.join(os.path.abspath(a.out_dir), run_id)
    os.makedirs(out)
    db = os.path.join(out, "app_data.db")
    clock = Clock()
    c = TestClient(create_app(db_path=db, skill_map_path=a.skill_map, admin_token=TOKEN, clock=clock))

    profiles = list(csv.DictReader(open(a.profiles, encoding="utf-8")))
    sims = []
    for p in profiles:
        for persona in PERSONAS:
            for arm in ("A", "B"):
                o = simulate_user(c, clock, p, persona, arm)
                sims.append({"user_id": o["user_id"], "profile_id": p["profile_id"], "persona": persona, "arm": arm,
                             "competency_level": p["competency_level"], "discipline": p["discipline"],
                             "employment_goal": p["employment_goal"], "is_edge_case": p["is_edge_case"],
                             "recommended": "Y" if o["recommended"] else "N", "decision": o["decision"],
                             "modules_passed": o["modules_passed"]})
    with open(os.path.join(out, "simulated_users.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(sims[0]))
        w.writeheader()
        w.writerows(sims)
    z = zipfile.ZipFile(io.BytesIO(c.get("/admin/export/all", headers={"X-Admin-Token": TOKEN}).content))
    for name in ("events.csv", "users.csv", "pathways.csv"):
        open(os.path.join(out, name), "wb").write(z.read(name))
    json.dump(PERSONAS, open(os.path.join(out, "personas.json"), "w", encoding="utf-8"), indent=1)

    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                                capture_output=True, text=True).stdout.strip())
    files = {fn: sha256(os.path.join(out, fn)) for fn in sorted(os.listdir(out)) if fn != "manifest.json"}
    json.dump({"run_id": run_id, "created": started.isoformat(timespec="seconds"), "build": commit + ("-dirty" if dirty else ""),
               "profiles_file": os.path.relpath(os.path.abspath(a.profiles), ROOT), "profiles": len(profiles),
               "personas": list(PERSONAS), "arms": ["A", "B"], "simulated_users": len(sims),
               "simulated_period": f"{BASE.date()} + {HORIZON_DAYS} days", "sha256": files,
               "note": "Scripted simulated users; behaviour identical in both arms. Not evidence of human behaviour."},
              open(os.path.join(out, "manifest.json"), "w", encoding="utf-8"), indent=1)
    n_events = sum(1 for _ in open(os.path.join(out, "events.csv"), encoding="utf-8")) - 1
    print(f"{run_id}: {len(sims)} simulated users ({len(profiles)} profiles x {len(PERSONAS)} personas x 2 arms), "
          f"{n_events} events\n-> {out}\nNext: python scripts/analyse_app_data.py \"{out}\"")


if __name__ == "__main__":
    main()
