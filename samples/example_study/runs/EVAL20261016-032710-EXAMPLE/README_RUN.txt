SKILLPATH EVALUATION RUN EVAL20261016-032710-EXAMPLE

Engine: SkillPath (--engine skillpath), build 96fa987, run on 2026-10-16 03:27.
Results describe SkillPath outputs for researcher-built synthetic profiles. No real persons involved.

Contents
- inputs/: exact copies of the profile specification sheet and skill data used.
- profiles_ready.csv: specification sheet after prepare_profiles.py (acceptable sets fixed before testing).
- test_output_log.csv: raw outputs from run_synthetic_tests.py.
- results/: output of analyse_outputs.py (results.xlsx, figures, analysis_log.txt).
- PART3_RESULTS.md: Section 5 tables generated from results/results.xlsx.
- run_outputs_summary.csv: per-profile recommendation, category and demand cluster.
- code/: the scripts and engine used. manifest.json: versions, commands, exit codes, SHA-256 checksums.

Reproduce (from this folder, with the packages in code/requirements.txt):
  python code/prepare_profiles.py inputs/profiles.csv inputs/skill_map.csv --fill-acceptable
  python code/run_synthetic_tests.py profiles_ready.csv inputs/skill_map.csv --app-version 96fa987 --engine skillpath
  python code/analyse_outputs.py profiles_ready.csv test_output_log.csv
Outputs should match test_output_log.csv except the run_id and timestamp columns.
