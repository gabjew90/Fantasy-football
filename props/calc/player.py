"""One player before one week: who he is, his blended rates, the pools the
calculator draws from, and the plain history rows the card shows.

Everything here is cut at the priced week (data.before): nothing from that
week or later is read.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import calc, data, names, rates
from .checks import finite, in_range, kicked_off_before, no_missing, require
from .markets import min_own, workload_col


class NotFound(Exception):
    """A typed name or a game could not be found (a message for the user, not a bug)."""


class Bundle:
    """The seasons a card or a test needs, loaded once and cut per week."""

    def __init__(self, seasons, fixed: dict, *, manifest=None):
        self.manifest = manifest
        self.seasons = sorted(set(seasons))
        self.fixed = fixed
        stype = fixed["season_type"]
        plays = [data.pbp(s, manifest=manifest, season_type=stype) for s in self.seasons]
        self.pbp = pd.concat(plays, ignore_index=True)
        self.carries = data.carries(self.pbp)
        self.targets = data.targets(self.pbp)
        self.completions = data.completions(self.pbp)
        self.starters = data.starters(self.pbp)
        self.rosters = pd.concat([data.rosters(s, manifest=manifest) for s in self.seasons], ignore_index=True)
        snaps = pd.concat([data.snaps(s, manifest=manifest) for s in self.seasons], ignore_index=True)
        played = data.played(snaps, self.rosters)
        # every game he played: with work (play-by-play) or without it (an offensive snap)
        self.games = data.games_played(data.player_games(self.pbp), played)
        # his share of his team's offensive snaps per game, for the fewer-snaps marker (display only)
        self.snap_share = played.reindex(columns=["game_id", "gsis_id", "offense_pct"])   # no share column: no marks
        # who started each game is the play-by-play's, not the schedule's pre-game guess (DECISIONS #246)
        self.schedule = data.starters_on_schedule(data.schedule(manifest=manifest, game_type=stype),
                                                  self.pbp, self.rosters)
        self._kickoffs: dict | None = None
        self._week_starts: dict = {}
        r = self.rosters.dropna(subset=["gsis_id", "position"]).sort_values(["season", "week"])
        self._roster_pos = r[["season", "week", "gsis_id", "position"]]
        # a whole past season's label: used for the pools, which only read earlier seasons
        pos = r.drop_duplicates(["season", "gsis_id"], keep="last")
        self.position = {(s, g): p for s, g, p in zip(pos["season"], pos["gsis_id"], pos["position"])}
        self._pools: dict = {}
        self._injury_reports: dict = {}

    def injury_report(self, season: int):
        """The season's official injury report, read once; None when the file cannot be read (display
        only: the lineup check then cannot say a teammate is Out today)."""
        cache = self.__dict__.setdefault("_injury_reports", {})     # a Bundle built without __init__ (tests)
        if season not in cache:
            try:
                cache[season] = data.injuries(season, manifest=getattr(self, "manifest", None))
            except (OSError, ValueError, KeyError):    # a missing or unreadable file, never a code error
                cache[season] = None
        return cache[season]

    def kickoffs(self) -> dict:
        """game_id -> kickoff time, from the schedule."""
        if self._kickoffs is None:
            k = self.schedule.dropna(subset=["kickoff_utc"])
            self._kickoffs = dict(zip(k["game_id"], pd.to_datetime(k["kickoff_utc"], utc=True)))
        return self._kickoffs

    def cut(self, df: pd.DataFrame, season: int, week: int, name: str) -> pd.DataFrame:
        """data.before (the leakage cut on season and week) plus the check
        against an independent source: every remaining game kicked off before
        the priced week's first kickoff. Every input to a card goes through here."""
        out = data.before(df, season, week)
        kicked_off_before(name, out["game_id"], self.kickoffs(), self.week_starts(season, week))
        return out

    def week_starts(self, season: int, week: int):
        """The priced week's first kickoff."""
        if (season, week) not in self._week_starts:
            ko = self.kickoffs()
            s = self.schedule[(self.schedule["season"] == season) & (self.schedule["week"] == week)]
            times = [ko[g] for g in s["game_id"] if g in ko]
            require(bool(times), f"no {season} week {week} games with a kickoff time on the schedule")
            self._week_starts[(season, week)] = min(times)
        return self._week_starts[(season, week)]

    def position_at(self, gsis: str, season: int, week: int) -> str | None:
        """His roster position as it stood in `week` (the latest roster week up
        to it), else his last listing of the season before. Never later weeks."""
        r = self._roster_pos
        mine = r[(r["gsis_id"] == gsis) & (r["season"] == season) & (r["week"] <= week)]
        if len(mine):
            return mine["position"].iloc[-1]
        return self.position.get((season - 1, gsis))

    def with_position(self, df: pd.DataFrame) -> pd.DataFrame:
        pos = [self.position.get((s, g)) for s, g in zip(df["season"], df["gsis_id"])]
        return df.assign(position=pos)

    def pools(self, season: int, pool_seasons: int) -> dict:
        """Per-play pools from the `pool_seasons` seasons before `season`."""
        key = (season, pool_seasons)
        if key not in self._pools:
            yrs = list(range(season - pool_seasons, season))
            missing = [y for y in yrs if y not in self.seasons]
            require(not missing, f"pool seasons {missing} are not loaded")
            c = self.with_position(self.carries[self.carries["season"].isin(yrs)])
            t = self.with_position(self.targets[self.targets["season"].isin(yrs)])
            empty = [y for y in yrs if not ((c["season"] == y).any() and (t["season"] == y).any())]
            require(not empty, f"pool seasons {empty} loaded no carries or no targets")
            cutoff = self.week_starts(season, 1)
            kicked_off_before("pool carries", c["game_id"], self.kickoffs(), cutoff)
            kicked_off_before("pool targets", t["game_id"], self.kickoffs(), cutoff)
            pools = make_pools(c, t, self.fixed)
            q = self.completions[self.completions["season"].isin(yrs)]
            q = q.merge(self.starters, on=["game_id", "posteam", "gsis_id"], how="inner")   # starters' completions only
            no_q = [y for y in yrs if not (q["season"] == y).any()]
            require(not no_q, f"pool seasons {no_q} gave no starting quarterbacks' completions")
            kicked_off_before("pool completions", q["game_id"], self.kickoffs(), cutoff)
            pools.update(completion_pools(q, self.fixed))
            self._pools[key] = pools
        return self._pools[key]


