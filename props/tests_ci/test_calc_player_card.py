"""The player card (DECISIONS #249): one card per player in a game read -- his lines side by side, this
season once, the facts sorted high or low with shared ones once -- built only from the leg card's pieces,
so every number on it is on his leg cards. Synthetic player, no network."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from props.calc import card, odds, player_card, settings  # noqa: E402
from test_calc_four_part import GA, GL, OPP, SCORING  # noqa: E402
from test_calc_model import _games, _player, rec_model, rush_model  # noqa: E402


def _items():
    fixed = settings.load()["fixed"]
    season, window = _games()
    pl = _player(season, window)
    perf = window.tail(4).assign(opp=["NYG", "PHI", "WAS", "PHI"], snap_pct=[0.6, 0.12, 0.7, 0.65],
                                 fewer_snaps=[False, True, False, False], left_early=[False, True, False, False],
                                 hurt_next=[None, "Out", None, None], rec_yds=[10.0, 4.0, 12.0, 8.0])
    perf["reasons"] = [[], [], ["Lead Back out"], []]
    pl.perf, pl.perf_scope = perf, "recent"
    rush = card.compute(pl, rush_model(ypc=4.2), "rush_yds", 64.5, odds.multiplier_from_american(-125),
                        odds.multiplier_from_american(-132), fixed)
    rec = card.compute(pl, rec_model(rate=0.75), "receptions", 1.5, odds.multiplier_from_american(-172),
                       odds.multiplier_from_american(104), fixed)
    stub = {"player": "Test Back", "team": "DAL"}

    def shown(row, grades):
        return {"opp": "TB", "game_lines": GL, "opp_row": row, "grades": grades, "qb_today": "", "scoring": SCORING,
                "grades_all": GA, "line_note": "Test Back is listed Questionable on this week's official injury report"}
    return [{"pl": pl, "c": rec, "stub": stub, "md_footer": "Sleeper line as of Oct 26, 2:56 PM PT.",
             "shown": shown({"value": 61.0, "games": 4, "who": " to RBs"}, {"off": "A-", "def": "B"})},
            {"pl": pl, "c": rush, "stub": stub, "md_footer": "Sleeper line as of Oct 26, 2:56 PM PT.",
             "shown": shown(OPP, {"off": "B", "def": "C"})}]


def test_one_card_holds_every_line_and_both_sides():
    md = player_card.render_md(_items(), ["Rec yds 12.5: not enough data, so no bar: 9 targets (needs 30)"],
                               ["over", "under"])
    L = md.splitlines()
    assert L[0] == "**Test Back · DAL**" and L[2] == "Rush yds 64.5 · Catches 1.5", "lines in market order"
    assert md.count("Check first: Test Back is listed Questionable") == 1, "one warning, not one per line"
    assert md.count("_Sleeper line as of Oct 26, 2:56 PM PT._") == 1
    # part 1 in three short tables, one question each (readability first, the user 2026-10-26)
    assert L.count("|  | Rush yds 64.5 | Catches 1.5 |") == 3
    for title in ("What the book says", "What each side needs", "His history"):
        assert title in L, title
    for lab in ("Prices", "Its split, margin removed", "Where its 50/50 sits (our math)",
                "Workload it expects (our math)", "Over", "Under", "Average in his last 4 games",
                "Went over the line (in his last 4 games)"):
        assert any(x.startswith(f"| {lab} |") for x in L), lab
    assert not any(x.startswith("| Last-4 average |") for x in L), "the same games as the average: said once"
    assert "| Prices | Over -125 / Under -132 | Over -172 / Under +104 |" in L
    assert "| Went over the line (in his last 4 games) | 1 of 4; 0 of 2 without weeks 2 and 3 | " \
           "0 of 4; 0 of 2 without weeks 2 and 3 |" in L
    assert not any(x.startswith("Test results") for x in L), "the user dropped the section (2026-10-26)"
    assert "- Rec yds 12.5: not enough data, so no bar: 9 targets (needs 30)" in L
    heads = [L.index(x) for x in ("**1 · The lines**", "**2 · His last games**", "**4 · Does it hold up**")]
    assert heads == sorted(heads) and "Part 3, the matchup, is in the game header above." in L
    # a table per stat group, no note column: special weeks starred, the reasons listed once underneath
    assert "| Week | Opp | Carries | Rush yds | Yds/carry | Snaps |" in L
    assert "| Week | Opp | Targets | Catches | Rec yds | Yds/target | Snaps |" in L
    assert "| 2 * | PHI | 12 | 30 | 2.5 | 12% |" in L and "| 2 * | PHI | 2 | 1 | 4 | 2.0 | 12% |" in L
    assert "- Week 2 *: left early (Out next game)" in L and "- Week 3 *: Lead Back out" in L
    assert "| Rush yds 64.5 at 15.5 carries | Yards per carry |" in L and "| Over needs | 4.7 |" in L
    assert "| Average (4) |  | 15.5 | 57.8 | 3.7 |  |" in L and "| Without * (2) |  | 15.5 | 51.5 | 3.3 |  |" in L
    # what needs to be true: one short table, a row per line and a column per side, the basis said once
    i = L.index("What needs to be true")
    assert L[i + 2] == "|  | Over | Under |"
    rows = [x for x in L[i + 4:i + 6]]
    assert rows[0].startswith("| Rush yds 64.5 | ") and rows[1].startswith("| Catches 1.5 | ")
    assert "than his recent average" not in "".join(rows) and "He needs" not in "".join(rows)
    assert "Against his last-4 average workload and his longer-run rate." in L


def test_part_four_is_one_grid_with_a_column_per_line():
    L = player_card.render_md(_items(), [], ["over"]).splitlines()
    assert "| What the card shows | Rush yds 64.5 | Catches 1.5 |" in L
    assert "| Implied points vs his team's scoring | ▼ low · 29.5 vs 27.3 a game | ▼ low · 29.5 vs 27.3 a game |" in L
    assert "| Game script | ▼ low · favored by 9.5: teams ahead tend to run more | " \
           "▲ high · favored by 9.5: teams ahead tend to throw less |" in L
    assert sum(x.startswith("| ") and x.split(" | ")[0][2:] in card.FACTORS for x in L) == len(card.FACTORS)


def test_each_table_stars_its_own_lines_special_games():
    """A receiver out is special for the back's catches, not his carries: the rushing table's Without *
    row must match the rushing column of parts 1 and 4."""
    items = _items()
    rec = items[0]
    rec["pl"] = __import__("copy").copy(rec["pl"])
    rec["pl"].perf = rec["pl"].perf.assign(reasons=[[], [], ["Lead Back out"], ["Top WR out"]])
    L = player_card.render_md(items, [], ["over"]).splitlines()
    assert "| 4 | PHI | 19 | 62 | 3.3 | 65% |" in L, "not starred in the rushing table"
    assert "| 4 * | PHI | 2 | 1 | 8 | 4.0 | 65% |" in L, "starred in the receiving table"
    assert "- Week 4 *: Top WR out (receiving only)" in L
    assert "| Without * (2) |  | 15.5 | 51.5 | 3.3 |  |" in L, "rushing still leaves out weeks 2 and 3 only"


def test_short_keeps_the_longer_run_qualifier():
    assert player_card._short("At his longer-run rate, he needs about 1 more target than his recent average.") == \
        "at his longer-run rate, about 1 more target"
    assert player_card._short("He needs about 8 more carries than his recent average, or 4 more yards a carry than "
                              "his longer-run rate at his recent workload.") == "about 8 more carries, or 4 more yards a carry"


def test_every_number_on_the_player_card_is_on_his_leg_cards():
    items = _items()
    md = player_card.render_md(items, [], ["over", "under"])
    legs = ""
    for g in items:
        kw = {k: g["shown"][k] for k in ("opp", "game_lines", "opp_row", "grades", "qb_today", "scoring", "grades_all",
                                         "line_note")}
        for sd in ("over", "under"):
            legs += card.render_md(g["pl"], g["c"], sd, footer=g["md_footer"], **kw) + "\n"
    nums = lambda t: set(re.findall(r"(?<![\w-])-?\d+(?:\.\d+)?", t))     # noqa: E731
    # the season table shows every stat he has (a catches-only receiver's yards too), checked row by row
    # above; everything else on the card must be a number his leg cards print
    a, b = md.index("**2 · "), md.index("**Rates at his last-4 workload**")
    extra = nums(md[:a] + md[b:]) - nums(legs) - {"4"}       # "last-4" names the window
    assert not extra, extra
    for banned in ("better", "pick", "lean", "recommend", "likely"):
        assert not re.search(rf"\b{banned}\b", md.lower()), banned
