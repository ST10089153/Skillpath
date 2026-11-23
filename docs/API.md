# SkillPath API

FastAPI backend with SQLite event logging. Overview in the [README](../README.md); setup in the
[research guide](RESEARCH_GUIDE.md).

## Run it locally

```bash
cp .env.example .env          # then set SKILLPATH_ADMIN_TOKEN
uvicorn api.main:app --reload --port 8000
```

Interactive docs: http://localhost:8000/docs. Data is stored in `skillpath.db` (SQLite, local, git-ignored).

## Endpoints

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