def make_pools(c: pd.DataFrame, t: pd.DataFrame, fixed: dict) -> dict:
    """Pools from carries (season, yards, position) and targets (yards,
    caught, air_yards, position). Fails loudly on missing values or a league
    average outside its plausible range; records groups below their minimum
    sample (the card then says "not enough data")."""
    require(len(c) and len(t), "no plays loaded for the pools")
    finite("pool carry yards", c["yards"])
    finite("pool target yards", t["yards"])
    no_missing("roster position of pool carries", c["position"])
    no_missing("roster position of pool targets", t["position"])
    league_ypc = rates.yards_per_carry(c["yards"])
    league_catch = rates.catch_rate(t["caught"])
    league_ypt = rates.yards_per_target(t["yards"], t["caught"])      # incompletions already 0 (data.targets)
    in_range("league yards per carry", league_ypc, fixed["league_ypc_range"])
    in_range("league catch rate", league_catch, fixed["league_catch_rate_range"])
    in_range("league yards per target", league_ypt, fixed["league_yards_per_target_range"])
    rb = c.loc[c["position"] == "RB", "yards"].to_numpy(float)
    t = t.assign(bucket=depth_buckets(t["air_yards"], fixed["depth_short_below"], fixed["depth_deep_from"]))
    # a target without a recorded depth (1 a season in some years) cannot join
    # a depth group; it still counts in the league averages above, and the
    # count is shown on receptions cards
    g = t.dropna(subset=["bucket"]).groupby(["position", "bucket"])["caught"]
    caught = t[t["caught"] & t["bucket"].notna()]
    return {
        # real catch yards by position and depth, for receiving yards; and by depth over every position,
        # used at a depth where his position has too few (the user, 2026-10-10)
        "catch_yards_by_pos_bucket": {k: v.to_numpy(float) for k, v in caught.groupby(["position", "bucket"])["yards"]},
        "catch_yards_by_bucket": {k: v.to_numpy(float) for k, v in caught.groupby("bucket")["yards"]},
        "targets_without_depth": int(t["bucket"].isna().sum()),
        "rb_residuals": rb - rb.mean() if len(rb) else rb,
        "rb_n": len(rb),
        "ypc_by_pos": c.groupby("position")["yards"].mean().to_dict(),
        "carries_by_pos": c.groupby("position").size().to_dict(),
        "catch_by_pos_bucket": g.mean().to_dict(),
        "targets_by_pos_bucket": g.size().to_dict(),
        "league_ypc": league_ypc, "league_catch": league_catch, "league_ypt": league_ypt,
    }


