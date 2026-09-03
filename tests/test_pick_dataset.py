"""The pick-level rival dataset and fit (DECISIONS #35)."""

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


pd_ = _load("pick_dataset")
rf = _load("rival_fit")

SLOTS = {"QB": 1, "RB": 1, "WR": 1, "TE": 1, "FLEX": 1, "K": 1, "DEF": 1}


def _trail():
    # 2 teams x 3 rounds: picks 1..6 snake (slot1, slot2, slot2, slot1, slot1, slot2); we are team "1"
    names = [("A One", "RB", "2"), ("B Two", "WR", "2"), ("C Three", "RB", "2"), ("D Four", "TE", "1"), ("E Five", "QB", "1"), ("F Six", "K", "2")]
    picks = [{"pick_no": i + 1, "team_id": t, "name": n, "pos": p, "team": "XX"} for i, (n, p, t) in enumerate(names)]
    # our team is "1" but team "1" picks at 1,4,5 in a 2-team snake: slot1 = picks 1,4,5. Make team 2 the rival at 2,3,6.
    picks[0]["team_id"] = "1"; picks[3]["team_id"] = "1"; picks[4]["team_id"] = "1"
    picks[1]["team_id"] = "2"; picks[2]["team_id"] = "2"; picks[5]["team_id"] = "2"
    return {"room": "r1", "teams": 2, "my_team": "1", "picks": picks,
            "managers": {"1": {"away": False}, "2": {"away": True}}}


def _snap():
    order = ["A One", "B Two", "C Three", "D Four", "E Five", "G Seven", "F Six"]
    pos = {"A One": "RB", "B Two": "WR", "C Three": "RB", "D Four": "TE", "E Five": "QB", "G Seven": "WR", "F Six": "K"}
    return {(pd_.key(n), pos[n]): {"o_rank": i + 1, "avg_pick": None, "psr_rank": None} for i, n in enumerate(order)}


def test_away_label_comes_from_team_ids_at_the_nearest_preceding_call():
    side = [{"call": 1, "current_pick": 1, "state_in": {"away_teams": []}},
            {"call": 2, "current_pick": 3, "state_in": {"away_teams": ["2"]}},
            {"call": 3, "current_pick": 6, "state_in": {"away_teams": []}}]
    assert pd_.away_teams_at(side, 2) == []
    assert pd_.away_teams_at(side, 3) == ["2"]          # the call made while pick 3 was on the clock
    assert pd_.away_teams_at(side, 5) == ["2"]
    assert pd_.away_teams_at(side, 6) == []
    assert pd_.away_teams_at([], 4) is None


def test_rows_rank_the_taken_player_and_apply_starters_first():
    trail, snap = _trail(), _snap()
    side = [{"call": 1, "current_pick": 1, "state_in": {"away_teams": ["2"]}}]
    board_adp = {k: float(v["o_rank"]) * 2 for k, v in snap.items()}
    pools = []
    rows = pd_.build_rows("r1", trail, side, snap, board_adp, SLOTS, 2, pools)
    assert [r["seat_class"] for r in rows] == ["ours", "away", "away", "ours", "ours", "away"]
    r2 = rows[1]                       # pick 2: B Two (WR), A One already gone -> B Two is #1 by yrank among available
    assert r2["rank_by_yrank"] == 1 and r2["rank_fit_by_yrank"] == 1 and r2["fits_open_starter"] is True
    r6 = rows[5]                       # pick 6: F Six (K) taken while G Seven (WR) is the better-ranked available
    assert r6["rank_by_yrank"] == 2 and r6["needs_before"].startswith("QB1")
    rival = [q for q in pools if q["seat_class"] != "ours"]      # main() drops our own picks
    assert len(pools) == 6 and len(rival) == 3
    assert rival[0]["taken"] == 0 and rival[0]["seat_class"] == "away"
    assert rival[0]["pos"][0] == "WR" and rival[0]["fits"][0] is True


def test_seat_class_precedence():
    assert pd_.seat_class(True, "instant", "away") == "ours"
    assert pd_.seat_class(False, "instant", "present") == "instant"
    assert pd_.seat_class(False, "unknown", "away") == "away"
    assert pd_.seat_class(False, "human", "no_sidecar") == "human"
    assert pd_.seat_class(False, None, "present") == "human"
    assert pd_.seat_class(False, None, "no_sidecar") == "unknown"


def _pool(taken, starters_open=True, pick_no=10, rnd=1):
    yr = [1.0, 2.0, 3.0, 4.0]
    return {"room": "r", "pick_no": pick_no, "round": rnd, "seat": 2, "seat_class": "away", "taken": taken,
            "starters_open": starters_open, "yrank_a": np.array(yr), "adp_a": np.array([30.0, 10.0, 12.0, 14.0]),
            "fits_a": np.array([False, True, True, True]), "kdef_a": np.array([False] * 4), "pos": ["QB", "RB", "WR", "TE"]}


def test_list_hit_is_the_lowest_yrank_that_fits_an_open_starter():
    assert rf.list_hit(_pool(taken=1)) is True          # the best-ranked fit
    assert rf.list_hit(_pool(taken=0)) is False         # better yrank, but does not fit
    assert rf.list_hit(_pool(taken=0, starters_open=False)) is True   # no starter open: any position


def test_mixture_likelihood_prefers_the_list_walk_when_picks_walk_the_list():
    walkers = [_pool(taken=1) for _ in range(30)]
    params = {"sigma_early": 6.0, "sigma_late": 27.0, "need_damp": 0.15}
    ll0 = rf.loglik(walkers, "mixture", dict(params, pi=0.0))
    ll9 = rf.loglik(walkers, "mixture", dict(params, pi=0.9))
    assert ll9 > ll0
    # and a pure Gaussian-in-ADP crowd is not helped by pi
    adp_pickers = [_pool(taken=1)] * 0 + [_pool(taken=0, starters_open=False) for _ in range(0)]
    best, ll, prof = rf.fit(walkers, "mixture", with_scale=True)
    assert best["pi"] >= 0.8 and prof["pi"]["ci90"][0] >= 0.5
