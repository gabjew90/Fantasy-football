"""The opponent row of the AT block: what his opponent's defense has allowed
this season before the priced week, in the same unit as the needed rate
(card rule 8). Display only: nothing here changes a bar or a rate.

- rushing yards: yards a carry allowed to running backs
- receptions: catches per 10 targets allowed to his position (WR, TE or RB)

Garbage time is left out as the grades leave it out: plays where the
offense's win probability is outside garbage_wp_low-high. Positions are each
ball carrier's roster listing as it stood in the week of the play. Under
thin_games games: "[Opponent]: only G games." (value None)."""

from __future__ import annotations

import pandas as pd

WHO = {"RB": " to RBs", "WR": " to WRs", "TE": " to TEs"}


def _listed(b, season: int) -> pd.DataFrame:
    """(week, gsis_id, position): each player's latest roster listing up to
    each week of the season (a player's position as it stood then)."""
    r = b._roster_pos[b._roster_pos["season"] == season][["week", "gsis_id", "position"]]
    return r.sort_values("week")


def _with_position(plays: pd.DataFrame, listed: pd.DataFrame) -> pd.DataFrame:
    if plays.empty:
        return plays.assign(position=pd.Series(dtype=object))
    p = plays.sort_values("week").reset_index(drop=True)
    return pd.merge_asof(p, listed.rename(columns={"week": "roster_week"}).sort_values("roster_week"),
                         left_on="week", right_on="roster_week", by="gsis_id", direction="backward")


def allows(b, market: str, opp: str, position: str, season: int, week: int, fixed: dict) -> dict:
    """{"value", "games", "who"}: value None under the minimum games."""
    lo, hi = fixed["garbage_wp_low"], fixed["garbage_wp_high"]
    src = b.carries if market == "rush_yds" else b.targets
    d = b.cut(src[(src["season"] == season) & (src["defteam"] == opp)], season, week, "opponent plays")
    plays = b.cut(b.pbp[(b.pbp["season"] == season)
                        & ((b.pbp["posteam"] == opp) | (b.pbp["defteam"] == opp))], season, week, "opponent games")
    games = int(plays["game_id"].nunique())
    who = " to RBs" if market == "rush_yds" else WHO.get(position, f" to {position}s")
    if games < int(fixed["thin_games"]):
        return {"value": None, "games": games, "who": who}
    d = d[d["wp"].between(lo, hi)]
    d = _with_position(d, _listed(b, season))
    d = d[d["position"] == ("RB" if market == "rush_yds" else position)]
    if d.empty:
        return {"value": None, "games": games, "who": who}
    if market == "rush_yds":
        value = float(d["yards"].sum() / len(d))
    else:
        value = float(10 * d["caught"].mean())
    return {"value": value, "games": games, "who": who, "plays": int(len(d))}