BUCKETS = ("short", "medium", "deep")


def completion_pools(q: pd.DataFrame, fixed: dict) -> dict:
    """Starting quarterbacks' completion yards by depth (design note #8), for
    passing yards. A completion without a recorded depth joins no group."""
    finite("pool completion yards", q["yards"])
    require(len(q), "no starting quarterbacks' completions in the pool")
    in_range("league yards per completion", rates.yards_per_completion(q["yards"]),
             fixed["league_yards_per_completion_range"])
    bk = depth_buckets(q["air_yards"], fixed["depth_short_below"], fixed["depth_deep_from"])
    q = q.assign(bucket=bk).dropna(subset=["bucket"])
    return {"comp_yards_by_bucket": {b: g.to_numpy(float) for b, g in q.groupby("bucket")["yards"]},
            "completions_without_depth": int(bk.isna().sum())}


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
    not_enough: dict = field(default_factory=dict)    # market -> [reasons the card shows no numbers]
    no_depth: int = 0                                 # his targets without a recorded depth
    receiving: dict = field(default_factory=dict)     # rec_yds: catch rate, yards per catch, depth mix, pools
    passing: dict = field(default_factory=dict)       # pass_yds: depth mix and the starters' completion pools
    lineup: list = field(default_factory=list)        # the lineup check's cause lines for his marked last-4 games
    lineup_flags: list = field(default_factory=list)  # main teammates Questionable today (a flag on the screen row)

    def usual(self, market: str, games: int) -> float | None:
        """His average workload over his last `games` games played; None with
        fewer games than that (the minimum sample is the number averaged)."""
        if len(self.window) < games:
            return None
        return float(self.window.tail(games)[workload_col(market)].mean())


def find_player(b: Bundle, name: str, season: int, team: str | None = None,
                week: int | None = None, initial_match: list | None = None) -> tuple[str, str, str]:
    """(gsis_id, full name, team) for a typed name. The name must point at one
    player on the season's rosters (with the team when given), as the rosters
    stood in `week` (the latest roster week up to it; the latest on file when
    no week is given), so a player traded later is found on his team then.
    `initial_match` (a one-item list) is set True when a full typed name was
    resolved by first initial + surname (Scotty Miller -> Scott Miller): the
    caller must say so and must not log on it."""
    initial_match = initial_match if initial_match is not None else [False]
    r, amb = data.roster_split(b.rosters, season, week, skill_only=True)   # Sleeper prices skill players only
    r = r[r["gsis_id"].notna()]
    if r.empty:
        raise NotFound(f"no {season} roster on file" + (f" up to week {week}" if week is not None else ""))
    key = names.norm(name)
    # a namesake listed on two teams that week is set aside, never guessed: if
    # one could be the player meant, refuse rather than pick the other
    if data.set_aside_namesake(amb, name, teams=[names.team_code(team)] if team else None):
        raise NotFound(f"{name!r} matches a player listed on two teams in the same week of the {season} "
                       f"rosters; the roster data cannot say which")
    hit = r[r["full_name"].map(names.norm) == key]
    if team:
        hit = hit[hit["team"] == names.team_code(team)]
    if hit.empty:
        if team:
            gid, how = names.match(name, team, data.candidates(r), allow_initial=True)
            if gid:
                hit = r[r["gsis_id"] == gid]
                if how == "initial" and not names.abbreviated(name):
                    initial_match[0] = True       # the card says so, and --log refuses this run
        if hit.empty:
            raise NotFound(f"no {season} player matches {name!r}" + (f" on {team}" if team else "")
                           + " on a team's latest roster (a traded or released player drops off until his "
                             "new team's next roster)")
    if hit["gsis_id"].nunique() > 1:
        teams = ", ".join(sorted(hit["team"].astype(str)))
        raise NotFound(f"{name!r} matches players on {teams}; give the team")
    row = hit.iloc[0]
    return row["gsis_id"], row["full_name"], row["team"]


