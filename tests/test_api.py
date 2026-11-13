"""API tests (FastAPI TestClient). The API must only store state, call the engine and log events."""

import csv
import io
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from skillpath import assignment

from conftest import SKILL_MAP_CSV

TOKEN = "test-admin-token"


class Clock:
    def __init__(self):
        self.t = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.t

    def advance(self, days):
        self.t += timedelta(days=days)


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def client(tmp_path, clock):
    app = create_app(db_path=str(tmp_path / "t.db"), skill_map_path=SKILL_MAP_CSV, admin_token=TOKEN, clock=clock)
    return TestClient(app)


def new_user(client, arm=None, skills=("skill_a", "skill_b"), level="limited"):
    r = client.post("/users" + (f"?arm={arm}" if arm else ""), json={"consent": True, "age_confirmed": True})
    assert r.status_code == 201
    uid = r.json()["user_id"]
    if skills is not None:
        assert client.post(f"/users/{uid}/profile",
                           json={"skills": list(skills), "competency_level": level}).status_code == 200
    return uid


def events(client):
    rows = list(csv.DictReader(io.StringIO(client.get("/admin/export", headers={"X-Admin-Token": TOKEN}).text)))
    return rows


def test_create_user_pseudonymous_and_arm(client):
    r = client.post("/users", json={"consent": True, "age_confirmed": True}).json()
    assert r["user_id"].startswith("U") and len(r["user_id"]) == 7
    int(r["user_id"][1:], 16)
    assert r["arm"] == assignment.assign_arm(r["user_id"])
    assert r["consent"] is True and r["consent_at"]


def test_arm_assignment_rule():
    import hashlib
    for uid in ["U000000", "U00000A", "UABCDEF", "U123456"]:
        even = int(hashlib.sha256(uid.encode()).hexdigest(), 16) % 2 == 0
        assert assignment.assign_arm(uid) == ("A" if even else "B")


def test_arm_override(client):
    assert client.post("/users?arm=B", json={"consent": True, "age_confirmed": True}).json()["arm"] == "B"
    assert client.post("/users?arm=A", json={"consent": True, "age_confirmed": True}).json()["arm"] == "A"
    assert client.post("/users?arm=C", json={"consent": True, "age_confirmed": True}).status_code == 422


def test_consent_required(client):
    assert client.post("/users", json={"consent": False, "age_confirmed": True}).status_code == 400
    assert client.post("/users", json={"consent": True, "age_confirmed": False}).status_code == 400


def test_vocabulary(client):
    v = client.get("/vocabulary").json()
    assert "skill_a" in v["skills"]
    assert {"occupation": "occ_alpha", "skills": ["skill_a", "skill_b", "skill_c"]} in v["occupations"]
    assert sum(len(c["skills"]) for c in v["categories"]) == len(v["skills"])


def test_recommendation_matches_engine_and_arm(client):
    a, b = new_user(client, "A"), new_user(client, "B")
    ra, rb = client.get(f"/users/{a}/recommendation").json(), client.get(f"/users/{b}/recommendation").json()
    for k in ("recommended_skill", "alternatives", "pathway", "explanation"):
        assert ra[k] == rb[k]
    assert ra["recommended_skill"] == "skill_c"
    assert "estimate" in ra["income_displayed"] and rb["income_displayed"] == ""


def test_recommendation_fallback_empty_profile(client):
    uid = new_user(client, skills=None)
    r = client.get(f"/users/{uid}/recommendation").json()
    assert r["recommended_skill"] == "" and r["explanation"]
    assert client.post(f"/users/{uid}/pathway/accept").status_code == 409


def test_accept_and_full_pathway(client):
    uid = new_user(client, "B")
    client.get(f"/users/{uid}/recommendation")
    p = client.post(f"/users/{uid}/pathway/accept").json()
    assert p["skill"] == "skill_c" and p["total_modules"] == 6 and p["current_module"]["difficulty"] == 1
    milestones = []
    for i in range(6):
        mid = client.get(f"/users/{uid}/progress").json()["current_module"]["module_id"]
        assert mid == f"skill_c_m{i + 1}"
        r = client.post(f"/users/{uid}/modules/{mid}/result", json={"passed": True}).json()
        milestones += [r["milestone"]] if r["milestone"] else []
    prog = client.get(f"/users/{uid}/progress").json()
    assert milestones == ["MS1", "MS2"] and prog["milestones"] == ["MS1", "MS2"] and prog["completed"]
    assert client.post(f"/users/{uid}/modules/skill_c_m6/result", json={"passed": True}).status_code == 409
    types = [e["event_type"] for e in events(client) if e["user_id"] == uid]
    assert types.count("module_complete") == 6 and types.count("milestone_reached") == 2
    assert "pathway_adopted" in types and "pathway_recommended" in types


def test_wrong_module_rejected(client):
    uid = new_user(client)
    client.get(f"/users/{uid}/recommendation")
    client.post(f"/users/{uid}/pathway/accept")
    assert client.post(f"/users/{uid}/modules/skill_c_m3/result", json={"passed": True}).status_code == 409


