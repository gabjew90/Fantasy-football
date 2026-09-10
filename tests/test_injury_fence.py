"""The trade path and injuries (2026-09-10).

Henry + Warren for Egbuka + A.J. Brown priced at +1.16/wk with Brown Out
(ankle) on Sleeper: the trade path never read injury_status, the player file
it ran on was a day old, and every source still carried his full season.
Three fences: the ROS of a player who is not playing is scaled by the weeks
he misses; every such piece is named in the brief; the player file is
refetched after a few hours in season.
"""

from __future__ import annotations

import json
import time

from manager import marginal, trade_radar

_n = [0]


def _r(pos, ros, name, season=None):
    _n[0] += 1
    return {"sleeper_id": f"inj{_n[0]}", "pos": pos, "ros": ros, "weekly": 0.0,
            "ros_season": season if season is not None else ros, "name": name, "team": "SF"}


# ------------------------------------------------------------ injury_discount

def test_out_costs_one_week_and_ir_costs_four_by_default():
    out, ir, ok = _r("WR", 170.0, "out"), _r("RB", 170.0, "ir"), _r("TE", 170.0, "ok")
    inj = {out["sleeper_id"]: "Out", ir["sleeper_id"]: "IR", ok["sleeper_id"]: ""}
    rows = marginal.injury_discount([out, ir, ok], inj, weeks_left=17)
    by = {p["name"]: p for p in rows}
    assert by["out"]["ros"] == 160.0                    # 16/17 of 170
    assert by["ir"]["ros"] == 130.0                     # 13/17 of 170
    assert by["ok"] is ok, "a healthy row is the same object, not a copy"
    assert by["out"]["_injury"] == {"status": "Out", "weeks": 1, "healthy": 170.0}
    assert by["ir"]["_injury"]["weeks"] == 4


def test_fantasypros_weeks_override_the_default_and_questionable_is_untouched():
    ir, q = _r("WR", 170.0, "ir"), _r("WR", 170.0, "q")
    inj = {ir["sleeper_id"]: "IR", q["sleeper_id"]: "Questionable"}
    rows = marginal.injury_discount([ir, q], inj, weeks_left=17, weeks_out={ir["sleeper_id"]: 8})
    by = {p["name"]: p for p in rows}
    assert by["ir"]["ros"] == 90.0                      # 9/17
    assert by["q"] is q and "_injury" not in q


def test_weeks_out_is_capped_at_the_weeks_left_and_ros_season_is_kept():
    """DNR (99) late in the year: zero ROS, not negative. ros_season is not
    touched, so the per-source range scales each shop by the same discount."""
    p = _r("RB", 100.0, "done", season=300.0)
    rows = marginal.injury_discount([p], {p["sleeper_id"]: "DNR"}, weeks_left=5)
    assert rows[0]["ros"] == 0.0 and rows[0]["ros_season"] == 300.0


def test_no_injury_map_is_a_no_op():
    p = _r("RB", 100.0, "x")
    assert marginal.injury_discount([p], None, 17) == [p]
    assert marginal.injury_discount([p], {}, 17) == [p]


# --------------------------------------------------------------- the flags

def test_injury_flags_name_status_priced_and_healthy_ros():
    p = _r("WR", 247.0, "A.J. Brown")
    [q] = marginal.injury_discount([p], {p["sleeper_id"]: "Out"}, 17)
    [line] = marginal.injury_flags([q, _r("RB", 10, "fine")])
    assert line.startswith("INJURED: A.J. Brown (WR) is Out")
    assert "232 ROS" in line and "247 healthy" in line and "1 wk out" in line


def test_verdict_puts_injured_pieces_first_in_the_warnings():
    d = marginal.Deal(100.0, 117.0, 100.0, 105.0,
                      acceptance={"accept": True, "test1": True, "test2": True, "why": []})
    v = marginal.verdict(d, 17, mode="slots", injured=["INJURED: X (WR) is Out — ..."],
                         con={"n": 3, "spread": 60.0, "per_source": {}, "mean": 0.0})
    assert v["send"] is True, "advisory, never a gate"
    assert v["warnings"][0].startswith("⚠ INJURED: X")
    assert any("disagreement" in w for w in v["warnings"][1:])


