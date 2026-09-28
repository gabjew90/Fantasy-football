"""fantasy.evidence.team_context: a player among the teammates he competes
with for the same volume, week by week, and the table that shows it.

Hand-built usage, no network. Pinned: the group is the right one (receivers
share targets across WR and TE, backs share carries), the team is the one he
plays for NOW, a missed week is a gap not a zero, a partial game is marked,
the order follows recent usage, and the asked-for player is always shown."""

from __future__ import annotations

import pandas as pd

from fantasy import evidence as EV


def _u(rows):
    base = dict(season=2026, targets=0, carries=0, tgt_share=0.0, ay_share=0.0, adot=None, wopr=0.0,
                carry_share=0.0, i10_tgt=0, i10_car=0, two_min=0, air_yards=0.0, team_tgt=30, team_ay=300,
                team_car=25, offense_snaps=60)
    return pd.DataFrame([dict(base, **r) for r in rows])


def _wk(g, team, week, snap, tgt=0.0, car=0.0, i10t=0, i10c=0):
    return dict(gsis_id=g, team=team, week=week, snap_pct=snap, tgt_share=tgt, wopr=1.5 * tgt, carry_share=car,
                i10_tgt=i10t, i10_car=i10c)


POS = {"wr1": "WR", "wr2": "WR", "te1": "TE", "rb1": "RB", "rb2": "RB", "qb": "QB", "moved": "WR"}
NAMES = {g: g.upper() for g in POS}


def _usage():
    rows = []
    for w in (1, 2, 3, 4):
        rows += [_wk("wr1", "KC", w, 0.9, tgt=0.28, i10t=1), _wk("te1", "KC", w, 0.8, tgt=0.20),
                 _wk("rb1", "KC", w, 0.7, tgt=0.10, car=0.60, i10c=2), _wk("qb", "KC", w, 1.0, car=0.1)]
        if w != 3:                                             # wr2 missed week 3
            rows.append(_wk("wr2", "KC", w, 0.8 if w != 4 else 0.3, tgt=0.10 if w < 3 else 0.35))
        if w >= 3:                                             # rb2 arrives in week 3
            rows.append(_wk("rb2", "KC", w, 0.3, car=0.30))
    # "moved" played weeks 1-2 for BUF, then 3-4 for KC
    rows += [_wk("moved", "BUF", w, 0.9, tgt=0.30) for w in (1, 2)]
    rows += [_wk("moved", "KC", w, 0.5, tgt=0.05) for w in (3, 4)]
    return _u(rows)


def test_receivers_share_targets_across_wr_and_te():
    tc = EV.team_context("te1", _usage(), POS, None, NAMES)
    assert tc["team"] == "KC" and tc["group"] == "WR/TE"
    assert {r["gsis_id"] for r in tc["rows"]} == {"wr1", "wr2", "te1", "moved"}, "no backs, no QB"
    assert tc["metrics"] == ["snap_pct", "tgt_share", "wopr"] and tc["inside10_metric"] == "i10_tgt"


def test_backs_share_carries_and_a_late_arrival_has_gaps_not_zeros():
    tc = EV.team_context("rb1", _usage(), POS, None, NAMES)
    assert tc["group"] == "RB" and [r["gsis_id"] for r in tc["rows"]] == ["rb1", "rb2"]
    rb2 = tc["rows"][1]
    assert rb2["by_week"]["carry_share"] == [None, None, 0.3, 0.3]
    assert tc["rows"][0]["inside10"] == 8


def test_the_order_follows_the_last_two_weeks_and_a_missed_week_is_a_gap():
    tc = EV.team_context("wr1", _usage(), POS, None, NAMES)
    order = [r["gsis_id"] for r in tc["rows"]]
    assert order[0] == "wr2", "35% in week 4 (the only recent week he played) leads the group"
    wr2 = next(r for r in tc["rows"] if r["gsis_id"] == "wr2")
    assert wr2["by_week"]["tgt_share"][2] is None, "week 3: did not play"
    assert 4 in wr2["partial_weeks"], "30% of snaps after 80% is a partial game"


def test_a_traded_player_counts_only_his_weeks_on_the_current_team():
    tc = EV.team_context("moved", _usage(), POS, None, NAMES)
    me = next(r for r in tc["rows"] if r["is_player"])
    assert tc["team"] == "KC" and me["by_week"]["tgt_share"] == [None, None, 0.05, 0.05]
    assert me["weeks_played"] == 2


def test_the_player_is_always_kept_and_a_qb_has_no_group():
    tc = EV.team_context("moved", _usage(), POS, None, NAMES, top=2)
    assert len(tc["rows"]) == 2 and any(r["is_player"] for r in tc["rows"])
    assert EV.team_context("qb", _usage(), POS, None, NAMES) is None
    assert EV.team_context("nobody", _usage(), POS, None, NAMES) is None


def test_the_table_marks_the_player_gaps_and_partial_games():
    tc = EV.team_context("wr1", _usage(), POS, None, NAMES)
    L = EV.team_table(tc)
    assert L[0].startswith("Team context -- KC WR/TE, weeks 1-4")
    wr1 = next(x for x in L if "**WR1**" in x)
    assert "90 / 90 / 90 / 90" in wr1 and "28 / 28 / 28 / 28" in wr1 and "0.42 / 0.42 / 0.42 / 0.42" in wr1
    wr2 = next(x for x in L if "| WR2 (WR)" in x)
    assert "80 / 80 / - / 30*" in wr2


def test_the_player_tool_prints_the_table(monkeypatch):
    from fantasy import ask as A
    from tests.test_fantasy_ask import _snap
    tc = EV.team_context("wr1", _usage(), POS, None, NAMES)
    monkeypatch.setattr(A.EV, "for_sleeper", lambda pids, info, season, manifest=None, team=False:
                        {p: {"weeks": 4, "mean": {}, "series": {}, "team_context": tc} for p in pids})
    r = A.players(_snap(), ["Puka Nacua"])
    assert "Team context -- KC WR/TE" in r.text
    assert r.data["players"][0]["usage"]["team_context"]["rows"][0]["gsis_id"] == "wr2"
