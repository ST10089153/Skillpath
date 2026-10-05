"""Adapter contract, constants alignment, and end-to-end harness integration."""

import os
import subprocess
import sys

import pandas as pd
import pytest

import analyse_outputs
import run_synthetic_tests
from skillpath import config as C
from skillpath_adapter import SkillPathEngine

from conftest import PROFILES_CSV, ROOT, SKILL_MAP_CSV


def test_constants_match_harness_and_analysis():
    ref = run_synthetic_tests.ReferenceEngine
    assert C.MODULES == run_synthetic_tests.STEADY_MODULES
    assert C.MODULES_PER_MILESTONE == ref.MODULES_PER_MILESTONE
    assert C.FAILS_BEFORE_REVISION == ref.FAILS_BEFORE_REVISION
    assert C.INACTIVE_DAYS_NUDGE == ref.INACTIVE_DAYS_NUDGE == analyse_outputs.NUDGE_DAY
    assert C.MIN_DIFFICULTY == analyse_outputs.MIN_DIFFICULTY
    assert C.K == 3


def test_adapter_contract_with_nan_cells():
    # pd.read_csv leaves empty income cells as NaN, exactly as the harness does
    eng = SkillPathEngine(pd.read_csv(SKILL_MAP_CSV))
    res = eng.recommend({"profile_id": "FX", "competency_level": "limited", "qualification": "",
                         "discipline": "", "current_skills": "skill_e; skill_f"}, "A")
    assert set(res) == {"recommended_skill", "alternatives", "explanation", "income_displayed", "pathway"}
    assert isinstance(res["alternatives"], list) and isinstance(res["pathway"], list)
    assert res["income_displayed"] == ""
    st = {"passes": 0, "fails": 0, "difficulty": res["pathway"][0][1]}
    assert set(eng.progress(st, True)) == {"milestone", "revised", "next_difficulty"}
    assert eng.should_nudge(1) is False and eng.should_nudge(2) is True


def test_adapter_delegates_to_engine(monkeypatch):
    from skillpath import engine as E
    calls = []
    real = E.recommend
    monkeypatch.setattr(E, "recommend", lambda *a, **k: calls.append(1) or real(*a, **k))
    SkillPathEngine(pd.read_csv(SKILL_MAP_CSV)).recommend({"current_skills": "skill_a"}, "B")
    assert calls


def test_harness_and_analysis_run_end_to_end(tmp_path):
    log = os.path.join("tests", "tmp_log.csv")
    try:
        run = subprocess.run([sys.executable, "run_synthetic_tests.py", "tests/fixtures/profiles.csv",
                              "tests/fixtures/skill_map.csv", "--app-version", "test", "--engine", "skillpath",
                              "--out", log], cwd=ROOT, capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
        assert "Engine: skillpath" in run.stdout
        assert "ReferenceEngine" not in run.stdout

        out = pd.read_csv(os.path.join(ROOT, log)).fillna("")
        assert (out.error == "").all(), out[out.error != ""].error.tolist()
        base_b = out[(out.scenario == "baseline") & (out.logic_version == "B")].set_index("profile_id")
        assert base_b.loc["FX01", "recommended_skill"] == "skill_c"
        assert base_b.loc["FX03", "explanation_text"] != ""

        ana = subprocess.run([sys.executable, os.path.join(ROOT, "analyse_outputs.py"), PROFILES_CSV,
                              os.path.join(ROOT, log)], cwd=tmp_path, capture_output=True, text=True)
        assert ana.returncode == 0, ana.stderr
        assert (tmp_path / "results" / "results.xlsx").exists()
    finally:
        if os.path.exists(os.path.join(ROOT, log)):
            os.remove(os.path.join(ROOT, log))
