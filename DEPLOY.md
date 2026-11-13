# Hosted demo on Render

A public demo of SkillPath for supervisors and markers, online even when your computer is off.

- One address serves the app (`/`) and the API (`/api`), from `Dockerfile` and `deploy/server.py`.
- Demo mode shows "Public demo for supervisors and markers. Not part of the study." on every screen, uses honest
  privacy text, and starts every boot with an empty database. Nothing entered there is study data.
- Admin export is switched off (no `SKILLPATH_ADMIN_TOKEN` is set).
- Free plan: the site sleeps after about 15 minutes without visitors; the next visit takes about a minute to wake it.
  Memory peaks at about 250 MB of the 512 MB allowed (the CV reader runs single-threaded, set in the Dockerfile).

## First deploy (about 10 minutes, once)

1. Push this repository to GitHub (it is already at `ST10089153/Skillpath`).
2. Go to <https://render.com> and sign up with **GitHub** (free; no card needed for the free plan).
3. When Render asks, give it access to the **Skillpath** repository only.
4. In the Render dashboard choose **New > Blueprint**, pick the **Skillpath** repository and click **Apply**.
   Render reads `render.yaml` and creates a free web service called `skillpath-demo`.
5. Wait for the first build (5 to 10 minutes). When it shows **Live**, the address is at the top of the page,
   for example `https://skillpath-demo.onrender.com`. Share that link.

## Updating the demo

Every push to `main` redeploys automatically. Nothing else to do.

## Checking it

- `https://<your-address>/api/health` should return `{"ok":true,...}`.
- The **Logs** tab in Render shows each request and any errors.

## Run the same demo locally

```powershell
cd app
$env:EXPO_PUBLIC_API_URL="/api"; $env:EXPO_PUBLIC_DEMO="1"; npx.cmd expo export --platform web --output-dir dist
cd ..
$env:SKILLPATH_DEMO="1"; $env:SKILLPATH_WEB="app\dist"; $env:SKILLPATH_DB="$env:TEMP\skillpath-demo.db"
.venv\Scripts\python -m uvicorn deploy.server:site --port 10000
```

Then open <http://localhost:10000>.
