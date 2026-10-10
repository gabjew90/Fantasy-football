"""The four markets, their workload, and the names other sources use for them."""

from __future__ import annotations

MARKETS = {
    # key: (label on the card, workload column, stat column, workload words)
    "rush_yds": ("rushing yards", "carries", "rush_yds", "carries"),
    "receptions": ("receptions", "targets", "receptions", "passes thrown to him"),
    "rec_yds": ("receiving yards", "targets", "rec_yds", "passes thrown to him"),
    "pass_yds": ("passing yards", "completions", "pass_yds", "completions"),
}
SLEEPER_WAGER = {"rushing_yards": "rush_yds", "receptions": "receptions",
                 "receiving_yards": "rec_yds", "passing_yards": "pass_yds"}
ARCHIVE_MARKET = {"player_rush_yds": "rush_yds", "player_receptions": "receptions",
                  "player_reception_yds": "rec_yds", "player_pass_yds": "pass_yds"}


def label(market: str) -> str:
    return MARKETS[market][0]


def workload_col(market: str) -> str:
    return MARKETS[market][1]


def stat_col(market: str) -> str:
    return MARKETS[market][2]


def workload_words(market: str) -> str:
    return MARKETS[market][3]
