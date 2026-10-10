"""props/calc calculator and card: the draws, the searches, the round trip,
and a card rendered from a synthetic player (no network)."""

from __future__ import annotations

import argparse
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
    n = calc.counts(d, 18.0, calc.default_limits().max_count["carries"])
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
    assert calc.over_share(rush_model(), 64.5, 17.0) == calc.over_share(rush_model(), 64.5, 17.0)


def test_chance_rises_with_workload_and_rate():
    m = rush_model()
    ch = [calc.over_share(m, 64.5, w) for w in (10, 14, 18, 22, 26)]
    assert ch == sorted(ch) and ch[0] < 0.2 < 0.8 < ch[-1]
    assert calc.over_share(m, 64.5, 17, rate=4.5) > calc.over_share(m, 64.5, 17, rate=3.5)


def test_needed_workloads_bracket_book_expects_and_round_trip():
    m = rush_model()
    mo, mu = odds.multiplier_from_american(-125), odds.multiplier_from_american(-132)
    over = calc.solve_workload(m, 64.5, odds.break_even(mo)).value
    under = calc.solve_workload(m, 64.5, 1 - odds.break_even(mu)).value
    book = calc.solve_workload(m, 64.5, odds.no_vig(mo, mu)).value
    assert under < book < over
    # round trip: "book expects" fed back returns the no-vig chance within 1 point
    assert abs(calc.over_share(m, 64.5, book) - odds.no_vig(mo, mu)) < 0.01
    r = rec_model()
    w = calc.solve_workload(r, 5.5, 0.5).value
    assert abs(calc.over_share(r, 5.5, w) - 0.5) < 0.01


def test_the_rate_search_inverts_the_chance():
    m = rush_model()
    r = calc.solve_rate(m, 64.5, 0.56, 16.0).value
    assert abs(calc.over_share(m, 64.5, 16.0, rate=r) - 0.56) < 0.01
    rr = rec_model()
    c = calc.solve_rate(rr, 6.5, 0.55, 10.0).value
    assert 0 < c < 1 and abs(calc.over_share(rr, 6.5, 10.0, rate=c) - 0.55) < 0.01


def test_an_unreachable_line_says_so():
    s = calc.solve_workload(rush_model(ypc=1.0), 400.5, 0.56)
    assert s.value is None and s.status == "high"
    s = calc.solve_rate(rush_model(), -500.5, 0.56, 16.0)    # clears even at the lowest rate in range
    assert s.status == "low" and s.value == calc.default_limits().rate_range["rush_yds"][0]


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
    assert card.value(c, "needed_under") < card.value(c, "book_expects") < card.value(c, "needed_over")
    assert c["gap_over"] == pytest.approx(card.value(c, "needed_over") - 15.5)
    import re
    for banned in ("bet", "value", "edge", "lean", "pick", "recommend", "play this", "lock"):
        assert not re.search(rf"\b{banned}\b", text.lower()), banned
    # every line fits a phone (one wrap at most on a narrow screen)
    assert max(len(x) for x in text.splitlines()) <= 100


def test_card_says_when_the_usual_reaches_into_last_season():
    fixed = settings.load()["fixed"]
    season, window = _games()
    pl = _player(season.iloc[:3], window.iloc[:4])          # '25 wk17 and 2026 weeks 1-3
    c = card.compute(pl, rush_model(), "rush_yds", 64.5, 1.8, 1.8, fixed)
    assert "reach back into last season" in card.render(pl, c)


def test_a_user_target_replaces_break_even():
    fixed = settings.load()["fixed"]
    season, window = _games()
    pl = _player(season, window)
    m = rush_model()
    lo = card.compute(pl, m, "rush_yds", 64.5, 1.8, 1.76, fixed)
    hi = card.compute(pl, m, "rush_yds", 64.5, 1.8, 1.76, fixed, target=0.65)
    assert hi["target_over"] == 0.65 and card.value(hi, "needed_over") > card.value(lo, "needed_over")


def test_a_market_below_its_minimum_sample_shows_no_numbers():
    season, window = _games()
    pl = _player(season, window)
    pl.not_enough["rush_yds"] = ["12 of his own carries in his last 16 games (needs 30)"]
    text = card.render_not_enough(pl, "rush_yds", 64.5, 1.8, 1.76)
    assert "Not enough data, so no workload numbers" in text and "  - 12 of his own carries" in text
    assert "wins often enough" not in text and "Book expects" not in text
    c = card.compute(pl, rush_model(), "rush_yds", 64.5, 1.8, 1.76, settings.load()["fixed"])
    with pytest.raises(ValueError):
        card.render(pl, c)


