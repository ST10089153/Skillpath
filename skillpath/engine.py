"""SkillPath recommendation engine.

Pure, deterministic rules. The only I/O is loading the skill map (SkillMap.from_csv).
No randomness, no clock, no network. Every tie is broken alphabetically.
All similarity arithmetic uses exact fractions so that equal scores are truly
equal and the alphabetical tie-break is applied rule-exactly.

The engine only ever reads these profile fields:
    competency_level, current_skills   (profile_id, qualification and discipline
                                        are accepted but do not affect the output)
Any other key (e.g. target_occupation) is ignored.
"""

from __future__ import annotations

import csv
import math
import os
import re
from dataclasses import dataclass
from fractions import Fraction

from . import config as C

PROFILE_FIELDS = ("profile_id", "competency_level", "qualification", "discipline", "current_skills")

STATUS_OK = "ok"
STATUS_NO_SKILLS = "no_skills"
STATUS_UNRECOGNISED = "unrecognised_only"
STATUS_SATURATED = "saturated"


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------
def _text(value) -> str:
    """Convert a cell value to text; None and NaN become ''."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value)


def normalise(skill) -> str:
    """Lowercase, trim and collapse internal whitespace."""
    return " ".join(_text(skill).lower().split())


def split_skills(value) -> list[str]:
    """Split a semicolon-separated string into normalised, de-duplicated skills (input order kept)."""
    out: list[str] = []
    for part in _text(value).split(";"):
        s = normalise(part)
        if s and s != "nan" and s not in out:
            out.append(s)
    return out


def slugify(skill: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", normalise(skill)).strip("_")
    return slug or "skill"


def _name_key(name: str):
    """Alphabetical (A->Z) ordering key for occupation names; case-insensitive, then exact."""
    return (name.casefold(), name)


# ---------------------------------------------------------------------------
# Skill map
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Occupation:
    name: str
    skills: frozenset
    income_estimate: str
    source: str


class SkillMap:
    """The researcher's occupation -> essential skills reference table."""

    def __init__(self, rows):
        occupations: dict[str, Occupation] = {}
        for row in rows:
            if "occupation" not in row or "essential_skills" not in row:
                raise ValueError("skill map needs the columns 'occupation' and 'essential_skills'")
            name = " ".join(_text(row["occupation"]).split())
            if not name:
                continue
            if name in occupations:
                raise ValueError(f"skill map contains the occupation '{name}' more than once")
            occupations[name] = Occupation(
                name=name,
                skills=frozenset(split_skills(row["essential_skills"])),
                income_estimate=_text(row.get("income_estimate", "")).strip(),
                source=_text(row.get("source", "")).strip(),
            )
        self.occupations: list[Occupation] = sorted(occupations.values(), key=lambda o: _name_key(o.name))
        self.vocabulary: frozenset = frozenset().union(*(o.skills for o in self.occupations))

    @classmethod
    def from_csv(cls, path: str) -> "SkillMap":
        with open(path, newline="", encoding="utf-8-sig") as f:
            return cls(list(csv.DictReader(f)))

    def by_occupation(self) -> list[dict]:
        """Vocabulary grouped by occupation (for the profile picker)."""
        return [{"occupation": o.name, "skills": sorted(o.skills)} for o in self.occupations]


def default_skill_map_path(root: str | None = None) -> str:
    """data/skill_map.csv if it exists, otherwise the fake development example."""
    root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    real = os.path.join(root, "data", "skill_map.csv")
    return real if os.path.exists(real) else os.path.join(root, "data", "skill_map.example.csv")


# ---------------------------------------------------------------------------
# Recommendation (DD1, DD2, DD8, DD9)
# ---------------------------------------------------------------------------
def jaccard(a, b) -> Fraction:
    """J(A, B) = |A n B| / |A u B| as an exact fraction (0 when both are empty)."""
    a, b = set(a), set(b)
    union = a | b
    return Fraction(len(a & b), len(union)) if union else Fraction(0)


def nearest_occupations(skills, skill_map: SkillMap, k: int = C.K) -> list[tuple[Occupation, Fraction]]:
    """Top k occupations by Jaccard similarity; ties broken by occupation name A->Z.

    Only occupations sharing at least one skill with the profile (J > 0) qualify, so fewer than k
    may be returned. Adjacency-first: never steer towards occupations with no overlap at all
    (DECISIONS.md #34; proposal section 2.6, Autor et al., 2024).
    """
    scored = [(o, j) for o in skill_map.occupations if (j := jaccard(skills, o.skills)) > 0]
    scored.sort(key=lambda t: (-t[1], _name_key(t[0].name)))
    return scored[:k]


def _mean_jaccard(skills, occupations) -> Fraction:
    return sum((jaccard(skills, o.skills) for o in occupations), Fraction(0)) / len(occupations)


def score_candidates(skills, nearest: list[Occupation]) -> list[tuple[str, Fraction]]:
    """Adjacency gain of each missing skill, sorted by gain (desc) then skill name A->Z."""
    skills = set(skills)
    candidates = set().union(*(o.skills for o in nearest)) - skills if nearest else set()
    before = _mean_jaccard(skills, nearest) if nearest else Fraction(0)
    scored = [(c, _mean_jaccard(skills | {c}, nearest) - before) for c in candidates]
    scored.sort(key=lambda t: (-t[1], t[0]))
    return scored


def competency_level(profile: dict) -> str:
    level = normalise(profile.get("competency_level", ""))
    return level if level in C.START_LEVELS else C.DEFAULT_COMPETENCY


def module_minutes(difficulty: int) -> int:
    return min(C.MODULE_MAX_MINUTES, C.MODULE_MIN_MINUTES + (difficulty - C.MIN_DIFFICULTY))


def build_pathway(skill: str, level: str) -> list[tuple[str, int]]:
    """Six modules: start, start, start+1, start+1, start+2, start+2 (capped at MAX_DIFFICULTY)."""
    start = C.START_LEVELS.get(level, C.START_LEVELS[C.DEFAULT_COMPETENCY])
    slug = slugify(skill)
    return [(f"{slug}_m{i + 1}", min(C.MAX_DIFFICULTY, start + i // 2)) for i in range(C.MODULES)]


def _occupation_lines(skills, nearest) -> list[str]:
    lines = ["Your nearest occupations:"]
    for o, _ in nearest:
        held = len(set(skills) & o.skills)
        lines.append(f"- {o.name}: you already have {held} of {len(o.skills)} skills "
                     f"(source: {o.source or 'not recorded'})")
    return lines


def _unrecognised_line(unrecognised: list[str]) -> str:
    return ("Not recognised (ignored): " + ", ".join(unrecognised)
            + ". Choose skills from the SkillPath skills list to include them.")


def _income(version, recommended: str, nearest) -> str:
    """DD9: computed after ranking; never used for ranking. Version B always returns ''."""
    if str(version).strip().upper() != C.INCOME_VISIBLE_VERSION or not nearest:
        return ""
    containing = [o for o, _ in nearest if recommended in o.skills]
    occ = containing[0] if containing else nearest[0][0]
    return C.INCOME_TEMPLATE.format(income=occ.income_estimate) if occ.income_estimate else ""


def _empty_result(status: str, explanation: str, level: str, unrecognised, nearest_info) -> dict:
    return {"recommended_skill": "", "alternatives": [], "explanation": explanation,
            "income_displayed": "", "pathway": [], "status": status, "competency_level": level,
            "unrecognised_skills": unrecognised, "nearest_occupations": nearest_info, "pathway_details": []}


def recommend(profile: dict, version: str, skill_map: SkillMap) -> dict:
    """Recommend the next skill for a profile. Never raises for any profile content.

    Returns the harness keys (recommended_skill, alternatives, explanation,
    income_displayed, pathway) plus display keys used by the API
    (status, competency_level, unrecognised_skills, nearest_occupations, pathway_details).
    """
    profile = profile if isinstance(profile, dict) else {}
    level = competency_level(profile)
    entered = split_skills(profile.get("current_skills", ""))
    skills = {s for s in entered if s in skill_map.vocabulary}
    unrecognised = sorted(s for s in entered if s not in skill_map.vocabulary)

    if not skills and not unrecognised:
        return _empty_result(STATUS_NO_SKILLS, "\n".join([
            "Your skills profile is empty, so SkillPath cannot suggest a next skill yet.",
            "Please add the skills you already have to your profile.",
            C.DISCLAIMER]), level, [], [])

    if not skills:
        return _empty_result(STATUS_UNRECOGNISED, "\n".join([
            "None of the skills you entered are recognised by SkillPath, so it cannot suggest a next skill yet.",
            _unrecognised_line(unrecognised),
            C.DISCLAIMER]), level, unrecognised, [])

    nearest = nearest_occupations(skills, skill_map)
    nearest_info = [{"occupation": o.name, "similarity": round(float(j), 4),
                     "skills_held": len(skills & o.skills), "skills_total": len(o.skills),
                     "source": o.source} for o, j in nearest]
    names = ", ".join(o.name for o, _ in nearest)
    ranked = score_candidates(skills, [o for o, _ in nearest])

    if not ranked:
        lines = [f"Your profile already covers every skill of its nearest occupations ({names}).",
                 "There is no next skill to add from these occupations. "
                 "Review the full occupation list to choose a new direction."]
        lines += _occupation_lines(skills, nearest)
        if unrecognised:
            lines.append(_unrecognised_line(unrecognised))
        lines.append(C.DISCLAIMER)
        return _empty_result(STATUS_SATURATED, "\n".join(lines), level, unrecognised, nearest_info)

    top = ranked[0][0]
    alternatives = [s for s, _ in ranked[1:4]]
    pathway = build_pathway(top, level)
    lines = [f"Recommended next skill: {top}.",
             f"Why this skill? It is the smallest step that brings you closest to your nearest occupations "
             f"({names}): adding it gives the largest average increase in skill overlap with them."]
    lines += _occupation_lines(skills, nearest)
    if unrecognised:
        lines.append(_unrecognised_line(unrecognised))
    lines.append(C.DISCLAIMER)

    return {"recommended_skill": top,
            "alternatives": alternatives,
            "explanation": "\n".join(lines),
            "income_displayed": _income(version, top, nearest),
            "pathway": pathway,
            "status": STATUS_OK,
            "competency_level": level,
            "unrecognised_skills": unrecognised,
            "nearest_occupations": nearest_info,
            "pathway_details": [{"module_id": m, "difficulty": d, "minutes": module_minutes(d)}
                                for m, d in pathway]}


# ---------------------------------------------------------------------------
# Progress (DD3, DD5, DD10)
# ---------------------------------------------------------------------------
REVISION_MESSAGE = ("We've added an easier step to your pathway. Two attempts in a row felt hard, "
                    "which usually means the step was too big, not that you can't do it. "
                    "The easier step builds the same skill at a more comfortable pace.")


def new_state(first_difficulty: int) -> dict:
    return {"passes": 0, "fails": 0, "difficulty": int(first_difficulty)}


def progress(state: dict, passed: bool) -> dict:
    """Advance one module result. Mutates and returns via `state`.

    Pass: passes += 1, fails = 0; every 3rd pass awards MS<n>; every 2nd pass raises
          difficulty by 1 (max MAX_DIFFICULTY).
    Fail: fails += 1; on the 2nd consecutive fail the roadmap is revised: difficulty
          lowered by 1 (min MIN_DIFFICULTY) and fails reset to 0.
    """
    state.setdefault("passes", 0)
    state.setdefault("fails", 0)
    state.setdefault("difficulty", C.START_LEVELS[C.DEFAULT_COMPETENCY])
    out = {"milestone": "", "revised": False, "message": ""}
    if passed:
        state["passes"] += 1
        state["fails"] = 0
        if state["passes"] % C.MODULES_PER_MILESTONE == 0:
            out["milestone"] = f"MS{state['passes'] // C.MODULES_PER_MILESTONE}"
            out["message"] = f"Milestone {out['milestone']} reached. Well done."
        if state["passes"] % C.PASSES_PER_DIFFICULTY_STEP == 0:
            state["difficulty"] = min(C.MAX_DIFFICULTY, state["difficulty"] + 1)
    else:
        state["fails"] += 1
        if state["fails"] >= C.FAILS_BEFORE_REVISION:
            state["difficulty"] = max(C.MIN_DIFFICULTY, state["difficulty"] - 1)
            state["fails"] = 0
            out["revised"] = True
            out["message"] = REVISION_MESSAGE
    out["next_difficulty"] = state["difficulty"]
    return out


# ---------------------------------------------------------------------------
# Nudge (DD7)
# ---------------------------------------------------------------------------
def should_nudge(days_inactive) -> bool:
    try:
        return int(days_inactive) >= C.INACTIVE_DAYS_NUDGE
    except (TypeError, ValueError):
        return False


def nudge_message(passes: int) -> str:
    """Trigger text tied to the user's next milestone (Fogg: a prompt linked to a near goal)."""
    remaining = C.MODULES_PER_MILESTONE - (passes % C.MODULES_PER_MILESTONE)
    next_ms = passes // C.MODULES_PER_MILESTONE + 1
    unit = "module" if remaining == 1 else "modules"
    return f"You're {remaining} short {unit} away from milestone MS{next_ms}. A 5 to 10 minute session gets you closer."


class Engine:
    """Convenience wrapper binding the rules to one skill map."""

    def __init__(self, skill_map: SkillMap):
        self.skill_map = skill_map

    def recommend(self, profile: dict, version: str) -> dict:
        return recommend(profile, version, self.skill_map)

    @staticmethod
    def progress(state: dict, passed: bool) -> dict:
        return progress(state, passed)

    @staticmethod
    def should_nudge(days_inactive) -> bool:
        return should_nudge(days_inactive)
