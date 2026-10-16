"""SkillPath REST API (Milestone 2).

Wraps skillpath.engine. Holds no recommendation, progress, nudge or arm logic of
its own: it stores state, calls the engine, and logs events to SQLite.

Run:  uvicorn api.main:app --reload   (settings come from .env, see .env.example)
"""

from __future__ import annotations

import csv
import io
import json
import os
import secrets
from datetime import datetime, timezone
from typing import Literal, Optional

import threading

from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from pydantic import BaseModel

from skillpath import assignment, engine

from . import db

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_env(path: str = os.path.join(ROOT, ".env")) -> dict:
    """Minimal KEY=VALUE reader for the local .env (never committed)."""
    env = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------
class NewUser(BaseModel):
    consent: bool
    age_confirmed: bool


class ProfileIn(BaseModel):
    skills: list[str]
    competency_level: Literal["limited", "foundational", "moderate"]


class SwapIn(BaseModel):
    skill: str


class ResultIn(BaseModel):
    passed: bool


class EventIn(BaseModel):
    event_type: str
    item_id: str = ""


def create_app(db_path: Optional[str] = None, skill_map_path: Optional[str] = None,
               admin_token: Optional[str] = None, clock=utcnow, cv_embed=None) -> FastAPI:
    env = {**load_env(), **os.environ}
    db_path = db_path or env.get("SKILLPATH_DB", os.path.join(ROOT, "skillpath.db"))
    skill_map_path = skill_map_path or env.get("SKILLPATH_SKILL_MAP") or engine.default_skill_map_path(ROOT)
    admin_token = admin_token if admin_token is not None else env.get("SKILLPATH_ADMIN_TOKEN", "")
    skill_map = engine.SkillMap.from_csv(skill_map_path)
    modules_path = os.path.join(ROOT, "data", "modules.json")
    descriptions_path = os.path.join(ROOT, "data", "skill_descriptions.json")
    descriptions = {}
    if os.path.exists(descriptions_path):
        with open(descriptions_path, encoding="utf-8") as f:
            descriptions = json.load(f)
    eng = engine.Engine(skill_map)

    extractor = {"obj": None}
    extractor_lock = threading.Lock()

    def get_extractor():
        """Load the local embedding model on first use (about 20 s once; then cached in memory)."""
        with extractor_lock:
            if extractor["obj"] is None:
                from skillpath.cv import CVSkillExtractor
                extractor["obj"] = CVSkillExtractor(skill_map, descriptions, embed=cv_embed)
            return extractor["obj"]

    app = FastAPI(title="SkillPath API", version="0.2.0",
                  description="Research prototype. AI-generated suggestions; not career or financial advice.")
    # Local prototype: the Expo app runs on another origin (web) or device (Expo Go). No cookies are used.
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    def get_conn():
        conn = db.connect(db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def now_iso() -> str:
        return clock().isoformat(timespec="seconds")

    def log(conn, user, event_type: str, item_id: str = ""):
        assert event_type in db.EVENT_TYPES, event_type
        conn.execute("INSERT INTO events (user_id, arm, event_type, timestamp, item_id) VALUES (?,?,?,?,?)",
                     (user["user_id"], user["arm"], event_type, now_iso(), item_id or ""))

    def touch(conn, user_id: str):
        conn.execute("UPDATE users SET last_active_at=?, nudges_unopened=0 WHERE user_id=?", (now_iso(), user_id))

    def get_user(conn, user_id: str):
        user = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        if user is None:
            raise HTTPException(404, "User not found")
        return user

    def get_pathway(conn, user_id: str):
        return conn.execute("SELECT * FROM pathways WHERE user_id=?", (user_id,)).fetchone()

    def profile_of(user) -> dict:
        return {"profile_id": user["user_id"], "competency_level": user["competency_level"] or "",
                "qualification": "", "discipline": "", "current_skills": user["current_skills"] or ""}

    def adopt(conn, user, skill: str, pathway: list):
        state = engine.new_state(pathway[0][1])
        conn.execute("UPDATE pathways SET status='adopted', chosen_skill=?, pathway=?, state=?, milestones='[]', "
                     "last_message='' WHERE user_id=?",
                     (skill, json.dumps(pathway), json.dumps(state), user["user_id"]))

    def progress_view(user_id: str, p) -> dict:
        if p is None or p["status"] != "adopted":
            return {"status": p["status"] if p else "none", "skill": "", "milestones": [], "modules": [],
                    "modules_completed": 0, "total_modules": 0, "current_module": None, "difficulty": None,
                    "message": "", "completed": False}
        pathway, state = json.loads(p["pathway"]), json.loads(p["state"])
        done = state["passes"]
        current = None
        if done < len(pathway):
            mid = pathway[done][0]
            current = {"module_id": mid, "index": done + 1, "difficulty": state["difficulty"],
                       "minutes": engine.module_minutes(state["difficulty"])}
        modules = [{"module_id": m, "difficulty": d, "minutes": engine.module_minutes(d), "done": i < done}
                   for i, (m, d) in enumerate(pathway)]
        return {"status": "adopted", "skill": p["chosen_skill"], "milestones": json.loads(p["milestones"]),
                "modules": modules, "modules_completed": done, "total_modules": len(pathway),
                "current_module": current, "difficulty": state["difficulty"], "message": p["last_message"],
                "completed": done >= len(pathway),
                "next_milestone_message": engine.nudge_message(done) if done < len(pathway) else ""}

    # -----------------------------------------------------------------------
    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def root():
        return ("<!doctype html><title>SkillPath API</title><body style='font-family:sans-serif;max-width:560px;"
                "margin:40px auto;line-height:1.5'><h1>SkillPath API is running</h1><p>This is the engine behind "
                "the app, not the app itself.</p><p><b>Open the app at <a href='http://localhost:8081'>"
                "http://localhost:8081</a></b></p><p>API documentation: <a href='/docs'>/docs</a></p></body>")

    @app.get("/health")
    def health():
        return {"ok": True, "skill_map": os.path.basename(skill_map_path)}

    @app.post("/users", status_code=201)
    def create_user(body: NewUser, arm: Optional[Literal["A", "B"]] = Query(None), conn=Depends(get_conn)):
        if not (body.consent and body.age_confirmed):
            raise HTTPException(400, "Consent and 18+ confirmation are required to use SkillPath")
        while True:
            user_id = "U" + secrets.token_hex(3).upper()
            if conn.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)).fetchone() is None:
                break
        chosen = arm or assignment.assign_arm(user_id)
        ts = now_iso()
        conn.execute("INSERT INTO users (user_id, arm, consent, consent_at, age_confirmed, last_active_at) "
                     "VALUES (?,?,?,?,?,?)", (user_id, chosen, 1, ts, 1, ts))
        user = get_user(conn, user_id)
        log(conn, user, "onboarding_complete")
        return {"user_id": user_id, "arm": chosen, "consent": True, "consent_at": ts}

    @app.get("/modules")
    def module_content():
        """Placeholder module content (title, description, optional resource link) from data/modules.json."""
        with open(modules_path, encoding="utf-8") as f:
            return json.load(f)

    @app.get("/skills/{skill}")
    def skill_info(skill: str):
        """What a skill means, how to show it, demand evidence, and the occupations that need it."""
        key = engine.normalise(skill)
        if key not in skill_map.vocabulary:
            raise HTTPException(404, "Skill not in the SkillPath vocabulary")
        d = descriptions.get(key, {})
        esco_uri = d.get("esco_uri", "")
        return {"skill": key, "label": d.get("label", key), "category": d.get("category", ""),
                "description": d.get("description", ""), "how_to_show": d.get("how_to_show", ""),
                "demand_evidence": d.get("demand_evidence", ""), "demand_source": d.get("demand_source", ""),
                "esco_uri": esco_uri,
                "esco_url": f"https://esco.ec.europa.eu/en/classification/skill?uri={esco_uri}" if esco_uri else "",
                "occupations": [o.name for o in skill_map.occupations if key in o.skills]}

    @app.post("/cv/extract")
    async def cv_extract(file: UploadFile = File(...)):
        """Propose skills found in a CV (PDF, DOCX or TXT) using the local embedding model.

        The file and its text are processed in memory only and never stored or logged (POPIA).
        """
        data = await file.read()
        if len(data) > 5 * 1024 * 1024:
            raise HTTPException(413, "CV file is too large (maximum 5 MB)")
        from skillpath.cv import extract_text
        try:
            text = extract_text(data, file.filename or "")
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception:
            raise HTTPException(400, "Could not read this file. Try a PDF, Word (.docx) or text file.")
        if not text.strip():
            return {"skills": [], "message": "No text found in this file (scanned PDFs are not supported)."}
        found = get_extractor().extract(text)
        return {"skills": [{"skill": d.skill, "score": d.score, "evidence": d.evidence, "method": d.method}
                           for d in found],
                "message": "" if found else "No SkillPath skills were recognised. Add your skills manually."}

    @app.get("/vocabulary")
    def vocabulary():
        """Skills grouped by category (for drop-down pickers) and by occupation."""
        groups: dict[str, list[str]] = {}
        for sk in sorted(skill_map.vocabulary):
            d = descriptions.get(sk, {})
            groups.setdefault(d.get("category") or "Other", []).append(sk)
        labels = {sk: descriptions.get(sk, {}).get("label", sk) for sk in skill_map.vocabulary}
        return {"categories": [{"category": c, "skills": groups[c]} for c in sorted(groups)],
                "labels": labels, "occupations": skill_map.by_occupation(), "skills": sorted(skill_map.vocabulary)}

    @app.get("/users/{user_id}")
    def view_my_data(user_id: str, conn=Depends(get_conn)):
        user = get_user(conn, user_id)
        p = get_pathway(conn, user_id)
        events = [dict(r) for r in conn.execute(
            "SELECT event_type, timestamp, item_id FROM events WHERE user_id=? ORDER BY id", (user_id,))]
        return {"user": dict(user), "pathway": dict(p) if p else None, "events": events}

    @app.post("/users/{user_id}/profile")
    def save_profile(user_id: str, body: ProfileIn, conn=Depends(get_conn)):
        user = get_user(conn, user_id)
        conn.execute("UPDATE users SET current_skills=?, competency_level=? WHERE user_id=?",
                     ("; ".join(body.skills), body.competency_level, user_id))
        touch(conn, user_id)
        log(conn, user, "assessment_complete")
        return {"user_id": user_id, "skills": body.skills, "competency_level": body.competency_level}

    @app.get("/users/{user_id}/recommendation")
    def recommendation(user_id: str, conn=Depends(get_conn)):
        user = get_user(conn, user_id)
        res = eng.recommend(profile_of(user), user["arm"])
        if res["recommended_skill"]:
            p = get_pathway(conn, user_id)
            if p is None:
                conn.execute("INSERT INTO pathways (user_id, status, recommended_skill, alternatives) "
                             "VALUES (?, 'recommended', ?, ?)",
                             (user_id, res["recommended_skill"], json.dumps(res["alternatives"])))
            elif p["status"] != "adopted" or p["recommended_skill"] != res["recommended_skill"]:
                conn.execute("UPDATE pathways SET status='recommended', recommended_skill=?, alternatives=?, "
                             "chosen_skill=NULL, pathway=NULL, state=NULL WHERE user_id=?",
                             (res["recommended_skill"], json.dumps(res["alternatives"]), user_id))
            log(conn, user, "pathway_recommended", res["recommended_skill"])
        touch(conn, user_id)
        return {**res, "arm": user["arm"]}

    @app.post("/users/{user_id}/pathway/accept")
    def accept(user_id: str, conn=Depends(get_conn)):
        user = get_user(conn, user_id)
        p = get_pathway(conn, user_id)
        if p is None:
            raise HTTPException(409, "Get a recommendation first")
        res = eng.recommend(profile_of(user), user["arm"])
        adopt(conn, user, res["recommended_skill"], res["pathway"])
        touch(conn, user_id)
        log(conn, user, "pathway_adopted", res["recommended_skill"])
        return progress_view(user_id, get_pathway(conn, user_id))

    @app.post("/users/{user_id}/pathway/swap")
    def swap(user_id: str, body: SwapIn, conn=Depends(get_conn)):
        user = get_user(conn, user_id)
        p = get_pathway(conn, user_id)
        if p is None:
            raise HTTPException(409, "Get a recommendation first")
        alternatives = json.loads(p["alternatives"])
        if body.skill not in alternatives:
            raise HTTPException(400, f"Choose one of the alternatives: {alternatives}")
        adopt(conn, user, body.skill, engine.build_pathway(body.skill, engine.competency_level(profile_of(user))))
        touch(conn, user_id)
        log(conn, user, "pathway_swapped", body.skill)
        return progress_view(user_id, get_pathway(conn, user_id))

    @app.post("/users/{user_id}/pathway/defer")
    def defer(user_id: str, conn=Depends(get_conn)):
        user = get_user(conn, user_id)
        p = get_pathway(conn, user_id)
        if p is None:
            raise HTTPException(409, "Get a recommendation first")
        conn.execute("UPDATE pathways SET status='deferred' WHERE user_id=?", (user_id,))
        touch(conn, user_id)
        log(conn, user, "pathway_deferred", p["recommended_skill"])
        return {"status": "deferred", "message": "No problem. Your recommendation will be here when you're ready."}

    @app.post("/users/{user_id}/modules/{module_id}/result")
    def module_result(user_id: str, module_id: str, body: ResultIn, conn=Depends(get_conn)):
        user = get_user(conn, user_id)
        p = get_pathway(conn, user_id)
        view = progress_view(user_id, p)
        if view["status"] != "adopted":
            raise HTTPException(409, "Accept a pathway first")
        if view["current_module"] is None:
            raise HTTPException(409, "Pathway already completed")
        if module_id != view["current_module"]["module_id"]:
            raise HTTPException(409, f"Current module is {view['current_module']['module_id']}")
        state = json.loads(p["state"])
        out = eng.progress(state, body.passed)
        milestones = json.loads(p["milestones"]) + ([out["milestone"]] if out["milestone"] else [])
        conn.execute("UPDATE pathways SET state=?, milestones=?, last_message=? WHERE user_id=?",
                     (json.dumps(state), json.dumps(milestones), out["message"], user_id))
        touch(conn, user_id)
        if body.passed:
            log(conn, user, "module_complete", module_id)
        if out["milestone"]:
            log(conn, user, "milestone_reached", out["milestone"])
        if out["revised"]:
            log(conn, user, "roadmap_revised", module_id)
        return {**out, "progress": progress_view(user_id, get_pathway(conn, user_id))}

    @app.get("/users/{user_id}/progress")
    def get_progress(user_id: str, conn=Depends(get_conn)):
        get_user(conn, user_id)
        return progress_view(user_id, get_pathway(conn, user_id))

    @app.get("/users/{user_id}/nudge")
    def nudge(user_id: str, conn=Depends(get_conn)):
        user = get_user(conn, user_id)
        today = clock().date()
        days = (today - datetime.fromisoformat(user["last_active_at"]).date()).days
        p = get_pathway(conn, user_id)
        view = progress_view(user_id, p)
        open_pathway = p is not None and assignment.has_open_pathway(p["status"], view["completed"])
        due = assignment.nudge_due(days, user["last_nudge_date"] == today.isoformat(), open_pathway,
                                   user["nudges_unopened"])
        message = ""
        if due:
            passes = json.loads(p["state"])["passes"] if p["state"] else 0
            message = engine.nudge_message(passes)
            conn.execute("UPDATE users SET last_nudge_date=?, nudges_unopened=nudges_unopened+1 WHERE user_id=?",
                         (today.isoformat(), user_id))
            log(conn, user, "notification_sent")
        return {"nudge": due, "days_inactive": days, "message": message}

    @app.post("/users/{user_id}/events", status_code=201)
    def client_event(user_id: str, body: EventIn, conn=Depends(get_conn)):
        user = get_user(conn, user_id)
        if body.event_type not in db.CLIENT_EVENT_TYPES:
            raise HTTPException(400, f"event_type must be one of {sorted(db.CLIENT_EVENT_TYPES)}")
        if body.event_type in ("session_start", "notification_opened"):
            touch(conn, user_id)
        log(conn, user, body.event_type, body.item_id)
        return {"logged": body.event_type}

    @app.delete("/users/{user_id}")
    def delete_user(user_id: str, conn=Depends(get_conn)):
        get_user(conn, user_id)
        counts = {t: conn.execute(f"DELETE FROM {t} WHERE user_id=?", (user_id,)).rowcount
                  for t in ("events", "pathways", "users")}
        return {"deleted": True, "rows": counts}

    def require_admin(token: str):
        if not admin_token:
            raise HTTPException(503, "Set SKILLPATH_ADMIN_TOKEN in .env to enable the export")
        if not secrets.compare_digest(token, admin_token):
            raise HTTPException(401, "Invalid admin token")

    @app.get("/admin/export/all")
    def export_all(x_admin_token: str = Header(""), conn=Depends(get_conn)):
        """ZIP of every table (users, pathways, events) as CSV, plus a README. Pseudonymous IDs only."""
        require_admin(x_admin_token)
        import zipfile
        buf = io.BytesIO()
        stamp = clock().strftime("%Y%m%d-%H%M%S")
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for table in ("users", "pathways", "events"):
                cur = conn.execute(f"SELECT * FROM {table} ORDER BY rowid")
                out = io.StringIO()
                w = csv.writer(out)
                w.writerow([c[0] for c in cur.description])
                w.writerows(list(r) for r in cur)
                z.writestr(f"{table}.csv", out.getvalue())
            z.writestr("README.txt", f"SkillPath app data export {stamp}. Pseudonymous IDs only; no names, emails or "
                                     f"phone numbers are collected. Tables: users, pathways, events. Event types: "
                                     f"{', '.join(sorted(db.EVENT_TYPES))}." + os.linesep)
        return Response(buf.getvalue(), media_type="application/zip",
                        headers={"Content-Disposition": f"attachment; filename=skillpath_export_{stamp}.zip"})

    @app.get("/admin/export", response_class=PlainTextResponse)
    def export(x_admin_token: str = Header(""), conn=Depends(get_conn)):
        require_admin(x_admin_token)
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(db.EXPORT_COLUMNS)
        for r in conn.execute(f"SELECT {', '.join(db.EXPORT_COLUMNS)} FROM events ORDER BY id"):
            w.writerow(list(r))
        return PlainTextResponse(buf.getvalue(), media_type="text/csv",
                                 headers={"Content-Disposition": "attachment; filename=events.csv"})

    return app


app = create_app()
