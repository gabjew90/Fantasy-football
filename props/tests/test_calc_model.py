"""props/calc calculator and card: the draws, the searches, the round trip,
and a card rendered from a synthetic player (no network)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from props.calc import calc, card, odds, player, settings  # noqa: E402

SIMS, SEED = 20000, 20261010
# A stand-in for real RB carries: right-skewed like them, centred on zero.
_rng = np.random.default_rng(1)
RESID = _rng.gamma(1.2, 3.6, 50000) - 2.0
RESID = RESID - RESID.mean()


def rush_model(ypc=4.0, r=16, sd=0.15):
    return calc.Model("rush_yds", "carries", calc.make_draws("carries", r, SIMS, SEED), ypc, RESID, sd)


def rec_model(rate=0.7, r=8):
    return calc.Model("receptions", "targets", calc.make_draws("targets", r, SIMS, SEED), rate)


def test_counts_have_the_negative_binomial_mean_and_spread():
    d = calc.make_draws("carries", 16, SIMS, SEED)
    n = calc.counts(d, 18.0, calc.MAX_COUNT["carries"])
    assert n.mean() == pytest.approx(18.0, rel=0.02)
    assert n.var() == pytest.approx(18 + 18 ** 2 / 16, rel=0.06)


def test_poisson_inverse_is_increasing_in_the_mean():
    u = np.linspace(0.01, 0.99, 99)
    a = calc.poisson_inverse(u, np.full(99, 10.0), 60)
    b = calc.poisson_inverse(u, np.full(99, 10.5), 60)
    assert (b >= a).all() and a.mean() == pytest.approx(10, abs=0.3)


def test_the_day_factor_has_mean_one_and_the_set_spread():
    f = calc.day_factor(calc.make_draws("carries", 16, SIMS, SEED), 0.15)
    assert f.mean() == pytest.approx(1.0, abs=0.005) and f.std() == pytest.approx(0.15, abs=0.005)


def test_the_same_inputs_give_the_same_numbers():
    assert rush_model().chance_over(64.5, 17.0) == rush_model().chance_over(64.5, 17.0)


def test_chance_rises_with_workload_and_rate():
    m = rush_model()
    ch = [m.chance_over(64.5, w) for w in (10, 14, 18, 22, 26)]
    assert ch == sorted(ch) and ch[0] < 0.2 < 0.8 < ch[-1]
    assert m.chance_over(64.5, 17, rate=4.5) > m.chance_over(64.5, 17, rate=3.5)


def test_needed_workloads_bracket_book_expects_and_round_trip():
    m = rush_model()
    mo, mu = odds.multiplier_from_american(-125), odds.multiplier_from_american(-132)
    over = calc.workload_for(m, 64.5, odds.break_even(mo))
    under = calc.workload_for(m, 64.5, 1 - odds.break_even(mu))
    book = calc.workload_for(m, 64.5, odds.no_vig(mo, mu))
    assert under < book < over
    # round trip: "book expects" fed back returns the no-vig chance within 1 point
    assert abs(m.chance_over(64.5, book) - odds.no_vig(mo, mu)) < 0.01
    r = rec_model()
    w = calc.workload_for(r, 5.5, 0.5)
    assert abs(r.chance_over(5.5, w) - 0.5) < 0.01


def test_the_rate_search_inverts_the_chance():
    m = rush_model()
    r = calc.rate_for(m, 64.5, 0.56, 16.0)
    assert abs(m.chance_over(64.5, 16.0, rate=r) - 0.56) < 0.01
    rr = rec_model()
    c = calc.rate_for(rr, 6.5, 0.55, 10.0)
    assert 0 < c < 1 and abs(rr.chance_over(6.5, 10.0, rate=c) - 0.55) < 0.01


def test_an_unreachable_line_says_so():
    assert calc.workload_for(rush_model(ypc=1.0), 400.5, 0.56) is None


def test_fixed_counts_have_no_workload_variation():
    m = rec_model(rate=1.0)
    assert (m.outcomes_fixed(7) == 7).all()


# ------------------------------------------------------------------ card

def _player(season_games, window):
    pl = player.Player("00-1", "Test Back", "DAL", "RB", 2026, 5, window, season_games)
    pl.rates["ypc"] = player.Rate(4.2, 4.4, 200, 3.9, 60, 4.3)
    pl.rates["catch"] = player.Rate(0.75, 0.78, 50, 0.7, 10, 0.72)
    return pl


def _games():
    rows = [(2025, 17, 13, 54), (2026, 1, 12, 41), (2026, 2, 12, 30), (2026, 3, 19, 98), (2026, 4, 19, 62)]
    window = pd.DataFrame([dict(season=s, week=w, carries=c, rush_yds=y, targets=2, receptions=1, completions=0)
                           for s, w, c, y in rows])
    season = window[window["season"] == 2026].copy()
    season["result_group"] = ["won by 8+", "within 7", "within 7", "lost by 8+"]
    season["qb_id"] = ["q1", "q1", "q2", "q2"]
    season["qb_name"] = ["A.Starter", "A.Starter", "B.Backup", "B.Backup"]
    return season, window


def test_card_renders_the_rows_the_brief_asks_for():
    fixed = settings.load()["fixed"]
    season, window = _games()
    pl = _player(season, window)
    c = card.compute(pl, rush_model(ypc=4.2), "rush_yds", 64.5, odds.multiplier_from_american(-125),
                     odds.multiplier_from_american(-132), fixed)
    text = card.render(pl, c, source="line typed in")
    assert text.startswith("TEST BACK (DAL RB) - rushing yards - week 5")
    for needle in ("Over -125", "Under -132", "Over wins often enough (56%)", "Book expects: about",
                   "At his last-4 average of 15.5 carries", "won by 8+: ", "A.Starter starting", "B.Backup starting",
                   "His last games (carries-yards): wk4 19-62", "Gap: the Over needs", "Tested:"):
        assert needle in text, needle
    assert c["needed_under"] < c["book_expects"] < c["needed_over"]
    assert c["gap_over"] == pytest.approx(c["needed_over"] - 15.5)
    import re
    for banned in ("bet", "value", "edge", "lean", "pick", "recommend", "play this", "lock"):
        assert not re.search(rf"\b{banned}\b", text.lower()), banned
    # every line fits a phone (one wrap at most on a narrow screen)
    assert max(len(x) for x in text.splitlines()) <= 100


def test_card_says_when_the_usual_reaches_into_last_season():
    fixed = settings.load()["fixed"]
    season, window = _games()
    pl = _player(season.iloc[:1], window.iloc[:2])
    c = card.compute(pl, rush_model(), "rush_yds", 64.5, 1.8, 1.8, fixed)
    assert "reach back into last season" in card.render(pl, c)


def test_a_user_target_replaces_break_even():
    fixed = settings.load()["fixed"]
    season, window = _games()
    pl = _player(season, window)
    m = rush_model()
    lo = card.compute(pl, m, "rush_yds", 64.5, 1.8, 1.76, fixed)
    hi = card.compute(pl, m, "rush_yds", 64.5, 1.8, 1.76, fixed, target=0.65)
    assert hi["target_over"] == 0.65 and hi["needed_over"] > lo["needed_over"]
