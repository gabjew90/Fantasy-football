"""fantasy/: the projection contract, the two weekly sources and the range model."""

from __future__ import annotations

import math

import pytest

from fantasy import dispersion as D
from fantasy.contract import QUANTILES, WEEK, ContractError, Projection, validate
from fantasy.sources import market_points as MP
from fantasy.sources import sleeper_weekly as SW

PPR = {"rec": 1.0, "rec_yd": 0.1, "rec_td": 6.0, "rush_yd": 0.1, "rush_td": 6.0,
       "pass_yd": 0.04, "pass_td": 4.0, "pass_int": -1.0, "fum_lost": -2.0}
Q5 = dict(zip(QUANTILES, (2.0, 5.0, 9.0, 13.0, 18.0)))


# ---------------------------------------------------------------- contract

def test_a_coherent_projection_passes_and_exposes_floor_and_ceiling():
    p = validate(Projection("1", "s", WEEK, 9.5, quantiles=Q5, range_from="x"))
    assert (p.floor, p.ceiling) == (2.0, 18.0)
    assert validate(Projection("1", "s", WEEK, 9.5)).floor is None, "mean-only is allowed"


@pytest.mark.parametrize("bad", [
    Projection("", "s", WEEK, 1.0),
    Projection("1", "s", "season", 1.0),
    Projection("1", "s", WEEK, float("nan")),
    Projection("1", "s", WEEK, 1.0, quantiles={0.5: 1.0}, range_from="x"),
    Projection("1", "s", WEEK, 1.0, quantiles=dict(zip(QUANTILES, (5, 4, 3, 2, 1))), range_from="x"),
    Projection("1", "s", WEEK, 1.0, quantiles=Q5),                 # no range_from
])
def test_the_contract_rejects_incoherent_projections(bad):
    with pytest.raises(ContractError):
        validate(bad)


# ----------------------------------------------------------- sleeper_weekly

def test_sleeper_weekly_scores_in_league_scoring_and_skips_placeholders():
    rows = [{"player_id": "4046", "team": "BUF", "opponent": "LAC",
             "player": {"fantasy_positions": ["WR"]},
             "stats": {"rec": 6, "rec_yd": 80, "rec_td": 0.5, "pts_ppr": 99.0, "adp_ppr": 12, "gp": 1}},
            {"player_id": "9", "stats": {"adp_ppr": 150.0, "pos_adp_ppr": 40}}]
    r = SW.from_rows(rows, PPR)
    assert set(r.projections) == {"4046"}
    p = r.projections["4046"]
    assert p.mean == pytest.approx(6 + 8 + 3), "pts_ppr and adp are not stats"
    assert p.detail["pos"] == "WR" and p.detail["opponent"] == "LAC"
    half = SW.from_rows(rows, dict(PPR, rec=0.5)).projections["4046"].mean
    assert half == pytest.approx(3 + 8 + 3)


def test_a_week_of_placeholders_is_unavailable_not_zeroes():
    r = SW.from_rows([{"player_id": "9", "stats": {"adp_ppr": 150.0}}], PPR)
    assert not r.available and r.projections == {} and r.notes


# ------------------------------------------------------------ market_points

def test_the_migrated_conversions_reproduce_the_skill_exactly():
    """Golden values from the skill's scripts/market_points.py on 2026-09-24."""
    params = MP.load_params()
    assert MP.market_mean_continuous(params, "rec_yds", "WR", 64.5, 0.47)[0] == pytest.approx(71.68242440923825)
    assert MP.market_mean_count(params, "catches", "WR", 4.5, 0.45)[0] == pytest.approx(5.019627440166438)
    assert MP.market_mean_continuous(params, "rush_yds", "RB", 58.5, 0.52)[0] == pytest.approx(60.358764254070024)
    assert MP.market_mean_continuous(params, "pass_yds", "QB", 231.5, 0.5)[0] == pytest.approx(227.796)


def _market(pid, wager, line, over, under, team="SF"):
    return {"sport": "nfl", "wager_type": wager, "subject_id": pid, "game_id": "g1", "updated_at": 5,
            "options": [{"outcome": "over", "status": "active", "payout_multiplier": over,
                         "outcome_value": line, "game_status": "pre_game", "subject_team": team},
                        {"outcome": "under", "status": "active", "payout_multiplier": under,
                         "outcome_value": line, "game_status": "pre_game", "subject_team": team}]}


def test_a_quarterbacks_anytime_td_is_scored_as_his_own_rushing_td():
    """The skill priced it as a passing TD (4 points); the market pays when the
    QB himself scores, which is a rush worth 6."""
    lines = [_market("qb1", "anytime_touchdowns", 0.5, 3.0, 1.4)]
    book = MP.collect_markets(lines, {"qb1": {"position": "QB", "team": "SF"}})
    p = MP.from_markets(book, PPR, MP.load_params()).projections["qb1"]
    etd = p.detail["components"]["etd"]
    assert p.mean == pytest.approx(round(6.0 * etd, 2), abs=0.01)
    assert p.detail["partial"] and "pass_td (never posted)" in p.detail["missing_markets"]


def test_one_sided_and_unknown_players_are_skipped_and_partials_flagged():
    lines = [_market("wr1", "receptions", 4.5, 1.9, 1.9),
             _market("ghost", "receptions", 4.5, 1.9, 1.9),
             dict(_market("wr2", "receptions", 4.5, 1.9, 1.9), options=[
                 {"outcome": "over", "status": "active", "payout_multiplier": 1.9, "outcome_value": 4.5,
                  "game_status": "pre_game"}])]
    players = {"wr1": {"position": "WR"}, "wr2": {"position": "WR"}}
    book = MP.collect_markets(lines, players)
    assert set(book) == {"wr1"}
    p = MP.from_markets(book, PPR, MP.load_params()).projections["wr1"]
    assert p.detail["partial"] and p.detail["missing_markets"] == ["anytime_td", "rec_yds"]


