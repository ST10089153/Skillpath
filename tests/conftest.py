import os

import pytest

from skillpath.engine import Engine, SkillMap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, "tests", "fixtures")
SKILL_MAP_CSV = os.path.join(FIXTURES, "skill_map.csv")
PROFILES_CSV = os.path.join(FIXTURES, "profiles.csv")


@pytest.fixture
def skill_map():
    return SkillMap.from_csv(SKILL_MAP_CSV)


@pytest.fixture
def engine(skill_map):
    return Engine(skill_map)


def profile(skills, level="foundational", **extra):
    p = {"profile_id": "FX", "competency_level": level, "qualification": "fake_qual",
         "discipline": "fake_discipline", "current_skills": skills}
    p.update(extra)
    return p
