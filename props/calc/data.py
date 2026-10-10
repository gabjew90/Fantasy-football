"""The calculator's data: nflverse play-by-play, schedules, weekly rosters and
snap counts, read through core.fetch (the repo's one fetch layer), plus the
rules for what counts as a carry, a target or a completion.

The known traps, each handled here and unit-tested:
  * receiving_yards is NaN on an incompletion: filled with 0, so yards per
    target counts the misses;
  * a sack is neither a target nor a pass attempt (it has no receiver and is
    dropped from completions);
  * two-point tries and kneels are not carries, targets or completions;
  * only games before the priced week are used (`before`).
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from core import fetch as F

PBP_COLS = [
    "game_id", "season", "week", "season_type", "posteam", "defteam", "home_team", "away_team",
    "rush_attempt", "pass_attempt", "complete_pass", "sack", "two_point_attempt", "qb_kneel",
    "rusher_player_id", "receiver_player_id", "passer_player_id",
    "rushing_yards", "receiving_yards", "passing_yards", "air_yards", "wp", "epa", "success",
    "play_type", "qb_dropback", "qb_scramble",
    "lateral_receiver_player_id", "lateral_receiving_yards", "lateral_rusher_player_id", "lateral_rushing_yards",
]


def _flag(s: pd.Series) -> pd.Series:
    return s.fillna(0).astype(float) == 1


def before(df: pd.DataFrame, season: int, week: int) -> pd.DataFrame:
    """Rows from games strictly before `week` of `season` (earlier seasons
    included). The leakage cut: nothing from the priced week or later."""
    return df[(df["season"] < season) | ((df["season"] == season) & (df["week"] < week))]


# ------------------------------------------------------------------ loading

def pbp(season: int, *, manifest=None, season_type: str = "REG") -> pd.DataFrame:
    path = F.nflverse("pbp", season, manifest=manifest)
    df = pd.read_csv(path, usecols=lambda c: c in PBP_COLS, low_memory=False)
    return df[df["season_type"] == season_type].reset_index(drop=True)


def schedule(*, manifest=None, game_type: str = "REG") -> pd.DataFrame:
    df = pd.read_csv(F.schedule(manifest=manifest), low_memory=False)
    df = df[df["game_type"] == game_type].copy()
    df["kickoff_utc"] = [kickoff_utc(d, t) for d, t in zip(df["gameday"], df["gametime"])]
    return df.reset_index(drop=True)


def rosters(season: int, *, manifest=None) -> pd.DataFrame:
    cols = ["season", "week", "team", "position", "full_name", "gsis_id", "sleeper_id", "pfr_id", "status"]
    df = pd.read_csv(F.nflverse("rosters_weekly", season, manifest=manifest),
                     usecols=lambda c: c in cols, low_memory=False)
    df["sleeper_id"] = df["sleeper_id"].map(_id_str)
    return df


def snaps(season: int, *, manifest=None) -> pd.DataFrame:
    cols = ["game_id", "season", "game_type", "week", "pfr_player_id", "team", "offense_snaps"]
    df = pd.read_csv(F.nflverse("snaps", season, manifest=manifest),
                     usecols=lambda c: c in cols, low_memory=False)
    return df[df["game_type"] == "REG"].reset_index(drop=True)


def _id_str(x) -> str | None:
    """Sleeper ids arrive as text or as floats ("4034.0"); one string form."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    s = str(x).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s or None


# ------------------------------------------------------------------ time

def _first_sunday(year: int, month: int) -> dt.date:
    d = dt.date(year, month, 1)
    return d + dt.timedelta(days=(6 - d.weekday()) % 7)


def eastern_offset_hours(day: dt.date) -> int:
    """US Eastern's UTC offset: -4 from the second Sunday of March to the first
    Sunday of November, else -5. (No tz database needed on Windows.)"""
    start = _first_sunday(day.year, 3) + dt.timedelta(days=7)
    end = _first_sunday(day.year, 11)
    return -4 if start <= day < end else -5


def kickoff_utc(gameday: str, gametime: str) -> str | None:
    """nflverse lists kickoffs in US Eastern time; ISO UTC string."""
    try:
        d = dt.date.fromisoformat(str(gameday))
        hh, mm = (int(x) for x in str(gametime).split(":")[:2])
    except (TypeError, ValueError):
        return None
    local = dt.datetime(d.year, d.month, d.day, hh, mm)
    return (local - dt.timedelta(hours=eastern_offset_hours(d))).replace(tzinfo=dt.timezone.utc).isoformat()


# ------------------------------------------------------------------ plays

def carries(p: pd.DataFrame) -> pd.DataFrame:
    """One row per carry: a rush attempt that is not a two-point try or a kneel."""
    m = (_flag(p["rush_attempt"]) & ~_flag(p["two_point_attempt"]) & ~_flag(p["qb_kneel"])
         & p["rusher_player_id"].notna())
    out = p.loc[m, ["game_id", "season", "week", "posteam", "defteam", "rusher_player_id", "rushing_yards"]]
    out = out.rename(columns={"rusher_player_id": "gsis_id", "rushing_yards": "yards"})
    out["yards"] = out["yards"].fillna(0.0)
    return out.reset_index(drop=True)