def fewer_snaps(mine: pd.DataFrame, share: pd.DataFrame, k: float) -> pd.DataFrame:
    """Adds snap_pct and fewer_snaps: a game where his share of the offensive
    snaps was under k times his average share in his other games of that
    season (games before the priced week only; `mine` is already cut). A game
    with no snap share, or no other game to compare with, is not marked.
    Display only: the marker changes no number."""
    s = share[share["gsis_id"].isin(set(mine["gsis_id"]))].drop_duplicates(["game_id", "gsis_id"])
    if s.empty or mine.empty:                  # no snap shares for him: nothing to mark
        return mine.assign(snap_pct=np.nan, fewer_snaps=False)
    out = mine.merge(s, on=["game_id", "gsis_id"], how="left")
    out.index = mine.index
    pct = pd.to_numeric(out["offense_pct"], errors="coerce")
    marks = []
    for i, (yr, p) in enumerate(zip(out["season"], pct)):
        others = pct[(out["season"] == yr).to_numpy() & (np.arange(len(out)) != i)].dropna()
        marks.append(bool(pd.notna(p) and len(others) and p < k * others.mean()))
    return out.drop(columns=["offense_pct"]).assign(snap_pct=pct.to_numpy(), fewer_snaps=marks)


def _starter(g, team: str, what: str = "id"):
    """The team's starting QB id (or name) in one schedule row, or None."""
    q = g[f"home_qb_{what}"] if g["home_team"] == team else (g[f"away_qb_{what}"] if g["away_team"] == team else None)
    return q if isinstance(q, str) and q else None


def played_before(schedule: pd.DataFrame, team: str, season: int, week: int) -> pd.DataFrame:
    """His team's games before `week` that have been played (a final score). nflverse's schedule also
    lists a quarterback for games not yet played; that name is never read as a starter (the user
    declined it as a source, 2026-10-11)."""
    t = schedule[(schedule["season"] == season) & (schedule["week"] < week)
                 & ((schedule["home_team"] == team) | (schedule["away_team"] == team))]
    if "home_score" in t:
        t = t[t["home_score"].notna()]
    return t.sort_values("week")


def current_starter(schedule: pd.DataFrame, team: str, season: int, week: int):
    """The quarterback who started his team's most recent played game before `week` (DECISIONS #241:
    the current starter, not the opening-day one), or None before the team's first game."""
    t = played_before(schedule, team, season, week)
    known = [q for q in (_starter(g, team) for _, g in t.iterrows()) if q]
    return known[-1] if known else None     # a final score posted before its plays has no starter yet


def backup_qb(mine: pd.DataFrame, schedule: pd.DataFrame, team: str, season: int, week: int) -> pd.DataFrame:
    """Adds backup_qb (and qb_started, the starter's name): a game started by a quarterback other
    than his team's current starter (who started its most recent game before the priced week). The
    new starter's own games are not marked once he has the job (DECISIONS #241; it was the
    opening-day starter, which marked every game after any change for the rest of the season).
    Before the team's first game there is no current starter and nothing is marked. Display only."""
    sch = schedule.set_index("game_id")
    now = current_starter(schedule, team, season, week)
    marks, names_ = [], []
    for gid, tm in zip(mine["game_id"], mine["team"]):
        q = _starter(sch.loc[gid], tm) if gid in sch.index else None
        marks.append(bool(now and q and q != now))
        names_.append(_starter(sch.loc[gid], tm, "name") if gid in sch.index and "home_qb_name" in sch else None)
    return mine.assign(backup_qb=marks, qb_started=names_)