def test_an_unreachable_rate_is_said_in_words():
    season, window = _games()
    pl = _player(season, window)                      # last-4 average: 2 targets a game
    c = card.compute(pl, rec_model(0.75), "receptions", 4.5, 1.69, 1.89, settings.load()["fixed"])
    text = card.render(pl, c)
    assert card.value(c, "rate_needed_over") is None and "the Over cannot win often enough at any catch rate" in text
    # the Under wins at every rate here (the Over tops out near 8%): it must say so, not the reverse
    assert "the Under wins often enough at any catch rate" in text
    assert "Under cannot" not in text


def test_an_under_that_wins_at_any_workload_is_said_in_words():
    season, window = _games()
    pl = _player(season, window)
    c = card.compute(pl, rush_model(ypc=1.0), "rush_yds", 300.5, 1.8, 1.76, settings.load()["fixed"])
    text = card.render(pl, c)
    assert "Over cannot win often enough (56%) at any workload up to 45 carries" in text
    assert "Under wins often enough (57%) at any workload up to 45 carries" in text
    assert "more than 45 carries or fewer" not in text and "Book expects: more than 45" in text
    assert "45 or fewer" not in text                      # no always-true history row


def test_position_is_read_as_of_the_priced_week():
    from props.calc import player
    b = object.__new__(player.Bundle)
    b._roster_pos = pd.DataFrame([{"season": 2026, "week": w, "gsis_id": "x", "position": p}
                                  for w, p in ((1, "WR"), (8, "WR"), (9, "RB"), (12, "RB"))])
    b.position = {(2025, "x"): "TE"}
    assert b.position_at("x", 2026, 5) == "WR"        # not the later RB listing
    assert b.position_at("x", 2026, 10) == "RB"
    assert b.position_at("y", 2026, 5) is None and b.position_at("x", 2027, 1) is None


def test_every_card_variant_fits_a_phone():
    fixed = settings.load()["fixed"]
    season, window = _games()
    pl = _player(season, window)
    texts = [card.render(pl, card.compute(pl, rush_model(ypc=1.0), "rush_yds", 300.5, 1.8, 1.76, fixed)),
             card.render(pl, card.compute(pl, rec_model(0.75), "receptions", 4.5, 1.69, 1.89, fixed)),
             card.render(pl, card.compute(pl, rush_model(), "rush_yds", 64.5, 1.8, 1.76, fixed))]
    pl.not_enough["rush_yds"] = ["12 of his own carries in his last 16 games (needs 30)",
                                 "140 TE carries in the pool for his position's average (needs 500)"]
    texts.append(card.render_not_enough(pl, "rush_yds", 64.5, 1.8, 1.76, source="line typed in"))
    texts.append(card.render_not_enough(pl, "rush_yds", None, None, None, source=(
        "Unmatched: no saved Sleeper quote belongs to Sam LaPorta (DET) in 2026_05_DET_ARI for rush_yds; "
        "give --line --over --under")))
    worst = max((len(x), x) for t in texts for x in t.splitlines())
    assert worst[0] <= 100, worst


def test_a_push_on_a_whole_number_line_is_void_for_both_sides():
    m = rec_model(0.7)
    n = m._counts_at(8.0)
    out = m.outcome(n)
    po, pu = np.mean(out > 5), np.mean(out < 5)
    assert np.mean(out == 5) > 0.05                       # exactly 5 catches is common at 8 targets
    assert calc.over_share(m, 5, 8.0) == pytest.approx(po / (po + pu))
    assert calc.over_share(m, 5.5, 8.0) == pytest.approx(np.mean(out > 5.5))   # half-point line: plain chance
    # rushing yards are whole numbers, so they can push too
    r = rush_model()
    y = r.outcome(r._counts_at(16.0))
    assert (y == np.round(y)).all() and np.mean(y == 65) > 0


