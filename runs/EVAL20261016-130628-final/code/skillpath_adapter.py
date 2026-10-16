"""Adapter imported by run_synthetic_tests.py (--engine skillpath).

Thin wrapper: converts the harness's pandas DataFrame into a SkillMap and
delegates every decision to skillpath.engine. Returns exactly the contract keys.
"""

from skillpath import engine

RECOMMEND_KEYS = ("recommended_skill", "alternatives", "explanation", "income_displayed", "pathway")
PROGRESS_KEYS = ("milestone", "revised", "next_difficulty")


class SkillPathEngine:
    def __init__(self, skill_map: "pandas.DataFrame"):
        self._engine = engine.Engine(engine.SkillMap(skill_map.to_dict("records")))

    def recommend(self, profile: dict, version: str) -> dict:
        res = self._engine.recommend(profile, version)
        return {k: res[k] for k in RECOMMEND_KEYS}

    def progress(self, state: dict, passed: bool) -> dict:
        res = self._engine.progress(state, passed)
        return {k: res[k] for k in PROGRESS_KEYS}

    def should_nudge(self, days_inactive: int) -> bool:
        return self._engine.should_nudge(days_inactive)
