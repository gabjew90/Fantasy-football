"""Marginal value: a projection is not what a player is worth to a roster."""

from manager import marginal

SHAPE = {"slots": {"QB": 1, "RB": 2, "WR": 2, "TE": 1}, "flex": 1}


def p(pid, pos, weekly, name=None):
    return {"sleeper_id": pid, "pos": pos, "weekly": weekly, "name": name or pid}


# QB1 / RB 20,18 / WR 16,15 / TE 10, flex takes the best leftover (RB 12)
ROSTER = [
    p("qb", "QB", 25), p("rb1", "RB", 20), p("rb2", "RB", 18), p("rb3", "RB", 12),
    p("rb4", "RB", 11), p("wr1", "WR", 16), p("wr2", "WR", 15), p("te1", "TE", 10),
]


def test_lineup_points_uses_flex_for_the_best_leftover():
    # 25 + 20 + 18 + 16 + 15 + 10 + 12(flex) = 116
    assert marginal.lineup_points(ROSTER, SHAPE) == 116.0


def test_cost_to_lose_is_the_replacement_gap_not_the_projection():
    # rb3 (12) starts in the flex; rb4 (11) replaces him. Costs 1, not 12.
    assert marginal.cost_to_lose(ROSTER, p("rb3", "RB", 12), SHAPE) == 1.0


def test_a_bench_player_behind_an_equal_body_costs_nothing():
    # rb4 never starts and nothing changes when he leaves
    assert marginal.cost_to_lose(ROSTER, p("rb4", "RB", 11), SHAPE) == 0.0


def test_the_only_player_at_a_position_costs_his_whole_slot():
    # no second TE anywhere on the roster, so the slot goes empty
    assert marginal.cost_to_lose(ROSTER, p("te1", "TE", 10), SHAPE) == 10.0


def test_high_projection_can_cost_less_than_low_projection():
    """The LaPorta/Wilson case: the bigger number is the smaller loss."""
    cheap_star = marginal.cost_to_lose(ROSTER, p("rb3", "RB", 12), SHAPE)   # proj 12
    dear_scrub = marginal.cost_to_lose(ROSTER, p("te1", "TE", 10), SHAPE)   # proj 10
    assert cheap_star < dear_scrub


def test_gain_to_add_is_zero_for_someone_who_cannot_crack_the_lineup():
    assert marginal.gain_to_add(ROSTER, p("new", "RB", 5), SHAPE) == 0.0
    # WR30 takes a WR slot, WR15 slides to flex over rb3(12): 116 -> 134
    assert marginal.gain_to_add(ROSTER, p("new", "WR", 30), SHAPE) == 18.0


def test_price_reports_both_sides_and_they_need_not_be_symmetric():
    theirs = [p("tqb", "QB", 24), p("trb1", "RB", 22), p("trb2", "RB", 9),
              p("twr1", "WR", 21), p("twr2", "WR", 20), p("tte", "TE", 14),
              p("tte2", "TE", 13)]
    d = marginal.price(ROSTER, theirs, [p("rb4", "RB", 11)], [p("tte2", "TE", 13)], SHAPE)
    assert d.my_delta == 3.0          # tte2(13) beats rb3(12) in my flex, and covers TE
    # tte2 was their FLEX, not their bench, so rb4(11) replacing it costs them 2.
    # The asymmetry is the point: the same swap is +3 one way and -2 the other.
    assert d.their_delta == -2.0
    assert d.mutual is (d.my_delta > 0 and d.their_delta > 0)
    assert "rb4" in str(d) and "tte2" in str(d)


def test_dead_weight_finds_the_players_worth_nothing_to_lose():
    dead = {r["player"]["sleeper_id"] for r in marginal.dead_weight(ROSTER, SHAPE)}
    assert "rb4" in dead
    assert "te1" not in dead and "rb1" not in dead


def test_tradeable_counts_buyers_and_a_player_nobody_wants_has_none():
    rich = ([p("rqb", "QB", 40)] + [p(f"r{i}", "RB", 40) for i in range(4)]
            + [p(f"w{i}", "WR", 40) for i in range(3)])
    rows = marginal.tradeable(ROSTER, {"rich": rich}, SHAPE)
    by_id = {r["player"]["sleeper_id"]: r for r in rows}
    assert by_id["rb4"]["buyers"] == 0          # 11 points helps nobody
    assert by_id["qb"]["buyers"] == 0           # their QB slot is full at 40 > 25
    assert by_id["rb4"]["ratio"] is None        # cost 0 -> undefined, not infinite


def test_ros_key_prices_a_season_trade_not_a_week():
    ros = [dict(x, ros=(x["weekly"] or 0) * 10) for x in ROSTER]
    assert marginal.lineup_points(ros, SHAPE, key="ros") == 1160.0
    assert marginal.cost_to_lose(ros, "te1", SHAPE, key="ros") == 100.0
