# Disclosure of AI assistance

This codebase was developed with the assistance of **Claude Code** (Anthropic; model Claude Opus 5.5), an
AI coding assistant, on 2026-10-05, from a specification written by the researcher (`CLAUDE_CODE_PROMPT.md`).

## What the AI assistant did
- Wrote the engine (`skillpath/`), adapter (`skillpath_adapter.py`), API (`api/`), app (`app/`), tests
  (`tests/`), placeholder module text (`data/modules.json`), the fake development skill map
  (`data/skill_map.example.csv`), the fake test fixtures (`tests/fixtures/`), and the documentation
  (README, DECISIONS, TRACEABILITY).
- Extracted Stats SA median earnings figures from the text of *Labour Market Dynamics in South Africa, 2024*
  (Report 02-11-02) into `data/income_reference_statssa.csv` as **reference material for the researcher to verify**.
  This file is not read by any code.

## What the AI assistant did not do
- It did not create, fill in or edit any research data: synthetic profiles, CVs, acceptable recommendations,
  `data/skill_map.csv`, test output logs or results.
- It did not modify the researcher-provided scripts (`run_synthetic_tests.py`, `analyse_outputs.py`,
  `prepare_profiles.py`), their CSV formats, or the acceptance thresholds.

## Verification by the researcher
All AI-written code is covered by automated tests (`pytest`), and the git commit history records each step
(commits are marked `Co-Authored-By: Claude`). The researcher remains responsible for reviewing the code,
the design decisions in DECISIONS.md, and every figure taken from the income reference file.
