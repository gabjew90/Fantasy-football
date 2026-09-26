"""The props question tools (props/ask.py).

The engine is not run: a game's output files are written by hand into a temp
NFL_OUT, the way score_game.py writes them. What is pinned is that every
number comes from those files unchanged, that a line the ladder does not carry
is never interpolated, that the card keeps the engine's order, and that the
engine's honesty rules ride on every answer."""

from __future__ import annotations

import datetime as dt
import os
import time

import pandas as pd
import pytest

from props import ask as A

SLUG = "2026_wk03_KC_MIA"
REPORT = """# KC at MIA
### 2026 Week 3 · 2026-09-27 13:00 ET · Hard Rock Stadium

**2 of 3 priced rows have positive expected value at the posted price** -- none is eligible to bet (no market is validated against sportsbook lines).

## Game header

- **Frame:** DK MIA +10, total 45.5, implied MIA 17.8 / KC 27.8.
- **Weather:** 78-84F, wind to 5 mph.

<details><summary>Method</summary>
- **Not a bullet:** inside details.
</details>

**Game-script thesis.** 2 of the card's legs ride on 'KC throws high'.

## Bet card

table

## KC (away)

Offense projects about 33 throws, 27 runs, 2.9 offensive touchdowns.

### Travis Kelce — TE1

**Role.** 20% of his team's throws last season.

| Call | Prop |
|---|---|

### Rashee Rice — WR1

**Role.** WR1.

## MIA (home)

Offense projects about 27 throws, 24 runs, 1.9 offensive touchdowns.

## If a Questionable player is out

Every line above is priced as if the Questionable players play.

### If Rashee Rice (KC WR) is out

| player | line |
"""


def _shadow(**over):
    base = dict(logged_at_utc="2026-09-26T20:00:00Z", season=2026, week=3, event_id="e", book="sleeper",
                team="KC", slot="TE1", model_mean=5.2, p_push=0.0, last_update="x", new_team=False,
                questionable=False, td_model=None, two_sided=None, p_market=None, p_blend=None, blend_w=None,
                questionable_teammate=False, flag=None, model_state="receiving_hier_v2, MODEL_UNVALIDATED",
                decision="PASS", eligible=False, ineligible_because="model not validated",
                clears_edge_rule_if_validated=False, tier=None)
    base.update(over)
    return base