def test_every_row_uses_the_same_push_rule():
    m = rec_model(0.7)
    fixed = settings.load()["fixed"]
    season, window = _games()
    pl = _player(season, window)
    c = card.compute(pl, m, "receptions", 5, 1.9, 1.9, fixed)
    # at equal prices the Over's and the Under's needed workloads sit either side of "book expects"
    assert card.value(c, "needed_under") < card.value(c, "book_expects") < card.value(c, "needed_over")
    assert abs(calc.over_share(m, 5, card.value(c, "book_expects")) - 0.5) < 0.01
    assert abs(calc.over_share(m, 5, card.value(c, "needed_over")) - c["target_over"]) < 0.01
    assert abs(1 - calc.over_share(m, 5, card.value(c, "needed_under")) - c["target_under"]) < 0.01


# ------------------------------------------------------------------ the leg command's branches

def _leg_args(**kw):
    import argparse
    base = dict(name="Test Back", market="rush_yds", team=None, season=2026, week=5, line=None, over=None,
                under=None, target=None)
    return argparse.Namespace(**{**base, **kw})


@pytest.fixture
def stub_leg(monkeypatch, tmp_path):
    from props.calc import __main__ as cli, lines, player
    from props.calc.shared import journal
    season, window = _games()
    pl = _player(season, window)
    pl.pools = {"rb_residuals": RESID}
    game = pd.Series({"week": 5, "game_id": "2026_05_DAL_ARI", "kickoff_utc": "2099-10-11T20:05:00+00:00"})
    monkeypatch.setattr(player, "Bundle", lambda *a, **k: type("B", (), {
        "rosters": None, "schedule": None, "position_at": lambda self, *a: "RB"})())
    monkeypatch.setattr(player, "find_player", lambda *a, **k: ("00-1", "Test Back", "DAL"))
    monkeypatch.setattr(cli, "Manifest", lambda *a, **k: type("M", (), {"stale": lambda self: []})())
    monkeypatch.setattr(cli, "_next_game", lambda *a, **k: game)
    monkeypatch.setattr(player, "build", lambda *a, **k: pl)
    real = journal.journal_path(2026)
    before = (real.stat().st_size, real.stat().st_mtime_ns) if real.exists() else None
    monkeypatch.setattr(journal, "JOURNAL_ROOT", tmp_path / "journal")
    lookup = type("L", (), {"quote": None, "asked": [],
                            "find": lambda self, leg, line=None: self.asked.append(line) or (
                                self.quote if self.quote and line in (None, self.quote["line"]) else None)})()
    monkeypatch.setattr(lines, "LineLookup", lambda *a, **k: lookup)
    yield cli, lookup, pl
    monkeypatch.setattr(journal, "JOURNAL_ROOT", None)
    after = (real.stat().st_size, real.stat().st_mtime_ns) if real.exists() else None
    assert after == before, f"a test changed the real journal {real}"


QUOTE = {"source": "your capture", "at_utc": "2099-10-11T18:00:00+00:00", "line": 64.5, "mult_over": 1.78,
         "mult_under": 1.95}


def _entry_args(**kw):
    base = dict(stake=5.0, payout=15.0, angle="role", why="more carries with the starter out",
                leg=["Test Back|rush_yds|over|64.5", "Other Back|rush_yds|under|64.5|DAL"], season=2026, week=None)
    return argparse.Namespace(**{**base, **kw})


def test_leg_not_enough_and_no_quote_shows_the_gap(stub_leg):
    cli, lookup, pl = stub_leg
    pl.not_enough["rush_yds"] = ["12 of his own carries in his last 16 games (needs 30)"]
    text = cli.leg(_leg_args())
    assert "Not enough data" in text and "Unmatched: no saved Sleeper quote" in text


def test_leg_reports_a_bad_saved_row_as_unmatched(stub_leg, monkeypatch):
    cli, lookup, pl = stub_leg
    from props.calc.checks import DataError

    def bad(leg, line=None):
        raise DataError("a saved week-5 archive row for Test Back: time 'x' is not a readable time")
    monkeypatch.setattr(lookup, "find", bad)
    with pytest.raises(SystemExit, match="Unmatched: a saved week-5 archive row"):
        cli.leg(_leg_args())


def test_leg_refuses_a_multiplier_typed_as_odds(stub_leg):
    cli, _, _ = stub_leg
    with pytest.raises(SystemExit, match="American odds"):
        cli.leg(_leg_args(line=64.5, over=1.8, under=1.9))
    with pytest.raises(SystemExit, match="need --line"):
        cli.leg(_leg_args(over=-120, under=-110))


