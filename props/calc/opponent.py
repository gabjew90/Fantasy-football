"""The opponent row of the AT block: what his opponent's defense has allowed
this season before the priced week, in the same unit as the needed rate
(card rule 8). Display only: nothing here changes a bar or a rate.

- rushing yards: yards a carry allowed to running backs
- receptions: catches per 10 targets allowed to his position (WR, TE or RB)
- receiving yards: yards a target allowed to his position (incompletions 0)
- passing yards: yards a completion allowed (every passer)

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


def allows(b, market: str, opp: str, position: str | None, season: int, week: int, fixed: dict) -> dict:
    """{"value", "games", "who", "thin", "left_out"[, "plays"]}: value None
    under the minimum games (thin) or with no plays to his position. A play
    with no win probability, or whose ball carrier has no roster listing up to
    that week (nor last season), is left out and counted in left_out, which
    the card shows: never dropped without a word."""
    lo, hi = fixed["garbage_wp_low"], fixed["garbage_wp_high"]
    src = b.carries if market == "rush_yds" else (b.completions if market == "pass_yds" else b.targets)
    d = b.cut(src[(src["season"] == season) & (src["defteam"] == opp)], season, week, "opponent plays")
    plays = b.cut(b.pbp[(b.pbp["season"] == season)
                        & ((b.pbp["posteam"] == opp) | (b.pbp["defteam"] == opp))], season, week, "opponent games")
    games = int(plays["game_id"].nunique())
    want = "RB" if market == "rush_yds" else (None if market == "pass_yds" else position)
    who = "" if market == "pass_yds" else WHO.get(want, f" to {want}s" if want else " to his position")
    if games < int(fixed["thin_games"]):
        return {"value": None, "games": games, "who": who, "thin": True, "left_out": 0}
    no_wp = int(d["wp"].isna().sum())
    d = d[d["wp"].between(lo, hi)]
    if market == "pass_yds":                   # every passer counts: no position to look up
        out = {"value": None, "games": games, "who": who, "thin": False, "left_out": no_wp}
        return out if d.empty else {**out, "value": float(d["yards"].mean()), "plays": int(len(d))}
    d = _with_position(d, _listed(b, season))
    miss = d["position"].isna()
    if miss.any():                             # no listing yet this season: his last listing of last season
        prior = getattr(b, "position", {}) or {}
        d.loc[miss, "position"] = [prior.get((season - 1, g)) for g in d.loc[miss, "gsis_id"]]
    unlisted = int(d["position"].isna().sum())
    d = d[d["position"] == want] if want else d.iloc[0:0]
    out = {"value": None, "games": games, "who": who, "thin": False, "left_out": no_wp + unlisted}
    if d.empty:
        return out
    if market == "receptions":
        value = float(10 * d["caught"].mean())
    else:                                      # yards a carry, or yards a target (data.targets: incompletions are 0)
        value = float(d["yards"].sum() / len(d))
    return {**out, "value": value, "plays": int(len(d))}