def main_teammates(b: Bundle, gsis: str, team: str, pos: str, season: int, week: int) -> list[str]:
    """His position group's main players (the user, 2026-10-13): WR/TE -- the team's top 3 receivers
    (WR or TE) by targets this season before the priced week; RB -- its lead carrier by carries. He is
    never his own teammate. Ties go to the smaller gsis id, so the list is stable. (The starting QB is
    the other main teammate; lineup_marks reads him from the QB footnote's starters.)"""
    if pos in ("WR", "TE"):
        plays, group, n = b.cut(b.targets[b.targets["season"] == season], season, week, "targets"), ("WR", "TE"), 3
    elif pos == "RB":
        plays, group, n = b.cut(b.carries[b.carries["season"] == season], season, week, "carries"), ("RB",), 1
    else:
        return []
    mine = plays[(plays["posteam"] == team) & (plays["gsis_id"] != gsis)]
    if mine.empty:                               # no teammate plays yet (week 1): no main teammates
        return []
    counts = mine.groupby("gsis_id").size().rename("n").reset_index()
    keep = counts["gsis_id"].map(lambda g: b.position_at(g, season, week) in group).astype(bool)
    counts = counts[keep]
    return list(counts.sort_values(["n", "gsis_id"], ascending=[False, True])["gsis_id"].head(n))


def _surname(name: str) -> str:
    words = [w for w in str(name).split() if w.rstrip(".").upper() not in ("JR", "SR", "II", "III", "IV", "V")]
    return words[-1] if words else str(name)


def lineup_marks(b: Bundle, last: pd.DataFrame, gsis: str, team: str, pos: str, season: int,
                 week: int) -> tuple[list[bool], list[str], list[str]]:
    """The lineup check (the user, 2026-10-13; DECISIONS #247): a last-4 game is marked when a main
    teammate's status in it differs from today's --
      a. he took no offensive snap in that game and is active today, or
      b. he played in it and is Out or on injured reserve today.
    Main teammates: his position group's (main_teammates) and the team's starting QB -- the current
    starter of the QB footnote; a game another QB started is case a, a game the starter played while
    he is Out or on IR today is case b. 'Active today' = not Out on the priced week's official report
    and not on injured reserve (RES on his latest roster listing); Questionable counts as active and
    is returned as a flag. Case a counts only a game he played for this team while the teammate was on
    its roster that week (a teammate who joined later, or the player's games for another team, are not
    "out"). Before the priced week's report is published nobody is Out today. Returns (a mark per row of
    `last`, the card's cause lines, the flags).
    Display, the second average and the screen's gate only: no rate or bar reads it."""
    n = len(last)
    if not n:
        return [], [], []
    rep = b.injury_report(season)
    wk_rep = rep[(rep["season"] == season) & (rep["week"] == week)] if rep is not None else None
    status = {} if wk_rep is None else dict(zip(wk_rep["gsis_id"], wk_rep["report_status"]))
    ros = b.rosters
    latest = ros[(ros["season"] == season) & (ros["week"] <= week)].sort_values("week").drop_duplicates("gsis_id", keep="last")
    on_ir = set(latest[latest["status"].astype(str).str.startswith("RES")]["gsis_id"]) if "status" in latest else set()
    names_ = dict(zip(ros["gsis_id"], ros["full_name"]))
    played = set(zip(b.snap_share["game_id"], b.snap_share["gsis_id"]))

    def today(m):
        if m in on_ir:
            return "on IR"
        return "Out" if status.get(m) == "Out" else None

    marks = [False] * n
    lines, flags = [], []
    published = wk_rep is not None and "team" in wk_rep and bool((wk_rep["team"] == team).any())
    if not published:                            # a Tuesday read is not a Sunday one (the user, 2026-10-13; DECISIONS #248)
        lines.append("Injury report not yet published: nobody counts as Out today.")
    for m in main_teammates(b, gsis, team, pos, season, week):
        gone = today(m)
        if status.get(m) == "Questionable" and not gone:
            flags.append(f"{names_.get(m, m)} Questionable")
        rostered = set(zip(*ros[(ros["gsis_id"] == m) & (ros["team"] == team)][["season", "week"]].T.values)) \
            if len(ros) else set()
        ours = list(last["team"] == team) if "team" in last else [True] * n
        out_games = [i for i, (gid, yr, wk) in enumerate(zip(last["game_id"], last["season"], last["week"]))
                     if (gid, m) not in played and not gone and ours[i] and (yr, wk) in rostered]
        in_games = [i for i, gid in enumerate(last["game_id"]) if (gid, m) in played and gone]
        for i in out_games + in_games:
            marks[i] = True
        name = names_.get(m, m)
        if out_games:
            lines.append(f"{len(out_games)} of his last {n} came with {name} out. {_surname(name)} is active.")
        if in_games:
            lines.append(f"{len(in_games)} of his last {n} came with {name} playing. {_surname(name)} is {gone}.")
    # the starting QB, as the QB footnote reads him (DECISIONS #241 / #246): the current starter
    qb = current_starter(b.schedule, team, season, week)
    if qb and qb != gsis:
        gone = today(qb)
        if status.get(qb) == "Questionable" and not gone:
            flags.append(f"{names_.get(qb, qb)} (QB) Questionable")
        backup = list(last["backup_qb"]) if "backup_qb" in last else [False] * n
        for i, gid in enumerate(last["game_id"]):
            if backup[i] and not gone:
                marks[i] = True                 # another QB started; the QB footnote names him
        with_him = [i for i, gid in enumerate(last["game_id"]) if gone and not backup[i] and (gid, qb) in played]
        for i in with_him:
            marks[i] = True
        if with_him:
            name = names_.get(qb, qb)
            lines.append(f"{len(with_him)} of his last {n} came with {name} at QB. {_surname(name)} is {gone}.")
    return marks, lines, flags


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


