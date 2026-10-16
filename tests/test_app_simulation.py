"""Simulated-user app data collection runs end to end through the real API and is analysable."""

import csv
import os
import subprocess
import sys

from conftest import ROOT


def test_simulation_and_analysis(tmp_path):
    prof = tmp_path / "p.csv"
    src = list(csv.DictReader(open(os.path.join(ROOT, "tests", "fixtures", "profiles.csv"), encoding="utf-8")))
    with open(prof, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(src[0]))
        w.writeheader()
        w.writerows(src[:2])                                   # one core profile, one more
    sim = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "simulate_app_users.py"), str(prof),
                          "--skill-map", os.path.join(ROOT, "tests", "fixtures", "skill_map.csv"),
                          "--out-dir", str(tmp_path), "--label", "t"], capture_output=True, text=True)
    assert sim.returncode == 0, sim.stderr
    run = next(p for p in tmp_path.iterdir() if p.is_dir())
    users = list(csv.DictReader(open(run / "simulated_users.csv", encoding="utf-8")))
    assert len(users) == 2 * 7 * 2                             # profiles x personas x arms
    events = list(csv.DictReader(open(run / "events.csv", encoding="utf-8")))
    types = {e["event_type"] for e in events}
    assert {"onboarding_complete", "pathway_adopted", "pathway_swapped", "pathway_deferred", "module_complete",
            "milestone_reached", "roadmap_revised", "notification_sent", "notification_opened",
            "session_start", "session_end"} <= types
    ana = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "analyse_app_data.py"), str(run)],
                         capture_output=True, text=True)
    assert ana.returncode == 0, ana.stderr
    assert (run / "APP_DATA_RESULTS.md").exists() and (run / "app_metrics.xlsx").exists()
