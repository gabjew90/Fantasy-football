"""One player before one week: who he is, his blended rates, the pools the
calculator draws from, and the plain history rows the card shows.

Everything here is cut at the priced week (data.before): nothing from that
week or later is read.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import calc, data, names
from .markets import workload_col


class Bundle:
    """The seasons a card or a test needs, loaded once and cut per week."""

    def __init__(self, seasons, *, manifest=None):
        self.seasons = sorted(set(seasons))
        plays = [data.pbp(s, manifest=manifest) for s in self.seasons]
        self.pbp = pd.concat(plays, ignore_index=True)
        self.carries = data.carries(self.pbp)
        self.targets = data.targets(self.pbp)
        self.games = data.player_games(self.pbp)
        self.rosters = pd.concat([data.rosters(s, manifest=manifest) for s in self.seasons], ignore_index=True)
        self.schedule = data.schedule(manifest=manifest)
        pos = (self.rosters.dropna(subset=["gsis_id", "position"])
               .sort_values(["season", "week"]).drop_duplicates(["season", "gsis_id"], keep="last"))
        self.position = {(s, g): p for s, g, p in zip(pos["season"], pos["gsis_id"], pos["position"])}
        self._pools: dict = {}

    def position_of(self, gsis: str, season: int) -> str | None:
        for s in (season, season - 1, season + 1):
            p = self.position.get((s, gsis))
            if p:
                return p
        return None

    def with_position(self, df: pd.DataFrame) -> pd.DataFrame:
        pos = [self.position.get((s, g)) for s, g in zip(df["season"], df["gsis_id"])]
        return df.assign(position=pos)

    def pools(self, season: int, pool_seasons: int) -> dict:
        """Per-play pools from the `pool_seasons` seasons before `season`."""
        key = (season, pool_seasons)
        if key not in self._pools:
            yrs = range(season - pool_seasons, season)
            c = self.with_position(self.carries[self.carries["season"].isin(yrs)])
            t = self.with_position(self.targets[self.targets["season"].isin(yrs)])
            if c.empty or t.empty:
                raise ValueError(f"no plays from {list(yrs)} loaded for the pools")
            rb = c.loc[c["position"] == "RB", "yards"].to_numpy(float)
            self._pools[key] = {
                "rb_residuals": rb - rb.mean(),
                "ypc_by_pos": c.groupby("position")["yards"].mean().to_dict(),
                "catch_by_pos": t.groupby("position")["caught"].mean().to_dict(),
                "catch_by_pos_bucket": t.assign(bucket=depth_buckets(t["air_yards"]))
                                        .groupby(["position", "bucket"])["caught"].mean().to_dict(),
            }
        return self._pools[key]


def depth_buckets(air: pd.Series, short_below: float = 5, deep_from: float = 15) -> pd.Series:
    out = pd.Series(np.where(air < short_below, "short", np.where(air >= deep_from, "deep", "medium")),
                    index=air.index)
    return out.where(air.notna(), None)


@dataclass
class Rate:
    blended: float
    own: float | None       # his own rate over the window (None with no plays)
    own_n: int              # his opportunities in the window
    season: float | None    # his plain rate this season before the week
    season_n: int
    baseline: float


def blend(own_sum: float, n: int, baseline: float, k: float) -> float:
    """w * own + (1 - w) * baseline with w = n / (n + k)."""
    return (own_sum + k * baseline) / (n + k)


@dataclass
class Player:
    gsis_id: str
    name: str
    team: str
    position: str
    season: int
    week: int
    window: pd.DataFrame               # his last games played before the week (player_games rows)
    season_games: pd.DataFrame         # this season's games before the week, with result and starter
    rates: dict = field(default_factory=dict)
    pools: dict = field(default_factory=dict)

    def usual(self, market: str, games: int) -> float | None:
        w = self.window.tail(games)
        return float(w[workload_col(market)].mean()) if len(w) else None


def find_player(b: Bundle, name: str, season: int, team: str | None = None) -> tuple[str, str, str]:
    """(gsis_id, full name, team) for a typed name. The name must point at one
    player on the season's rosters (with the team when given)."""
    r = b.rosters[(b.rosters["season"] == season) & b.rosters["gsis_id"].notna()]
    r = r.sort_values("week").drop_duplicates("gsis_id", keep="last")
    key = names.norm(name)
    hit = r[r["full_name"].map(names.norm) == key]
    if team:
        hit = hit[hit["team"] == names.team_code(team)]
    if hit.empty:
        cands = [{"gsis_id": g, "name": n, "team": t} for g, n, t in zip(r["gsis_id"], r["full_name"], r["team"])]
        if team:
            gid, how = names.match(name, team, cands)
            if gid:
                hit = r[r["gsis_id"] == gid]
        if hit.empty:
            raise LookupError(f"no {season} player matches {name!r}" + (f" on {team}" if team else ""))
    if hit["gsis_id"].nunique() > 1:
        teams = ", ".join(sorted(hit["team"].astype(str)))
        raise LookupError(f"{name!r} matches players on {teams}; give the team")
    row = hit.iloc[0]
    return row["gsis_id"], row["full_name"], row["team"]


