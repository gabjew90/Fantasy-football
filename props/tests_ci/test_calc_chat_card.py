"""The chat card (card.render_md, DECISIONS #238): the user's layout for chat, printed from the same
parts as the text card -- every number on it is on the text card, the test wording is exact, and
every rate names its unit. A synthetic player, no network."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from props.calc import card, odds, settings  # noqa: E402
from test_calc_model import _games, _player, rec_model, rush_model  # noqa: E402

GL = {"favorite": "DAL", "points": 9.5, "spread_text": "DAL -9.5", "spread_unread": False, "total": 49.5}
OPP = {"value": 4.43, "games": 4, "who": " to RBs"}
KW = dict(opp="TB", game_lines=GL, footer="Line as of Oct 8, 4:59 PM PT.", opp_row=OPP, grades={"off": "B", "def": "C"})


def _rush(side="over", **kw):
    fixed = settings.load()["fixed"]
    season, window = _games()
    pl = _player(season, window)
    c = card.compute(pl, rush_model(ypc=4.2), "rush_yds", 64.5, odds.multiplier_from_american(-125),
                     odds.multiplier_from_american(-132), fixed)
    return pl, c, card.render(pl, c, side, **{**KW, **kw}), card.render_md(pl, c, side, **{**KW, **kw})


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"-?\d+(?:\.\d+)?", text))


def test_the_chat_card_follows_the_users_layout():
    pl, c, text, md = _rush()
    L = md.splitlines()
    assert L[0] == "**Test Back · Rushing yards**" and L[2] == "Over 64.5 rushing yards · -125"
    assert "Reliability: Tested on 2018-25: held up where it could be checked." in L
    bar = card._round(card.value(c, "needed_over"))
    assert f"**Average workload needed: ~{bar} carries**" in L
    assert "| Workload | Carries |" in L and f"| Needed at this price | **~{bar} carries** |" in L
    assert "| Recent 4-game average | 15.5 |" in L
    assert "Last 4: 12 · 12 · 19 · 19" in L and any(x.startswith(f"{bar}+ carries this season: ") for x in L)
    assert not any(x.endswith(" ") for x in L), "no trailing-space line breaks: each line is its own paragraph"
    assert "**At his recent workload (15.5 carries)**" in L and "| Yards per carry | Rate |" in L
    assert "| Calculator's assumed rate | 4.2 yards a carry |" in L
    assert "| Opponent has allowed | 4.4 yards a carry to RBs |" in L
    assert "Opponent figure: 4 games, garbage time left out." in md
    assert "Matchup: DAL run offense B vs TB run defense C. Dallas favored by 9.5. Total 49.5." in L
    assert any(x.startswith("What needs to be true: ") for x in L) and "?" not in md
    assert L[-1] == "_Line as of Oct 8, 4:59 PM PT._"
    assert "```" not in md and "~" not in md.replace(f"~{bar}", "")
    # bold only on what the bet needs: the bar (heading and cell) and the needed rate
    bolds = re.findall(r"\*\*(.+?)\*\*", md)
    assert bolds[0] == "Test Back · Rushing yards" and len(bolds) == 5, bolds


def test_every_number_on_the_chat_card_is_on_the_text_card():
    for side in ("over", "under"):
        pl, c, text, md = _rush(side)
        body = md.split("What needs to be true:")[0]       # the condition restates the asks (checked below)
        extra = _numbers(body) - _numbers(text) - {"4"}     # "Recent 4-game average" names the window
        assert not extra, (side, extra)
        assert card.TEST_STATUS["rush_yds"] in md


def test_the_condition_states_the_same_asks_as_the_question():
    q, cnd = card.question, card.condition
    assert q("rush_yds", "over", 1.6, 0.46) == "About 1.5 more carries, or 0.5 more yards a carry?"
    assert cnd("rush_yds", "over", 1.6, 0.46) == ("He needs about 1.5 more carries than his recent average, or 0.5 "
                                                  "more yards a carry than the assumed rate at his recent workload.")
    assert cnd("rush_yds", "over", 2.8, -0.2) == "At his recent rate, he needs about 3 more carries than his recent average."
    assert cnd("rush_yds", "over", -0.2, 0.3) == "His recent workload is there; he needs 0.3 more yards a carry than the assumed rate."
    assert cnd("rush_yds", "over", 0.1, -0.1) == "His recent workload and rate both meet the bar."
    assert cnd("rush_yds", "over", -2.0, -0.1) == "His recent workload and rate meet the bar, with room for about 2 fewer carries."
    assert cnd("rush_yds", "under", -1.1, None) == "He needs about 1 fewer carry than his recent average."
    assert cnd("receptions", "over", None, 0.5) == "He needs 0.5 more catches per 10 targets than the assumed rate."
    assert cnd("rush_yds", "under", None, -0.3) == "He needs 0.3 yards a carry less than the assumed rate."
    assert cnd("rush_yds", "over", -1.0, None, reached=1) == "His recent average meets the bar, but only 1 of his last 4 games did."
    assert cnd("rush_yds", "over", None, None) == "" == q("rush_yds", "over", None, None)


def test_every_rate_names_its_unit_on_both_cards():
    fixed = settings.load()["fixed"]
    season, window = _games()
    pl = _player(season, window)
    c = card.compute(pl, rec_model(0.75), "receptions", 1.5, 1.8, 1.9, fixed)
    row = {"value": 6.71, "games": 5, "who": " to RBs"}
    text = " ".join(card.render(pl, c, "over", opp="TB", opp_row=row).splitlines())
    md = card.render_md(pl, c, "over", opp="TB", opp_row=row)
    assert re.search(r"His recent rate \(5 games\): \d\.\d catches per 10 targets", text)
    assert re.search(r"This season: \d\.\d catches per 10 targets", text)
    assert "Tampa Bay allows: 6.7 catches per 10 targets to RBs (5 games)" in text
    assert "| Catches per 10 targets | Rate |" in md and "| Opponent has allowed | 6.7 catches per 10 targets to RBs |" in md
    assert re.search(r"\| This season \| \d\.\d catches per 10 targets( \(\d+ targets\))? \|", md)


def test_out_of_range_bars_and_the_not_enough_card_in_chat():
    fixed = settings.load()["fixed"]
    season, window = _games()
    pl = _player(season, window)
    c = card.compute(pl, rush_model(ypc=1.0), "rush_yds", 300.5, 1.8, 1.76, fixed)
    over = card.render_md(pl, c, "over", opp="TB")
    assert "**Average workload needed: no workload up to 45 carries clears it**" in over
    assert "| Workload |" not in over, "no bar: no workload table"
    assert "Last 4: 12 · 12 · 19 · 19 (average 15.5)" in over, "the average still shows, beside the games"
    pl.not_enough["rush_yds"] = ["12 of his own carries in his last 16 games (needs 30)"]
    ne = card.render_not_enough_md(pl, "rush_yds", "over", 64.5, 1.8, 1.76, footer="Line typed in.")
    assert ne.splitlines()[:3] == ["**Test Back · Rushing yards**", "", "Over 64.5 rushing yards · -125"]
    assert "- 12 of his own carries in his last 16 games (needs 30)" in ne and "Average workload" not in ne
    assert "Last games (carries): 12 · 12 · 19 · 19" in ne         # oldest first, as on the text card
    assert ne.rstrip().endswith("_Line typed in._")
    with pytest.raises(ValueError):
        card.render_md(pl, c, "over", opp="TB")


def test_a_marked_game_and_the_short_history_reach_the_chat_card():
    fixed = settings.load()["fixed"]
    season, window = _games()
    window["fewer_snaps"] = [False, False, False, True, False]      # 2026 week 3
    window["backup_qb"] = [False, False, False, True, False]
    window["qb_started"] = [None, None, None, "B.Backup", None]
    pl = _player(season, window)
    c = card.compute(pl, rush_model(ypc=4.2), "rush_yds", 64.5, 1.8, 1.76, fixed)
    md, text = card.render_md(pl, c, "over", opp="TB"), card.render(pl, c, "over", opp="TB")
    assert "Last 4: 12 · 12 · 19* · 19" in md and "Last 4: 12, 12, 19*, 19" in text
    assert "* Week 3: played far fewer snaps than usual." in md.splitlines()
    assert "* Week 3: B.Backup started at QB." in md.splitlines(), "two notes for one game: two bullets"
    short = _player(season.iloc[:2], window.iloc[3:])                  # two games: weeks 3-4
    cs = card.compute(short, rush_model(ypc=4.2), "rush_yds", 64.5, 1.8, 1.76, fixed)
    smd = card.render_md(short, cs, "over", opp="TB")
    assert "Last 2: 19* · 19" in smd and "Short history: 2 games." in smd
    assert "| Workload |" not in smd and "no recent average yet" in smd


# ---------------------------------------------------------------- the entry and the commands in chat layout

from props.calc import summary  # noqa: E402
from test_calc_model import QUOTE, _entry_args, _leg_args, stub_leg  # noqa: E402,F401
from test_calc_summary import LEGS  # noqa: E402


def test_the_chat_entry_puts_the_comparison_first_then_cards_then_the_fit_check():
    md = summary.render_md(LEGS, 5.0, 50.0, False, ["CARD ONE", "CARD TWO"])
    text = summary.render(LEGS, 5.0, 50.0, payout_from_legs=False)
    L = md.splitlines()
    assert L[0] == "**Your $5 entry · 4 legs**" and "Return if all win: **$50.00**. Includes your $5 stake." in L
    i_tab, i_one, i_two, i_fit = (L.index("| Leg | What each needs (biggest ask first) |"), L.index("CARD ONE"),
                                  L.index("CARD TWO"), L.index("**Fit check**"))
    assert i_tab < i_one < i_two < i_fit
    assert L[i_tab + 2] == "| Javonte Williams · rushing yards Over | ~17 carries, about 1.5 more than recent |"
    assert L.count("---") == 3, "one divider before each card and before the fit check"
    assert "- Javonte Williams: more than 55.6 wins in 100." in L
    assert "**To cover the entry cost:** all must win more than 56.2 in 100." in L
    assert "Average loss: $1.88 per $5 entry." in md and md.endswith(summary.FOLLOW_UPS)
    # the same numbers as the text summary, nothing added
    flat = " ".join(text.splitlines())
    for a, b in summary.opposing_pairs(LEGS):
        assert f"{a} {b} These lean on opposite game stories." in md and a in flat
    import re
    nums = lambda s: set(re.findall(r"\d+(?:\.\d+)?", s))      # noqa: E731
    assert nums(md.replace("CARD ONE", "").replace("CARD TWO", "")) - {"10"} <= nums(text) | {"1", "2"}


def test_the_chat_entry_says_when_every_leg_is_on_one_team():
    md = summary.render_md([LEGS[0], LEGS[1]], 5.0, 20.0, True, [])
    assert "SECOND TEAM NEEDED: every leg is on DAL." in md and "worked out from the legs' own prices" in md
    assert md.index("SECOND TEAM NEEDED") < md.index("| Leg |"), "said before the numbers"


def test_leg_and_entry_print_the_chat_layout_with_format_md(stub_leg, monkeypatch):
    cli, lookup, pl = stub_leg
    from props.calc import player
    monkeypatch.setattr(player, "model", lambda *a, **k: rush_model(ypc=4.2))
    lookup.quote = dict(QUOTE)
    text, md = cli.leg(_leg_args()), cli.leg(_leg_args(format="md"))
    assert text.splitlines()[2] == "TEST BACK" and md.startswith("**Test Back · Rushing yards**")
    assert md.rstrip().endswith("_Sleeper line as of Oct 11, 11:00 AM PT._"), "the chat card names the source"
    assert text.rstrip().endswith("Line as of Oct 11, 11:00 AM PT.")
    out = cli.entry(_entry_args(dry_run=True, format="md"))
    assert out.startswith("**Your $5 entry · 2 legs**")
    assert out.index("| Leg |") < out.index("**Test Back · Rushing yards**") < out.index("**Fit check**")
    assert "DRY RUN: nothing written" in out
