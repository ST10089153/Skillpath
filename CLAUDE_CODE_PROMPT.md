# Build SkillPath: Claude Code prompt

> Paste everything below the line into Claude Code, from the root of a new, empty repository.
> First, copy these files into the repo: `run_synthetic_tests.py`, `analyse_outputs.py`, `prepare_profiles.py`, `requirements.txt`, and the `templates/` folder.

---

## Context

You are building **SkillPath**, a research prototype for an Honours Design Science Research (DSR) study at The Independent Institute of Education (REIT8419). SkillPath is a mobile-first recommender for unemployed and underemployed South African graduates. It reads a graduate's current skills, identifies the highest-leverage next skill through **adjacency-first** logic, and delivers a short, staged micro-learning pathway that builds confidence through visible milestones.

The prototype will be evaluated through **controlled synthetic testing**, as approved by the ethics committee. The researcher feeds researcher-built synthetic profiles into the engine through a Python test harness (`run_synthetic_tests.py`) and analyses the logged outputs (`analyse_outputs.py`). No real users take part. **The engine's behaviour must therefore be deterministic, rule-exact and testable**, because every rule below is measured by a specific evaluation metric.

### Priorities, in order (deadline: today)

1. **Milestone 1 (critical):** the Python engine package, `skillpath_adapter.py`, and passing unit tests. This alone unblocks data collection.
2. **Milestone 2:** FastAPI backend wrapping the engine, with SQLite event logging.
3. **Milestone 3:** mobile-first front end.

Finish and verify each milestone before starting the next. After Milestone 1, stop and show me the test results.

---

## Hard constraints

