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
from pathlib import Path

import pandas as pd

from core import fetch as F

from . import names
from .checks import DataError, no_missing, require

PBP_COLS = [
    "game_id", "season", "week", "season_type", "posteam", "defteam", "home_team", "away_team",
    "rush_attempt", "pass_attempt", "complete_pass", "sack", "two_point_attempt", "qb_kneel",
    "rusher_player_id", "receiver_player_id", "passer_player_id",
    "rushing_yards", "receiving_yards", "passing_yards", "air_yards", "wp", "epa", "success",
    "play_type", "qb_dropback", "qb_scramble", "pass", "rush", "qb_spike",
    "lateral_receiver_player_id", "lateral_receiving_yards", "lateral_rusher_player_id", "lateral_rushing_yards",
    "total_home_score", "total_away_score",
]


def _flag(s: pd.Series) -> pd.Series:
    return s.fillna(0).astype(float) == 1


def before(df: pd.DataFrame, season: int, week: int) -> pd.DataFrame:
    """Rows from games strictly before `week` of `season` (earlier seasons
    included). The leakage cut: nothing from the priced week or later."""
    return df[(df["season"] < season) | ((df["season"] == season) & (df["week"] < week))]


# ------------------------------------------------------------------ loading

def parsed_csv(path, cols, what: str) -> pd.DataFrame:
    """read_csv(path) on `cols`, kept beside the source as a pickle for the rest of the session
    (DECISIONS #236: three seasons of play-by-play took about 17 of a card's 27 seconds, paid again by
    every command). The cache is keyed on the source's size and modification time, the columns and
    the pandas version, so a refreshed source (core.fetch replaces the file) or a new pandas is
    always re-read; an unreadable cache is re-read too, and a cache that cannot be written only
    costs the saving. The frame returned is the parse itself, never a fallback."""
    import hashlib
    import json as _json
    import os
    path = Path(path)
    st = path.stat()
    key = hashlib.sha256(_json.dumps([path.name, st.st_size, st.st_mtime_ns, sorted(cols), pd.__version__])
                         .encode("utf-8")).hexdigest()[:16]
    cache = path.with_name(f"{path.name}.{what}.{key}.pkl")
    if cache.exists():
        try:
            return pd.read_pickle(cache)
        except Exception:  # noqa: BLE001 -- a cut or foreign cache file: re-read the source below
            cache.unlink(missing_ok=True)
    df = pd.read_csv(path, usecols=lambda c: c in cols, low_memory=False)
    tmp = cache.with_name(cache.name + f".{os.getpid()}.tmp")
    try:
        df.to_pickle(tmp)
        os.replace(tmp, cache)
        for old in path.parent.glob(f"{path.name}.{what}.*.pkl"):
            if old != cache:
                old.unlink(missing_ok=True)       # an earlier copy of the source
    except OSError:
        tmp.unlink(missing_ok=True)
    return df


def pbp(season: int, *, manifest=None, season_type: str = "REG") -> pd.DataFrame:
    path = F.nflverse("pbp", season, manifest=manifest)
    df = parsed_csv(path, PBP_COLS, "calc-pbp")
    df = df[df["season_type"] == season_type].reset_index(drop=True)
    no_missing(f"{season} play-by-play season", df["season"])
    no_missing(f"{season} play-by-play week", df["week"])      # data.before would drop such a play silently
    return df


def schedule(*, manifest=None, game_type: str = "REG") -> pd.DataFrame:
    df = pd.read_csv(F.schedule(manifest=manifest), low_memory=False)
    df = df[df["game_type"] == game_type].copy()
    df["kickoff_utc"] = [kickoff_utc(d, t) for d, t in zip(df["gameday"], df["gametime"])]
    return df.reset_index(drop=True)


def rosters(season: int, *, manifest=None) -> pd.DataFrame:
    cols = ["season", "week", "team", "position", "full_name", "gsis_id", "sleeper_id", "pfr_id", "status"]
    df = parsed_csv(F.nflverse("rosters_weekly", season, manifest=manifest), cols, "calc-rosters").copy()
    df["sleeper_id"] = df["sleeper_id"].map(_id_str)
    return df


