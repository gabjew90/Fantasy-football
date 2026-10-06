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


def test_a_range_reads_low_expected_high_and_prices_three_rule_sets():
    """DECISIONS #175: 'carries=10/12/15' is your low / expected / high; the expected run
    uses the middle value and the low / high runs move every range to its own end."""
    r = SC.parse(["Alvin Kamara (NO): carries=10/12/15", "NO: pass=-4/-2/+1", "Chris Olave: targets=8"],
                 {"NO", "ATL"})
    assert [x["value"] for x in r] == [12.0, -2.0, 8.0]
    assert r[0]["values"] == [10.0, 12.0, 15.0] and "values" not in r[2]
    v = dict(SC.range_variants(SC.resolve_players(r, ["Alvin Kamara", "Chris Olave"], ["NO", "NO"])))
    assert list(v) == ["low", "expected", "high"]
    assert v["low"] == ["Alvin Kamara (NO): carries=10", "NO: pass=-4", "Chris Olave (NO): targets=8"]
    assert v["high"][1] == "NO: pass=+1"
    # every variant string reads back as the single value it names
    for lab, i in (("low", 0), ("expected", 1), ("high", 2)):
        back = SC.parse(v[lab], {"NO", "ATL"})
        assert [x["value"] for x in back] == [r[0]["values"][i], r[1]["values"][i], 8.0]
    pct = dict(SC.range_variants(SC.parse(["X: catch=60%/65%/70%", "NO: ypt=-10%/-5%/0%"], {"NO"})))
    assert SC.parse(pct["low"], {"NO"})[0]["value"] == pytest.approx(0.60)
    assert pct["high"][1] == "NO: ypt=+0%"
    assert SC.range_variants(SC.parse(["X: carries=12"], {"NO"})) is None
    for bad, why in [("X: carries=10/12", "low/expected/high"), ("X: carries=15/12/10", "smallest first"),
                     ("X: carries=10//15", "low/expected/high"), ("NO: pass=-4/-2/1", "CHANGE, not a total")]:
        with pytest.raises(ValueError, match=why):
            SC.parse([bad], {"NO"})


def test_range_verdict_reads_how_much_of_your_range_a_side_needs():
    be = 0.55
    assert SC.range_verdict(0.58, 0.62, 0.66, be) == "pays across your range"
    assert SC.range_verdict(0.50, 0.57, 0.63, be) == "pays at your expected, not at your low"
    assert SC.range_verdict(0.45, 0.52, 0.60, be) == "pays only at your high"
    assert SC.range_verdict(0.40, 0.45, 0.50, be) == "does not pay in your range"
    assert SC.range_verdict(0.50, 0.56, 0.50, be) == "pays only at your expected"
    # a teammate's chances run the other way across the range: the verdict names the end
    assert SC.range_verdict(0.63, 0.46, 0.26, be) == "pays only at your low"
    assert SC.range_verdict(0.66, 0.62, 0.50, be) == "pays at your expected, not at your high"
    assert SC.range_verdict(None, 0.62, None, be) == "pays at your expected; your low and high was not priced"
    assert SC.range_verdict(0.60, 0.62, float("nan"), be) == "pays at your expected; your high was not priced"
    assert SC.range_verdict(0.5, float("nan"), 0.6, be) is None
    assert SC.range_verdict(0.5, 0.6, 0.7, None) is None


def test_role_what_if_reads_player_and_slot():
    r = SC.parse_roles(["Bhayshul Tuten=RB1", "Kendre Miller (NO)=rb2"], {"NO", "JAX"})
    assert r == [{"who": "Bhayshul Tuten", "team_of": None, "slot": "RB1"},
                 {"who": "Kendre Miller", "team_of": "NO", "slot": "RB2"}]
    for bad, why in [("Bhayshul Tuten", "PLAYER=SLOT"), ("=RB1", "PLAYER=SLOT"), ("X=RB3", "slot is one of"),
                     ("X=FB1", "slot is one of")]:
        with pytest.raises(ValueError, match=why):
            SC.parse_roles([bad], {"NO"})


def test_an_out_starter_with_no_priced_replacement_is_flagged():
    pop = pd.DataFrame([
        {"team": "JAX", "name": "Travis Etienne", "pos": "RB", "slot": "RB1", "excluded": True},
        {"team": "JAX", "name": "Tank Bigsby", "pos": "RB", "slot": "RB2", "excluded": False},
        {"team": "JAX", "name": "Brian Thomas", "pos": "WR", "slot": "WR1", "excluded": False},
        {"team": "JAX", "name": "Gabe Davis", "pos": "WR", "slot": "WR2", "excluded": True},
        {"team": "JAX", "name": "Travis Hunter", "pos": "WR", "slot": "WR2", "excluded": False},
        {"team": "JAX", "name": "Parker Washington", "pos": "WR", "slot": "WR3", "excluded": False},
        {"team": "JAX", "name": "Deep Guy", "pos": "WR", "slot": "PROXY", "excluded": True},
    ])
    f = SC.missing_replacements(pop)
    assert [(x["name"], x["priced_left"]) for x in f] == [("Travis Etienne", ["Tank Bigsby"])]