@pytest.fixture
def game(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL_CACHE", str(tmp_path))
    d = A.root()
    (d / "scenarios").mkdir(parents=True)
    pd.DataFrame([
        _shadow(market="player_receptions", player="Travis Kelce", line=4.5, side="Over", p_model=0.548,
                p_novig=0.479, gap=0.069, price=-116, ER=0.021, tier="STRONG"),
        _shadow(market="player_reception_yds", player="Travis Kelce", line=52.5, side="Under", p_model=0.522,
                p_novig=0.503, gap=0.02, price=-130, ER=-0.076),
        _shadow(market="player_anytime_td", player="Travis Kelce", line=None, side="Yes", p_model=0.26,
                p_novig=0.386, gap=-0.125, price=129, ER=-0.40, td_model="anytime_td_v1", two_sided=True,
                p_market=0.386, p_blend=0.32, blend_w=0.5, flag="large gap - market likely holds info model lacks"),
        _shadow(market="player_receptions", player="Rashee Rice", slot="WR1", line=5.5, side="Under",
                p_model=0.6, p_novig=0.5, gap=0.1, price=-110, ER=0.05, tier="STRONG"),
    ]).to_csv(d / f"shadow_log_{SLUG}.csv", index=False)
    pd.DataFrame([dict(player="Travis Kelce", team="KC", prop="catches", book="sleeper", book_line=4.5,
                       our_median=5.0, under_at=5.5, over_at=4.5, call="no play")]).to_csv(
        d / f"betting_card_{SLUG}.csv", index=False)
    # the card in the ENGINE's order: Rice first although Kelce's EV is lower -- a
    # tool that re-sorted by EV would flip them
    pd.DataFrame([dict(player="Rashee Rice", team="KC", prop="catches", side="Under", line=5.5, book="sleeper",
                       price=-110, model_p=0.6, novig_p=0.5, edge_pts=10.0, ev_per_100=5.0, tier="STRONG", note=None,
                       correlated_with=None),
                  dict(player="Travis Kelce", team="KC", prop="catches", side="Over", line=4.5, book="sleeper",
                       price=-116, model_p=0.548, novig_p=0.479, edge_pts=7.0, ev_per_100=9.0, tier="STRONG",
                       note=None, correlated_with="KC throws high")]).to_csv(d / f"bet_card_{SLUG}.csv", index=False)
    pd.DataFrame([dict(player="Travis Kelce", team="KC", book="sleeper", price=129, p_model=0.26, p_novig=0.386,
                       p_market=0.386, p_blend=0.32, decision="PASS", flag=None)]).to_csv(
        d / f"td_board_{SLUG}.csv", index=False)
    lad = [dict(player="Travis Kelce", team="KC", stat="catches", threshold=float(k), p_at_or_below=p)
           for k, p in zip(range(0, 9), (0.02, 0.07, 0.17, 0.30, 0.45, 0.59, 0.70, 0.80, 0.88))]
    lad += [dict(player="Travis Kelce", team="KC", stat="rec yds", threshold=t, p_at_or_below=p)
            for t, p in ((50.5, 0.50), (55.5, 0.55), (60.5, 0.60))]
    pd.DataFrame(lad).assign(p_over_half=lambda x: 1 - x.p_at_or_below).to_csv(d / f"ladder_{SLUG}.csv", index=False)
    pd.DataFrame([dict(team="KC", gsis_id="00-1", name="Travis Kelce", pos="TE", slot="TE1", status="ACT",
                       questionable=False, new_team=False, prior_team="KC", snap_pct=0.78),
                  dict(team="KC", gsis_id="00-2", name="Rashee Rice", pos="WR", slot="WR1", status="ACT",
                       questionable=True, new_team=False, prior_team="KC", snap_pct=0.9)]).to_csv(
        d / f"player_params_{SLUG}.csv", index=False)
    pd.DataFrame([dict(player="Travis Kelce", team="KC", median=11.8, p10=4.1, p20=6.0, p80=18.0, p90=22.7,
                       mean=12.4, p_td=0.26)]).to_csv(d / f"fantasy_points_{SLUG}.csv", index=False)
    # the 'if Rice is out' run moves Kelce's catches Over from 55% to 60%
    pd.DataFrame([dict(book="sleeper", market="player_receptions", player="Travis Kelce", side="Over", line=4.5,
                       p_model=0.60)]).to_csv(d / "scenarios" / f"shadow_log_{SLUG}_out_00-2.csv", index=False)
    (d / f"report_{SLUG}.md").write_text(REPORT, encoding="utf-8")
    calls = []

    def fake_price(season, week, away, home, *, fresh=False):
        calls.append((away, home, fresh))
        return {"slug": A.slug(season, week, away, home), "dir": d, "age_min": 3.0, "ran": False}
    monkeypatch.setattr(A, "price_game", fake_price)
    monkeypatch.setattr(A, "season_week", lambda s=None, w=None: (2026, 3))
    return calls


# ------------------------------------------------------------------ player

def test_a_player_answer_is_every_priced_line_read_unchanged(game):
    r = A.player("Kelce", game="KC@MIA")
    lines = {x["market"]: x for x in r.data["lines"]}
    assert lines["catches"]["p_model"] == 0.548 and lines["catches"]["p_novig_same_side"] == 0.479
    assert lines["catches"]["call"] == "no play" and lines["catches"]["under_from"] == 5.5
    assert lines["anytime TD"]["p_blend"] == 0.32 and lines["anytime TD"]["p_market"] == 0.386
    assert r.data["fantasy_points"]["median"] == 11.8
    assert r.data["engine_on_him"][0] == "Travis Kelce — TE1", "the report's own words on him"


def test_a_player_answer_carries_the_rules_that_apply_to_it(game):
    r = A.player("Travis Kelce", game="KC@MIA")
    assert A.UNVALIDATED in r.data["rules"] and A.TD_RULE in r.data["rules"], "a TD row brings the no-fair-odds rule"
    assert any("market likely holds info" in x or "knowing something" in x for x in r.data["rules"])
    assert "no fair odds" in r.text
    assert A.NEW_TEAM_RULE not in r.data["rules"] and A.TD_V0_RULE not in r.data["rules"]
    rice = A.player("Rashee Rice", game="KC@MIA")
    assert any("Questionable" in x and "void" in x for x in rice.data["rules"])


def test_a_fallback_td_model_and_a_new_team_bring_their_rules(game):
    d = A.root()
    sl = pd.read_csv(d / f"shadow_log_{SLUG}.csv")
    sl.loc[sl.market == "player_anytime_td", "td_model"] = "anytime_td_v0"
    sl.to_csv(d / f"shadow_log_{SLUG}.csv", index=False)
    pp = pd.read_csv(d / f"player_params_{SLUG}.csv")
    pp.loc[pp.name == "Travis Kelce", "new_team"] = True
    pp.to_csv(d / f"player_params_{SLUG}.csv", index=False)
    r = A.player("Kelce", game="KC@MIA")
    assert A.TD_V0_RULE in r.data["rules"] and A.NEW_TEAM_RULE in r.data["rules"]


def test_a_questionable_teammates_absence_is_read_from_the_engines_scenario_run(game):
    r = A.player("Kelce", game="KC@MIA")
    assert r.data["if_teammate_out"] == [{"if_out": "Rashee Rice", "market": "catches", "side": "Over",
                                          "line": 4.5, "p_if_he_plays": 0.548, "p_if_out": 0.6}]


def test_a_player_already_priced_this_session_is_found_without_a_game(game):
    r = A.player("Kelce")
    assert r.data["player"] == "Travis Kelce" and game[-1][:2] == ("KC", "MIA")


def test_a_name_the_engine_did_not_price_says_so(game):
    with pytest.raises(A.AskError, match="no lines or role"):
        A.player("Tyreek Hill", game="KC@MIA")


# ------------------------------------------------------------------ line

def test_a_line_is_read_off_the_ladder_with_pushes_for_whole_numbers(game):
    half = A.line("Kelce", "receptions", 4.5, game="KC@MIA")
    assert half.data["p_under"] == 0.45 and half.data["p_over"] == 0.55
    whole = A.line("Kelce", "catches", 5, game="KC@MIA")
    assert whole.data["p_under"] == 0.45 and whole.data["p_push"] == 0.14 and whole.data["p_over"] == 0.41
    yds = A.line("Kelce", "rec_yds", 55.5, game="KC@MIA")
    assert yds.data["p_under"] == 0.55


def test_a_line_the_ladder_lacks_is_bracketed_never_interpolated(game):
    r = A.line("Kelce", "receiving yards", 58, game="KC@MIA")
    assert r.data["p_under"] is None
    assert r.data["nearest"] == [{"line": 55.5, "p_under": 0.55}, {"line": 60.5, "p_under": 0.6}]
    assert "Not interpolated" in r.text


def test_an_unknown_stat_is_refused(game):
    with pytest.raises(A.AskError, match="unknown stat"):
        A.line("Kelce", "tackles", 3.5, game="KC@MIA")


# ------------------------------------------------------------------ best, matchup

def test_the_card_keeps_the_engines_order(game):
    r = A.best("KC@MIA")
    assert [x["player"] for x in r.data["card"]] == ["Rashee Rice", "Travis Kelce"]
    assert r.data["headline"].startswith("**2 of 3 priced rows")
    assert A.UNVALIDATED in r.text and A.TD_RULE in r.text
    only = A.best("KC@MIA", market="td")
    assert only.data["card"] == [] and only.data["td_board"], "--market td shows the TD board only"


def test_the_matchup_is_the_reports_frame(game):
    r = A.matchup("KC@MIA")
    f = r.data["frame"]
    assert f["bullets"] == ["**Frame:** DK MIA +10, total 45.5, implied MIA 17.8 / KC 27.8.",
                            "**Weather:** 78-84F, wind to 5 mph."], "nothing from inside <details>"
    assert [t["team"] for t in f["teams"]] == ["KC", "MIA"]
    assert f["teams"][0]["offense"].startswith("Offense projects about 33 throws")
    assert f["thesis"].startswith("**Game-script thesis.**")
    assert any("If Rashee Rice" in x for x in r.data["questionable_out"])


def test_section_readers():
    assert A.section(REPORT, "Bet card") == ["", "table", ""]
    assert A.section(REPORT, "No such heading") == []
    assert A.player_section(REPORT, "Rashee Rice") == ["Rashee Rice — WR1", "**Role.** WR1."]
    assert A.player_section(REPORT, "Nobody") == []


def test_names_match_exactly_then_by_last_name():
    names = ["Travis Kelce", "Kenneth Walker III", "De'Von Achane", "Travis Etienne"]
    assert A.match("travis kelce", names) == ["Travis Kelce"]
    assert A.match("Walker", names) == ["Kenneth Walker III"]
    assert A.match("devon achane", names) == ["De'Von Achane"]
    assert A.match("Travis", names) == ["Travis Kelce", "Travis Etienne"]


# ------------------------------------------------------------------ runs

def test_a_run_is_reused_while_young_and_repriced_when_old(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL_CACHE", str(tmp_path))
    ran = []

    class R:
        returncode, stdout, stderr = 0, "", ""

    def fake_run(cmd, **kw):
        ran.append(cmd)
        (A.root() / f"shadow_log_{SLUG}.csv").write_text("x\n1\n", encoding="utf-8")
        return R()
    monkeypatch.setattr(A.subprocess, "run", fake_run)
    first = A.price_game(2026, 3, "KC", "MIA")
    assert first["ran"] and len(ran) == 1
    assert "--workdir" in ran[0], "one shared workdir: nflverse files fetched once a session"
    assert A.price_game(2026, 3, "KC", "MIA")["ran"] is False and len(ran) == 1
    old = time.time() - 60 * (A.TTL_MIN + 1)
    os.utime(A.root() / f"shadow_log_{SLUG}.csv", (old, old))
    assert A.price_game(2026, 3, "KC", "MIA")["ran"] and len(ran) == 2


def test_an_engine_failure_is_the_error_not_a_stale_answer(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL_CACHE", str(tmp_path))

    class R:
        returncode, stdout, stderr = 1, "", "Traceback\nValueError: no such game"
    monkeypatch.setattr(A.subprocess, "run", lambda cmd, **kw: R())
    with pytest.raises(A.AskError, match="no such game"):
        A.price_game(2026, 3, "KC", "MIA")