- **Never fabricate research data.** Do not create, fill in or edit synthetic profiles, CVs, acceptable recommendations, test output logs or results. The researcher builds all of these. Unit tests use tiny, obviously fake fixtures (e.g. `occ_a`, `skill_x`) kept under `tests/fixtures/` only.
- **Do not modify** `run_synthetic_tests.py`, `analyse_outputs.py` or `prepare_profiles.py`, their CSV column formats, or the thresholds in `analyse_outputs.py`. If you think a change is needed, tell me and explain why instead.
- **The engine must never read** `target_occupation`, `acceptable_recommendations`, `designed_to_test`, `employment_goal` or `is_edge_case`. The harness only passes `profile_id, competency_level, qualification, discipline, current_skills`.
- **Determinism:** identical input must give identical output. No randomness, no wall-clock dependence in the engine, no network calls. Break every tie alphabetically.
- **Income must never affect ranking.** Versions A and B must produce the same recommendation, alternatives and pathway; only `income_displayed` differs.
- **POPIA by design:** no names, emails or phone numbers are required. Use pseudonymous user IDs, keep data local (SQLite), use no third-party analytics or trackers, and provide a "delete my data" function.
- **No secrets in the repo.** Commit regularly with clear messages (the repo is private; commit history is part of the study's audit trail).

---

## Data inputs

### `data/skill_map.csv` (built by the researcher; read-only for you)

| column | meaning |
|---|---|
| `occupation` | occupation name (unique) |
| `essential_skills` | semicolon-separated skill names (this *is* SkillPath's vocabulary) |
| `income_estimate` | optional text, e.g. `R18 000 per month` |
| `source` | citation of the published report the row came from |

Create `data/skill_map.example.csv` with 4 obviously fake rows for development, and load `data/skill_map.csv` if it exists.

### Profile input to the engine (dict)

`profile_id` (str), `competency_level` (`limited` | `foundational` | `moderate`, anything else = `foundational`), `qualification` (str), `discipline` (str), `current_skills` (semicolon-separated str).

### Normalisation

Lowercase, trim, collapse internal whitespace. Skills not in the vocabulary are **ignored** and listed in the explanation as "not recognised".

---

## Engine specification (`skillpath/engine.py`)

Implement it as pure functions or a class with no I/O except loading the skill map. Each rule is tagged with the evaluation metric that tests it.

### 1. Recommendation: `recommend(profile, version) -> dict`

1. `S` = recognised current skills.
2. **Fallbacks (Q4: edge-case robustness).** Never raise an exception; always return a clear `explanation`:
   - `S` empty and no unrecognised skills: return no recommendation; explanation asks the user to add skills to their profile.
   - `S` empty but some unrecognised skills: return no recommendation; explanation lists the unrecognised skills and asks the user to choose from the vocabulary.
   - No missing skills in the nearest occupations (saturated): return no recommendation; explanation says the profile already covers its nearest occupations and suggests reviewing the full occupation list.
3. For every occupation `O`, compute the Jaccard similarity `J(S, O) = |S∩O| / |S∪O|`. The **nearest occupations** are the top `K = 3` by `J` (ties broken by occupation name A→Z).
4. Candidates = union of the nearest occupations' skills, minus `S`.
5. Score each candidate `c` as `mean_k J(S ∪ {c}, O_k) − mean_k J(S, O_k)` (the adjacency gain).
6. Sort by score descending, then skill name A→Z. The primary recommendation is first; `alternatives` are the next 3.
7. **Explanation (Q3: explanation completeness)** must always be non-empty and include: the nearest occupations; how many of each occupation's skills the user already has; why this skill was chosen ("smallest step that brings you closest to…"); the `source` of each nearest occupation; and the disclaimer *"AI-generated suggestion based on published labour-market literature. Not professional career or financial advice."*
8. **Income (DD9).** Version `"A"`: `income_displayed` = income estimate of the nearest occupation that contains the recommended skill (else the first nearest occupation), formatted as `"Estimated <income_estimate> (literature-derived estimate, not financial advice)"`. Return `""` if none exists. Version `"B"`: always `""`. Income is computed *after* ranking and must never influence it.
9. **Pathway (E2: graduated difficulty).** Six modules, each 5 to 10 minutes. Difficulty scale is 1 to 5. Start level: limited = 1, foundational = 2, moderate = 3. The sequence is `start, start, start+1, start+1, start+2, start+2`, capped at 5, so difficulty never rises by more than one level per step. Module IDs: `<skill-slug>_m1` … `_m6`.

Return `{recommended_skill, alternatives, explanation, income_displayed, pathway: [(module_id, difficulty), ...]}`.

### 2. Progress: `progress(state, passed) -> dict`

`state` starts as `{"passes": 0, "fails": 0, "difficulty": <first module difficulty>}`.

- **Pass:** increment `passes`; reset `fails` to 0. **Every 3rd pass awards a milestone** `MS1`, `MS2`, … (**E1: multi-milestone staging**: six passes must give exactly two milestones). After every 2nd pass, difficulty rises by 1 (capped at 5).
- **Fail:** increment `fails`. On the **2nd consecutive failure** (never the 1st), set `revised = True`, lower difficulty by 1 (minimum 1), and reset `fails` to 0 (**Q1: adaptive revision correctness**). The revision explanation should say an easier step was added and why, framed to protect competence (no "you failed" language).

Return `{milestone: "" or "MSn", revised: bool, next_difficulty: int}`.

### 3. Nudge: `should_nudge(days_inactive) -> bool`

Return `True` when `days_inactive >= 2`, otherwise `False` (**Q5: nudge rule correctness**). In the app, send at most one nudge per day. The nudge text should be tied to the user's next milestone, not a generic reminder (Fogg trigger logic).

### 4. Constants

Put `K = 3`, `MODULES = 6`, `MODULES_PER_MILESTONE = 3`, `FAILS_BEFORE_REVISION = 2`, `INACTIVE_DAYS_NUDGE = 2`, and the start levels in `skillpath/config.py` with comments. These must match the constants in `run_synthetic_tests.py` and `analyse_outputs.py`.

---

## `skillpath_adapter.py` (repo root)

Expose `class SkillPathEngine` with exactly this contract (the harness imports it):

```python
class SkillPathEngine:
    def __init__(self, skill_map: "pandas.DataFrame"): ...
    def recommend(self, profile: dict, version: str) -> dict: ...  # keys as above
    def progress(self, state: dict, passed: bool) -> dict: ...     # keys as above
    def should_nudge(self, days_inactive: int) -> bool: ...
```

It must call the real `skillpath.engine` code, not reimplement it.

---

## Tests (`tests/`, pytest)

Write tests for each of the following:

- Jaccard calculation and nearest-occupation tie-breaking.
- Ranking determinism: the same input called 3 times gives identical output (Q2).
- A and B give an identical recommendation, alternatives and pathway; A shows labelled income and B shows none (DD9).
- All three fallback cases return no exception and a non-empty explanation (Q4).
- Every recommendation has an explanation containing the disclaimer (Q3).
- Pathway difficulty steps are all between 0 and +1 (E2).
- Six passes give exactly `MS1` and `MS2` (E1).
- Fail → no revision; fail, fail → revision with lower difficulty; at difficulty 1 the floor holds (Q1).
- `should_nudge`: day 1 false, day 2 true (Q5).
- The engine ignores extra keys such as `target_occupation` if they are accidentally passed.
- **Integration test:** run `python run_synthetic_tests.py tests/fixtures/profiles.csv tests/fixtures/skill_map.csv --app-version test --engine skillpath --out tests/tmp_log.csv`, then run `analyse_outputs.py` on the result, and assert both exit successfully. Use a fixture `profiles.csv` with the full column set (see `templates/profile_specifications_TEMPLATE.csv`) and 3 or 4 fake profiles.

---

## Milestone 2: backend (`api/`, FastAPI + SQLite)

### Endpoints

| method and path | purpose |
|---|---|
| `POST /users` | Create a pseudonymous user (`U` + 6 hex characters) and assign an A/B arm: arm A if the SHA-256 of the user ID is even, else B. Store the arm; allow a `?arm=A\|B` override for the researcher. Record consent (boolean plus timestamp). |
| `GET /vocabulary` | Skills grouped by occupation, for the profile picker. |
| `POST /users/{id}/profile` | Save skills and self-rated competency level. |
| `GET /users/{id}/recommendation` | Call the engine with the user's arm. |
| `POST /users/{id}/pathway/accept` | Accept the recommendation. |
| `POST /users/{id}/pathway/swap` | Swap to an alternative (DD6, autonomy). |
| `POST /users/{id}/pathway/defer` | Defer the recommendation (DD6, autonomy). |
| `POST /users/{id}/modules/{module_id}/result` | Body `{passed: bool}`; calls `progress`. |
| `GET /users/{id}/progress` | Milestones, current module, difficulty. |
| `GET /users/{id}/nudge` | Uses days since last activity. |
| `DELETE /users/{id}` | Deletes every row for that user (POPIA). |
| `GET /admin/export` | Exports the events CSV, protected by a local admin token from `.env`. |

### Event logging

Log events to an `events` table with these columns: `user_id, arm, event_type, timestamp, item_id`.

Event types: `onboarding_complete, assessment_started, assessment_complete, pathway_recommended, pathway_adopted, pathway_swapped, session_start, session_end, module_complete, milestone_reached, roadmap_revised, notification_sent, notification_opened`.

The API must add no logic of its own. All decisions come from the engine.

Write API tests with `httpx`/`TestClient`.

---

## Milestone 3: front end (`app/`)

Build a mobile-first app with **Expo (React Native, TypeScript)** so it runs on a phone via Expo Go and in a browser (`npx expo start --web`). Use a light, accessible design, large tap targets, and keep it low-data (no heavy images).

### Screens

1. **Welcome and consent.** Explain what SkillPath does, what data it stores, that it is a research prototype, and the AI disclaimer. Include a consent checkbox and an 18+ confirmation. Collect no name.
2. **Skills profile.** Searchable picker built from `/vocabulary`, plus a competency self-rating with three plain-language options (limited / foundational / moderate).
3. **Your next skill.** One primary recommendation, shown big. Include a **"Why this skill?"** expandable panel showing the full explanation, nearest occupations and sources. Show income only when the API returns it, styled as a labelled estimate. Offer **Accept / Show alternatives / Not now** buttons.
4. **Pathway.** Six module cards with estimated minutes and a difficulty indicator. Each module has placeholder content (title, 2 to 3 sentence description, optional resource link) loaded from `data/modules.json`, plus **"I completed this"** and **"I struggled with this"** buttons, which report pass and fail.
5. **Progress.** Milestone badges (MS1, MS2), a visible progress bar, and the competence-framed message after a roadmap revision.
6. **Settings.** View my data, delete my data, and the disclaimer.

---

## Documentation

- **`README.md`:** setup, how to run the tests, API, app and harness, plus this exact data-collection command:

  ```
  python prepare_profiles.py profiles.csv data/skill_map.csv --fill-acceptable
  python run_synthetic_tests.py profiles_ready.csv data/skill_map.csv --app-version $(git rev-parse --short HEAD) --engine skillpath
  python analyse_outputs.py profiles_ready.csv test_output_log.csv
  ```

- **`DECISIONS.md`:** a design decision log. For every significant decision, record the date, the decision, the directive it serves (DD1–DD10 below), the alternatives considered and the reason. Pre-fill it with the decisions in this prompt.

- **`TRACEABILITY.md`:** a table mapping each directive to the module, function and test that implements it:

  | ID | Directive |
  |---|---|
  | DD1 | Direction before content |
  | DD2 | Adjacency prioritisation |
  | DD3 | Calibrate difficulty |
  | DD4 | Short units |
  | DD5 | Visible milestones |
  | DD6 | Autonomy |
  | DD7 | Trigger timing |
  | DD8 | Transparency |
  | DD9 | Income as information |
  | DD10 | Measure progression |

- **`AI_USE.md`:** a note that this codebase was developed with the assistance of Claude Code, for the researcher's disclosure annexure.

## Definition of done

- `pytest` passes.
- The integration test runs the real harness against `skillpath_adapter`.
- `run_synthetic_tests.py --engine skillpath` works on the fixture.
- The API and app run locally.
- The README commands work exactly as written.
- `DECISIONS.md` and `TRACEABILITY.md` are complete.
- Everything is committed.

Then give me a short summary of what was built, anything you could not complete, and any place where you had to make an assumption.