def test_entry_logs_each_leg_in_the_journal_with_its_card_numbers(stub_leg, monkeypatch):
    cli, lookup, pl = stub_leg
    from props.calc import player
    from props.calc.shared import journal
    monkeypatch.setattr(player, "model", lambda *a, **k: rush_model(ypc=4.2))
    lookup.quote = dict(QUOTE)
    text = cli.entry(_entry_args())
    rows = journal.read(2026)
    assert "Logged entry" in text and len(rows) == 2 and rows[0]["entry_id"] == rows[1]["entry_id"]
    over, under = rows
    assert (over["side"], under["side"]) == ("over", "under") and over["market"] == "player_rush_yds"
    assert over["line"] == 64.5 and over["team"] == "DAL" and over["gsis_id"] == "00-1"
    assert over["volume_unit"] == "carries"              # journal.grade saves his actual carries from it
    assert over["entry_stake"] == 5.0 and over["entry_payout"] == 15.0 and over["status"] == "open"
    assert over["price"] == journal.leg_price(5.0, 15.0, 2)
    assert (over["calc_mult_over"], over["calc_mult_under"]) == (1.78, 1.95)
    assert over["calc_bar_status"] == "ok" and over["calc_bar"] > under["calc_bar"]
    assert over["calc_bar"] == pytest.approx(over["calc_usual"] + over["calc_gap"])     # Over: bar minus usual
    assert under["calc_bar"] == pytest.approx(under["calc_usual"] - under["calc_gap"])  # Under: usual minus bar
    assert over["calc_settings"] == settings.load()["tuned"]


def test_entry_logs_nothing_when_one_leg_falls_short(stub_leg, monkeypatch):
    cli, lookup, pl = stub_leg
    from props.calc import player
    from props.calc.shared import journal
    monkeypatch.setattr(player, "model", lambda *a, **k: rush_model(ypc=4.2))
    text = cli.entry(_entry_args())                       # no saved quote for either leg
    assert text.startswith("Not logged") and "no full card" in text and journal.read(2026) == []
    lookup.quote = dict(QUOTE)
    pl.not_enough["rush_yds"] = ["12 of his own carries in his last 16 games (needs 30)"]
    assert "no full card" in cli.entry(_entry_args()) and journal.read(2026) == []
    with pytest.raises(SystemExit, match="Name\\|market"):
        cli.entry(_entry_args(leg=["Test Back|rush_yds|over"]))


def test_entry_logs_only_the_line_played_and_checks_cheap_inputs_first(stub_leg, monkeypatch):
    cli, lookup, pl = stub_leg
    from props.calc import player
    from props.calc.shared import journal
    monkeypatch.setattr(player, "model", lambda *a, **k: rush_model(ypc=4.2))
    lookup.quote = dict(QUOTE)                                            # saved quote: 64.5
    text = cli.entry(_entry_args(leg=["Test Back|rush_yds|over|67.5", "Other Back|rush_yds|under|64.5"]))
    assert "no saved Sleeper quote at 67.5" in text and journal.read(2026) == [] and 67.5 in lookup.asked
    monkeypatch.setattr(player, "Bundle", None)                           # loading data would fail
    for kw, msg in ((dict(leg=["Test Back|rush_yds|over|64.5"]), "at least two legs"),
                    (dict(payout=4.0), "above --stake"),
                    (dict(leg=["A.J. Brown|rush_yds|over|64.5", "AJ Brown|rush_yds|under|64.5"]), "twice"),
                    (dict(why="  "), "--why is required"),
                    (dict(leg=["Test Back|rush_yds|over|x", "B|rush_yds|over|1"]), "is a number")):
        with pytest.raises(SystemExit, match=msg):
            cli.entry(_entry_args(**kw))


def test_draw_streams_do_not_depend_on_the_order_of_the_yaml():
    shuffled = calc.Limits({"completions": 60, "targets": 40, "carries": 80}, calc.default_limits().search_max,
                           calc.default_limits().rate_range, 40)
    a = calc.make_draws("targets", 8, 1000, 7)
    b = calc.make_draws("targets", 8, 1000, 7, shuffled)
    assert (a.u_play == b.u_play).all() and (a.gamma == b.gamma).all()