def _rate(own_win: pd.DataFrame, own_season: pd.DataFrame, fn, col: str, base: float, k: float) -> Rate:
    """His blended rate (from `col`, summed) plus his plain window and season rates."""
    def plain(d):
        return fn(d[col]) if len(d) else None
    blended = rates.blend(float(own_win[col].sum()), len(own_win), base, k)
    finite("blended rate", [blended])
    return Rate(blended, plain(own_win), len(own_win), plain(own_season), len(own_season), base)


def build(b: Bundle, gsis: str, name: str, team: str, season: int, week: int,
          tuned: dict, fixed: dict, market: str) -> Player:
    """His rate for `market` and the pools it draws from, for `week` of
    `season`, from games before it only. Only the asked market's rate is built,
    so a short sample in another market cannot block this one; the league-wide
    checks on the loaded plays and the pools (missing values, plausible ranges)
    apply to every card on purpose: a bad league-wide input stops everything.
    A rate or pool below its
    minimum sample puts the market in not_enough (the card then shows no
    numbers, and model() refuses it)."""
    require(fixed == b.fixed, "build() was given other fixed settings than the ones its pools were built with")
    pos = b.position_at(gsis, season, week) or "?"
    mine = b.cut(b.games[b.games["gsis_id"] == gsis], season, week, "his games").sort_values(["season", "week"])
    mine = fewer_snaps(mine, b.snap_share, float(fixed["fewer_snaps_share"]))
    mine = backup_qb(mine, b.schedule, team, season, week)
    window = mine.tail(int(fixed["rate_window_games"]))
    last_n = int(fixed["usual_games"])
    marks, causes, qflags = lineup_marks(b, window.tail(last_n), gsis, team, pos, season, week)
    window = window.assign(lineup_mark=[False] * (len(window) - len(marks)) + marks)
    this = _results(b, mine[mine["season"] == season], int(fixed["result_margin"]))
    pools = b.pools(season, int(fixed["pool_seasons"]))
    pl = Player(gsis, name, team, pos, season, week, window, this, pools=pools, lineup=causes, lineup_flags=qflags)
    keys = pd.MultiIndex.from_frame(window[["season", "week"]]) if len(window) else None

    def own(df):
        d = b.cut(df[df["gsis_id"] == gsis], season, week, "his plays")      # window and season alike
        in_win = (pd.MultiIndex.from_frame(d[["season", "week"]]).isin(keys)
                  if keys is not None and len(d) else np.zeros(len(d), dtype=bool))
        win = d[np.asarray(in_win, dtype=bool)]
        return win, d[d["season"] == season]

    n_win = fixed["rate_window_games"]
    why = []
    if market == "rush_yds":
        c_win, c_season = own(b.carries)
        if len(c_win) < min_own(market, fixed):
            why.append(f"{len(c_win)} of his own carries in his last {n_win} games (needs {min_own(market, fixed)})")
        if pools["rb_n"] < fixed["min_pool_rb_carries"]:
            why.append(f"{pools['rb_n']} running-back carries in the residual pool "
                       f"(needs {fixed['min_pool_rb_carries']})")
        n_pos = pools["carries_by_pos"].get(pos, 0)
        if pos != "RB" and n_pos < fixed["min_pool_position_carries"]:   # for a back: the residual pool above
            why.append(f"{n_pos} {pos} carries in the pool for his position's average "
                       f"(needs {fixed['min_pool_position_carries']})")
        base = pools["ypc_by_pos"].get(pos, pools["league_ypc"])   # league value only when no numbers are shown
        pl.rates["ypc"] = _rate(c_win, c_season, rates.yards_per_carry, "yards", base, tuned["k_ypc"])
    elif market == "receptions":
        t_win, t_season = own(b.targets)
        if len(t_win) < min_own(market, fixed):
            why.append(f"{len(t_win)} passes thrown to him in his last {n_win} games "
                       f"(needs {min_own(market, fixed)})")
        bk = depth_buckets(t_win["air_yards"], fixed["depth_short_below"], fixed["depth_deep_from"])
        pl.no_depth = int(bk.isna().sum())          # shown on the card; left out of his depth mix only
        bk = bk.dropna()
        by, n_by = pools["catch_by_pos_bucket"], pools["targets_by_pos_bucket"]
        thin = [x for x in sorted(set(bk)) if n_by.get((pos, x), 0) < fixed["min_pool_targets_per_bucket"]]
        if thin:
            why.append(f"too few {pos} targets in the pool for depth {', '.join(thin)} "
                       f"(needs {fixed['min_pool_targets_per_bucket']} each)")
        if len(t_win) and not len(bk):
            why.append("none of his targets has a recorded depth")
        base = float(np.mean([by[(pos, x)] for x in bk])) if len(bk) and not thin else pools["league_catch"]
        pl.rates["catch"] = _rate(t_win, t_season, rates.catch_rate, "caught", base, tuned["k_catch"])
    elif market == "rec_yds":
        t_win, t_season = own(b.targets)
        if len(t_win) < min_own(market, fixed):
            why.append(f"{len(t_win)} passes thrown to him in his last {n_win} games "
                       f"(needs {min_own(market, fixed)})")
        bk_t = depth_buckets(t_win["air_yards"], fixed["depth_short_below"], fixed["depth_deep_from"])
        pl.no_depth = int(bk_t.isna().sum())
        bk_t = bk_t.dropna()
        by, n_by = pools["catch_by_pos_bucket"], pools["targets_by_pos_bucket"]
        cy = pools["catch_yards_by_pos_bucket"]
        caught_win = t_win[t_win["caught"]]
        bk_c = depth_buckets(caught_win["air_yards"], fixed["depth_short_below"], fixed["depth_deep_from"]).dropna()
        # the depths he catches at (yards) and is targeted at (catch rate) need real pool samples
        need = sorted(set(bk_c) | set(bk_t), key=BUCKETS.index)
        lo = fixed["min_pool_targets_per_bucket"]
        # a depth where his position has fewer than the minimum catches uses every position's catches there
        # (the user, 2026-10-10; said in the "Calculation" follow-up); only if those are thin too, not enough data
        every = pools.get("catch_yards_by_bucket", {})
        pooled_all = [x for x in need if len(cy.get((pos, x), ())) < lo]
        yards_pool = {x: (every.get(x, np.zeros(0)) if x in pooled_all else cy[(pos, x)]) for x in need}
        thin_c = [x for x in need if len(yards_pool[x]) < lo]
        thin_t = [x for x in need if n_by.get((pos, x), 0) < lo]
        if thin_c:
            why.append(f"too few catches in the pool for depth {', '.join(thin_c)}, even counting every "
                       f"position (needs {lo} each)")
        if thin_t:
            why.append(f"too few {pos} targets in the pool for depth {', '.join(thin_t)} (needs {lo} each)")
        if len(caught_win) and not len(bk_c):
            why.append("none of his catches has a recorded depth")
        if not why:
            # catch rate: as for receptions (his targets' depth mix sets the baseline)
            base_c = float(np.mean([by[(pos, x)] for x in bk_t])) if len(bk_t) else pools["league_catch"]
            cr = _rate(t_win, t_season, rates.catch_rate, "caught", base_c, tuned["k_catch"])
            # his catches' depth mix, and the position's average catch at that mix (yards per catch baseline)
            mix = tuple(float((bk_c == x).mean()) for x in BUCKETS)
            base_ypr = float(sum(m * yards_pool[x].mean() for m, x in zip(mix, BUCKETS) if m > 0))
            ypr = rates.blend(float(caught_win["yards"].sum()), len(caught_win), base_ypr, tuned["k_ypr"])
            finite("blended yards per catch", [ypr])
            own_ypt = rates.yards_per_target(t_win["yards"], t_win["caught"]) if len(t_win) else None
            season_ypt = rates.yards_per_target(t_season["yards"], t_season["caught"]) if len(t_season) else None
            pl.rates["ypt"] = Rate(cr.blended * ypr, own_ypt, len(t_win), season_ypt, len(t_season), base_c * base_ypr)
            pl.rates["catch"] = cr
            pl.receiving = {"catch": cr.blended, "ypr": ypr, "mix": mix, "pooled_all_positions": pooled_all,
                            # the blend's inputs, so the test harness can re-blend at another k_ypr
                            "own_yards": float(caught_win["yards"].sum()), "own_catches": len(caught_win),
                            "base_ypr": base_ypr,
                            "pools": tuple(yards_pool.get(x, np.zeros(1)) for x in BUCKETS)}   # a depth he never
            # catches at has share 0, so its pool (a placeholder when the position has none) is never drawn
    elif market == "pass_yds":
        q_win, q_season = own(b.completions)
        if len(q_win) < min_own(market, fixed):
            why.append(f"{len(q_win)} of his own completions in his last {n_win} games "
                       f"(needs {min_own(market, fixed)})")
        bk = depth_buckets(q_win["air_yards"], fixed["depth_short_below"], fixed["depth_deep_from"])
        pl.no_depth = int(bk.isna().sum())
        bk = bk.dropna()
        cp = pools.get("comp_yards_by_bucket", {})
        lo = fixed["min_pool_completions_per_bucket"]
        thin = [x for x in sorted(set(bk), key=BUCKETS.index) if len(cp.get(x, ())) < lo]
        if thin:
            why.append(f"too few starting quarterbacks' completions in the pool for depth {', '.join(thin)} "
                       f"(needs {lo} each)")
        if len(q_win) and not len(bk):
            why.append("none of his completions has a recorded depth")
        if not why:
            mix = tuple(float((bk == x).mean()) for x in BUCKETS)
            base = float(sum(m * cp[x].mean() for m, x in zip(mix, BUCKETS) if m > 0))
            pl.rates["ypcomp"] = _rate(q_win, q_season, rates.yards_per_completion, "yards", base, tuned["k_ypcomp"])
            pl.passing = {"mix": mix, "pools": tuple(cp.get(x, np.zeros(1)) for x in BUCKETS)}
    else:
        raise ValueError(f"{market} is not built yet")
    if why:
        pl.not_enough[market] = why
    return pl


