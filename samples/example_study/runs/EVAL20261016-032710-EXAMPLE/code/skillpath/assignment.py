"""Deterministic A/B arm assignment and nudge-frequency rule (kept out of the API so it holds no logic)."""

import hashlib

from . import engine


def assign_arm(user_id: str) -> str:
    """Arm A if the SHA-256 of the user ID (as an integer) is even, else B."""
    return "A" if int(hashlib.sha256(user_id.encode("utf-8")).hexdigest(), 16) % 2 == 0 else "B"


def nudge_due(days_inactive: int, already_nudged_today: bool) -> bool:
    """DD7: nudge after INACTIVE_DAYS_NUDGE days of inactivity, at most once per day."""
    return engine.should_nudge(days_inactive) and not already_nudged_today
