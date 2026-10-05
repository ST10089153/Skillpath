# SkillPath

Research prototype for an Honours Design Science Research study (REIT8419, The Independent Institute of
Education). SkillPath reads a graduate's current skills, recommends the highest-leverage **next skill**
through adjacency-first logic, and delivers a six-module micro-learning pathway with visible milestones.

Evaluation is by **controlled synthetic testing**: researcher-built synthetic profiles are fed to the engine by
`run_synthetic_tests.py`, and the logged outputs are analysed by `analyse_outputs.py`. No real users take part.

> AI-generated suggestion based on published labour-market literature. Not professional career or financial advice.

## Repository layout

| Path | What it is |
|---|---|
| `skillpath/` | The engine (pure, deterministic rules). `config.py` holds every design constant. |
| `skillpath_adapter.py` | `SkillPathEngine` class imported by the harness (`--engine skillpath`). |
| `skillpath/cv.py` | CV skill extraction with a locally hosted AI model (all-MiniLM-L6-v2 via fastembed). The model (~90 MB) downloads once into `models/` (git-ignored) on first use, then works offline. |
| `api/` | FastAPI backend with SQLite event logging (Milestone 2). |
| `app/` | Expo (React Native, TypeScript) mobile-first app (Milestone 3). |
| `data/skill_map.csv` | Occupation-skill map (24 DHET occupations × 71 condensed skills) built by `scripts/build_skill_map.py`. Loaded if present. |
| `data/skill_taxonomy.csv` | The condensed skill list: category, definition, how to show it, WEF demand cluster, evidencing ESCO labels, CV keywords. Edit this to change skills, then rebuild. |
| `data/esco_occupation_skills.json`, `data/wef_skills_2025.csv` | Cached ESCO occupation skills and WEF Future of Jobs 2025 figures used by the build. |
| `data/skill_descriptions.json` | Per-skill category, definition, how to show it and demand evidence (shown in the app). |
| `data/skill_map.example.csv` | Four FAKE rows for development, used when `skill_map.csv` is absent. |
| `data/modules.json` | Placeholder module content shown in the app. |
| `data/income_reference_statssa.csv` | Stats SA 2024 median earnings by occupation group, for the researcher to review (see `data/INCOME_SOURCES.md`). Not read by code. |
| `run_synthetic_tests.py`, `analyse_outputs.py`, `prepare_profiles.py` | Researcher-provided scripts. **Unmodified.** |
| `templates/` | Researcher-provided CSV templates. |
| `tests/` | pytest suite; `tests/fixtures/` holds tiny, obviously fake fixtures only. |
| `DECISIONS.md`, `TRACEABILITY.md`, `AI_USE.md` | Design decision log, directive traceability, AI-use disclosure. |

## Setup

Requires Python 3.10+ (tested on 3.13) and, for the app, Node 18+ (tested on Node 24).

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows (Git Bash: source .venv/Scripts/activate); macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Run the tests

```bash
pytest
```

This runs the engine unit tests, the API tests, and an integration test that executes the real harness
(`run_synthetic_tests.py ... --engine skillpath`) on the fake fixture and then `analyse_outputs.py` on its log.

## Rebuilding the skill map

```bash
python scripts/fetch_esco_occupations.py   # online, only when refreshing ESCO data
python scripts/build_skill_map.py          # offline: rebuilds the map from data/skill_taxonomy.csv
python scripts/make_skill_reference.py     # refreshes profiles/skill_reference.xlsx
```

Commit the outputs before any test run so `--app-version` identifies the exact data used.

## Evaluation run for Part 3 (recommended)

One command runs the whole evaluation and stores a replication package:

```bash
python run_evaluation.py profiles.csv --label final
```

It runs `prepare_profiles.py`, `run_synthetic_tests.py --engine skillpath` and `analyse_outputs.py` (all
unmodified) on copies of your inputs and writes `runs/EVAL<date-time>-final/` plus a `.zip` for export:

| File | Use in Part 3 |
|---|---|
| `PART3_RESULTS.md` | Section 5 tables: DSR criteria, A/B comparison, U2 by competency, discipline and goal, what SkillPath recommended |
| `results/results.xlsx`, `results/fig_criteria.png`, `results/fig_match.png` | Tables and figures from `analyse_outputs.py` |
| `test_output_log.csv` | Raw system outputs (annexure / supervisor) |
| `profiles_ready.csv`, `inputs/` | Exact inputs, including acceptable sets fixed before testing |
| `run_outputs_summary.csv` | Per-profile recommendation, category and WEF demand cluster |
| `manifest.json` | Date, git commit, package versions, engine constants, commands, exit codes, SHA-256 of every file |
| `code/`, `README_RUN.txt` | Code snapshot and the commands to reproduce the run |