def test_struggle_revises_after_second_fail(client):
    uid = new_user(client, level="moderate")
    client.get(f"/users/{uid}/recommendation")
    client.post(f"/users/{uid}/pathway/accept")
    first = client.post(f"/users/{uid}/modules/skill_c_m1/result", json={"passed": False}).json()
    second = client.post(f"/users/{uid}/modules/skill_c_m1/result", json={"passed": False}).json()
    assert first["revised"] is False and second["revised"] is True
    assert second["next_difficulty"] == 2 and "easier step" in second["progress"]["message"]
    assert [e["event_type"] for e in events(client)].count("roadmap_revised") == 1


def test_swap_and_defer(client):
    uid = new_user(client)
    rec = client.get(f"/users/{uid}/recommendation").json()
    assert client.post(f"/users/{uid}/pathway/swap", json={"skill": "not_offered"}).status_code == 400
    alt = rec["alternatives"][0]
    p = client.post(f"/users/{uid}/pathway/swap", json={"skill": alt}).json()
    assert p["skill"] == alt and p["modules"][0]["module_id"] == f"{alt}_m1"
    assert client.post(f"/users/{uid}/pathway/defer").json()["status"] == "deferred"
    types = [e["event_type"] for e in events(client)]
    assert "pathway_swapped" in types and "pathway_deferred" in types


def test_nudge_after_two_days_once_per_day(client, clock):
    uid = new_user(client)
    client.get(f"/users/{uid}/recommendation")
    assert client.get(f"/users/{uid}/nudge").json()["nudge"] is False
    clock.advance(1)
    assert client.get(f"/users/{uid}/nudge").json()["nudge"] is False
    clock.advance(1)
    r = client.get(f"/users/{uid}/nudge").json()
    assert r["nudge"] is True and r["days_inactive"] == 2 and "MS1" in r["message"]
    assert client.get(f"/users/{uid}/nudge").json()["nudge"] is False  # at most one per day
    clock.advance(1)
    assert client.get(f"/users/{uid}/nudge").json()["nudge"] is True
    assert [e["event_type"] for e in events(client)].count("notification_sent") == 2


def test_client_events(client):
    uid = new_user(client)
    assert client.post(f"/users/{uid}/events", json={"event_type": "session_start"}).status_code == 201
    assert client.post(f"/users/{uid}/events", json={"event_type": "milestone_reached"}).status_code == 400


def test_delete_my_data(client):
    uid, other = new_user(client), new_user(client)
    client.get(f"/users/{uid}/recommendation")
    client.post(f"/users/{uid}/pathway/accept")
    r = client.delete(f"/users/{uid}").json()
    assert r["deleted"] and r["rows"]["users"] == 1 and r["rows"]["events"] > 0
    assert client.get(f"/users/{uid}").status_code == 404
    assert all(e["user_id"] != uid for e in events(client))
    assert any(e["user_id"] == other for e in events(client))


def test_view_my_data_has_no_personal_identifiers(client):
    uid = new_user(client)
    data = client.get(f"/users/{uid}").json()
    assert not {"name", "email", "phone"} & set(data["user"])


def test_admin_export_requires_token(client):
    new_user(client)
    assert client.get("/admin/export").status_code == 401
    assert client.get("/admin/export", headers={"X-Admin-Token": "wrong"}).status_code == 401
    r = client.get("/admin/export", headers={"X-Admin-Token": TOKEN})
    assert r.status_code == 200 and r.text.splitlines()[0] == "user_id,arm,event_type,timestamp,item_id"


def test_export_disabled_without_token(tmp_path):
    c = TestClient(create_app(db_path=str(tmp_path / "x.db"), skill_map_path=SKILL_MAP_CSV, admin_token=""))
    assert c.get("/admin/export", headers={"X-Admin-Token": ""}).status_code == 503


def test_module_content_has_six_placeholders(client):
    m = client.get("/modules").json()
    assert len(m["default"]) == 6 and all(x["title"] and x["description"] for x in m["default"])


def test_skill_info(client):
    r = client.get("/skills/skill_c").json()
    assert r["skill"] == "skill_c" and r["occupations"] == ["occ_alpha", "occ_gamma"]
    assert client.get("/skills/not_a_skill").status_code == 404


def test_real_skill_descriptions_cover_vocabulary():
    import json
    import os
    from conftest import ROOT
    from skillpath.engine import SkillMap
    sm_path = os.path.join(ROOT, "data", "skill_map.csv")
    desc_path = os.path.join(ROOT, "data", "skill_descriptions.json")
    if not (os.path.exists(sm_path) and os.path.exists(desc_path)):
        pytest.skip("real skill map not built")
    desc = json.load(open(desc_path, encoding="utf-8"))
    assert SkillMap.from_csv(sm_path).vocabulary <= set(desc)


def test_admin_export_all_zip(client):
    import zipfile
    uid = new_user(client)
    client.get(f"/users/{uid}/recommendation")
    assert client.get("/admin/export/all").status_code == 401
    r = client.get("/admin/export/all", headers={"X-Admin-Token": TOKEN})
    assert r.status_code == 200 and r.headers["content-type"] == "application/zip"
    z = zipfile.ZipFile(io.BytesIO(r.content))
    assert {"users.csv", "pathways.csv", "events.csv", "README.txt"} <= set(z.namelist())
    users = z.read("users.csv").decode()
    assert uid in users and "email" not in users.splitlines()[0]


