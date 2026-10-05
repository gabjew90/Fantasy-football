"""Your scenario (scenario.py, DECISIONS #153): the user's workload assumptions,
read plainly, applied with fixed team totals, and never on the board."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "scripts"
sys.path.insert(0, str(ENGINE))

import scenario as SC  # noqa: E402

RESID = np.linspace(-4.0, 4.0, 201)


def test_rules_read_plainly_and_refuse_what_they_cannot_read():
    r = SC.parse(["Woody Marks: carries=14", "Nico Collins: targets=9, catch=70%", "hou: pass=-3, ypt=-5%"],
                 {"DAL", "HOU"})
    assert [(x["who"], x["key"], x["value"]) for x in r] == [
        ("Woody Marks", "carries", 14.0), ("Nico Collins", "targets", 9.0), ("Nico Collins", "catch", 0.7),
        ("HOU", "pass", -3.0), ("HOU", "ypt", -5.0)]
    assert SC.parse(["X: catch=0.65"], {"DAL"})[0]["value"] == 0.65
    for bad, why in [("Woody Marks carries=14", "PLAYER: key=value"), ("X: yards=80", "player keys are"),
                     ("HOU: targets=30", "team keys are"), ("X: targets=lots", "not a number"),
                     ("HOU: ypt=-5", "percent change"), ("HOU: pass=10%", "change in team targets"),
                     ("X: catch=140%", "between 0 and 100%"), ("X: carries=12%", "not a percent"),
                     ("X: ypc=0", "must be positive"),
                     ("HOU: pass=42", "CHANGE, not a total"), ("HOU: rush=3", "CHANGE, not a total"),
                     ("HOU: ypt=5%", "CHANGE, not a total")]:
        with pytest.raises(ValueError, match=why):
            SC.parse([bad], {"DAL", "HOU"})
    names, teams = ["Woody Marks", "D.J. Moore", "Mike Williams", "Mike Williams"], ["HOU", "CHI", "NYJ", "LAC"]
    r = SC.resolve_players(SC.parse(["woody marks: carries=14", "DJ Moore: targets=7",
                                     "Mike Williams (LAC): catch=60%"], {"HOU", "CHI", "NYJ", "LAC"}),
                           names, teams)
    assert [(x["who"], x["team_of"]) for x in r] == [("Woody Marks", "HOU"), ("D.J. Moore", "CHI"),
                                                    ("Mike Williams", "LAC")]
    assert r[1]["text"] == "D.J. Moore: targets=7"
    with pytest.raises(ValueError, match="Ghost is not in this game's player list"):
        SC.resolve_players(SC.parse(["Ghost: targets=5"], {"HOU"}), names, teams)
    with pytest.raises(ValueError, match="Nico Collins is ruled out"):
        SC.resolve_players(SC.parse(["Nico Collins: targets=5"], {"HOU"}), names, teams, ["Nico Collins"])
    with pytest.raises(ValueError, match=r"write 'Mike Williams \(NYJ\): \.\.\.'"):
        SC.resolve_players(SC.parse(["Mike Williams: targets=5"], {"NYJ", "LAC"}), names, teams)


def _team():
    M = pd.DataFrame({"name": ["A", "B", "C", "D"], "team": ["HOU", "HOU", "HOU", "DAL"],
                      "ts": [0.25, 0.20, 0.15, 0.30], "cr": 0.65, "ypt": 8.0, "ypc": 4.2, "rs": 0.1})
    env = {"HOU": {"targets": 34.0, "carries": 26.0}, "DAL": {"targets": 33.0, "carries": 27.0}}
    return M, env


def _rules(M, rules):
    return SC.resolve_players(SC.parse(rules, {"DAL", "HOU"}), M.name, M.team)


def test_targets_come_out_of_teammates_and_the_depth_receivers_in_proportion():
    M, env = _team()
    M2, env2 = SC.apply_before_sim(M, env, _rules(M, ["A: targets=10.2"]))
    hou = M2[M2.team == "HOU"].set_index("name").ts
    assert hou["A"] == pytest.approx(0.30), "10.2 of 34 targets"
    g = (1 - 0.30) / (1 - 0.25)
    assert hou["B"] == pytest.approx(0.20 * g) and hou["C"] == pytest.approx(0.15 * g)
    assert 1 - hou.sum() == pytest.approx((1 - 0.60) * g), "the depth receivers give up their part too"
    assert M2[M2.team == "DAL"].ts.tolist() == [0.30] and env2 == env, "the other team and the totals stay"
    assert M.ts.tolist() == [0.25, 0.20, 0.15, 0.30], "the board's frame is never touched"


def test_team_rules_apply_before_the_player_targets():
    M, env = _team()
    M2, env2 = SC.apply_before_sim(M, env, _rules(M, ["HOU: pass=-4, ypt=-10%", "B: targets=6, ypt=9.5"]))
    assert env2["HOU"]["targets"] == 30.0 and env["HOU"]["targets"] == 34.0
    b = M2.set_index("name").loc["B"]
    assert b.ts == pytest.approx(6 / 30) and b.ypt == 9.5, "his own ypt wins over the team change"
    assert M2.set_index("name").loc["A", "ypt"] == pytest.approx(7.2)
    with pytest.raises(ValueError, match="add up to"):
        SC.apply_before_sim(M, env, _rules(M, ["A: targets=20", "B: targets=14"]))


def test_carries_hit_the_number_and_teammates_give_up_the_difference():
    rs = [0.45, 0.30, 0.10]           # back 1, back 2, the QB
    ypc = [4.3, 4.1, 5.0]
    eff = SC.rush_effective_fn(26.0, 30.0, ypc, RESID, None, None, None, None)
    before = eff(rs)
    new = SC.solve_carries(rs, {1: 14.0}, eff)
    after = eff(new)
    assert after[1] == pytest.approx(14.0, abs=0.15), "back 2 gets the carries you set"
    assert sum(new) == pytest.approx(sum(rs)), "the shares' total stays: the team's carries do not grow"
    assert new[0] / new[2] == pytest.approx(rs[0] / rs[2]), "the others keep their proportions"
    assert after[0] < before[0] and after[2] < before[2]
    with pytest.raises(ValueError, match="more than the team's carries allow"):
        SC.solve_carries(rs, {1: 40.0}, eff)
    with pytest.raises(ValueError, match="cannot all be met together"):
        SC.solve_carries(rs, {0: 15.0, 1: 14.0}, eff)     # 29 of a 26-carry team


def test_net_per_100_at_an_american_price():
    assert SC.net_per_100(-110, 0.55, 0.45) == pytest.approx(0.55 * 100 / 1.1 - 45)
    assert SC.net_per_100(150, 0.40, 0.60) == pytest.approx(0.0)
    assert SC.net_per_100(-125, 0.5, 0.4) == pytest.approx(0.5 * 80 - 40), "a push returns the stake"


def test_the_board_never_reads_the_assumptions():
    src = (ENGINE / "score_game.py").read_text(encoding="utf-8")
    assert "if a.scenario_run:       # YOUR scenario" in src, "assumptions apply only inside the scenario run"
    assert "SCENARIO = bool(ASSUME_OUT) or a.scenario_run" in src and 'OUT = OUT / "scenarios"' in src
    assert 'argv = _scenario_argv(("--prior-log", "--prior-archive", "--assume"))' in src,         "an 'if he is out' run never carries them"
    assert "run_user_scenario(pd.DataFrame(rows) if rows" in src, "this run's lines, never the prior-log merge"


def test_the_fast_path_summary_carries_your_scenario():
    src = (ENGINE / "score_game.py").read_text(encoding="utf-8")
    assert "gate=GATE) + SCEN_L" in src, "a --markets run prints the scenario table chat reads"
