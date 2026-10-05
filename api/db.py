"""Local SQLite storage. Pseudonymous IDs only: no names, emails or phone numbers are stored."""

import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id          TEXT PRIMARY KEY,
    arm              TEXT NOT NULL,
    consent          INTEGER NOT NULL,
    consent_at       TEXT NOT NULL,
    age_confirmed    INTEGER NOT NULL,
    competency_level TEXT,
    current_skills   TEXT,
    last_active_at   TEXT NOT NULL,
    last_nudge_date  TEXT
);
CREATE TABLE IF NOT EXISTS pathways (
    user_id           TEXT PRIMARY KEY REFERENCES users(user_id),
    status            TEXT NOT NULL,          -- recommended | adopted | deferred
    recommended_skill TEXT NOT NULL,
    alternatives      TEXT NOT NULL,          -- JSON list
    chosen_skill      TEXT,
    pathway           TEXT,                   -- JSON list of [module_id, difficulty]
    state             TEXT,                   -- JSON engine progress state
    milestones        TEXT NOT NULL DEFAULT '[]',
    last_message      TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    TEXT NOT NULL,
    arm        TEXT NOT NULL,
    event_type TEXT NOT NULL,
    timestamp  TEXT NOT NULL,
    item_id    TEXT NOT NULL DEFAULT ''
);
"""

EVENT_TYPES = {
    "onboarding_complete", "assessment_started", "assessment_complete", "pathway_recommended",
    "pathway_adopted", "pathway_swapped", "pathway_deferred", "session_start", "session_end",
    "module_complete", "milestone_reached", "roadmap_revised", "notification_sent", "notification_opened",
}
# Events the app may report itself (everything else is logged by the server).
CLIENT_EVENT_TYPES = {"assessment_started", "session_start", "session_end", "notification_opened"}
EXPORT_COLUMNS = ["user_id", "arm", "event_type", "timestamp", "item_id"]


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn
