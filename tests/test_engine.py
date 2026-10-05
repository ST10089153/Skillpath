"""Unit tests for skillpath.engine. Each test names the evaluation metric / directive it covers.

Fixture: tests/fixtures/skill_map.csv (fake occupations occ_alpha ... occ_epsilon).
For S = {skill_a, skill_b}:
    J(alpha) = J(beta) = 2/3, J(gamma) = J(delta) = J(epsilon) = 0
    nearest = alpha, beta (tie, A->Z), delta (0-tie, A->Z before epsilon, gamma)
    gains: skill_c = skill_d = 1/18, skill_x = skill_y = -1/36
"""

import os
from fractions import Fraction

import pytest

from skillpath import config as C
from skillpath.engine import (Engine, SkillMap, build_pathway, jaccard, nearest_occupations, normalise,
                              score_candidates, slugify, split_skills)

from conftest import ROOT, SKILL_MAP_CSV, profile


# --- Jaccard and nearest occupations (DD2) --------------------------------
def test_jaccard_values():
    assert jaccard({"a", "b"}, {"a", "b", "c"}) == Fraction(2, 3)
    assert jaccard({"a"}, {"b"}) == 0
    assert jaccard(set(), set()) == 0
    assert jaccard({"a", "b"}, {"a", "b"}) == 1


def test_nearest_occupations_ties_broken_alphabetically(skill_map):
    near = nearest_occupations({"skill_a", "skill_b"}, skill_map)
    assert [o.name for o, _ in near] == ["occ_alpha", "occ_beta", "occ_delta"]
    assert [j for _, j in near] == [Fraction(2, 3), Fraction(2, 3), 0]


def test_nearest_ties_independent_of_row_order():
    rows = [{"occupation": n, "essential_skills": "s1; s2"} for n in ["zeta", "Alpha", "mid"]]
    near = nearest_occupations({"s1"}, SkillMap(rows))
    assert [o.name for o, _ in near] == ["Alpha", "mid", "zeta"]


def test_candidate_scores_and_tie_break(skill_map):
    near = [o for o, _ in nearest_occupations({"skill_a", "skill_b"}, skill_map)]
    ranked = score_candidates({"skill_a", "skill_b"}, near)
    assert ranked == [("skill_c", Fraction(1, 18)), ("skill_d", Fraction(1, 18)),
                      ("skill_x", Fraction(-1, 36)), ("skill_y", Fraction(-1, 36))]


def test_recommendation_and_alternatives(engine):
    res = engine.recommend(profile("skill_a; skill_b"), "B")
    assert res["recommended_skill"] == "skill_c"
    assert res["alternatives"] == ["skill_d", "skill_x", "skill_y"]


# --- Normalisation --------------------------------------------------------
def test_normalisation():
    assert normalise("  Multi   WORD skill ") == "multi word skill"
    assert split_skills(" Skill_A ;SKILL_B; ;skill_a") == ["skill_a", "skill_b"]
    assert split_skills(float("nan")) == []
    assert slugify("Multi word skill!") == "multi_word_skill"


def test_messy_input_matches_clean_input(engine):
    assert engine.recommend(profile(" SKILL_A ;  skill_b "), "A") == engine.recommend(profile("skill_a; skill_b"), "A")


def test_unrecognised_skills_listed(engine):
    res = engine.recommend(profile("skill_a; skill_b; foo bar"), "B")
    assert res["recommended_skill"] == "skill_c"
    assert "Not recognised" in res["explanation"] and "foo bar" in res["explanation"]


# --- Q2 determinism -------------------------------------------------------
@pytest.mark.parametrize("version", ["A", "B"])
def test_ranking_is_deterministic(engine, version):
    outs = [engine.recommend(profile("skill_a; skill_b", "limited"), version) for _ in range(3)]
    assert outs[0] == outs[1] == outs[2]


def test_fresh_engines_give_identical_output():
    a = Engine(SkillMap.from_csv(SKILL_MAP_CSV)).recommend(profile("skill_a; skill_b"), "A")
    b = Engine(SkillMap.from_csv(SKILL_MAP_CSV)).recommend(profile("skill_b; skill_a"), "A")
    assert a == b


# --- DD9 income as information --------------------------------------------
@pytest.mark.parametrize("skills", ["skill_a; skill_b", "skill_e; skill_f", "skill_x", "multi word skill; skill_c"])
def test_versions_a_and_b_differ_only_in_income(engine, skills):
    a, b = engine.recommend(profile(skills), "A"), engine.recommend(profile(skills), "B")
    for k in ("recommended_skill", "alternatives", "pathway", "explanation"):
        assert a[k] == b[k]
    assert b["income_displayed"] == ""


def test_version_a_shows_labelled_income(engine):
    a = engine.recommend(profile("skill_a; skill_b"), "A")
    # skill_c is in occ_alpha (R1), the first nearest occupation containing it
    assert a["income_displayed"] == "Estimated R1 per month (fake) (literature-derived estimate, not financial advice)"
    assert "estimate" in a["income_displayed"].lower()


def test_version_a_empty_when_no_income_recorded(engine):
    a = engine.recommend(profile("skill_e; skill_f"), "A")
    assert a["recommended_skill"] == "skill_c"  # contained first in occ_gamma, which has no income
    assert a["income_displayed"] == ""


# --- Q4 fallbacks ---------------------------------------------------------
FALLBACKS = {
    "empty": ("", "add the skills"),
    "unrecognised": ("not_a_skill; another unknown", "not_a_skill"),
    "saturated": ("skill_a; skill_b; skill_c; skill_d; skill_x; skill_y", "already covers"),
}


@pytest.mark.parametrize("case", FALLBACKS)
@pytest.mark.parametrize("version", ["A", "B"])
def test_fallbacks_never_raise_and_explain(engine, case, version):
    skills, phrase = FALLBACKS[case]
    res = engine.recommend(profile(skills), version)
    assert res["recommended_skill"] == "" and res["alternatives"] == [] and res["pathway"] == []
    assert res["income_displayed"] == ""
    assert res["explanation"].strip() and phrase in res["explanation"]
    assert C.DISCLAIMER in res["explanation"]


def test_saturated_suggests_full_occupation_list(engine):
    res = engine.recommend(profile(FALLBACKS["saturated"][0]), "B")
    assert res["status"] == "saturated" and "full occupation list" in res["explanation"]


@pytest.mark.parametrize("bad", [{}, {"current_skills": None}, {"current_skills": float("nan")},
                                 {"current_skills": 12345, "competency_level": None}, None])
def test_malformed_profiles_do_not_raise(engine, bad):
    res = engine.recommend(bad, "A")
    assert res["explanation"]


# --- Q3 explanation completeness ------------------------------------------
@pytest.mark.parametrize("skills", ["skill_a; skill_b", "skill_e; skill_f", "skill_x", "multi word skill"])
def test_explanation_complete(engine, skills):
    res = engine.recommend(profile(skills), "A")
    exp = res["explanation"]
    assert res["recommended_skill"]
    assert C.DISCLAIMER in exp
    assert "smallest step that brings you closest to" in exp
    for occ in res["nearest_occupations"]:
        assert occ["occupation"] in exp
        assert f"you already have {occ['skills_held']} of {occ['skills_total']} skills" in exp
        assert occ["source"] in exp


# --- E2 graduated difficulty ----------------------------------------------
@pytest.mark.parametrize("level,expected", [("limited", [1, 1, 2, 2, 3, 3]),
                                            ("foundational", [2, 2, 3, 3, 4, 4]),
                                            ("moderate", [3, 3, 4, 4, 5, 5]),
                                            ("edge", [2, 2, 3, 3, 4, 4]),
                                            ("", [2, 2, 3, 3, 4, 4])])
def test_pathway_difficulties(engine, level, expected):
    res = engine.recommend(profile("skill_a; skill_b", level), "B")
    diffs = [d for _, d in res["pathway"]]
    assert diffs == expected
    assert all(0 <= b - a <= 1 for a, b in zip(diffs, diffs[1:]))
    assert all(C.MIN_DIFFICULTY <= d <= C.MAX_DIFFICULTY for d in diffs)


def test_pathway_module_ids_and_minutes(engine):
    res = engine.recommend(profile("skill_c; skill_e", "moderate"), "B")
    assert [m for m, _ in res["pathway"]] == [f"{slugify(res['recommended_skill'])}_m{i}" for i in range(1, 7)]
    assert len(res["pathway"]) == C.MODULES
    assert all(5 <= m["minutes"] <= 10 for m in res["pathway_details"])


def test_pathway_capped_at_max():
    assert max(d for _, d in build_pathway("x", "moderate")) == C.MAX_DIFFICULTY


# --- Oracle isolation -----------------------------------------------------
class GuardedProfile(dict):
    FORBIDDEN = {"target_occupation", "acceptable_recommendations", "designed_to_test",
                 "employment_goal", "is_edge_case"}

    def __getitem__(self, k):
        if k in self.FORBIDDEN:
            raise AssertionError(f"engine read {k}")
        return super().__getitem__(k)

    def get(self, k, default=None):
        if k in self.FORBIDDEN:
            raise AssertionError(f"engine read {k}")
        return super().get(k, default)


def test_engine_ignores_and_never_reads_oracle_keys(engine):
    extra = dict(target_occupation="occ_delta", acceptable_recommendations="skill_x",
                 designed_to_test="anything", employment_goal="pivot", is_edge_case="Y")
    guarded = GuardedProfile(profile("skill_a; skill_b", **extra))
    for v in ("A", "B"):
        assert engine.recommend(guarded, v) == engine.recommend(profile("skill_a; skill_b"), v)


# --- Skill map validation -------------------------------------------------
def test_duplicate_occupation_rejected():
    with pytest.raises(ValueError):
        SkillMap([{"occupation": "x", "essential_skills": "a"}, {"occupation": "x", "essential_skills": "b"}])


def test_example_skill_map_loads():
    sm = SkillMap.from_csv(os.path.join(ROOT, "data", "skill_map.example.csv"))
    assert len(sm.occupations) == 4
