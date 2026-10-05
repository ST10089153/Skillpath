"""SkillPath: adjacency-first next-skill recommender (REIT8419 DSR prototype)."""

from .engine import Engine, SkillMap, default_skill_map_path, progress, recommend, should_nudge

__all__ = ["Engine", "SkillMap", "default_skill_map_path", "progress", "recommend", "should_nudge"]
