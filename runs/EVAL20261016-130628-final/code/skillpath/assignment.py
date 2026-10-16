"""Deterministic A/B arm assignment and nudge-frequency rule (kept out of the API so it holds no logic)."""

import hashlib

from . import config as C
from . import engine


def assign_arm(user_id: str) -> str:
    """Arm A if the SHA-256 of the user ID (as an integer) is even, else B."""
    return "A" if int(hashlib.sha256(user_id.encode("utf-8")).hexdigest(), 16) % 2 == 0 else "B"


def nudge_due(days_inactive: int, already_nudged_today: bool, has_open_pathway: bool = True,
              unopened_nudges: int = 0) -> bool:
    """DD7: nudge after INACTIVE_DAYS_NUDGE days of inactivity, at most once per day, only while the user has
    something to come back to (a recommended, deferred or adopted-but-unfinished pathway; DECISIONS.md #53), and
    not after MAX_UNOPENED_NUDGES consecutive unopened nudges (DECISIONS.md #55)."""
    return (has_open_pathway and engine.should_nudge(days_inactive) and not already_nudged_today
            and unopened_nudges < C.MAX_UNOPENED_NUDGES)


def has_open_pathway(status: str, completed: bool) -> bool:
    """True when a nudge has a purpose: the pathway is recommended or deferred, or adopted and not finished."""
    return status in ("recommended", "deferred") or (status == "adopted" and not completed)
