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

- At the researcher's request (2026-10-05), wrote and ran `scripts/build_skill_map.py`, which generated
  `data/skill_map.csv`, `data/skill_descriptions.json` and `data/skill_map_build.json` from the DHET 2024
  Occupations in High Demand list, the ESCO API and Stats SA (2024). The occupation selection (24 occupations)
  was proposed by the assistant using the rule in DECISIONS.md #32 and must be confirmed by the researcher.

- Added the CV skill-extraction component (`skillpath/cv.py`), which runs an open-source sentence-embedding
  model (all-MiniLM-L6-v2) locally. This is an AI component *inside* SkillPath; it is separate from the AI
  assistant used to write the code.

- Drafted the condensed skill taxonomy (`data/skill_taxonomy.csv`: 71 skills, definitions, "how to show it"
  tasks, WEF cluster assignment, evidencing ESCO labels, CV keywords) and extracted WEF Future of Jobs 2025
  figures (`data/wef_skills_2025.csv`). These are design choices for the researcher to review and approve.

- Wrote 8 clearly labelled DEMO CVs for development checks (later removed and superseded by the worked example).

- At the user's request (as a teacher), generated a watermarked WORKED EXAMPLE of the Phase 3 inputs
  (`samples/example_study/`: 28 example profiles and CVs). This is a teaching exemplar, not study data.
  At the user's request the same watermarked example was then placed in `profiles.csv` and `profiles/cvs/`
  so that the full pipeline could be run end to end on it (2026-10-16).

## What the AI assistant did not do
- It did not create, fill in or edit the study's synthetic profiles or study CVs, acceptable recommendations, test output logs
  or results. No skill, occupation or income figure was typed by hand: all come from the cited sources via the script.
- It did not modify the researcher-provided scripts (`run_synthetic_tests.py`, `analyse_outputs.py`,
  `prepare_profiles.py`), their CSV formats, or the acceptance thresholds.

## Verification by the researcher
All AI-written code is covered by automated tests (`pytest`), and the git commit history records each step
(commits are marked `Co-Authored-By: Claude`). The researcher remains responsible for reviewing the code,
the design decisions in DECISIONS.md, and every figure taken from the income reference file.