def snaps(season: int, *, manifest=None) -> pd.DataFrame:
    cols = ["game_id", "season", "game_type", "week", "player", "pfr_player_id", "position", "team", "offense_snaps",
            "offense_pct"]
    df = parsed_csv(F.nflverse("snaps", season, manifest=manifest), cols, "calc-snaps")
    return df[df["game_type"] == "REG"].reset_index(drop=True)


def injuries(season: int, *, manifest=None) -> pd.DataFrame:
    """The official weekly injury report (nflverse): team, week, gsis_id,
    full_name, position, report_status."""
    cols = ["season", "team", "week", "gsis_id", "full_name", "position", "report_status", "practice_status"]
    return pd.read_csv(F.nflverse("injuries", season, manifest=manifest), usecols=lambda c: c in cols,
                       low_memory=False)


def _id_str(x) -> str | None:
    """Sleeper ids arrive as text or as floats ("4034.0"); one string form."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    s = str(x).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s or None


# ------------------------------------------------------------------ time

def _eastern():
    """US Eastern from the tz database (zoneinfo, as props/guard.py uses). No
    hand-written fallback: without the database (Windows needs the tzdata
    package from requirements.txt) every kickoff time would be wrong."""
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("America/New_York")
    except Exception as ex:  # noqa: BLE001 -- ZoneInfoNotFoundError or a missing module
        raise DataError(f"no time-zone database for America/New_York ({ex}); install tzdata "
                        f"(pip install -r requirements.txt)") from ex


def kickoff_utc(gameday: str, gametime: str) -> str | None:
    """nflverse lists kickoffs in US Eastern time; ISO UTC string."""
    try:
        d = dt.date.fromisoformat(str(gameday))
        hh, mm = (int(x) for x in str(gametime).split(":")[:2])
    except (TypeError, ValueError):
        return None
    local = dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=_eastern())
    return local.astimezone(dt.timezone.utc).isoformat()


# ------------------------------------------------------------------ plays

def carries(p: pd.DataFrame) -> pd.DataFrame:
    """One row per carry: a rush attempt that is not a two-point try or a kneel."""
    m = (_flag(p["rush_attempt"]) & ~_flag(p["two_point_attempt"]) & ~_flag(p["qb_kneel"])
         & p["rusher_player_id"].notna())
    out = p.loc[m, ["game_id", "season", "week", "posteam", "defteam", "wp", "rusher_player_id", "rushing_yards"]]
    out = out.rename(columns={"rusher_player_id": "gsis_id", "rushing_yards": "yards"})
    no_missing("rushing yards on carries", out["yards"])
    return out.reset_index(drop=True)


def targets(p: pd.DataFrame) -> pd.DataFrame:
    """One row per target: a pass attempt with a named receiver, not a sack,
    not a two-point try. Yards are 0 on an incompletion (nflverse leaves NaN)."""
    m = (_flag(p["pass_attempt"]) & ~_flag(p["sack"]) & ~_flag(p["two_point_attempt"])
         & p["receiver_player_id"].notna())
    out = p.loc[m, ["game_id", "season", "week", "posteam", "defteam", "wp", "receiver_player_id",
                    "passer_player_id", "complete_pass", "receiving_yards", "air_yards"]]
    out = out.rename(columns={"receiver_player_id": "gsis_id", "receiving_yards": "yards"})
    no_missing("completion flag on targets", out["complete_pass"])
    out["caught"] = _flag(out["complete_pass"])
    no_missing("receiving yards on catches", out.loc[out["caught"], "yards"])
    out["yards"] = out["yards"].where(out["caught"], 0.0)       # an incompletion is 0 yards (nflverse: NaN)
    return out.drop(columns="complete_pass").reset_index(drop=True)


def completions(p: pd.DataFrame) -> pd.DataFrame:
    """One row per completion credited to a passer (box-score passing yards)."""
    m = (_flag(p["complete_pass"]) & ~_flag(p["sack"]) & ~_flag(p["two_point_attempt"])
         & p["passer_player_id"].notna())
    out = p.loc[m, ["game_id", "season", "week", "posteam", "defteam", "wp", "passer_player_id",
                    "passing_yards", "air_yards"]]
    out = out.rename(columns={"passer_player_id": "gsis_id", "passing_yards": "yards"})
    no_missing("passing yards on completions", out["yards"])
    return out.reset_index(drop=True)


def starters(p: pd.DataFrame) -> pd.DataFrame:
    """(game_id, posteam, gsis_id): each team's starting quarterback in each
    game, taken as its passer with the most dropbacks (the design note's
    definition; a tie goes to the smaller gsis id, so the choice is stable)."""
    d = p[_flag(p["qb_dropback"]) & p["passer_player_id"].notna()]
    n = d.groupby(["game_id", "posteam", "passer_player_id"]).size().rename("n").reset_index()
    top = n.sort_values("n", ascending=False, kind="stable").drop_duplicates(["game_id", "posteam"])
    return top.rename(columns={"passer_player_id": "gsis_id"})[["game_id", "posteam", "gsis_id"]]


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
    """(game_id, season, week, team, gsis_id, offense_pct) for every player with
    at least one offensive snap: a game he played even if he got no carries or targets.
    Snap rows whose pfr id has no gsis id on the rosters cannot be tied to a
    player; the skill players among them are listed in out.attrs["unmapped"]
    (player, team) so the caller can say so, not dropped silently."""
    ids = roster.dropna(subset=["pfr_id", "gsis_id"]).drop_duplicates("pfr_id")
    pfr = dict(zip(ids["pfr_id"], ids["gsis_id"]))
    s = snap[snap["offense_snaps"].fillna(0) > 0]
    s = s.assign(gsis_id=s["pfr_player_id"].map(pfr))
    lost = s[s["gsis_id"].isna()]
    if "position" in lost.columns:     # only skill players can be a leg; a lineman's missing id does not matter here
        lost = lost[lost["position"].isin(SKILL)]
    out = s.dropna(subset=["gsis_id"])
    keep = ["game_id", "season", "week", "team", "gsis_id"] + (["offense_pct"] if "offense_pct" in out.columns else [])
    out = out[keep].drop_duplicates(["game_id", "gsis_id"])
    out.attrs["unmapped"] = sorted({(str(p), str(t)) for p, t in
                                    zip(lost.get("player", lost["pfr_player_id"]), lost["team"])})
    return out


def games_played(player_games: pd.DataFrame, played_rows: pd.DataFrame) -> pd.DataFrame:
    """player_games plus a zero row for each game he played (snaps) without a
    carry, target or completion -- only for games whose plays are loaded: a
    game seen in snap counts before its play-by-play is not a game of zeros."""
    keys = ["game_id", "gsis_id"]
    have = set(zip(player_games["game_id"], player_games["gsis_id"]))
    loaded = set(player_games["game_id"])
    extra = played_rows[[k not in have and k[0] in loaded
                         for k in zip(played_rows["game_id"], played_rows["gsis_id"])]]
    if extra.empty:
        return player_games
    zeros = extra.assign(carries=0, rush_yds=0.0, targets=0, receptions=0, rec_yds=0.0, completions=0, pass_yds=0.0)
    return pd.concat([player_games, zeros[player_games.columns]], ignore_index=True).drop_duplicates(keys)


def complete_games(p: pd.DataFrame, schedule: pd.DataFrame) -> set:
    """Games whose play-by-play is complete: its last running score equals the
    schedule's final score. A cached copy taken mid-game, or before every
    play was published, does not count."""
    last = p.groupby("game_id")[["total_home_score", "total_away_score"]].max()
    sch = schedule.dropna(subset=["home_score", "away_score"]).set_index("game_id")
    both = last.join(sch[["home_score", "away_score"]], how="inner")
    ok = (both["total_home_score"] == both["home_score"]) & (both["total_away_score"] == both["away_score"])
    return set(both.index[ok])


# ------------------------------------------------------------------ ids

def sleeper_to_gsis(roster: pd.DataFrame) -> dict[str, str]:
    """Sleeper id -> gsis id from nflverse's weekly rosters (an ID join). A
    Sleeper id that nflverse gives to more than one player (2026: one id on
    two different players) is left out, so it goes to the checked fallback
    rather than to a guess."""
    r = roster.dropna(subset=["sleeper_id", "gsis_id"])
    shared = r.groupby("sleeper_id")["gsis_id"].nunique()
    r = r[~r["sleeper_id"].isin(shared[shared > 1].index)]
    return dict(zip(r["sleeper_id"], r["gsis_id"]))


# cut, retired, traded, released, unsigned (UFA/RFA) or not with the team: not on that team's roster
GONE = ("CUT", "RET", "TRD", "TRC", "TRT", "UFA", "RFA", "NWT")
SKILL = ("QB", "RB", "WR", "TE", "FB")


def _listings(roster: pd.DataFrame, season: int, week: int | None) -> pd.DataFrame:
    """Each team's latest published roster of `season` up to `week`, without
    cut, retired or traded rows (all players, identified or not)."""
    require("status" in roster.columns, "weekly rosters have no status column; cannot drop departed players")
    r = roster[roster["season"] == season]
    if week is not None:
        r = r[r["week"] <= week]
    r = r[r["team"].map(lambda t: isinstance(t, str)).astype(bool)]   # a bool mask even on an empty frame
    if r.empty:
        return r
    r = r[r["week"] == r.groupby("team")["week"].transform("max")]
    return r[~r["status"].isin(GONE)]


def roster_split(roster: pd.DataFrame, season: int, week: int | None = None, *,
                 skill_only: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(players, set aside), the one way the rosters are read as of a week.

    players: everyone on each team's latest published roster of `season` up
    to `week` (all weeks when None), identified or not. Per team, not one week
    for all: nflverse's weekly rosters leave out teams on bye, so a single
    latest week would drop whole teams; and per team, not each player's own
    latest row, so a player who dropped off his team's roster without a CUT
    row is not kept on it.
    set aside: ids listed on two teams in the same latest week (an nflverse
    glitch, e.g. one 2019 id shared by two linemen); never guessed.
    skill_only: QB, RB, WR, TE, FB only (the players Sleeper prices)."""
    r = _listings(roster, season, week)
    if skill_only and len(r):
        require("position" in r.columns, "weekly rosters have no position column; cannot limit to skill players")
        r = r[r["position"].isin(SKILL)]
    ided = r[r["gsis_id"].notna()]
    if ided.empty:
        return r, ided
    latest = ided[ided["week"] == ided.groupby("gsis_id")["week"].transform("max")]
    two = latest.groupby("gsis_id")["team"].transform("nunique") > 1
    return pd.concat([latest[~two].drop_duplicates("gsis_id"), r[r["gsis_id"].isna()]]), latest[two]


def set_aside_namesake(aside: pd.DataFrame, name: str, *, teams=None, other_than: str | None = None) -> bool:
    """The one rule for "a player listed on two teams that week could be the
    one meant": a set-aside skill player (roster_split) whom `name` could name
    (names.could_be), on one of `teams` if given, other than `other_than`."""
    a = aside[aside["position"].isin(SKILL)] if "position" in aside.columns else aside
    if teams is not None:
        a = a[a["team"].isin(set(teams))]
    return any(names.could_be(str(n), name) and g != other_than for g, n in zip(a["gsis_id"], a["full_name"]))


def candidates(players: pd.DataFrame) -> list[dict]:
    """[{gsis_id, name, team}] for the identified rows of a roster_split frame."""
    r = players[players["gsis_id"].notna()]
    return [{"gsis_id": g, "name": n, "team": t} for g, n, t in zip(r["gsis_id"], r["full_name"], r["team"])]