def targets(p: pd.DataFrame) -> pd.DataFrame:
    """One row per target: a pass attempt with a named receiver, not a sack,
    not a two-point try. Yards are 0 on an incompletion (nflverse leaves NaN)."""
    m = (_flag(p["pass_attempt"]) & ~_flag(p["sack"]) & ~_flag(p["two_point_attempt"])
         & p["receiver_player_id"].notna())
    out = p.loc[m, ["game_id", "season", "week", "posteam", "defteam", "receiver_player_id",
                    "passer_player_id", "complete_pass", "receiving_yards", "air_yards"]]
    out = out.rename(columns={"receiver_player_id": "gsis_id", "receiving_yards": "yards"})
    out["caught"] = _flag(out["complete_pass"])
    out["yards"] = out["yards"].fillna(0.0).where(out["caught"], 0.0)
    return out.drop(columns="complete_pass").reset_index(drop=True)


def completions(p: pd.DataFrame) -> pd.DataFrame:
    """One row per completion credited to a passer (box-score passing yards)."""
    m = (_flag(p["complete_pass"]) & ~_flag(p["sack"]) & ~_flag(p["two_point_attempt"])
         & p["passer_player_id"].notna())
    out = p.loc[m, ["game_id", "season", "week", "posteam", "defteam", "passer_player_id",
                    "passing_yards", "air_yards"]]
    out = out.rename(columns={"passer_player_id": "gsis_id", "passing_yards": "yards"})
    out["yards"] = out["yards"].fillna(0.0)
    return out.reset_index(drop=True)


def player_games(p: pd.DataFrame) -> pd.DataFrame:
    """Per player per game: carries, rush_yds, targets, receptions, rec_yds,
    completions, pass_yds, with his team that game. Yards gained after taking
    a lateral are added to his box-score yards (not counted as a carry or a
    target), as nflverse's weekly stats do."""
    keys = ["game_id", "season", "week", "posteam", "gsis_id"]
    c = carries(p).groupby(keys).agg(carries=("yards", "size"), rush_yds=("yards", "sum"))
    t = targets(p).groupby(keys).agg(targets=("yards", "size"), receptions=("caught", "sum"),
                                     rec_yds=("yards", "sum"))
    q = completions(p).groupby(keys).agg(completions=("yards", "size"), pass_yds=("yards", "sum"))
    lat = []
    for who, yds, col in (("lateral_receiver_player_id", "lateral_receiving_yards", "rec_yds"),
                          ("lateral_rusher_player_id", "lateral_rushing_yards", "rush_yds")):
        if who in p and yds in p:
            x = p[p[who].notna() & p[yds].notna() & ~_flag(p["two_point_attempt"])]
            lat.append(x.rename(columns={who: "gsis_id"}).groupby(keys)[yds].sum().rename(col))
    out = c.join(t, how="outer").join(q, how="outer")
    for extra in lat:      # a lateral's yards count in the box score; it is not a carry or a target
        out = out.join(extra.rename(f"{extra.name}_lat"), how="outer")
    out = out.fillna(0)
    for col in ("rec_yds", "rush_yds"):
        if f"{col}_lat" in out:
            out[col] = out[col] + out.pop(f"{col}_lat")
    out = out.reset_index()
    out = out.rename(columns={"posteam": "team"})
    for col in ("carries", "targets", "receptions", "completions"):
        out[col] = out[col].astype(int)
    return out


def played(snap: pd.DataFrame, roster: pd.DataFrame) -> pd.DataFrame:
    """(game_id, season, week, team, gsis_id) for every player with at least one
    offensive snap: a game he played even if he got no carries or targets."""
    ids = roster.dropna(subset=["pfr_id", "gsis_id"]).drop_duplicates("pfr_id")
    pfr = dict(zip(ids["pfr_id"], ids["gsis_id"]))
    s = snap[snap["offense_snaps"].fillna(0) > 0]
    out = s.assign(gsis_id=s["pfr_player_id"].map(pfr)).dropna(subset=["gsis_id"])
    return out[["game_id", "season", "week", "team", "gsis_id"]].drop_duplicates(["game_id", "gsis_id"])


def games_played(player_games: pd.DataFrame, played_rows: pd.DataFrame) -> pd.DataFrame:
    """player_games plus a zero row for each game he played (snaps) without a
    carry, target or completion."""
    keys = ["game_id", "gsis_id"]
    have = set(zip(player_games["game_id"], player_games["gsis_id"]))
    extra = played_rows[[k not in have for k in zip(played_rows["game_id"], played_rows["gsis_id"])]]
    if extra.empty:
        return player_games
    zeros = extra.assign(carries=0, rush_yds=0.0, targets=0, receptions=0, rec_yds=0.0, completions=0, pass_yds=0.0)
    return pd.concat([player_games, zeros[player_games.columns]], ignore_index=True).drop_duplicates(keys)


# ------------------------------------------------------------------ ids

def sleeper_to_gsis(roster: pd.DataFrame) -> dict[str, str]:
    """Sleeper id -> gsis id from nflverse's weekly rosters (an ID join)."""
    r = roster.dropna(subset=["sleeper_id", "gsis_id"])
    return dict(zip(r["sleeper_id"], r["gsis_id"]))


def roster_candidates(roster: pd.DataFrame, season: int, week: int | None = None) -> list[dict]:
    """[{gsis_id, name, team}] for the name fallback: the given week's rosters,
    or the latest week on file when `week` is None."""
    r = roster[roster["season"] == season]
    if week is not None and (r["week"] == week).any():
        r = r[r["week"] == week]
    elif len(r):
        r = r[r["week"] == r["week"].max()]
    r = r.dropna(subset=["gsis_id"])
    return [{"gsis_id": g, "name": n, "team": t} for g, n, t in zip(r["gsis_id"], r["full_name"], r["team"])]

