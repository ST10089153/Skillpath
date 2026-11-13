"""Hosted demo: the web app and the API from one server, on one address.

    uvicorn deploy.server:site --port 10000

The Expo web export (built with EXPO_PUBLIC_API_URL=/api) is served at "/", and the API at "/api".
Demo mode (SKILLPATH_DEMO=1) starts every boot with an empty database, so nothing a visitor enters outlives a restart
and none of it is study data. Admin export stays disabled because SKILLPATH_ADMIN_TOKEN is not set.
"""

import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.environ.setdefault("SKILLPATH_DB", "/tmp/skillpath-demo.db")
WEB = os.environ.get("SKILLPATH_WEB", os.path.join(ROOT, "web"))

if os.environ.get("SKILLPATH_DEMO") == "1":
    for suffix in ("", "-wal", "-shm"):
        try:
            os.remove(DB + suffix)
        except FileNotFoundError:
            pass

from api.main import app as api  # noqa: E402  (imported after the database is reset)

site = FastAPI(title="SkillPath demo", docs_url=None, redoc_url=None, openapi_url=None)
site.mount("/api", api)
site.mount("/", StaticFiles(directory=WEB, html=True), name="web")