Commit your changes first: the run refuses to start with uncommitted code or data, so the build is traceable
(`--allow-dirty` exists for trial runs only). If `prepare_profiles.py` reports problems the run stops; fix the
sheet and rerun.

## Data collection (the three commands individually)

Put your skill map at `data/skill_map.csv` and your specification sheet at `profiles.csv`, then run, from the repository root:

```bash
python prepare_profiles.py profiles.csv data/skill_map.csv --fill-acceptable
python run_synthetic_tests.py profiles_ready.csv data/skill_map.csv --app-version $(git rev-parse --short HEAD) --engine skillpath
python analyse_outputs.py profiles_ready.csv test_output_log.csv
```

- Commit all code changes first so `--app-version` identifies the exact engine build tested.
- `prepare_profiles.py` exits with code 1 if it finds problems; it still writes `profiles_ready.csv` when
  `--fill-acceptable` is used. Review its report before continuing.
- Outputs: `test_output_log.csv` (raw log) and `results/` (`results.xlsx`, figures, `analysis_log.txt`).
- `$(git rev-parse --short HEAD)` works in Git Bash, macOS/Linux shells and PowerShell.

## API (Milestone 2)

```bash
cp .env.example .env          # then set SKILLPATH_ADMIN_TOKEN
uvicorn api.main:app --reload --port 8000
```

Interactive docs: http://localhost:8000/docs. Data is stored in `skillpath.db` (SQLite, local, git-ignored).

| Method and path | Purpose |
|---|---|
| `POST /users` | Body `{consent, age_confirmed}`. Creates a pseudonymous user (`U` + 6 hex) and assigns arm A/B (SHA-256 parity). Researcher override: `?arm=A` or `?arm=B`. |
| `GET /vocabulary` | Skills grouped by occupation. |
| `POST /cv/extract` | Multipart `file` (PDF, DOCX, TXT). Returns proposed skills with the matching CV phrase and similarity. Nothing is stored. |
| `GET /skills/{skill}` | Official ESCO description and the occupations that need the skill. |
| `GET /modules` | Placeholder module content (`data/modules.json`). |
| `GET /users/{id}` | View my data (profile, pathway, events). |
| `POST /users/{id}/profile` | Body `{skills: [...], competency_level}`. |
| `GET /users/{id}/recommendation` | Calls the engine with the user's arm. |
| `POST /users/{id}/pathway/accept` | Accept the recommendation. |
| `POST /users/{id}/pathway/swap` | Body `{skill}`; switch to an alternative (DD6). |
| `POST /users/{id}/pathway/defer` | "Not now" (DD6). |
| `POST /users/{id}/modules/{module_id}/result` | Body `{passed}`; calls the engine's `progress`. |
| `GET /users/{id}/progress` | Milestones, current module, difficulty. |
| `GET /users/{id}/nudge` | Nudge decision from days since last activity (at most one per day). |
| `POST /users/{id}/events` | App-reported events: `session_start`, `session_end`, `assessment_started`, `notification_opened`. |
| `DELETE /users/{id}` | Deletes every row for that user (POPIA). |
| `GET /admin/export` | Events CSV (`user_id, arm, event_type, timestamp, item_id`); requires header `X-Admin-Token`. |
| `GET /admin/export/all` | ZIP of every table (users, pathways, events) as CSV; requires `X-Admin-Token`. |

```bash
curl -H "X-Admin-Token: <your token>" http://localhost:8000/admin/export -o events.csv
```

## App (Milestone 3)

```bash
cd app
npm install
npx expo start --web          # browser
npx expo start                # scan the QR code with Expo Go on a phone
```

The app calls the API at `http://localhost:8000` by default. On a phone, localhost is the phone itself, so start
the API on all interfaces and point the app at your computer's LAN IP:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
EXPO_PUBLIC_API_URL=http://192.168.1.10:8000 npx expo start   # PowerShell: $env:EXPO_PUBLIC_API_URL="http://192.168.1.10:8000"; npx expo start
```

## Privacy (POPIA by design)

No names, emails or phone numbers are collected. Users are identified by a random pseudonymous ID. All data stays in
a local SQLite file, there are no third-party analytics or trackers, and users can view and delete their data in
Settings. Secrets (`.env`) and the database are git-ignored.

## Quick start (Windows)

From the repository folder in PowerShell (or the VS Code terminal):

```powershell
.\start.ps1          # browser: opens http://localhost:8081
.\start.ps1 -Phone   # phone: scan the QR code with Expo Go
```

The API opens in its own window titled 'SkillPath API'. Ctrl+C stops the app; close that window to stop the API.