def test_a_callers_limits_reach_the_search():
    tight = calc.Limits(calc.default_limits().max_count, {"carries": 10.0, "targets": 25.0, "completions": 45.0},
                        calc.default_limits().rate_range, 40)
    m = calc.Model("rush_yds", "carries", calc.make_draws("carries", 16, SIMS, SEED, tight), 4.0, RESID, 0.15)
    assert calc.solve_workload(m, 64.5, 0.56).status == "high"     # 17 carries needed; the search stops at 10


def test_an_undecided_line_fails_loudly():
    from props.calc.checks import DataError
    m = rush_model()
    with pytest.raises(DataError, match="no simulated game is decided"):
        calc.over_share(m, 0, 0.0)                  # no carries: every game is exactly 0 = the line


def test_leg_refuses_nan_and_a_zero_line(stub_leg):
    cli, _, _ = stub_leg
    with pytest.raises(SystemExit, match="empty or infinite"):
        cli.leg(_leg_args(line=64.5, over=float("nan"), under=-110))
    with pytest.raises(SystemExit, match="above 0"):
        cli.leg(_leg_args(line=0.0, over=-125, under=-105))


def test_a_usual_from_too_few_games_is_not_shown():
    fixed = settings.load()["fixed"]
    season, window = _games()
    pl = _player(season.iloc[:2], window.iloc[1:3])          # two games played so far
    c = card.compute(pl, rush_model(), "rush_yds", 34.5, 1.8, 1.8, fixed)
    text = card.render(pl, c)
    assert c["usual"] is None and c["gap_over"] is None
    assert "only 2 games played, not enough data for an average (needs 4)" in text and "Gap:" not in text


def test_a_gap_near_zero_is_said_plainly():
    fixed = settings.load()["fixed"]
    season, window = _games()
    pl = _player(season, window)
    m = rush_model(ypc=4.2)
    c = card.compute(pl, m, "rush_yds", 64.5, 1.8, 1.76, fixed)
    c["gap_over"] = 0.03
    assert "is right at what the Over needs" in card.render(pl, c)


def test_leg_refuses_qb_rushing(stub_leg, monkeypatch):
    cli, _, _ = stub_leg
    from props.calc import player
    monkeypatch.setattr(player, "Bundle", lambda *a, **k: type("B", (), {
        "rosters": None, "schedule": None, "position_at": lambda self, *a: "QB"})())
    with pytest.raises(SystemExit, match="QB rushing"):
        cli.leg(_leg_args(line=30.5, over=-115, under=-115))


def test_the_rushing_rate_search_never_goes_below_zero():
    m = rush_model()
    s = calc.solve_rate(m, 10.5, 0.05, 30.0)              # a 5% target: met even at 0 yards a carry
    assert s.status == "low" and s.value == 0.0


def test_the_model_caches_follow_day_sd_and_residuals():
    m = rush_model()
    a = calc.over_share(m, 64.5, 18.0)
    m.day_sd = 0.30
    b = calc.over_share(m, 64.5, 18.0)
    m.residuals = RESID * 2
    c = calc.over_share(m, 64.5, 18.0)
    assert a != b and b != c


def test_entry_never_logs_a_game_that_has_kicked_off(stub_leg, monkeypatch):
    cli, lookup, pl = stub_leg
    from props.calc import player
    from props.calc.shared import journal
    monkeypatch.setattr(player, "model", lambda *a, **k: rush_model(ypc=4.2))
    lookup.quote = dict(QUOTE)
    monkeypatch.setattr(cli, "_next_game", lambda *a, **k: pd.Series(
        {"week": 5, "game_id": "2026_05_DAL_ARI", "kickoff_utc": "2026-10-04T17:00:00+00:00"}))
    text = cli.entry(_entry_args())
    assert "the game has kicked off" in text and journal.read(2026) == []


def test_entry_never_logs_a_name_matched_by_initial(stub_leg, monkeypatch):
    cli, lookup, pl = stub_leg
    from props.calc import player
    from props.calc.shared import journal

    def by_initial(b, name, season, team, week, flag):
        flag[0] = True
        return "00-1", "Test Back", "DAL"
    monkeypatch.setattr(player, "find_player", by_initial)
    monkeypatch.setattr(player, "model", lambda *a, **k: rush_model(ypc=4.2))
    lookup.quote = dict(QUOTE)
    assert "matched to Test Back by first initial" in cli.leg(_leg_args(name="Testy Back", team="DAL", line=64.5,
                                                                         over=-125, under=-132))
    text = cli.entry(_entry_args())
    assert "matched by initial" in text and journal.read(2026) == []
