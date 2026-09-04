"""Rest-of-season values shrink with the calendar (plan C1).

The field the manager calls `ros` held a SEASON TOTAL at every week, so in
week 14 it valued a free agent for eleven games he could no longer play. The
guard this change needs is a PROPERTY test across weeks, not a single
late-season render: a scale error that only inverts in a band renders fine in
week 14 and is invisible in week 1.
"""

from __future__ import annotations

import pytest

from draftkit.weekly import ros_prorate, weeks_remaining

# a 6-team bracket starting week 15 is three rounds, so week 17 is the title
LAST_WEEK = 17
WEEKS = (1, 8, 14)


# --------------------------------------------------------------- the function

def test_week_one_reproduces_the_season_total_exactly():
    """The acceptance criterion for the whole change: turning it on must not
    move a single week-1 number, or every recorded brief stops comparing."""
    for pts in (0.0, 60.0, 123.4, 300.0):
        assert ros_prorate(pts, 1, LAST_WEEK) == pytest.approx(pts)


def test_it_shrinks_monotonically_and_hits_zero_after_the_title():
    v = [ros_prorate(170.0, w, LAST_WEEK) for w in range(1, 20)]
    assert v == sorted(v, reverse=True)
    assert v[0] == pytest.approx(170.0)
    assert v[LAST_WEEK - 1] == pytest.approx(10.0)      # title week: one week left
    assert v[LAST_WEEK] == 0.0 and v[-1] == 0.0         # nothing left to buy


def test_the_horizon_is_the_championship_week_not_week_eighteen():
    """A week-10 claim is bought for the title. Points scored after the league
    has crowned a winner buy nothing."""
    assert weeks_remaining(10, 17) == 8
    assert weeks_remaining(10, 14) == 5, "a shorter bracket is a shorter horizon"
    assert weeks_remaining(18, 17) == 0


def test_a_shorter_bracket_prices_the_same_player_lower():
    assert ros_prorate(170.0, 10, 14) < ros_prorate(170.0, 10, 17)


# ------------------------------------------------- the property across weeks

def _score(p, week, weights_prorated: bool):
    """The waiver add-score, reproduced at its essentials: a rest-of-season
    value plus flat bonuses. `weights_prorated` is the fix under test."""
    from manager.waiver_brief import W_CONTINGENCY, W_TREND_MAX, W_USAGE

    wl = weeks_remaining(week, LAST_WEEK)
    value = ros_prorate(p["season"], week, LAST_WEEK)
    mult = wl if weights_prorated else 17.0     # 17 = the historical flat value
    return (value
            + (W_CONTINGENCY * mult if p["contingency"] else 0.0)
            + W_TREND_MAX * mult * p["trend"]
            + (W_USAGE * mult if p["usage"] else 0.0))


# A real mid-season add with a role, and the week's most-added name with no
# role behind it. 60 season points is a plausible waiver starter, not a stud:
# the inversion this guards against needs a realistic gap, and an implausibly
# large one would let the flat-weight bug pass.
REAL = {"name": "real add", "season": 60.0, "contingency": False, "trend": 0.0, "usage": True}
HYPE = {"name": "hype", "season": 12.0, "contingency": False, "trend": 1.0, "usage": False}


@pytest.mark.parametrize("week", WEEKS)
def test_a_real_add_outranks_a_trending_worthless_one_at_every_week(week):
    """The failure this test exists for: with the value shrinking and the
    bonuses flat, a trending free agent with no role passes a real add late in
    the season. No week-1 test would catch it."""
    assert _score(REAL, week, True) > _score(HYPE, week, True), (
        f"week {week}: the hype pickup outranked the real add")


def test_the_unfixed_version_actually_inverts_so_the_test_can_fail():
    """A guard that cannot fail guards nothing. With flat bonuses the ranking
    does invert late, which is the defect the prorated weights remove."""
    assert _score(REAL, 1, False) > _score(HYPE, 1, False)
    assert _score(REAL, 14, False) < _score(HYPE, 14, False)


@pytest.mark.parametrize("week", WEEKS)
def test_the_ratio_of_two_bonus_free_candidates_is_stable_across_weeks(week):
    """Prorating must rescale, not reshape. Two candidates with no bonuses
    keep their ratio at every week, so nothing reorders for a reason that is
    only the calendar."""
    a = dict(REAL, usage=False, season=140.0)
    b = dict(REAL, usage=False, season=70.0)
    sa, sb = _score(a, week, True), _score(b, week, True)
    assert sa / sb == pytest.approx(2.0)


def test_the_knob_defaults_on_and_bypasses_cleanly_when_off():
    """This is the repo's one knob that does NOT default to today's behaviour,
    because today's behaviour is no decay at all and no correctly-specified
    knob value reproduces it. So rollback must be exact: knob off takes the
    season total untouched, never a prorate with a neutral argument."""
    import inspect

    import yaml

    from draftkit import briefs
    from draftkit.config import Config

    cfg = Config.load()
    assert (cfg.get("inseason") or {}).get("ros_prorate", {}).get("enabled") is True
    raw = yaml.safe_load((Config.load().root / "config.yaml").read_text(encoding="utf-8"))
    assert raw["inseason"]["ros_prorate"]["enabled"] is True

    # off is a BYPASS, not ros_prorate(..., last_week=week) or similar
    src = inspect.getsource(briefs)
    assert "if prorate_ros else season_ros" in src
    for week in WEEKS[1:]:
        assert ros_prorate(140.0, week, LAST_WEEK) < 140.0


# ------------------------------------------------------ the mixed-scale seam

def test_the_bid_cap_reads_the_season_total_by_name():
    """value_cap stays on the season scale. It ships as a KNOWN inconsistency
    with a name, not a silent one: dollars-equals-points-over-two was always
    dimensionally odd, and prorating it would shrink every late-season ceiling
    on top of a bid model that is unmodelled rather than season-scaled."""
    import inspect

    from draftkit import briefs
    from manager import waiver_brief

    for mod in (briefs, waiver_brief):
        src = inspect.getsource(mod)
        assert 'value_cap=int(c["ros_season"] / 2)' in src or \
               'value_cap=int((p.get("ros_season") or 0) / 2)' in src, \
               f"{mod.__name__}: the bid cap must read ros_season BY NAME"
        assert 'value_cap=int(c["ros"] / 2)' not in src
        assert 'value_cap=int((p.get("ros") or 0) / 2)' not in src


def test_the_pool_filter_stays_on_the_season_rate():
    """Prorating a pool FILTER would empty the pool in week 16, when nobody
    has 60 points left to give."""
    import inspect

    from draftkit import briefs
    src = inspect.getsource(briefs)
    assert 'row["ros_season"] > 60' in src
    assert 'row["ros"] > 60' not in src
