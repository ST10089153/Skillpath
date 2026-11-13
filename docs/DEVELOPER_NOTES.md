# Notes for developers

Read this before changing the app. The research report describes this prototype, so some parts must not move.

## Do not change

- **The engine and the evaluation.** Nothing in `skillpath/` that the evaluation uses, and none of `run_synthetic_tests.py`, `analyse_outputs.py`, `prepare_profiles.py`, their CSV columns or the thresholds in `analyse_outputs.py`. The report's results come from the tagged build `v1.0-eval`.
- **What the engine reads.** It must never read `target_occupation`, `acceptable_recommendations`, `designed_to_test`, `employment_goal` or `is_edge_case`.
- **The phone layout.** Figures 8 to 11 in the report are 390 px phone screenshots. Any change that alters the phone screens makes those figures wrong. See "Checking the phone screens" below.
- **No secrets in the repository**, and no signed ethics documents.

## Wording

The report calls them *steps* and a *pathway*. The engine's reminder text still says "modules"; `App.tsx` rewords it on screen so the evaluated engine code stays untouched. Keep the app's wording in line with the report (decision #78).

## Layout: phones and wide screens

- `useWide()` in `app/src/ui.tsx` is true from 960 px. Below that, every screen renders its original phone layout.
- Each screen returns early with its own wide layout (`if (wide) return ...`). Change the wide branch freely; leave the phone branch alone unless the report figures are being redone too.
- Wide layouts lead with the screen's main task (where you are, the decision, the current step), then the supporting detail.
- Building blocks for wide screens:
  - `Panel` is an open section: a label over a hairline, no box. Use `raised` only for the one thing a user acts on (the current step, the consent). Avoid rows of cards.
  - `Summary` is a quiet strip of label and value pairs. Use it instead of number tiles. Do not bring back large display figures for counts.
  - `Grid` gives equal columns with a gap.
- Display type (Bebas Neue) is for headings only, not for numbers or IDs.

## Checking the phone screens

The claims walkthrough (37 report claims) drives the app at 390 px and saves a screenshot per screen. Compare the screenshots before and after a change: everything should be pixel-identical apart from per-run random data (user ID, income version, timestamps). Joining text differently can shift pixels: write `{`• ${t}`}`, not `• {t}`.

To redo the report figures from the research build (not the demo), run `scripts/capture_screens.py`, then `scripts/refresh_report_figures.py IN.docx OUT.docx`. The second script swaps only the four images.

## The hosted demo

- `https://skillpath-demo.onrender.com` runs the demo build (`SKILLPATH_DEMO=1`, `EXPO_PUBLIC_DEMO=1`) on Render's free plan; see `DEPLOY.md`. Every push to `main` redeploys it. Put `[skip render]` in the commit message for changes that should not redeploy.
- The database is emptied whenever the server restarts: after about 15 minutes without visitors, and after each deploy. The app handles this by returning to Welcome with a short note (decision #80); keep that working.
- Settings has demo-only "For markers" tools (income version A/B, simulate two inactive days). They exist only in demo mode and return 404 in the research build. Don't add them to the research build.
- Admin export is disabled in the demo because no admin token is set.

## Future work that is deliberately absent

The report lists these as future work, so the app must not have them: a goal input, reminders that adapt to the learner's rhythm, and task submission.

## Decision log

Record every change that affects the design or the study in `DECISIONS.md`, with the date, the reason and the alternative considered.