def model(pl: Player, market: str, tuned: dict, fixed: dict) -> calc.Model:
    """The calculator for this player-market. Refuses a market that is short of
    data, so no caller can get workload numbers for it."""
    require(market not in pl.not_enough, f"not enough data for {market}: {pl.not_enough.get(market)}")
    sims, seed, lim = int(fixed["sims"]), int(fixed["seed"]), calc.Limits.from_fixed(fixed)
    if market == "rush_yds":
        d = calc.make_draws("carries", tuned["carry_r"], sims, seed, lim)
        return calc.Model(market, "carries", d, pl.rates["ypc"].blended, pl.pools["rb_residuals"], tuned["day_sd"])
    if market == "receptions":
        d = calc.make_draws("targets", tuned["target_r"], sims, seed, lim)
        return calc.Model(market, "targets", d, pl.rates["catch"].blended)
    if market == "rec_yds":
        d = calc.make_draws("targets", tuned["target_r"], sims, seed, lim, yards=True)
        r = pl.receiving
        return calc.Model(market, "targets", d, pl.rates["ypt"].blended, catch=r["catch"], depth_mix=r["mix"],
                          catch_pools=r["pools"])
    if market == "pass_yds":
        d = calc.make_draws("completions", tuned["completion_r"], sims, seed, lim, yards=True)
        p = pl.passing
        return calc.Model(market, "completions", d, pl.rates["ypcomp"].blended, catch=1.0, depth_mix=p["mix"],
                          catch_pools=p["pools"])
    raise ValueError(f"{market} is not built yet")