def test_a_tight_end_premium_is_paid_per_market_catch():
    line = MP.stat_line({"catches": 4.0, "rec_yds": 40.0, "etd": 0.3}, "TE", dict(PPR, bonus_rec_te=0.5))
    assert line["bonus_rec_te"] == 4.0 and line["rec_td"] == 0.3
    assert "bonus_rec_te" not in MP.stat_line({"catches": 4.0}, "WR", dict(PPR, bonus_rec_te=0.5))


# ------------------------------------------------------------- dispersion

def _pairs(pos="WR", n=400):
    """A deterministic spread of outcomes around two projection levels."""
    out = []
    for i in range(n):
        u = (i + 0.5) / n
        out.append((pos, 5.0, 5.0 + 8 * (u - 0.4)))
        out.append((pos, 15.0, 15.0 + 16 * (u - 0.45)))
    return out


def test_the_fit_recovers_quantiles_and_interpolates_between_bins():
    t = D.fit(_pairs())
    lo, hi = D.quantiles_for(t, "WR", 5.0), D.quantiles_for(t, "WR", 15.0)
    assert lo[0.5] == pytest.approx(5.0 + 8 * (0.5 - 0.4), abs=0.05)
    assert hi[0.9] == pytest.approx(15.0 + 16 * (0.9 - 0.45), abs=0.05)
    mid = D.quantiles_for(t, "WR", 10.0)
    for q in QUANTILES:        # the residual at 10 sits between the residuals at 5 and 15
        r_lo, r_hi, r_mid = lo[q] - 5.0, hi[q] - 15.0, mid[q] - 10.0
        assert min(r_lo, r_hi) - 1e-6 <= r_mid <= max(r_lo, r_hi) + 1e-6
    assert all(a <= b for a, b in zip(mid.values(), list(mid.values())[1:]))
    assert D.quantiles_for(t, "K", 8.0) is None


def test_quantiles_never_fall_below_the_positions_observed_floor():
    t = D.fit(_pairs())
    assert min(D.quantiles_for(t, "WR", 0.5).values()) >= t["positions"]["WR"]["floor"]


def test_a_calibrated_table_passes_and_ties_on_a_quantile_are_not_misses():
    train = _pairs()
    t = D.fit(train)
    rep = D.evaluate(t, train, train)
    ok, why = D.verdict(rep)
    assert ok, why
    # a pile of exact zeros on a p10 of zero: "<=" alone would read it as a miss
    atoms = [("TE", 1.0, 0.0)] * 300 + [("TE", 1.0, x / 10) for x in range(1, 101)]
    ta = D.fit(atoms)
    r = D.evaluate(ta, atoms, atoms)["TE"]
    assert r["coverage"]["0.1"] > 0.5 and r["coverage_strict"]["0.1"] == 0.0
    assert D._off_by(r, 0.10) == 0.0


def test_apply_labels_the_range_and_carries_the_positions_caveats():
    t = D.fit(_pairs())
    t["validation"] = {"caveats": ["WR p10: 15.0%-15.0% of outcomes vs 10%", "QB: no better"]}
    p = D.apply(Projection("1", "sleeper_weekly", WEEK, 12.0, detail={"pos": "WR"}), t)
    assert p.floor is not None and p.range_from.startswith("dispersion_v0")
    assert p.detail["range_caveats"] == ["WR p10: 15.0%-15.0% of outcomes vs 10%"]
    own = Projection("1", "s", WEEK, 9.0, quantiles=Q5, range_from="the source", detail={"pos": "WR"})
    assert D.apply(own, t) is own, "a source's own range is never overwritten"


def test_the_shipped_tables_passed_their_own_holdout():
    for lg in ("omnibeta", "keefamania"):
        t = D.load_table(lg)
        assert t is not None and t["validation"]["passed"], lg
        assert t["fit_season"] < t["test_season"], "tested on a season the fit never saw"
        assert math.isclose(t["validation"]["overall"]["inside_p10_p90"], 0.8, abs_tol=0.05)


def test_a_two_way_player_is_placed_at_his_fantasy_position():
    from fantasy.contract import fantasy_position
    assert fantasy_position({"fantasy_positions": ["DB", "WR"], "position": "CB"}) == "WR"
    assert fantasy_position({"position": "FB"}) == "RB"
    assert fantasy_position({"fantasy_positions": ["LB"], "position": "LB"}) is None
    r = SW.from_rows([{"player_id": "11632", "player": {"fantasy_positions": ["DB", "WR"]},
                       "stats": {"rec": 4, "rec_yd": 50}}], PPR)
    assert r.projections["11632"].detail["pos"] == "WR"


def test_adjacent_bins_with_one_centre_do_not_divide_by_zero():
    t = {"positions": {"WR": {"floor": 0.0, "bins": [
        {"center": 9.0, "resid": {str(q): 0.0 for q in QUANTILES}},
        {"center": 9.0, "resid": {str(q): 1.0 for q in QUANTILES}},
        {"center": 12.0, "resid": {str(q): 2.0 for q in QUANTILES}}]}}}
    assert D.quantiles_for(t, "WR", 9.0)[0.5] == 9.0