# -------------------------------------------------------------- the radar

def _ctx():
    from tests.test_radar_pricing import MINE, THEIRS, _panel
    ctx = {"my_rid": 1, "roster_players": {1: list(MINE), 2: list(THEIRS)},
           "slots": {"QB": 1, "RB": 2, "WR": 2, "TE": 1}, "flex": 2,
           "flex_slots": None, "users_by_rid": {1: "me", 2: "them"},
           "weeks_left": 17, "_rank_panel": _panel(), "_wv_pool": []}
    return ctx


def _opp():
    from tests.test_radar_pricing import MINE, THEIRS
    return {"mgr": "them", "rid": 2, "give_p": [MINE[2], MINE[5]], "get_p": [THEIRS[3], THEIRS[6]]}


def _me_delta(out: str) -> float:
    import re
    return float(re.search(r"\*\*me ([+-]\d+\.\d+)\*\*", out).group(1))


def test_the_radar_prices_an_out_receiver_on_his_discounted_ros_and_says_so():
    healthy = "\n".join(trade_radar._priced(_ctx(), _opp(), {}))
    ctx = _ctx()
    twr1 = ctx["roster_players"][2][3]                  # the WR I receive
    ctx["injury"] = {twr1["sleeper_id"]: "Out"}
    hurt = "\n".join(trade_radar._priced(ctx, _opp(), {}))
    assert "⚠ INJURED: twr1 (WR) is Out" in hurt
    assert "INJURED" not in healthy
    assert _me_delta(hurt) < _me_delta(healthy), (hurt, healthy)


def test_an_ir_piece_asks_fantasypros_for_weeks_and_a_dead_feed_uses_the_default(monkeypatch):
    calls = []

    def fake_weeks(ctx, pids):
        calls.append(set(pids))
        return {}

    monkeypatch.setattr(trade_radar, "_weeks_out", fake_weeks)
    ctx = _ctx()
    twr1, mrb2 = ctx["roster_players"][2][3], ctx["roster_players"][1][2]
    ctx["injury"] = {twr1["sleeper_id"]: "IR", mrb2["sleeper_id"]: "Out"}
    out = "\n".join(trade_radar._priced(ctx, _opp(), {}))
    assert calls == [{twr1["sleeper_id"]}], "only reserve designations are asked about"
    assert "twr1 (WR) is IR" in out and "4 wks out" in out
    assert "mrb2 (RB) is Out" in out and "1 wk out" in out


def test_the_adjustment_is_built_once_per_context():
    ctx = _ctx()
    ctx["injury"] = {}
    trade_radar._priced(ctx, _opp(), {})
    first = ctx["_inj_adj"]
    trade_radar._chips_lines(ctx)
    assert ctx["_inj_adj"] is first


def test_an_injured_chip_is_labelled():
    ctx = _ctx()
    mrb2 = ctx["roster_players"][1][2]
    ctx["injury"] = {mrb2["sleeper_id"]: "Out"}
    out = "\n".join(trade_radar._chips_lines(ctx))
    if "mrb2" in out:
        assert "⚠ Out, 1 wk out" in out


# ------------------------------------------------------ the player file age

def test_players_cache_is_refetched_when_older_than_max_age(tmp_path, monkeypatch):
    from draftkit import sleeper

    cache = tmp_path / "players_nfl.json"
    cache.write_text(json.dumps({"1": {"injury_status": None}}), encoding="utf-8")
    old = time.time() - 5 * 3600
    import os
    os.utime(cache, (old, old))
    fetched = []
    monkeypatch.setattr(sleeper, "get_json", lambda url, timeout=30: fetched.append(url) or {"1": {"injury_status": "Out"}})
    client = sleeper.SleeperClient(tmp_path)
    assert client.players()["1"]["injury_status"] is None, "five hours is inside the daily TTL"
    assert client.players(max_age=3 * 3600)["1"]["injury_status"] == "Out"
    assert len(fetched) == 1
