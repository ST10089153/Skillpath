"""The profile builder converts researcher entries into the harness format (exercised with throwaway test values)."""

import csv
import os
import shutil
import subprocess
import sys

from openpyxl import load_workbook

from conftest import ROOT


def test_builder_converts_to_profiles_csv(tmp_path):
    src = os.path.join(ROOT, "profiles", "profile_builder.xlsx")
    if not os.path.exists(src):
        import pytest
        pytest.skip("profile builder not generated")
    wb_path = tmp_path / "builder.xlsx"
    shutil.copy(src, wb_path)
    wb = load_workbook(wb_path)
    ws = wb["Profiles"]
    head = [c.value for c in ws[1]]
    col = {h: i + 1 for i, h in enumerate(head)}
    ws.cell(2, col["qualification"], "TEST qualification")       # SP01 (limited: 2 skills)
    ws.cell(2, col["target_occupation"], "Financial Accountant")
    ws.cell(2, col["skill_1"], "Payroll")
    ws.cell(2, col["skill_2"], "Tax & VAT")
    ws.cell(29, col["skill_1"], "ALL SKILLS")                     # SP28
    wb.save(wb_path)
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "profiles_from_builder.py"),
                        "--builder", str(wb_path), "--out", str(tmp_path / "profiles.csv"),
                        "--cv-dir", str(tmp_path / "cvs")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    rows = {p["profile_id"]: p for p in csv.DictReader(open(tmp_path / "profiles.csv", encoding="utf-8"))}
    assert len(rows) == 28
    assert rows["SP01"]["current_skills"] == "Payroll; Tax & VAT" and rows["SP01"]["acceptable_recommendations"] == ""
    assert rows["SP28"]["current_skills"].count(";") >= 60 and rows["SP28"]["is_edge_case"] == "Y"
    assert "SP02: no target_occupation" in r.stdout
    exp = list(csv.DictReader(open(tmp_path / "cvs" / "expected_skills.csv", encoding="utf-8")))
    assert exp[0]["cv_file"] == "CV_SP01.pdf"