def test_root_points_to_the_app(client):
    r = client.get("/")
    assert r.status_code == 200 and "localhost:8081" in r.text


def test_no_nudge_without_pathway_or_after_completion(client, clock):
    no_rec = new_user(client, skills=None)          # never got a recommendation
    done = new_user(client)
    client.get(f"/users/{done}/recommendation")
    client.post(f"/users/{done}/pathway/accept")
    for _ in range(6):
        mid = client.get(f"/users/{done}/progress").json()["current_module"]["module_id"]
        client.post(f"/users/{done}/modules/{mid}/result", json={"passed": True})
    clock.advance(3)
    assert client.get(f"/users/{no_rec}/nudge").json()["nudge"] is False
    assert client.get(f"/users/{done}/nudge").json()["nudge"] is False


def test_deferred_user_is_nudged(client, clock):
    uid = new_user(client)
    client.get(f"/users/{uid}/recommendation")
    client.post(f"/users/{uid}/pathway/defer")
    clock.advance(2)
    assert client.get(f"/users/{uid}/nudge").json()["nudge"] is True


def test_nudges_stop_after_three_unopened_and_resume_after_return(client, clock):
    uid = new_user(client)
    client.get(f"/users/{uid}/recommendation")
    sent = 0
    for _ in range(10):                     # ten inactive days
        clock.advance(1)
        sent += client.get(f"/users/{uid}/nudge").json()["nudge"]
    assert sent == 3
    client.post(f"/users/{uid}/events", json={"event_type": "session_start"})   # user returns
    clock.advance(2)
    assert client.get(f"/users/{uid}/nudge").json()["nudge"] is True


def test_opening_a_nudge_resets_the_count(client, clock):
    uid = new_user(client)
    client.get(f"/users/{uid}/recommendation")
    clock.advance(2)
    assert client.get(f"/users/{uid}/nudge").json()["nudge"] is True
    client.post(f"/users/{uid}/events", json={"event_type": "notification_opened"})
    user = client.get(f"/users/{uid}").json()["user"]
    assert user["nudges_unopened"] == 0


# --- Marker tools on the hosted demo (SKILLPATH_DEMO=1); absent from the research build -----------------------

@pytest.fixture
def demo_client(tmp_path, clock, monkeypatch):
    monkeypatch.setenv("SKILLPATH_DEMO", "1")
    app = create_app(db_path=str(tmp_path / "d.db"), skill_map_path=SKILL_MAP_CSV, admin_token=TOKEN, clock=clock)
    return TestClient(app)


def test_demo_tools_absent_from_research_build(client):
    uid = new_user(client)
    assert client.post(f"/users/{uid}/demo/arm", json={"arm": "A"}).status_code == 404
    assert client.post(f"/users/{uid}/demo/inactive", json={"days": 2}).status_code == 404


def test_demo_arm_switch_changes_income_not_recommendation(demo_client):
    uid = new_user(demo_client, arm="B")
    b = demo_client.get(f"/users/{uid}/recommendation").json()
    assert demo_client.post(f"/users/{uid}/demo/arm", json={"arm": "A"}).json() == {"arm": "A"}
    a = demo_client.get(f"/users/{uid}/recommendation").json()
    assert a["arm"] == "A" and b["arm"] == "B"
    assert a["recommended_skill"] == b["recommended_skill"] and a["alternatives"] == b["alternatives"]
    assert b["income_displayed"] == ""
    assert demo_client.post(f"/users/{uid}/demo/arm", json={"arm": "C"}).status_code == 422


def test_demo_inactive_triggers_the_real_nudge_rule(demo_client):
    uid = new_user(demo_client)
    demo_client.get(f"/users/{uid}/recommendation")          # open pathway: recommended
    assert demo_client.get(f"/users/{uid}/nudge").json()["nudge"] is False
    assert demo_client.post(f"/users/{uid}/demo/inactive", json={"days": 2}).json() == {"days_inactive": 2}
    n = demo_client.get(f"/users/{uid}/nudge").json()
    assert n["nudge"] is True and n["days_inactive"] == 2 and "milestone" in n["message"]
    assert demo_client.get(f"/users/{uid}/nudge").json()["nudge"] is False   # still at most once a day
    # two more days pass each time: reminders 2 and 3 are sent, then the three-unopened cap stops them
    for expected in (True, True, False):
        demo_client.post(f"/users/{uid}/demo/inactive", json={"days": 2})
        assert demo_client.get(f"/users/{uid}/nudge").json()["nudge"] is expected
    # opening the app (activity) resets the cap
    demo_client.post(f"/users/{uid}/events", json={"event_type": "session_start"})
    demo_client.post(f"/users/{uid}/demo/inactive", json={"days": 2})
    assert demo_client.get(f"/users/{uid}/nudge").json()["nudge"] is True
