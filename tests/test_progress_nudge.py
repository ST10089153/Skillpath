"""Progress (E1, Q1) and nudge (Q5) rules."""

import pytest

from skillpath import config as C
from skillpath.engine import nudge_message, progress, should_nudge


def state(d=2):
    return {"passes": 0, "fails": 0, "difficulty": d}


# --- E1 multi-milestone staging -------------------------------------------
def test_six_passes_give_exactly_ms1_and_ms2():
    st = state(1)
    outs = [progress(st, True) for _ in range(6)]
    assert [o["milestone"] for o in outs] == ["", "", "MS1", "", "", "MS2"]
    assert [o["milestone"] for o in outs if o["milestone"]] == ["MS1", "MS2"]
    assert not any(o["revised"] for o in outs)


def test_difficulty_rises_every_second_pass_and_caps():
    st = state(1)
    assert [progress(st, True)["next_difficulty"] for _ in range(6)] == [1, 2, 2, 3, 3, 4]
    st = state(4)
    assert [progress(st, True)["next_difficulty"] for _ in range(6)] == [4, 5, 5, 5, 5, 5]


# --- Q1 adaptive revision -------------------------------------------------
def test_single_fail_does_not_revise():
    st = state(3)
    o = progress(st, False)
    assert o["revised"] is False and o["next_difficulty"] == 3


def test_two_consecutive_fails_revise_and_lower_difficulty():
    st = state(3)
    first, second = progress(st, False), progress(st, False)
    assert first["revised"] is False
    assert second["revised"] is True and second["next_difficulty"] == 2
    assert st["fails"] == 0
    assert "easier step" in second["message"] and "fail" not in second["message"].lower()


def test_revision_floor_holds_at_one():
    st = state(1)
    progress(st, False)
    o = progress(st, False)
    assert o["revised"] is True and o["next_difficulty"] == C.MIN_DIFFICULTY


def test_pass_resets_consecutive_fails():
    st = state(3)
    progress(st, False)
    progress(st, True)
    assert progress(st, False)["revised"] is False


def test_harness_struggle_script():
    st = state(2)
    outs = [progress(st, p) for p in (False, False, True)]
    assert [o["revised"] for o in outs] == [False, True, False]
    assert outs[1]["next_difficulty"] == 1


# --- Q5 nudge rule --------------------------------------------------------
@pytest.mark.parametrize("days,expected", [(0, False), (1, False), (2, True), (3, True), (4, True)])
def test_should_nudge(days, expected):
    assert should_nudge(days) is expected


def test_nudge_message_tied_to_next_milestone():
    assert "MS1" in nudge_message(0) and "3 short modules" in nudge_message(0)
    assert "MS2" in nudge_message(5) and "1 short module " in nudge_message(5)