def _results(b: Bundle, games: pd.DataFrame, margin: int) -> pd.DataFrame:
    """Add his team's margin, result group and starting QB to player_games rows."""
    sch = b.schedule.set_index("game_id")
    rows = []
    for gid, team in zip(games["game_id"], games["team"]):
        g = sch.loc[gid] if gid in sch.index else None
        if g is None or pd.isna(g["home_score"]):
            rows.append((np.nan, None, None, None))
            continue
        home = g["home_team"] == team
        m = (g["home_score"] - g["away_score"]) * (1 if home else -1)
        grp = f"won by {margin}+" if m >= margin else (f"lost by {margin}+" if m <= -margin else f"within {margin - 1}")
        qb_id = g["home_qb_id"] if home else g["away_qb_id"]
        qb_nm = g["home_qb_name"] if home else g["away_qb_name"]
        rows.append((m, grp, qb_id, qb_nm))
    extra = pd.DataFrame(rows, columns=["margin", "result_group", "qb_id", "qb_name"], index=games.index)
    return pd.concat([games, extra], axis=1)


def build(b: Bundle, gsis: str, name: str, team: str, season: int, week: int,
          tuned: dict, fixed: dict) -> Player:
    """His rates and pools for `week` of `season`, from games before it only."""
    pos = b.position_of(gsis, season) or "?"
    mine = data.before(b.games[b.games["gsis_id"] == gsis], season, week)
    mine = mine[(mine["carries"] + mine["targets"] + mine["completions"]) > 0]
    mine = mine.sort_values(["season", "week"])
    window = mine.tail(int(fixed["rate_window_games"]))
    this = _results(b, mine[mine["season"] == season], int(fixed["result_margin"]))
    pools = b.pools(season, int(fixed["pool_seasons"]))
    pl = Player(gsis, name, team, pos, season, week, window, this, pools=pools)
    keys = set(zip(window["season"], window["week"]))

    def own(df):
        d = data.before(df[df["gsis_id"] == gsis], season, week)
        return d[[k in keys for k in zip(d["season"], d["week"])]], d[d["season"] == season]

    # yards per carry
    c_win, c_season = own(b.carries)
    base = pools["ypc_by_pos"].get(pos, pools["ypc_by_pos"].get("RB"))
    pl.rates["ypc"] = Rate(blend(c_win["yards"].sum(), len(c_win), base, tuned["k_ypc"]),
                           c_win["yards"].mean() if len(c_win) else None, len(c_win),
                           c_season["yards"].mean() if len(c_season) else None, len(c_season), base)
    # catch rate, against a baseline of his position at his own depth mix
    t_win, t_season = own(b.targets)
    bk = depth_buckets(t_win["air_yards"], fixed["depth_short_below"], fixed["depth_deep_from"]).dropna()
    by = pools["catch_by_pos_bucket"]
    if len(bk) and all((pos, x) in by for x in bk.unique()):
        base = float(np.mean([by[(pos, x)] for x in bk]))
    else:
        base = pools["catch_by_pos"].get(pos, pools["catch_by_pos"].get("WR"))
    pl.rates["catch"] = Rate(blend(t_win["caught"].sum(), len(t_win), base, tuned["k_catch"]),
                             t_win["caught"].mean() if len(t_win) else None, len(t_win),
                             t_season["caught"].mean() if len(t_season) else None, len(t_season), base)
    return pl


def model(pl: Player, market: str, tuned: dict, fixed: dict) -> calc.Model:
    sims, seed = int(fixed["sims"]), int(fixed["seed"])
    if market == "rush_yds":
        d = calc.make_draws("carries", tuned["carry_r"], sims, seed)
        return calc.Model(market, "carries", d, pl.rates["ypc"].blended, pl.pools["rb_residuals"], tuned["day_sd"])
    if market == "receptions":
        d = calc.make_draws("targets", tuned["target_r"], sims, seed)
        return calc.Model(market, "targets", d, pl.rates["catch"].blended)
    raise ValueError(f"{market} is not built yet (rushing yards and receptions only)")
