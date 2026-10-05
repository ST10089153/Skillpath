"""run_evaluation.py produces a complete, checksummed replication package (on fake fixtures)."""

import json
import os
import subprocess
import sys
import zipfile

from conftest import PROFILES_CSV, ROOT, SKILL_MAP_CSV


def test_evaluation_package(tmp_path):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "run_evaluation.py"), PROFILES_CSV,
                        "--skill-map", SKILL_MAP_CSV, "--out-dir", str(tmp_path), "--label", "pytest",
                        "--allow-dirty", "--continue-on-check-problems"],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    runs = [d for d in os.listdir(tmp_path) if os.path.isdir(tmp_path / d)]
    assert len(runs) == 1
    run = tmp_path / runs[0]
    for f in ["inputs/profiles.csv", "inputs/skill_map.csv", "profiles_ready.csv", "test_output_log.csv",
              "results/results.xlsx", "results/fig_criteria.png", "PART3_RESULTS.md", "run_outputs_summary.csv",
              "README_RUN.txt", "manifest.json", "code/skillpath/engine.py", "code/run_synthetic_tests.py"]:
        assert (run / f).exists(), f
    m = json.load(open(run / "manifest.json", encoding="utf-8"))
    assert m["complete"] and all(s["exit_code"] == 0 for s in m["steps"][1:])
    assert "test_output_log.csv" in m["sha256"] and m["engine_constants"]["K"] == 3
    assert "Table 1: DSR evaluation criteria" in (run / "PART3_RESULTS.md").read_text(encoding="utf-8")
    assert zipfile.ZipFile(str(run) + ".zip").testzip() is None
    assert not os.path.exists(run / "inputs" / "skill_taxonomy.csv")  # only copied for the real map
