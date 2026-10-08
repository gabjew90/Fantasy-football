#!/usr/bin/env python3
"""Score one upcoming NFL game's player props. Self-contained per invocation.

  python score_game.py --away DET --home BUF [--season 2026] [--week N]
                       [--prior-archive FILE] [--prior-log FILE]
                       [--books all|draftkings,fanduel] [--min-er 0.03] [--min-gap 0.03]
                       [--no-odds]

Reads bundled prior-season tables from resources/ (built by build_priors.py), fetches
only the CURRENT season's play-by-play, rosters, depth charts, injuries and snap counts,
pulls a decision-time quote from Sleeper Picks (The Odds API as fallback), and writes:

  report.md                      the skill's required report structure
  line_archive_nfl_{season}.jsonl decision snapshot rows (merged with --prior-archive)
  shadow_log_{season}_wk{W}_{AWAY}_{HOME}.csv  one row per posted line, all PASS

EVERY probability here is EXPLORATORY. receiving_hier_v2 and anytime_td_v1 are PROTOTYPE
(outcome-backtested, not tested against posted lines); rush_yds_v0 is PROTOTYPE too. Since
props-v1.20 the yardage samplers carry the width settings (resources/width_params.json), and
all three yardage markets pass the 2022-25 harness (reports/yardage_harness.md): unbiased,
~20% of outcomes outside p10-p90, every 60-90% bucket within 3 points.
Nothing is a fair price or an entry threshold.
Recommendation is PASS on every line, per the model registry.
"""
import argparse, json, os, subprocess, sys, time, zlib
from datetime import datetime, timezone
from pathlib import Path

import re
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eligibility
import model as MODEL
import research as RSCH
import scenario as SC
import td_joint as TDJ
import td_market as TDM
import td_v1 as TDV1
from model import norm_name, name_key_loose, is_team_entry, blend

# The report contains "≥" and other non-cp1252 characters. The Linux
# runner writes UTF-8 by default so this was invisible in CI, while every
# local run died on the final print. Same reconfigure the draftkit CLI does.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):  # pragma: no cover - non-tty streams
        pass


HERE = Path(__file__).resolve().parent
RES = HERE.parent / "resources"
NFLVERSE = "https://github.com/nflverse/nflverse-data/releases/download"
GAMES_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
# nflverse team codes -> the codes two other sources use. Everything else is identical.
ESPN_TEAM = {"WAS": "WSH", "LA": "LAR"}
SLEEPER_TEAM = {"LA": "LAR"}


def cached_json(path, ttl_s, loader):
    """Read `path` if it is younger than ttl_s seconds, else call loader(), write, return.
    Slate runs (score_week.py) share one workdir, so one Sleeper/ESPN pull serves all games."""
    import time
    p = Path(path)
    if p.exists() and (time.time() - p.stat().st_mtime) < ttl_s:
        return json.load(open(p, encoding="utf-8"))
    obj = loader()
    p.parent.mkdir(parents=True, exist_ok=True)
    json.dump(obj, open(p, "w", encoding="utf-8"))
    return obj


# SLEEPER'S INJURY FEED (DECISIONS #183): the official report lands Wednesday (Monday for
# a Thursday game) and nflverse after it; Sleeper's player feed carries each player's
# status as soon as it is news (Baker Mayfield "Out, thumb" four days before a Thursday
# game with no report out yet). Used ONLY where this week's official report has no entry,
# and -- once a team's report is out -- only for a player it lists as missing or limited in
# practice (a player off the report is healthy; Sleeper can still carry last week's "Out"),
# or on a reserve list, which the weekly report never carries (code review, 2026-10-06).
SLEEPER_OUT = {"Out": "Out", "Doubtful": "Doubtful", "IR": "Out", "PUP": "Out", "Sus": "Out", "NFI": "Out"}
SLEEPER_RESERVE = {"IR", "PUP", "Sus", "NFI"}


def sleeper_injury_map(players, sleeper_team=None) -> dict:
    """{("gsis", gsis_id): (status, body part)} and, for players the feed gives no gsis_id,
    {(our team code, norm_name): (status, body part)} from Sleeper's player feed, for
    players it lists as Out / Doubtful / Questionable or on IR / PUP / suspended. The id
    is the join (CLAUDE.md: players are joined by ID, never by name alone); the name key
    is the fallback."""
    back = {v: k for k, v in (sleeper_team or {}).items()}
    out = {}
    for v in (players or {}).values():
        st = v.get("injury_status")
        if st not in SLEEPER_OUT and st != "Questionable":
            continue
        hit = (st, v.get("injury_body_part"))
        gid = str(v.get("gsis_id") or "").strip()
        if gid:
            out[("gsis", gid)] = hit
        name = v.get("full_name") or f'{v.get("first_name", "")} {v.get("last_name", "")}'.strip()
        if name and v.get("team"):
            out.setdefault((back.get(v["team"], v["team"]), norm_name(name)), hit)
    return out


def _missed_practice(practice_status) -> bool:
    """Whether a report's practice status says he missed practice or was limited."""
    p = str(practice_status or "").lower()
    return "did not" in p or "limited" in p or p in ("dnp", "lp")


def injuries_with_fallback(official, roster, sleeper, practice=None, reported_teams=()):
    """This week's status per (team, gsis_id): the official report where it has an entry,
    else Sleeper's (IR / PUP / suspended read as Out). For a team whose report is out
    (reported_teams), Sleeper fills in only a player the report lists as missing or
    limited in practice (practice: {(team, gsis_id): practice status}), or a reserve-list
    designation. Returns (status, source) dicts; source names Sleeper and the body part
    for every status it supplied."""
    status, source = dict(official), {}
    reported = set(reported_teams or ())
    for t, g, n in zip(roster.team, roster.gsis_id, roster.full_name):
        if isinstance(status.get((t, g)), str):
            continue
        hit = sleeper.get(("gsis", str(g).strip())) or sleeper.get((t, norm_name(n)))
        if not hit:
            continue
        st, part = hit
        if t in reported and st not in SLEEPER_RESERVE:
            if not _missed_practice((practice or {}).get((t, g))):
                continue          # off the report or practising fully: the report says he is fine
            why = "the official report has his practice but no game status yet"
        else:
            why = "no official report yet" if t not in reported else "a reserve list"
        status[(t, g)] = SLEEPER_OUT.get(st, st)
        source[(t, g)] = f"Sleeper injury feed{', ' + part.lower() if part else ''}; {why}"
    return status, source


def resolve_roof(roof, stadium_id, games):
    """The game's roof. nflverse leaves it blank until the game is played, and a blank read
    as outdoors fired the wind screen for a closed retractable roof (AT&T Stadium, outside
    review 2026-10-06). Blank: the roof this stadium recorded most often in its last 16
    games, with a note saying so. Returns (roof, note or None)."""
    r = str(roof).strip().lower() if roof is not None else ""
    if r and r != "nan":
        return r, None
    if stadium_id is None or games is None or "stadium_id" not in games or "roof" not in games:
        return "unknown", "roof not posted yet and no stadium history"
    h = games[(games.stadium_id == stadium_id) & games.roof.notna()]
    h = h.sort_values("gameday").tail(16) if "gameday" in h else h.tail(16)
    if h.empty:
        return "unknown", "roof not posted yet and no stadium history"
    vc = h.roof.astype(str).str.lower().value_counts()
    top = vc.index[0]
    return top, (f"roof not posted yet; {int(vc.iloc[0])} of this stadium's last {len(h)} games were "
                 f"{top}" + ("; retractable, the call is made on game day" if len(vc) > 1 or top in ("open", "closed")
                             else ""))


def promote_qb(roles, team, qb_order, is_out, on_roster):
    """When a team's depth-chart QB1 is out, the next quarterback who is on the roster and
    not out starts: only one QB plays, so unlike the other positions his job goes to one
    man (DECISIONS #183). qb_order: the team's QBs, best first. Returns (roles, promoted
    gsis_id or None)."""
    q1 = roles[(roles.team == team) & (roles.slot == "QB1")] if not roles.empty else roles
    if q1.empty or not is_out(q1.gsis_id.iloc[0]):
        return roles, None
    for g in qb_order:
        if g != q1.gsis_id.iloc[0] and on_roster(g) and not is_out(g):
            keep = roles[~((roles.team == team) & (roles.gsis_id == g))]
            return pd.concat([keep, pd.DataFrame([{"team": team, "gsis_id": g, "slot": "QB1",
                                                   "dc_dt": pd.NaT}])], ignore_index=True), g
    return roles, None
N_SIM = 20000
OUT = Path(os.environ.get("NFL_OUT", "/mnt/user-data/outputs"))

# nflverse abbreviation -> The Odds API team name. The API filters on the full name, so
# passing "BUF" returns nothing; the old date-based fallback then grabbed whichever game the
# API listed first that day. Verified wrong-game archive write on a Sunday. Hard map + assert.
TEAM_NAMES = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LA": "Los Angeles Rams", "LAR": "Los Angeles Rams",
    "LAC": "Los Angeles Chargers", "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings", "NE": "New England Patriots", "NO": "New Orleans Saints",
    "NYG": "New York Giants", "NYJ": "New York Jets", "PHI": "Philadelphia Eagles",
    "PIT": "Pittsburgh Steelers", "SEA": "Seattle Seahawks", "SF": "San Francisco 49ers",
    "TB": "Tampa Bay Buccaneers", "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}
YARD_MARKETS = {"player_reception_yds": "rec_yards", "player_rush_yds": "rush_yards",
                "player_pass_yds": "pass_yards",
                # a back's rushing + receiving, the sum of his two draws in each simulation
                # (reports/rush_rec_calibration.md: priced since it passed, DECISIONS #187)
                "player_rush_reception_yds": "rush_rec_yards"}
COUNT_MARKETS = {"player_receptions": "receptions"}
# DEFERRED (user, 2026-10-06; DECISIONS #190): the engine's focus is receptions, receiving
# yards, non-QB rushing, rushing + receiving and passing yards. Anytime TDs are still priced,
# LOGGED and graded (the record keeps measuring them) but left off what the user reads -- the
# report's player tables and TD pairs -- unless he asks (--markets td).
DEFERRED_MARKETS = {"player_anytime_td"}
CONSENSUS_TOL = {"player_receptions": 1.0, "player_reception_yds": 4.0, "player_rush_yds": 5.0,
                 "player_pass_yds": 10.0, "player_rush_reception_yds": 6.0}


def now(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def eastern_to_utc(date_str, time_str):
    """Convert a games.csv ET kickoff to UTC without needing the tzdata package.
    US DST: second Sunday of March 02:00 to first Sunday of November 02:00 (since 2007)."""
    from datetime import timedelta
    naive = pd.Timestamp(f"{date_str} {time_str}")
    y = naive.year
    mar = pd.Timestamp(y, 3, 1); dst_start = mar + pd.Timedelta(days=(6 - mar.weekday()) % 7 + 7)
    nov = pd.Timestamp(y, 11, 1); dst_end = nov + pd.Timedelta(days=(6 - nov.weekday()) % 7)
    offset = 4 if (dst_start.replace(hour=2) <= naive < dst_end.replace(hour=2)) else 5
    return (naive + pd.Timedelta(hours=offset)).tz_localize("UTC")
def log(m): print(m, file=sys.stderr)


FETCH_MAX_AGE_S = int(os.environ.get("NFL_FETCH_MAX_AGE_S", str(6 * 3600)))


def fetch(url, dest, max_age_s=None):
    """Download `url` to `dest` unless a copy younger than `max_age_s` exists.

    THE AGE CHECK IS THE POINT. This used to return any file that existed. The
    props workflow restores props/.cache on every tick, so the first capture's
    play-by-play, injuries, depth charts, rosters and snaps were reused for every
    capture after it: week 3 would have been priced without week 2's usage or
    this week's injury report. A failed refresh falls back to the stale copy and
    says so -- a capture on older inputs beats no capture."""
    import urllib.request
    dest = Path(dest)
    max_age_s = FETCH_MAX_AGE_S if max_age_s is None else max_age_s
    if dest.exists() and time.time() - dest.stat().st_mtime < max_age_s:
        return dest
    log(f"  fetch {url.rsplit('/',1)[-1]}")
    tmp = dest.with_name(dest.name + ".part")
    try:
        urllib.request.urlretrieve(url, tmp)
        tmp.replace(dest)
    except Exception as ex:  # noqa: BLE001
        tmp.unlink(missing_ok=True)
        if not dest.exists():
            raise
        age_h = (time.time() - dest.stat().st_mtime) / 3600
        log(f"  STALE INPUT: refresh of {dest.name} failed ({type(ex).__name__}); "
            f"using the copy from {age_h:.1f} h ago")
    return dest


def season_inputs(season, wd) -> dict:
    """The current-season nflverse files a capture reads: name -> (url, local path).
    One list, so score_week can refresh them once for the whole slate."""
    wd = Path(wd)
    return {"pbp": (f"{NFLVERSE}/pbp/play_by_play_{season}.csv", wd / f"pbp_{season}.csv"),
            "rosters": (f"{NFLVERSE}/weekly_rosters/roster_weekly_{season}.csv", wd / f"ros_{season}.csv"),
            "injuries": (f"{NFLVERSE}/injuries/injuries_{season}.csv", wd / f"inj_{season}.csv"),
            "depth_charts": (f"{NFLVERSE}/depth_charts/depth_charts_{season}.csv", wd / f"dc_{season}.csv"),
            "snaps": (f"{NFLVERSE}/snap_counts/snap_counts_{season}.csv", wd / f"snap_{season}.csv"),
            "games": (GAMES_URL, wd / "games.csv")}


def refresh_season_inputs(season, wd) -> dict:
    """Refresh every current-season input once and return each file's age in
    hours. score_week calls this before the first game so one slate is priced
    on one version of the inputs, then pins the per-game fetches to it."""
    ages = {}
    for name, (url, dest) in season_inputs(season, wd).items():
        try:
            fetch(url, dest)
            ages[name] = round(max(0.0, time.time() - Path(dest).stat().st_mtime) / 3600, 1)
        except Exception as ex:  # noqa: BLE001 -- the per-game run reports it
            ages[name] = f"unavailable ({type(ex).__name__})"
    return ages


# ---------------------------------------------------------------- odds helpers
def amer_to_p(a): return 100 / (a + 100) if a > 0 else -a / (-a + 100)
def payout(a): return a / 100 if a > 0 else 100 / (-a)


def espn_scoreboard_url(season, week):
    """The regular-season scoreboard for ONE week. The bare endpoint shows the current week,
    which lags a day behind at the Tuesday rollover."""
    return ("https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
            f"?seasontype=2&week={int(week)}&dates={int(season)}")


def run_odds(stage, args_list):
    cmd = [sys.executable, str(HERE / "odds_client.py"), stage] + args_list
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(HERE))
    if r.returncode != 0 and not r.stdout.strip():
        raise RuntimeError(f"odds_client {stage} failed: {r.stderr[:400]}")
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        # odds_client prints its own plain reason on stdout (e.g. no key in this
        # environment); it never contains the key itself
        raise RuntimeError(f"odds_client {stage} returned no JSON (exit {r.returncode}): "
                           f"{(r.stdout.strip() or r.stderr.strip())[-300:]}")


# ---------------------------------------------------------------- CLI conveniences
# Abbreviations people type that games.csv spells differently.
CLI_ALIASES = {"LAR": "LA", "WSH": "WAS", "JAC": "JAX", "LVR": "LV"}
MARKET_ALIASES = {"receptions": "player_receptions", "rec": "player_receptions",
                  "rec_yds": "player_reception_yds", "receiving_yards": "player_reception_yds",
                  "rush_yds": "player_rush_yds", "rushing_yards": "player_rush_yds",
                  "pass_yds": "player_pass_yds", "passing_yards": "player_pass_yds",
                  "td": "player_anytime_td", "anytime_td": "player_anytime_td", "atd": "player_anytime_td",
                  "rush_rec": "player_rush_reception_yds", "rush_rec_yds": "player_rush_reception_yds"}
# A TD-only run takes DraftKings anytime prices from The Odds API when the last
# known quota leaves at least this many credits; otherwise Sleeper. (ESPN's
# free prop feed lists anytime-TD markets but carries no price for them.)
TD_QUOTA_MIN = 100
FANTASY_PRESETS = {"ppr": {"rec": 1.0}, "half": {"rec": 0.5}, "std": {"rec": 0.0}}
FANTASY_BASE = {"rec": 1.0, "rec_yd": 0.1, "rush_yd": 0.1, "rush_td": 6.0, "rec_td": 6.0}


def et_today() -> str:
    """Today's date in US Eastern time, the calendar games.csv uses. The chat
    container and Actions runners run on UTC, which is already tomorrow on a
    Monday night. DST: second Sunday of March to first Sunday of November."""
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    y = now.year

    def nth_sunday(month, n):
        d = datetime(y, month, 1, tzinfo=timezone.utc)
        first = d + timedelta(days=(6 - d.weekday()) % 7)
        return first + timedelta(weeks=n - 1)
    dst = nth_sunday(3, 2) + timedelta(hours=7) <= now < nth_sunday(11, 1) + timedelta(hours=6)
    return (now - timedelta(hours=4 if dst else 5)).strftime("%Y-%m-%d")


def resolve_team(x: str) -> str:
    x = x.strip().upper()
    return CLI_ALIASES.get(x, x)


def parse_markets(spec: str | None) -> set[str]:
    """--markets receptions,rec_yds,rush_yds,td -> the engine's market keys."""
    if not spec:
        return set()
    out = set()
    for t in spec.split(","):
        t = t.strip().lower()
        if not t:
            continue
        key = MARKET_ALIASES.get(t, t if t.startswith("player_") else None)
        if key is None:
            sys.exit(f"--markets: unknown market '{t}'. Use: {', '.join(sorted(MARKET_ALIASES))}")
        out.add(key)
    return out


# Roster statuses that mean "on the team, not playing" (DECISIONS #162). INA is a
# game-day inactive; the rest are reserve lists. Anything else that is not ACT
# (practice squad, cut, traded) keeps the old handling: not in the pool at all.
NOT_PLAYING = ("INA", "RES", "PUP", "SUS", "NFI")


def week_roster(ros: pd.DataFrame, season: int, week: int):
    """This week's roster rows, or -- before they are published -- the latest week's as
    provisional (returned with that week). INA is one game's inactive list: last week's
    says nothing about this week, where the injury report decides (Baker Mayfield, INA
    in week 4, was priced out of the week 5 board before the week 5 report existed,
    2026-10-05), so a provisional INA reads as ACT."""
    cols = ["team", "gsis_id", "full_name", "position", "status"]
    rw = ros[(ros.season == season) & (ros.week == week)][cols].drop_duplicates(["team", "gsis_id"])
    if not rw.empty:
        return rw, None
    last = ros[ros.season == season].week.max()
    rw = ros[(ros.season == season) & (ros.week == last)][cols].drop_duplicates(["team", "gsis_id"])
    rw = rw.assign(was_inactive=rw.status.eq("INA"))
    return rw.assign(status=rw.status.replace({"INA": "ACT"})), last


def keep_in_pool(status, played_this_season: bool) -> bool:
    """Whether a rostered, eligible player enters the pool. ACT and INA always;
    a reserve-list player only if he played this season -- his share is in his
    teammates' numbers and must be handed on. One out since before the season
    is already absent from them, so handing a prior share on would count it twice."""
    if status in ("ACT", "INA"):
        return True
    return status in NOT_PLAYING and played_this_season


def apply_designations(pop: pd.DataFrame, assume_out=frozenset()) -> pd.DataFrame:
    """A2: Out/Doubtful removed, Questionable flagged for regime treatment, and
    a scenario's assumed-out players marked out whatever their report says.
    `report_status` is made an object column first: an all-NaN one is float64,
    and pandas 3 refuses a string written into it (the chat-log crash,
    2026-09-26)."""
    pop = pop.copy()
    pop["report_status"] = pop["report_status"].astype(object)
    # INA (game-day inactive) and the reserve lists are not playing (DECISIONS #162)
    pop["excluded"] = pop.report_status.isin(["Out", "Doubtful"]) | pop.status.isin(NOT_PLAYING)
    pop["questionable"] = pop.report_status.eq("Questionable")
    if assume_out:
        ao = pop.gsis_id.isin(assume_out)
        pop.loc[ao, "report_status"] = "Out (scenario)"
        pop["excluded"] = pop["excluded"] | ao
        pop["questionable"] = pop["questionable"] & ~ao
    return pop


COMPARE_QUOTA_MIN = 100      # --compare-books never spends the last credits
COMPARE_BOOKS = ("draftkings", "fanduel")
COMPARE_MARKETS = "player_receptions,player_reception_yds,player_rush_yds,player_pass_yds"


def last_oddsapi_quota() -> int | None:
    """Remaining Odds API credits from the newest cached odds response, if any."""
    files = sorted((HERE / "cache").glob("odds_*.json"), key=lambda f: f.stat().st_mtime)
    for f in reversed(files):
        try:
            q = json.loads(f.read_text(encoding="utf-8")).get("quota", {})
            v = q.get("x-requests-remaining")
            if v is not None:
                return int(float(v))
        except Exception:  # noqa: BLE001 -- a bad cache file just means "unknown"
            continue
    return None


def parse_scoring(spec: str) -> dict:
    """--fantasy-scoring ppr | half | std | path/to.json | 'rec=0.5,rec_yd=0.1,...'.
    Keys follow the league files: rec, rec_yd, rush_yd, rush_td, rec_td."""
    sc = dict(FANTASY_BASE)
    if spec in FANTASY_PRESETS:
        sc.update(FANTASY_PRESETS[spec])
    elif spec.endswith(".json") and Path(spec).exists():
        sc.update({k: float(v) for k, v in json.loads(Path(spec).read_text(encoding="utf-8")).items() if k in sc})
    else:
        for kv in spec.split(","):
            if "=" in kv:
                k, v = kv.split("=", 1)
                if k.strip() in sc:
                    sc[k.strip()] = float(v)
    return sc


def fantasy_table(M, sims, V1TD, td_lambda, scoring: dict, rng, n_sim: int) -> pd.DataFrame:
    """Fantasy points per player from the joint simulation's draws: receptions,
    receiving and rushing yards from the yardage model's draws; touchdowns
    drawn from anytime_td_v1 (each team's offensive-TD count, then each TD to a
    player by his per-TD share) or, for a player v1 did not price, Poisson from
    the v0 rate. Passing is not modelled, so a QB row is rushing only."""
    import td_model as _T
    tds = {}
    for t in M.team.unique():
        Mt = M[M.team == t]
        v = V1TD[V1TD.team == t] if V1TD is not None and len(V1TD) else None
        if v is not None and len(v):
            mu = float(v["mu"].iloc[0])
            pmf = _T.count_pmf([mu], n=_T.LAYER1["trials"])[0]
            N = rng.choice(len(pmf), size=n_sim, p=pmf / pmf.sum())
            ids = [g for g in Mt.gsis_id if g in v.index]
            q = np.array([float(v.loc[g, "q"]) for g in ids])
            pv = np.append(q, max(1.0 - q.sum(), 0.0))
            alloc = rng.multinomial(N, pv / pv.sum())
            for j, g in enumerate(ids):
                tds[g] = alloc[:, j]
        for _, m in Mt.iterrows():
            if m.gsis_id not in tds:
                tds[m.gsis_id] = rng.poisson(max(td_lambda(m), 0.0), size=n_sim)
    rows = []
    for _, m in M.iterrows():
        sm = sims[m["name"]]
        td_pts = scoring["rec_td"] if m.pos in ("WR", "TE") else scoring["rush_td"]
        pts = (sm["receptions"] * scoring["rec"] + sm["rec_yards"] * scoring["rec_yd"]
               + sm["rush_yards"] * scoring["rush_yd"] + tds[m.gsis_id] * td_pts)
        # gsis_id: the fantasy scenario command joins on it, never on the name;
        # p10-p90 are the percentiles the fantasy projection contract uses
        rows.append({"player": m["name"], "gsis_id": m.gsis_id, "team": m.team, "pos": m.pos, "slot": m.slot,
                     "median": float(np.median(pts)), "p20": float(np.percentile(pts, 20)),
                     "p80": float(np.percentile(pts, 80)), "mean": float(pts.mean()),
                     "p10": float(np.percentile(pts, 10)), "p25": float(np.percentile(pts, 25)),
                     "p75": float(np.percentile(pts, 75)), "p90": float(np.percentile(pts, 90)),
                     "p_td": float((tds[m.gsis_id] > 0).mean()),
                     "note": "rushing only: passing not modelled" if m.pos == "QB" else ""})
    return pd.DataFrame(rows).sort_values("median", ascending=False)


# Joint (parlay) pricing is gated off until a joint-outcome holdout exists.
# The research escape hatch is --enable-parlays, which stamps the output as
# unvalidated; it exists so the validation itself can be built.
ENABLE_PARLAYS = False

# ---------------------------------------------------------------- shrinkage
# blend() comes from model.py (imported above) so score_game.py and backtest.py
# can never define it differently by accident.


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--away", required=True); ap.add_argument("--home", required=True)
    ap.add_argument("--season", type=int, default=None)
    ap.add_argument("--week", type=int, default=None)
    ap.add_argument("--prior-season", type=int, default=None)
    ap.add_argument("--books", default="all")
    ap.add_argument("--min-gap", type=float, default=0.03)
    ap.add_argument("--min-er", type=float, default=0.03)
    ap.add_argument("--prior-archive"); ap.add_argument("--prior-log")
    ap.add_argument("--no-odds", action="store_true")
    ap.add_argument("--source", choices=["sleeper", "oddsapi"], default=None,
                    help="price source: Sleeper Picks (default; no key, no quota, pick'em multipliers converted to American) "
                         "or The Odds API (DK/FD, 8 credits a run). Whichever is not chosen is the automatic fallback. "
                         f"A TD-only run (--markets td) defaults to The Odds API when the cached quota shows {TD_QUOTA_MIN}+ credits.")
    ap.add_argument("--compare-books", action="store_true",
                    help="beside Sleeper, pull DraftKings and FanDuel player lines from The Odds API for this game "
                         "(~4 credits; skipped when no key or fewer than COMPARE_QUOTA_MIN credits remain)")
    ap.add_argument("--no-oddsapi-fallback", action="store_true",
                    help="never spend Odds API credits, even when Sleeper has no lines for this game")
    ap.add_argument("--sleeper-cache-ttl", type=int, default=int(os.environ.get("SLEEPER_CACHE_TTL", "600")),
                    help="seconds a cached Sleeper lines pull stays valid (slate runs share one pull)")
    ap.add_argument("--lines-file", default=None, help="CSV of manually entered lines (player,market,line,over_price,under_price,book); used instead of The Odds API")
    ap.add_argument("--env", choices=["history", "market"], default="history",
                    help="team-environment source. 'market' (spread/total re-centring) is UNVALIDATED: "
                         "2025 backtest showed no CRPS difference vs history. Default history.")
    ap.add_argument("--workdir", default="/tmp/nflrun")
    ap.add_argument("--assume-out", default="",
                    help="comma-separated gsis ids priced as OUT: the 'if he is out' case for a Questionable "
                         "player. Outputs go to OUT/scenarios, which the record never reads.")
    ap.add_argument("--assume", action="append", default=[],
                    help="YOUR scenario, repeatable: 'PLAYER: targets=8' / 'carries=14' / 'catch=70%%' / 'ypt=9' / "
                         "'ypc=4.5', or 'TEAM: pass=-3' / 'rush=+2' / 'ypt=-5%%'. The board is priced as usual; the "
                         "report adds 'Your scenario' with every line priced again under the assumptions "
                         "(scenario.py). Experimental, never recorded.")
    ap.add_argument("--role", action="append", default=[],
                    help="ROLE what-if, repeatable: 'PLAYER=SLOT' (QB1 RB1 RB2 WR1 WR2 WR3 TE1) prices a player "
                         "the depth chart has not promoted, with that slot's role average as his prior. Nobody "
                         "else moves. Outputs go to OUT/role, which the record never reads.")
    ap.add_argument("--scenario-run", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--odds-snapshot", default=None,
                    help="price from the lines and spread/total a main run saved; no fetch, no credits, no archive")
    ap.add_argument("--no-scenarios", action="store_true",
                    help="skip the 'if he is out' pricing for Questionable players (captures do not need it)")
    ap.add_argument("--markets", default="",
                    help="only these markets: receptions, rec_yds, rush_yds, td (comma list); prints a short summary")
    ap.add_argument("--fantasy-scoring", default="ppr",
                    help="fantasy_points_*.csv scoring: ppr | half | std | path.json | 'rec=0.5,rec_yd=0.1,...'")
    a = ap.parse_args()
    MARKETS = parse_markets(a.markets)
    SOURCE_NOTE = None
    if a.source is None:
        q_left = last_oddsapi_quota()
        if MARKETS == {"player_anytime_td"} and q_left is not None and q_left >= TD_QUOTA_MIN:
            a.source = "oddsapi"
            SOURCE_NOTE = f"TD-only run: DraftKings anytime prices from The Odds API ({q_left} credits left before this run)"
        else:
            a.source = "sleeper"
            if MARKETS == {"player_anytime_td"}:
                SOURCE_NOTE = (f"TD-only run on Sleeper: Odds API quota {'unknown' if q_left is None else q_left} "
                               f"(needs {TD_QUOTA_MIN}+ to switch to DraftKings)")
    global OUT
    ASSUME_OUT = {x for x in a.assume_out.split(",") if x}
    SNAP = json.loads(Path(a.odds_snapshot).read_text(encoding="utf-8")) if a.odds_snapshot else None
    # a scenario run ('if he is out', or the user's own assumptions) writes to
    # OUT/scenarios, which record_run never reads, and skips the research search
    SCENARIO = bool(ASSUME_OUT) or a.scenario_run
    # a ROLE what-if (DECISIONS #175) is a full run -- research included -- in its own
    # folder; its 'if he is out' and scenario children nest under it
    if a.role:
        OUT = OUT / "role"
    if SCENARIO:
        OUT = OUT / "scenarios"

    AWAY, HOME = resolve_team(a.away), resolve_team(a.home)
    try:
        ROLE_OVERRIDES = SC.parse_roles(a.role, {AWAY, HOME})
    except ValueError as exc:
        sys.exit(f"--role: {exc}")
    try:
        RULES = SC.parse(a.assume, {AWAY, HOME})
    except ValueError as exc:
        sys.exit(f"--assume: {exc}")
    if a.scenario_run and not RULES:
        sys.exit("--scenario-run needs at least one --assume")
    wd = Path(a.workdir); wd.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    # ONE RANDOM STREAM PER TEAM AND STAGE (fourth expert review, 2026-10-07): a what-if on one
    # team must not reshuffle the other team's draws. A single stream shared in draw order gave the
    # unchanged team fresh random numbers (Over chances moved by up to ~1 point, a quarter of them
    # past the scenario report's half-point listing threshold). The backtest already seeds per
    # team-game; stages: 101 receiving, 102 rushing, 103 passing, 34 / 39 the reversal shadows.
    # Within a team a what-if still re-splits the shared draws, so a teammate's listed move mixes
    # his real share change with ~0.3-0.4 points of simulation noise.
    team_stream = lambda t, stage: np.random.default_rng([20260917, stage, zlib.crc32(str(t).encode("utf-8"))])

    # ---------- 1. verify matchup from games.csv ----------
    games = pd.read_csv(fetch(GAMES_URL, wd / "games.csv"))
    SEASON = a.season or int(games[games.gameday >= datetime.now().strftime("%Y-%m-%d")].season.min())
    g = games[(games.season == SEASON) & (games.game_type == "REG")
              & (games.away_team == AWAY) & (games.home_team == HOME)]
    if a.week:
        g = g[g.week == a.week]
    elif len(g) > 1:
        # no --week: the NEXT meeting (divisional teams meet twice), else the latest
        upcoming = g[g.gameday >= et_today()]
        g = upcoming.sort_values("gameday").head(1) if len(upcoming) else g.sort_values("gameday").tail(1)
    if g.empty:
        seen = games[(games.season == SEASON) & (games.game_type == "REG")
                     & (games.away_team.isin([AWAY, HOME])) & (games.home_team.isin([AWAY, HOME]))]
        where = "; ".join(f"week {int(r.week)}: {r.away_team} at {r.home_team} ({r.gameday})" for r in seen.itertuples())
        sys.exit(f"MATCHUP NOT FOUND: {AWAY} at {HOME}" + (f" week {a.week}" if a.week else "")
                 + f" in {SEASON} REG. " + (f"These teams meet: {where}." if where else
                                             "They do not meet this season; check the abbreviations "
                                             f"(aliases accepted: {', '.join(f'{k}->{v}' for k, v in CLI_ALIASES.items())})."))
    G = g.iloc[0]; WEEK = int(G.week)
    roof, ROOF_NOTE = resolve_roof(G.roof, G.get("stadium_id"), games)
    log(f"verified: {AWAY} at {HOME}, {SEASON} week {WEEK}, {G.gameday} {G.gametime} ET, "
        f"{G.stadium}, roof={roof}" + (f" ({ROOF_NOTE})" if ROOF_NOTE else ""))

    PRIOR = a.prior_season or SEASON - 1
    P = json.load(open(RES / f"priors_{PRIOR}_params.json"))
    K0 = P["K0"]                              # fallback flat constant, kept for any rate not in k0_per_rate
    K0R = MODEL.k0_rates(P.get("k0_per_rate", MODEL.DEFAULT_K0))   # build_priors.py's fit, MODEL.K0_FIXED over it
    LEAGUE_PASS_RATE = P.get("league_pass_rate", 0.55)
    LEAGUE_PLAYS = P.get("league_plays_per_game", 64.0)
    pri_players = pd.read_csv(RES / f"priors_{PRIOR}_players.csv").set_index("gsis_id")
    pri_slots = pd.read_csv(RES / f"priors_{PRIOR}_slots.csv").set_index("slot")
    pri_teams = pd.read_csv(RES / f"priors_{PRIOR}_teams.csv").set_index("team")
    resid = np.array(P["carry_residual_quantiles"])

    SOURCES = []   # (name, what it's for, status, detail)
    if SOURCE_NOTE:
        SOURCES.append(("Price source choice", "which book prices this run", "ok", SOURCE_NOTE))
    SOURCES.append(("Schedule (nflverse games.csv)", "matchup, kickoff, stadium, roof", "ok",
                    f"{AWAY} at {HOME} week {WEEK} verified"))
    SOURCES.append((f"Prior-season priors ({PRIOR}, bundled)", "each player's baseline rates",
                    "ok", f"{len(pri_players)} players, {len(pri_slots)} role slots"))

    # ---------- 1b. market-anchored team environment (round 5) ----------
    # Backtest finding (2025, weeks 5-8 train / 9-18 test): re-centring team plays
    # and pass rate on the same-book spread/total beat the pure team-history blend
    # on BOTH receptions and reception-yards CRPS (+0.044 vs +0.038, +0.76 vs
    # +0.65). Pulled here, early, so it's available before player rates are built.
    # Costs 2 API requests (spreads+totals); the full player-prop pull later
    # re-fetches these anyway, which is a small, accepted duplication. Only runs under
    # --source oddsapi; the Sleeper path takes spread/total from the ESPN scoreboard,
    # which carries the same DK line for free.
    market_env = None
    if SNAP is not None:
        market_env = SNAP.get("market_env")
        SOURCES.append(("Market spread/total", "anchors each team's touchdown total to its implied points",
                        "ok" if market_env else "unavailable", "the same as the main run (scenario; no fetch)"))
    if SNAP is None and not a.no_odds and a.source == "oddsapi":
        home_name0, away_name0 = TEAM_NAMES.get(HOME), TEAM_NAMES.get(AWAY)
        try:
            ev0 = run_odds("events", ["--home", home_name0, "--away", away_name0,
                                      "--key-file", str(RES / "credential.env")])
            evs0 = ev0.get("events", [])
            if len(evs0) == 1:
                od0 = run_odds("odds", [evs0[0]["id"], "--key-file", str(RES / "credential.env"),
                                        "--markets", "spreads,totals", "--books", "draftkings"])
                dk0 = od0.get("markets", {}).get("draftkings", {})
                if "spreads" in dk0 and "totals" in dk0:
                    if od0.get("reused_cache"):
                        cache0 = [HERE / "cache" / od0["reused_cache"]]
                    else:
                        cache0 = [f for f in sorted((HERE / "cache").glob(f"odds_{evs0[0]['id']}_*.json"))
                                  if json.load(open(f)).get("class") == "OK"]
                    data0 = json.load(open(cache0[-1]))["data"]
                    dkb = next(b for b in data0["bookmakers"] if b["key"] == "draftkings")
                    sp0 = next(m for m in dkb["markets"] if m["key"] == "spreads")
                    tot0 = next(m for m in dkb["markets"] if m["key"] == "totals")
                    home_spread = next(o["point"] for o in sp0["outcomes"] if o["name"] == home_name0)
                    total_line = tot0["outcomes"][0]["point"]
                    market_env = {"home_spread": home_spread, "total_line": total_line,   # TD anchor always; plays/pass-rate only with --env market
                                  "book": "DraftKings (The Odds API)", "as_of": now()}
                    SOURCES.append(("Market spread/total (DK)", "anchors each team's touchdown total to its implied points",
                                    "ok", f"{HOME} {home_spread:+g}, total {total_line}"))
        except Exception as ex:
            log(f"  market environment pull failed ({type(ex).__name__}); falling back to history-only team environment")
    if SNAP is None and market_env is None and not a.no_odds:
        # ESPN scoreboard fallback (allowlisted, no key, no quota). Carries the DraftKings
        # spread/total that ESPN displays; used only for the TD anchor, never for props.
        try:
            import urllib.request as _ur
            # Ask for THIS game's week: the bare scoreboard shows the current week, which stays on
            # the previous week until ESPN rolls over (Tuesday morning it still shows last week),
            # so every game of an early-week run found no odds and fell back to anytime_td_v0.
            sb = cached_json(wd / f"espn_scoreboard_{SEASON}_wk{WEEK:02d}.json", a.sleeper_cache_ttl,
                             lambda: json.load(_ur.urlopen(_ur.Request(espn_scoreboard_url(SEASON, WEEK),
                headers={"User-Agent": "curl/8.5.0"}), timeout=20)))
            # ESPN codes differ from nflverse for two teams (WSH, LAR); an unmapped
            # comparison silently returns no spread/total for those games.
            _home_e, _away_e = ESPN_TEAM.get(HOME, HOME), ESPN_TEAM.get(AWAY, AWAY)
            for e_ in sb.get("events", []):
                c_ = e_["competitions"][0]
                abbr = {x["homeAway"]: x["team"]["abbreviation"] for x in c_["competitors"]}
                if abbr.get("home") == _home_e and abbr.get("away") == _away_e and c_.get("odds"):
                    o_ = c_["odds"][0]
                    _sbp = wd / f"espn_scoreboard_{SEASON}_wk{WEEK:02d}.json"
                    market_env = {"home_spread": float(o_["spread"]), "total_line": float(o_["overUnder"]),
                                  "book": f"{o_.get('provider', {}).get('name', 'book')} (ESPN scoreboard)",
                                  # the scoreboard may be a cached copy: its own fetch time, not now
                                  "as_of": (datetime.fromtimestamp(_sbp.stat().st_mtime, timezone.utc)
                                            .strftime("%Y-%m-%dT%H:%M:%SZ") if _sbp.exists() else now())}
                    SOURCES.append(("Market spread/total (ESPN scoreboard, %s)" % o_.get("provider", {}).get("name", "book"),
                                    "anchors each team's touchdown total to its implied points" + (" (fallback)" if a.source == "oddsapi" else ""),
                                    "ok", f"{HOME} {market_env['home_spread']:+g}, total {market_env['total_line']}"))
                    log(f"  spread/total from ESPN fallback: {HOME} {market_env['home_spread']:+g}, total {market_env['total_line']}")
                    break
        except Exception as ex:
            log(f"  ESPN spread/total fallback failed ({type(ex).__name__})")
    if market_env is None:
        SOURCES.append(("Market spread/total (DK)", "anchors each team's touchdown total to its implied points",
                        "unavailable", "team TD totals fall back to the history blend; TD calls capped at MODERATE"))

    # ---------- 2. current-season evidence ----------
    cur = season_inputs(SEASON, wd)
    pbp = pd.read_csv(fetch(*cur["pbp"]), low_memory=False)
    pbp = pbp[(pbp.season_type == "REG") & (pbp.week < WEEK)]
    ros = pd.read_csv(fetch(*cur["rosters"]), low_memory=False)
    inj = pd.read_csv(fetch(*cur["injuries"]), low_memory=False)
    dcf = pd.read_csv(fetch(*cur["depth_charts"]), low_memory=False)
    snp = pd.read_csv(fetch(*cur["snaps"]))
    snp = MODEL.snap_names_from_roster(snp, ros)      # joined by ID first, the name only as a fallback

    passes = pbp[(pbp.play_type == "pass") & pbp.receiver_player_id.notna()]
    rushes = pbp[(pbp.play_type == "run") & (pbp.qb_kneel != 1) & pbp.rusher_player_id.notna()]
    n_weeks = pbp.week.nunique()
    SOURCES.append((f"Play-by-play {SEASON}", "this season's targets, carries, yards, TDs",
                    "ok" if n_weeks else "empty", f"weeks 1-{WEEK-1} present: {n_weeks}"))
    _rw = ros[(ros.season == SEASON) & (ros.week == WEEK)]
    SOURCES.append((f"Weekly roster {SEASON}", "who is on the active roster (ACT/INA)",
                    "ok" if len(_rw) else "week not posted yet", f"week {WEEK}: {len(_rw)} rows"))
    _iw = inj[(inj.season == SEASON) & (inj.week == WEEK)]
    SOURCES.append((f"Injury report {SEASON}", "Out / Doubtful / Questionable",
                    "ok" if len(_iw) else "week not posted yet",
                    f"week {WEEK}: {int((_iw.team.isin([AWAY,HOME])).sum())} entries for these teams"))
    _dcd = pd.to_datetime(dcf["dt"], errors="coerce", utc=True)
    SOURCES.append((f"Depth charts {SEASON}", "who is WR1/WR2/RB1 etc.", "ok" if len(dcf) else "empty",
                    f"latest snapshot {str(_dcd.max())[:10]}" if len(dcf) else ""))
    _sn = snp[(snp.season == SEASON) & (snp.week < WEEK)]
    SOURCES.append((f"Snap counts {SEASON}", "how much each player is on the field",
                    "ok" if len(_sn) else "empty", f"weeks 1-{WEEK-1}, {_sn.team.nunique()} teams" if len(_sn) else ""))
    tw = pd.DataFrame({
        "targets": passes.groupby(["posteam", "week"]).size(),
        "carries": rushes.groupby(["posteam", "week"]).size(),
        "i10_targets": passes[passes.yardline_100 <= 10].groupby(["posteam", "week"]).size(),
        "i10_carries": rushes[rushes.yardline_100 <= 10].groupby(["posteam", "week"]).size(),
        "pass_td": passes.groupby(["posteam", "week"])["pass_touchdown"].sum(),
        "rush_td": rushes.groupby(["posteam", "week"])["rush_touchdown"].sum(),
    }).fillna(0).reset_index().rename(columns={"posteam": "team"})
    cur_team = tw.groupby("team")[["targets", "carries", "i10_targets", "i10_carries",
                                   "pass_td", "rush_td"]].mean()
    cur_n = tw.groupby("team").size()

    # League drift correction (round 9). The per-team expanding mean above is the
    # low-variance estimate of a team's volume, but it lags league-wide within-season
    # drift: total targets/game rose 3.4% inside 2024 and fell 4.2% inside 2025, leaving
    # projections ~4% low in one season and ~2% high in the other. Scale by a single
    # league-wide recent/expanding ratio, estimated across all 32 teams so it adds
    # almost no noise. Backtested on both seasons: bias 1.045->1.026 (2024) and
    # 0.976->0.995 (2025), with receptions CRPS improving on 2024 (+0.004, CI excludes
    # zero) and unchanged on 2025. A per-team trailing window fixed the same bias but
    # cost CRPS; this does not. Insensitive to the window length (2-5 give the same
    # answer), so it is not a tuned parameter.
    _drift = MODEL.league_drift_ratio(
        tw.rename(columns={"targets": "team_targets", "carries": "team_carries"}),
        WEEK, recent_games=3)
    # Applied AFTER the prior-season blend in section 4, not here: applying it to
    # cur_team alone left it diluted by the blend weight (50% strength at week 5), so
    # the deployed correction was weaker than the backtested one (round-9 review #1).
    _drift_on = (_drift["targets"] != 1.0 or _drift["carries"] != 1.0)
    SOURCES.append(("League volume drift correction", "keeps projections level with recent league-wide passing volume",
                    "ok",
                    f"targets x{_drift['targets']:.3f}, carries x{_drift['carries']:.3f}"
                    if _drift_on else "no adjustment yet (needs 4+ weeks of the season)"))

    prec = passes.groupby(["posteam", "receiver_player_id"]).agg(
        targets=("play_id", "size"), receptions=("complete_pass", "sum"),
        rec_yards=("receiving_yards", "sum")).reset_index().rename(
        columns={"receiver_player_id": "gsis_id", "posteam": "team"})
    prec_i10 = passes[passes.yardline_100 <= 10].groupby(
        ["posteam", "receiver_player_id"]).size().rename("i10_targets").reset_index().rename(
        columns={"receiver_player_id": "gsis_id", "posteam": "team"})
    prush = rushes.groupby(["posteam", "rusher_player_id"]).agg(
        carries=("play_id", "size"), rush_yards=("rushing_yards", "sum")).reset_index().rename(
        columns={"rusher_player_id": "gsis_id", "posteam": "team"})
    prush_i10 = rushes[rushes.yardline_100 <= 10].groupby(
        ["posteam", "rusher_player_id"]).size().rename("i10_carries").reset_index().rename(
        columns={"rusher_player_id": "gsis_id", "posteam": "team"})
    cur = (prec.merge(prec_i10, how="outer", on=["team", "gsis_id"])
              .merge(prush, how="outer", on=["team", "gsis_id"])
              .merge(prush_i10, how="outer", on=["team", "gsis_id"]).fillna(0)
              .set_index(["team", "gsis_id"]))

    # ---------- 3. eligible set: depth chart + share proxy, ACT/INA only ----------
    if pd.isna(G.gametime):
        sys.exit(f"KICKOFF TIME TBD in games.csv for {AWAY} at {HOME} week {WEEK}; cannot resolve "
                 f"the pre-game depth chart cutoff. Re-run once the time is published.")
    kick = eastern_to_utc(G.gameday, G.gametime)
    dcf["dt"] = pd.to_datetime(dcf["dt"], errors="coerce", utc=True)
    roles = []
    DC_QB = {}           # team -> its QBs in depth-chart order (the QB promotion reads it)
    for t in (AWAY, HOME):
        d = dcf[(dcf.team == t) & (dcf.dt < kick) & dcf.pos_abb.isin(["QB", "RB", "WR", "TE"])]
        if d.empty:
            continue
        d = d[d.dt == d.dt.max()]
        DC_QB[t] = d[d.pos_abb == "QB"].sort_values("pos_rank").gsis_id.tolist()
        for pos, mx in [("QB", 1), ("RB", 2), ("WR", 3), ("TE", 1)]:
            for _, r in d[(d.pos_abb == pos) & (d.pos_rank <= mx)].iterrows():
                roles.append({"team": t, "gsis_id": r.gsis_id, "slot": f"{pos}{int(r.pos_rank)}",
                              "dc_dt": d.dt.max()})
    roles = pd.DataFrame(roles).drop_duplicates(["team", "gsis_id"])

    rw, prov_wk = week_roster(ros, SEASON, WEEK)
    if prov_wk is not None:
        log(f"  WARNING: no week {WEEK} roster rows; using week {prov_wk} as provisional")

    for ro in ROLE_OVERRIDES:
        cand = rw[rw.team.isin([ro["team_of"]] if ro["team_of"] else [AWAY, HOME])]
        hit = cand[cand.full_name.map(norm_name) == norm_name(ro["who"])]
        if hit.empty:
            sys.exit(f"--role: {ro['who']} is not on {ro['team_of'] or 'either team'}'s roster this week")
        if len(hit) > 1:
            sys.exit(f"--role: {ro['who']} is on both rosters: write '{ro['who']} (TEAM)={ro['slot']}'")
        t_, pid_ = hit.team.iloc[0], hit.gsis_id.iloc[0]
        ro.update(name=hit.full_name.iloc[0], team=t_, gsis_id=pid_,
                  was=(roles[(roles.team == t_) & (roles.gsis_id == pid_)].slot.iloc[0]
                       if not roles.empty and ((roles.team == t_) & (roles.gsis_id == pid_)).any() else None))
        keep = roles[~((roles.team == t_) & (roles.gsis_id == pid_))] if not roles.empty else roles
        roles = pd.concat([keep, pd.DataFrame([{"team": t_, "gsis_id": pid_, "slot": ro["slot"],
                                                "dc_dt": pd.NaT}])], ignore_index=True)

    iw = inj[(inj.season == SEASON) & (inj.week == WEEK)]
    inj_practice = iw.set_index(["team", "gsis_id"])["practice_status"].to_dict()
    # Sleeper's feed fills in where the official report has no entry yet (#183)
    import urllib.request as _ur0
    try:
        SLP_PLAYERS = cached_json(wd / "sleeper_players.json", 86400, lambda: json.load(_ur0.urlopen(
            _ur0.Request("https://api.sleeper.app/v1/players/nfl", headers={"User-Agent": "Mozilla/5.0"}),
            timeout=120)))
    except Exception as exc:           # no feed: the official report alone, said in the sources
        SLP_PLAYERS = None
        log(f"  Sleeper player feed unavailable ({exc}); injuries from the official report only")
    inj_status, INJ_SOURCE = injuries_with_fallback(
        iw.set_index(["team", "gsis_id"])["report_status"].to_dict(), rw,
        sleeper_injury_map(SLP_PLAYERS, SLEEPER_TEAM), practice=inj_practice, reported_teams=set(iw.team))
    # THE NEXT QB STARTS when the depth chart's QB1 is out (#183) -- Sleeper's depth order
    # first (fresher), then the depth chart's; a --role for that team's QB wins
    _rw_st = {(t_, g_): st_ for t_, g_, st_ in zip(rw.team, rw.gsis_id, rw.status)}
    _slp_qb = {}
    for v_ in (SLP_PLAYERS or {}).values():
        if v_.get("position") == "QB" and v_.get("gsis_id") and v_.get("depth_chart_order"):
            _slp_qb[str(v_["gsis_id"]).strip()] = int(v_["depth_chart_order"])
    AUTO_QB = []
    for t in (AWAY, HOME):
        if any(ro["team"] == t and ro["slot"] == "QB1" for ro in ROLE_OVERRIDES):
            continue
        qbs = [g_ for (tt_, g_) in _rw_st if tt_ == t and g_ in set(rw[rw.position == "QB"].gsis_id)]
        order = sorted(qbs, key=lambda g_: (_slp_qb.get(g_, 99),
                                            DC_QB.get(t, []).index(g_) if g_ in DC_QB.get(t, []) else 99))
        q1_before = roles[(roles.team == t) & (roles.slot == "QB1")].gsis_id.tolist() if not roles.empty else []
        roles, got = promote_qb(
            roles, t, order,
            is_out=lambda g_, t=t: (inj_status.get((t, g_)) in ("Out", "Doubtful") or g_ in ASSUME_OUT
                                    or _rw_st.get((t, g_)) in NOT_PLAYING),
            on_roster=lambda g_, t=t: _rw_st.get((t, g_)) == "ACT")
        if got:
            nm_ = lambda g_: rw[rw.gsis_id == g_].full_name.iloc[0] if (rw.gsis_id == g_).any() else g_
            AUTO_QB.append({"team": t, "starter": nm_(got), "out": nm_(q1_before[0]) if q1_before else "QB1",
                            "why": ("assumed out in this scenario" if q1_before and q1_before[0] in ASSUME_OUT else
                                    INJ_SOURCE.get((t, q1_before[0]), inj_status.get((t, q1_before[0])) or ""))})

    snp_ = snp[(snp.season == SEASON) & (snp.week < WEEK)].copy()
    snp_["key"] = snp_["player"].map(norm_name)
    snap_cur = snp_.groupby(["team", "key"])["offense_pct"].mean().rename("snap_pct")

    pop = []
    for t in (AWAY, HOME):
        elig = set(roles[roles.team == t].gsis_id) if not roles.empty else set()
        if t in cur_team.index:
            for (tt, pid), row in cur.iterrows():
                if tt != t:
                    continue
                ts = row.targets / max(cur_team.loc[t, "targets"] * cur_n[t], 1)
                rs_ = row.carries / max(cur_team.loc[t, "carries"] * cur_n[t], 1)
                if ts >= 0.10 or rs_ >= 0.20:
                    elig.add(pid)
        for pid in sorted(elig):
            r = rw[(rw.team == t) & (rw.gsis_id == pid)]
            if r.empty or not keep_in_pool(r.status.iloc[0], (t, pid) in cur.index):
                continue      # off the roster, practice squad / cut / traded, or out since before the season
            # ON THE ROSTER BUT NOT PLAYING (reserve/IR, PUP, suspended, practice squad):
            # kept, and excluded below like an Out player, so his share is handed to his
            # teammates by the out rule and the board says he is out. Dropping him here
            # (the pre-2026-10-05 behaviour) left his carries with nobody (Travis Etienne,
            # NO week 4).
            pop.append({"team": t, "gsis_id": pid, "name": r.full_name.iloc[0],
                        "pos": r.position.iloc[0], "status": r.status.iloc[0]})
    pop = pd.DataFrame(pop)
    if roles.empty:
        pop["slot"] = "PROXY"
    else:
        pop = pop.merge(roles[["team", "gsis_id", "slot"]], on=["team", "gsis_id"], how="left")
        pop["slot"] = pop["slot"].fillna("PROXY")
    # Text columns, stored as objects: a game where nobody carries a designation
    # gives an all-NaN list, which pandas types float64, and pandas 3 (what the
    # chat container runs) refuses the "Out (scenario)" string written below.
    pop["report_status"] = pd.Series([inj_status.get((t, p)) for t, p in zip(pop.team, pop.gsis_id)],
                                     index=pop.index, dtype=object)
    pop["practice_status"] = pd.Series([inj_practice.get((t, p)) for t, p in zip(pop.team, pop.gsis_id)],
                                       index=pop.index, dtype=object)
    pop = apply_designations(pop, ASSUME_OUT)
    for ro in ROLE_OVERRIDES:
        hit = pop[(pop.team == ro["team"]) & (pop.gsis_id == ro["gsis_id"])]
        if hit.empty:
            sys.exit(f"--role: {ro['name']} is on the roster but not available to play "
                     f"({rw[(rw.team == ro['team']) & (rw.gsis_id == ro['gsis_id'])].status.iloc[0]})")
        if bool(hit.excluded.iloc[0]):
            sys.exit(f"--role: {ro['name']} is ruled out ({hit.report_status.iloc[0] or hit.status.iloc[0]}), "
                     "so there is nothing to price")
    n_excl = int(pop.excluded.sum())
    active = pop[~pop.excluded].copy()

    # ---------- 4. team environment ----------
    env = {}
    for t in (AWAY, HOME):
        env[t] = {}
        for c in ["targets", "carries", "i10_targets", "i10_carries", "pass_td", "rush_td"]:
            own = cur_team.loc[t, c] if t in cur_team.index else np.nan
            n = cur_n.get(t, 0)
            env[t][c] = blend(own, n, pri_teams.loc[t, c] if t in pri_teams.index else np.nan, K0)
        # League drift correction, applied to the BLENDED environment so the deployed
        # strength matches the backtest (review #1). Pass volume and its downstream
        # quantities (goal-line targets, passing TDs) scale with the targets ratio; rush
        # volume and its downstream with the carries ratio (review #3).
        for c, key in [("targets", "targets"), ("i10_targets", "targets"), ("pass_td", "targets"),
                       ("carries", "carries"), ("i10_carries", "carries"), ("rush_td", "carries")]:
            if pd.notna(env[t][c]):
                env[t][c] = env[t][c] * _drift[key]
        env[t]["td_total_history"] = env[t]["pass_td"] + env[t]["rush_td"]
        env[t]["td_anchor"] = "history"
        env[t]["source"] = ("history (no spread/total this run: the market pass volume could not be applied)"
                            if market_env is None and MODEL.MARKET_PASS_WEIGHT else "history")
        if market_env is not None:
            hs, tl = market_env["home_spread"], market_env["total_line"]
            implied_pts = (tl - hs) / 2 if t == HOME else (tl + hs) / 2
            # TOUCHDOWN ANCHOR (on by default). One blowout can swing a history-blended team
            # TD total by a full touchdown at 20% week weight (CHI: 2.76 avg, 8 TDs in week 1,
            # blend 3.8 vs market-implied 2.74), and that one number drives every player's
            # anytime-TD probability. The spread/total cannot be swung by one game. Keep the
            # history blend's pass/rush split; rescale the total to implied points x league
            # TD-per-point. Plays and pass rate stay on the history blend unless --env market
            # (that re-centre showed no accuracy gain in backtesting and is off by default).
            total_td_mkt = implied_pts * P.get("league_td_per_point", 0.1055)
            hist_total = env[t]["td_total_history"]
            if hist_total > 0:
                env[t]["pass_td"] = total_td_mkt * env[t]["pass_td"] / hist_total
                env[t]["rush_td"] = total_td_mkt * env[t]["rush_td"] / hist_total
            env[t]["td_total_market"] = total_td_mkt
            env[t]["implied_points"] = implied_pts
            env[t]["td_anchor"] = "market"
            if a.env != "market" and MODEL.MARKET_PASS_WEIGHT and P.get("market_env_fit"):
                # round 16: the market's fitted pass volume at MODEL.MARKET_PASS_WEIGHT;
                # carries keep the team's history (DECISIONS #134)
                env[t]["targets"], env[t]["carries"] = MODEL.market_pass_volume(
                    MODEL.team_spread_from_home(hs, t == HOME), tl, P["market_env_fit"],
                    env[t]["targets"], env[t]["carries"], MODEL.MARKET_PASS_WEIGHT)
                env[t]["source"] = f"history + market pass volume ({MODEL.MARKET_PASS_WEIGHT:g})"
            if a.env != "market" and MODEL.MARKET_RUSH_WEIGHT and P.get("market_env_fit"):
                # round 29: the backs' carries move toward the market's fitted carries;
                # the starting QB's are held (hold_qb_carries, below)
                env[t]["carries_history"] = env[t]["carries"]     # the reversal-check shadow (#204)
                env[t]["carries"], env[t]["carry_factor"] = MODEL.market_rush_volume(
                    MODEL.team_spread_from_home(hs, t == HOME), tl, P["market_env_fit"],
                    env[t]["carries"], MODEL.MARKET_RUSH_WEIGHT)
            if a.env == "market":
                hist_targets, hist_carries = env[t]["targets"], env[t]["carries"]
                team_pr = hist_targets / max(hist_targets + hist_carries, 1e-6)
                hp, ap_ = (team_pr, LEAGUE_PASS_RATE) if t == HOME else (LEAGUE_PASS_RATE, team_pr)
                mkt = MODEL.market_implied_environment(hs, tl, hp, ap_, hist_targets + hist_carries)
                side = mkt["home"] if t == HOME else mkt["away"]
                env[t]["targets"] = side["plays"] * side["pass_rate"]
                env[t]["carries"] = side["plays"] * (1 - side["pass_rate"])
                env[t]["source"] = "market"

    # ---------- 4c. anytime_td_v1 ----------
    # The anytime-touchdown model, from the SAME module the backtest scores
    # (td_v1), so the number validated is the number priced. It needs the
    # market's implied points for both teams; without them, or if its inputs
    # fail, every anytime price falls back to anytime_td_v0 and the sources
    # table says so -- a missing v1 is visible, never silent.
    V1TD = None
    if all(env[t].get("implied_points") is not None for t in (HOME, AWAY)):
        try:
            _cur = TDV1.current_inputs(pbp, ros, snp, dcf, games, inj, SEASON, WEEK)
            if ASSUME_OUT:
                _cur["actives"] = _cur["actives"][~_cur["actives"]["player_id"].isin(ASSUME_OUT)]
            V1TD = TDV1.anytime_probabilities(TDV1.load_bundled(RES, PRIOR), _cur,
                                              {t: env[t]["implied_points"] for t in (HOME, AWAY)})
            SOURCES.append(("Anytime TD model", "who scores, and how likely", "ok",
                            f"{TDV1.LABEL} (PROTOTYPE): {len(V1TD)} active players priced"))
        except Exception as exc:  # noqa: BLE001 -- a failed v1 must not cost the slate
            V1TD = None
            SOURCES.append(("Anytime TD model", "who scores, and how likely", "FAILED",
                            f"{TDV1.LABEL} unavailable ({type(exc).__name__}: {exc}); "
                            "anytime prices fall back to anytime_td_v0, which runs ~1.3 points low"))
    else:
        SOURCES.append(("Anytime TD model", "who scores, and how likely", "unavailable",
                        f"{TDV1.LABEL} needs the market's implied points; anytime_td_v0 used "
                        "(runs ~1.3 points low)"))

    # ---------- 4b. opponent efficiency table (round 5) ----------
    # Backtest finding: at usable shrinkage (k0=50-150 plays) this made
    # reception-yards CRPS WORSE than not adjusting at all; only stops hurting
    # once shrunk to near-no-op. Built and applied at that near-no-op default
    # (model.opponent_multiplier's k0_opp=1000) so the data path exists without
    # currently changing projections much. See model_registry.md, receiving_hier_v2.
    # Uses the full-league roster (not just this game's two teams) for position
    # classification -- the per-game `roles` frame only covers 14 players, which
    # would leave nearly every opposing-defense play unclassified.
    league_roles = ros[["gsis_id", "position"]].dropna().drop_duplicates("gsis_id").rename(
        columns={"position": "slot"})
    opp_table = MODEL.build_opponent_table(pbp, league_roles) if len(pbp) else pd.DataFrame(
        columns=["team", "posgrp", "metric", "n", "value", "league"])

    # ---------- 5. player rates, with snap-share role prior (A1) ----------
    def slot_val(slot, col, default):
        if slot in pri_slots.index and pd.notna(pri_slots.loc[slot, col]):
            return float(pri_slots.loc[slot, col])
        return float(pri_slots[col].mean()) if col in pri_slots else default

    # Usage by week (research columns, props-v1.29) -- built BEFORE the share
    # blend because round 23 (model.SNAP_REACT) moves target share by last
    # week's snap change: LAST = the latest week before this one, BASE = his
    # earlier weeks with this team (research.usage_change).
    _snp_w = snp_.groupby(["team", "key", "week"])["offense_pct"].mean()
    _tg_w = passes.groupby(["posteam", "receiver_player_id", "week"]).size()
    _ca_w = rushes.groupby(["posteam", "rusher_player_id", "week"]).size()
    _tw_i = tw.set_index(["team", "week"])
    USAGE, ROLE, BACKFIELD, CARRY_U = {}, {}, {}, {}
    WEEK_SH = {}         # name -> this season's games he played: (week, snap, target share, carry share, ...)
    # a back's three jobs by week (research columns): early-down carries,
    # passing-down targets (3rd/4th down or the last two minutes of a half),
    # inside-5 carries. Display only: nothing here moves a price.
    _rush_job = rushes[["posteam", "week", "down", "yardline_100", "rusher_player_id"]]
    _pass_job = passes[["posteam", "week", "down", "half_seconds_remaining", "receiver_player_id"]]
    for _, m_ in active.iterrows():
        key_ = norm_name(m_["name"])
        wks = []
        for (t_, k_, w_), sv in _snp_w.items():
            if t_ == m_.team and k_ == key_ and sv > 0 and (m_.team, w_) in _tw_i.index:
                tt_ = float(_tw_i.loc[(m_.team, w_), "targets"]); tc_ = float(_tw_i.loc[(m_.team, w_), "carries"])
                n_t, n_c = float(_tg_w.get((m_.team, m_.gsis_id, w_), 0)), float(_ca_w.get((m_.team, m_.gsis_id, w_), 0))
                wks.append((int(w_), float(sv), n_t / tt_ if tt_ else np.nan, n_c / tc_ if tc_ else np.nan,
                            n_t, n_c))
        WEEK_SH[m_["name"]] = sorted(wks)
        USAGE[m_["name"]] = RSCH.usage_change(sorted(wks))
        CARRY_U[m_["name"]] = RSCH.carry_change(sorted(wks))     # the takeover flag's own definition
        ROLE[m_["name"]] = RSCH.role_flag(USAGE[m_["name"]], WEEK - 1)
        if str(m_.get("pos")) in ("RB", "FB", "HB"):
            bwk = []
            for w_ in sorted(w[0] for w in wks):
                r_t = _rush_job[(_rush_job.posteam == m_.team) & (_rush_job.week == w_)]
                p_t = _pass_job[(_pass_job.posteam == m_.team) & (_pass_job.week == w_)]
                e_t = r_t[r_t.down.isin([1, 2])]
                d_t = p_t[p_t.down.isin([3, 4]) | (p_t.half_seconds_remaining <= 120)]
                g_t = r_t[r_t.yardline_100 <= 5]
                bwk.append((w_,
                            float((e_t.rusher_player_id == m_.gsis_id).sum()) / len(e_t) if len(e_t) else np.nan,
                            float((d_t.receiver_player_id == m_.gsis_id).sum()) / len(d_t) if len(d_t) else np.nan,
                            float((g_t.rusher_player_id == m_.gsis_id).sum()) / len(g_t) if len(g_t) else np.nan,
                            int((g_t.rusher_player_id == m_.gsis_id).sum()), len(g_t)))
            BACKFIELD[m_["name"]] = RSCH.backfield_jobs(bwk)

    recs = []
    for _, p in active.iterrows():
        t, pid, slot = p.team, p.gsis_id, p.slot
        pri = pri_players.loc[pid] if pid in pri_players.index else None
        n25 = float(pri.n_games) if pri is not None else 0.0
        prior_team = pri.team_prior if pri is not None and pd.notna(pri.team_prior) else None
        new_team = prior_team is not None and prior_team != t

        # A1: snap share as the role signal for new-team / no-history players
        snap_now = snap_cur.get((t, norm_name(p["name"])), np.nan)
        snap_prior = pri.snap_pct_25 if (pri is not None and "snap_pct_25" in pri
                                         and pd.notna(pri.snap_pct_25)) else np.nan
        role_scale = 1.0
        if new_team and pd.notna(snap_now) and pd.notna(snap_prior) and snap_prior > 0.05:
            role_scale = float(np.clip(snap_now / snap_prior, 0.3, 2.0))

        cw = cur.loc[(t, pid)] if (t, pid) in cur.index else None
        # A player who was ACT but recorded no targets and no carries has no PBP row. He
        # still played those games: his observed share is 0, not "unknown". Count weeks he
        # was ACT for this team as current-season evidence, and give him a zero row.
        weeks_act = ros[(ros.season == SEASON) & (ros.week < WEEK) & (ros.team == t)
                        & (ros.gsis_id == pid) & (ros.status == "ACT")].week.nunique()
        n_cur = int(weeks_act)
        if cw is None and n_cur > 0:
            cw = pd.Series({"targets": 0.0, "receptions": 0.0, "rec_yards": 0.0,
                            "carries": 0.0, "rush_yards": 0.0,
                            "i10_targets": 0.0, "i10_carries": 0.0})
        tt_cur = env[t]["targets"] * max(n_weeks, 1)
        tc_cur = env[t]["carries"] * max(n_weeks, 1)
        # Denominators are the team's ACTUAL totals in the weeks this player was ACT,
        # not projected volume x weeks. Using the projection made a 14-of-39 week look
        # like 14-of-34 for a team that ran hot, inflating every share on that side.
        act_weeks = ros[(ros.season == SEASON) & (ros.week < WEEK) & (ros.team == t)
                        & (ros.gsis_id == pid) & (ros.status == "ACT")].week.unique()
        tw_p = tw[(tw.team == t) & tw.week.isin(act_weeks)]
        if len(tw_p):
            tt_cur = float(tw_p.targets.sum()); tc_cur = float(tw_p.carries.sum())
        ti10t_cur = float(tw_p.i10_targets.sum()) if len(tw_p) else 0.0
        ti10c_cur = float(tw_p.i10_carries.sum()) if len(tw_p) else 0.0

        # opponent for this player's team, used for the efficiency (not share) adjustment
        opp_team = HOME if t == AWAY else AWAY
        posgrp = re.match(r"[A-Z]+", str(p.pos or slot)).group(0) if re.match(r"[A-Z]+", str(p.pos or slot)) else "OTHER"

        ev_chain = {}
        PRIOR_N_COL = {"target_share": "team_targets_n", "i10_target_share": "i10_targets_n",
                       "catch_rate": "targets_n", "ypt": "targets_n",
                       "rush_share": "team_carries_n", "i10_carry_share": "i10_carries_n", "ypc": "carries_n"}
        def rate(cur_num, cur_den, pri_col, slot_col, default, opp_metric=None):
            rate_k0 = K0R.get(slot_col, K0)
            sp = slot_val(slot, slot_col, default)
            own_pri = float(pri[pri_col]) if (pri is not None and pd.notna(pri[pri_col])) else np.nan
            # n in OPPORTUNITY units (team targets for shares, own targets for catch rate / ypt,
            # carries for ypc), matching how K0 was tuned in build_priors.py
            ncol = PRIOR_N_COL.get(slot_col)
            n_pri_opp = float(pri[ncol]) if (pri is not None and ncol in pri and pd.notna(pri[ncol])) else n25 * 30.0
            # THE BLEND ITSELF LIVES IN model.py so the backtest runs the same
            # one. Everything above this line is gathering inputs; everything
            # the blend does is now shared.
            #
            # opponent multiplier: team-level, fixed shrinkage k0=150 plays.
            # After the YPT-reference bug was fixed this was the best of four
            # variants on 2025 (reception yards +0.061 CRPS, CI excludes zero;
            # receptions unchanged). The earlier "harmful" verdict was entirely
            # that bug. Between-defense YPT spread is ~8% SD.
            opp_mult = 1.0
            if opp_metric is not None and len(opp_table):
                opp_mult = MODEL.opponent_multiplier(opp_table, opp_team, "ALL", opp_metric,
                                                     k0_opp=150.0, mode="fixed")
            final, chain = MODEL.blended_rate(
                own_pri, n_pri_opp, sp, rate_k0,
                cur_num=cur_num, cur_den=cur_den,
                role_scale=role_scale,
                scale_role=slot_col in ("target_share", "rush_share"),
                new_team=new_team, opp_mult=opp_mult,
                clip=(0.05, 1.0) if slot_col == "catch_rate" else None)
            chain["n_prior"] = n25
            chain["n_cur"] = n_cur
            ev_chain[pri_col] = chain
            return final

        ts = rate(cw.targets if cw is not None else None, tt_cur if cw is not None else None,
                  "target_share", "target_share", 0.05)
        # round 23: last week's snap change moves the target share (off when SNAP_REACT is None)
        u_sr = USAGE.get(p["name"])
        if MODEL.SNAP_REACT is not None and u_sr and u_sr["week"] == WEEK - 1:
            ts_before = ts
            ts = MODEL.snap_react(ts, u_sr["snap"], u_sr["snap_base"], MODEL.SNAP_REACT,
                                  gamma_up=MODEL.SNAP_REACT_UP)
            ev_chain["target_share"]["snap_react"] = (ts / ts_before) if ts_before else None
        cr = rate(cw.receptions if (cw is not None and cw.targets > 0) else None,
                  cw.targets if (cw is not None and cw.targets > 0) else None,
                  "catch_rate", "catch_rate", 0.62, opp_metric="catch_rate")
        ypt = rate(cw.rec_yards if (cw is not None and cw.targets > 0) else None,
                   cw.targets if (cw is not None and cw.targets > 0) else None,
                   "ypt", "ypt", 7.0, opp_metric="ypt")
        rs_ = rate(cw.carries if cw is not None else None, tc_cur if cw is not None else None,
                   "rush_share", "rush_share", 0.03)
        ypc = rate(cw.rush_yards if (cw is not None and cw.carries > 0) else None,
                   cw.carries if (cw is not None and cw.carries > 0) else None,
                   "ypc", "ypc", P["league_mean_ypc"], opp_metric="ypc")
        i10ts = rate(cw.i10_targets if cw is not None else None,
                     ti10t_cur if cw is not None else None,
                     "i10_target_share", "i10_target_share", np.nan)
        i10rs = rate(cw.i10_carries if cw is not None else None,
                     ti10c_cur if cw is not None else None,
                     "i10_carry_share", "i10_carry_share", np.nan)

        # A Questionable player is priced at his NORMAL share, as if he plays. The
        # other case -- he is out and his share goes to his teammates -- is a
        # separate full pricing (run_scenarios). The user sees both and decides;
        # there is no blended discount.
        i10ts_mix = i10ts if pd.notna(i10ts) else ts
        i10rs_mix = i10rs if pd.notna(i10rs) else rs_

        recs.append(dict(team=t, gsis_id=pid, name=p["name"], pos=p.pos, slot=slot,
                         status=p.status, questionable=p.questionable, new_team=new_team,
                         prior_team=prior_team, n_prior_games=n25, snap_pct=snap_now,
                         snap_prior=snap_prior, role_scale=role_scale, evidence=ev_chain,
                         ts=ts, cr=cr, ypt=ypt, rs=rs_, ypc=ypc,
                         i10ts=i10ts_mix, i10rs=i10rs_mix))
    M = pd.DataFrame(recs)
    if MODEL.SNAP_REACT is not None:
        _sr_moved = sum(1 for ev in M.evidence
                        if abs((ev.get("target_share", {}).get("snap_react") or 1.0) - 1.0) > 0.005)
        _sr_ready = sum(1 for u in USAGE.values() if u and u["week"] == WEEK - 1)
        _sr_last = max((u["week"] for u in USAGE.values() if u), default=None)
        SOURCES.append(("Snap-change rule (round 23)", "target share moved by last week's snap share",
                        "ok" if _sr_ready else "no player has last week's snaps yet",
                        f"{_sr_moved} of {_sr_ready} players with week {WEEK - 1} snaps moved; "
                        f"latest snap week in the file: {_sr_last}"))
    miss = M[M.snap_pct.isna()]
    if len(miss):
        log(f"  snap-share join missed {len(miss)}/{len(M)} players (role_scale=1 for them): "
            + ", ".join(miss.name.head(8)))

    # A2: where an excluded player's share goes (reports/absence_tune.md). It does NOT
    # go pro rata to the priced teammates, as this path assumed until props-v1.8: when
    # a 15%+ target player sits, the players who had under 5% of targets go from 0.112
    # to 0.267 -- the call-up or promoted backup takes most of it. A fraction y of his share stays with the priced set; of that, x goes to
    # every priced teammate pro rata and 1 - x to priced teammates at HIS position.
    # Tuned 2022-23, scored as-is on 2024-25 absence games. Do NOT renormalise the
    # eligible set to sum to 1: it never covers a team's whole volume.
    excl_rates = []
    for _, p in pop[pop.excluded].iterrows():
        pri = pri_players.loc[p.gsis_id] if p.gsis_id in pri_players.index else None
        sl = p.slot
        excl_rates.append({
            "team": p.team, "gsis_id": p.gsis_id, "pos": POS_GROUP.get(p.pos, p.pos),
            "ts": float(pri.target_share) if pri is not None and pd.notna(pri.target_share)
                  else slot_val(sl, "target_share", 0.0),
            "rs": float(pri.rush_share) if pri is not None and pd.notna(pri.rush_share)
                  else slot_val(sl, "rush_share", 0.0),
            "i10ts": float(pri.i10_target_share) if pri is not None and pd.notna(pri.i10_target_share)
                     else slot_val(sl, "i10_target_share", 0.0),
            "i10rs": float(pri.i10_carry_share) if pri is not None and pd.notna(pri.i10_carry_share)
                     else slot_val(sl, "i10_carry_share", 0.0)})
    E = pd.DataFrame(excl_rates)
    # ROUND 35 (DECISIONS #192): the carry handoff hands on the absent player's carry share
    # THIS season (games he played), and to each teammate only the fraction of the absence
    # not yet in his own share. A player who has not played this season keeps the shipped
    # share (the round had no evidence for that case). Targets keep the shipped rule.
    OUT_MULT = {"rs": {}}
    if len(E):
        _act = ros[(ros.season == SEASON) & (ros.week < WEEK) & (ros.status == "ACT")]
        for i_, e_ in E.iterrows():
            aw_ = {g_: set(w_) for g_, w_ in _act[_act.team == e_.team].groupby("gsis_id").week}
            mates_ = list(M[M.team == e_.team].gsis_id)
            sh_, fr_ = carry_handoff_inputs(rushes, passes, aw_, e_.team, e_.gsis_id, mates_)
            if sh_ is not None:
                E.loc[i_, "rs"] = sh_
                OUT_MULT["rs"][i_] = fr_
    M, redistributed = apply_out_rule(M, E, (AWAY, HOME), mult=OUT_MULT)
    # WIDTH SETTINGS (resources/width_params.json): game-to-game variation in
    # shares, catch rate and yards per touch, tuned on 2022-23 by backtest.py
    # --tune-width and judged on 2024-25 (reports/width_tuning.md,
    # reports/yardage_harness.md). No file = the pre-width sampler, draw for draw.
    _wf = RES / "width_params.json"
    WIDTH = MODEL.validate_width(json.loads(_wf.read_text(encoding="utf-8"))) if _wf.exists() else None
    # ROUND 41 (DECISIONS #200): tight ends' target share x te_share_mult on the projection
    # itself, so the projected targets, the 50/50 search and the card all carry it; the
    # simulation then runs without the multiplier (the harness applies it inside the draw:
    # the same shares, the depth bucket giving up what the tight end gains)
    TE_MULT = float((WIDTH or {}).get("te_share_mult") or 1.0)
    if TE_MULT != 1.0:
        _te = M.slot.map(MODEL.role_group) == "TE"
        M.loc[_te, "ts"] = M.loc[_te, "ts"] * TE_MULT
    WIDTH_SIM = {**WIDTH, "te_share_mult": None} if WIDTH else None
    for t in (AWAY, HOME):
        m = M.team == t
        # Shares are estimated per player with no joint constraint, so the eligible set's
        # total can exceed 1 (observed: DET inside-10 target share summed to 1.035). A team
        # cannot allocate more than 100% of its TDs or targets. Scale DOWN only when over;
        # never scale up (the eligible set legitimately never covers all of a team's volume).
        for col in ["ts", "rs", "i10ts", "i10rs"]:
            tot = M.loc[m, col].sum()
            if tot > 1.0:
                M.loc[m, col] = M.loc[m, col] / tot
    if RULES:
        try:
            RULES = SC.resolve_players(RULES, M.name, M.team, pop[pop.excluded].name)
            if a.scenario_run:       # YOUR scenario: team volume, efficiency and targets (carries below)
                M, env = SC.apply_before_sim(M, env, RULES)
        except ValueError as exc:
            sys.exit(f"--assume: {exc}")

    # ---------- 6. simulate: JOINT per-team draws (round 5, review item 6) ----------
    # One team-targets draw and one team-carries draw per simulation, shared by every
    # player on that team, then a multinomial split across the eligible set plus an
    # "other" bucket. Teammates are negatively correlated within a simulation (a fixed
    # total means more for A is less for B) and every player shares the team's own
    # play-count variance. Independent per-player draws had neither property, which
    # made same-game-parlay probabilities impossible to state.
    SH = P["shape_ypc_per_catch"]
    TVD = P.get("team_volume_dispersion", {"targets_r": 30.0, "carries_r": 30.0})
    QB_RESID = np.array(P["qb_carry_residual_quantiles"]) if "qb_carry_residual_quantiles" in P else None
    # QB rushing props are priced once the priors carry the QB carry grid and the
    # kneel-down grids (props-v1.21; reports/yardage_harness.md, DECISIONS #100):
    # the book settles them WITH kneel-downs, which the sampler now draws.
    QB_RUSH_ON = QB_RESID is not None
    STARTER_QB = {}      # team -> the QB treated as the starter (kneels, QB width)
    sims = {}
    sim_inputs = {}      # team -> the simulation's inputs, for the research columns (no draws)
    team_targets_draw, team_carries_draw = {}, {}
    SHADOW_RUSH = {}     # back -> (rushing yards draws, carries draws) WITHOUT market carries (#204)
    SHADOW_REC = {}      # receiver -> (catches draws, yards draws) at target spread 40 (#204)
    pass_inputs = {}     # team -> (every receiver's yards draws, the other bucket's targets)
    for t in (AWAY, HOME):
        Mt = M[M.team == t]
        names = list(Mt.name)
        shares_t = {n: float(v) for n, v in zip(Mt.name, Mt.ts)}
        crs_t = {n: float(v) for n, v in zip(Mt.name, Mt.cr)}
        ypt_t = {n: float(v) for n, v in zip(Mt.name, Mt.ypt)}
        out_rec, tt_draw, tg_draws = MODEL.simulate_team_game(
            team_stream(t, 101), N_SIM, env[t]["targets"], TVD["targets_r"], shares_t, crs_t, ypt_t, SH,
            other_bucket=True, width=WIDTH_SIM, return_other=True, return_targets=True,
            player_roles={n: MODEL.role_group(s_) for n, s_ in zip(Mt.name, Mt.slot)})
        pass_inputs[t] = ([out_rec[n][1] for n in names], out_rec.pop(MODEL.OTHER))
        # ROUND 34'S REVERSAL SHADOW (DECISIONS #204): receiving again at target spread 40 (the
        # setting before round 34), its own stream, logged as p_over_spread40 for the week-8 check
        if WIDTH_SIM and WIDTH_SIM.get("share_conc_targets") != 40.0 and not SCENARIO:
            _o40, _ = MODEL.simulate_team_game(team_stream(t, 34),
                                               N_SIM, env[t]["targets"], TVD["targets_r"], shares_t, crs_t, ypt_t, SH,
                                               other_bucket=True, width={**WIDTH_SIM, "share_conc_targets": 40.0},
                                               player_roles={n: MODEL.role_group(s_) for n, s_ in zip(Mt.name, Mt.slot)})
            for n in names:
                SHADOW_REC[n] = _o40[n]
        team_targets_draw[t] = tt_draw
        # carries: same joint structure, per-carry yards from the empirical league residual grid.
        # QBs (plan step 3): their own carry grid, and the starter's kneel-downs by the
        # team's pregame spread -- the book settles QB rushing yards with them. Both
        # need priors that carry them; no other player's draws move either way.
        p_resid = p_kneel = None
        if QB_RESID is not None:
            p_resid = [QB_RESID if pos == "QB" else None for pos in Mt.pos]
            t_spread = (MODEL.own_spread_from_book(market_env["home_spread"], t == HOME)
                        if market_env is not None else None)
            kg = MODEL.kneel_grid(P, t_spread)            # no spread yet: the pooled grid
            qb_i = MODEL.starter_qb_index(list(Mt.pos), [float(v) for v in Mt.rs], slots=list(Mt.slot))
            p_kneel = [kg if j == qb_i else None for j in range(len(Mt))]
            if qb_i is not None:
                STARTER_QB[t] = Mt.name.iloc[qb_i]
        else:
            qb_i = None
        rs_t = [float(v) for v in Mt.rs]
        rs_hist = list(rs_t)                            # before the QB hold: the history-only shadow
        if env[t].get("carry_factor", 1.0) != 1.0:      # round 29: the QB's carries held
            # the starter by the same rule the harness uses, whether or not the QB grid is loaded
            qb_h = qb_i if qb_i is not None else MODEL.starter_qb_index(list(Mt.pos), rs_t, slots=list(Mt.slot))
            rs_t = [float(v) for v in MODEL.hold_qb_carries(rs_t, qb_h, env[t]["carry_factor"])]
        car_want = {names.index(r_["who"]): r_["value"] for r_ in RULES
                    if a.scenario_run and not r_["team"] and r_["key"] == "carries" and r_["team_of"] == t}
        if car_want:                 # YOUR scenario: carries per game, teammates give up the difference
            try:
                rs_t = SC.solve_carries(rs_t, car_want, SC.rush_effective_fn(
                    env[t]["carries"], TVD["carries_r"], [float(v) for v in Mt.ypc], resid, WIDTH,
                    p_resid, p_kneel, qb_i))
            except ValueError as exc:
                sys.exit(f"--assume ({t}): {exc}")
            M.loc[Mt.index, "rs"] = rs_t
        sim_inputs[t] = dict(names=names, shares=shares_t, crs=crs_t, ypt=ypt_t,
                             rs=rs_t, ypc=[float(v) for v in Mt.ypc],
                             p_resid=p_resid, p_kneel=p_kneel, qb_i=qb_i)
        car_t, rush_t, tc_draw = MODEL.simulate_team_rush(team_stream(t, 102), N_SIM, env[t]["carries"], TVD["carries_r"],
                                                          rs_t, [float(v) for v in Mt.ypc], resid,
                                                          width=WIDTH, player_resid=p_resid, player_kneel=p_kneel,
                                                          qb_index=qb_i)
        team_carries_draw[t] = tc_draw
        # THE REVERSED SHADOW (DECISIONS #204): round 39 ships market carries, so the backs'
        # rushing is priced again WITHOUT them (history carries, the QB not held), on its own
        # stream so no board number moves; logged as p_over_hist_carries for the week-8
        # reversal check (revert if rushing is clearly worse at real lines, weeks 5-8).
        if ("carries_history" in env[t] and env[t].get("carry_factor", 1.0) != 1.0 and not SCENARIO):
            car_m, rush_m, _tcm = MODEL.simulate_team_rush(
                team_stream(t, 39), N_SIM,
                env[t]["carries_history"], TVD["carries_r"], rs_hist, [float(v) for v in Mt.ypc], resid,
                width=WIDTH, player_resid=p_resid, player_kneel=p_kneel, qb_index=qb_i)
            for j, (_, m) in enumerate(Mt.iterrows()):
                if str(m.pos) != "QB":
                    SHADOW_RUSH[m["name"]] = (rush_m[j], car_m[j])
        for j, (_, m) in enumerate(Mt.iterrows()):
            rec, yds = out_rec[m["name"]]
            sims[m["name"]] = {"receptions": rec, "rec_yards": yds, "rush_yards": rush_t[j], "carries": car_t[j],
                               "rush_rec_yards": yds + rush_t[j], "targets": tg_draws[m["name"]]}
    # QB PASSING (plan step 4, props-v1.24; reports/yardage_harness.md, DECISIONS
    # #105): the starter's passing yards are his receivers' yards in THIS
    # simulation, plus the other bucket's targets at the depth receivers' rates,
    # times his share of the team's passing yards (the prior season's grid).
    # Drawn after both teams, from child streams, so the kneel-down streams keep
    # their order and no other number moves.
    PASS_ON = (QB_RUSH_ON and "other_receiver_rates" in P and "qb_starter_pass_share_quantiles" in P)
    pass_skipped = set()     # (player, team): a posted passing line for a QB the model does not start
    if PASS_ON:
        _share = np.array(P["qb_starter_pass_share_quantiles"])
        for t in (AWAY, HOME):
            if STARTER_QB.get(t) is not None:
                ys_t, other_t = pass_inputs[t]
                sims[STARTER_QB[t]]["pass_yards"] = MODEL.simulate_qb_passing(
                    team_stream(t, 103), N_SIM, ys_t, other_t, P["other_receiver_rates"], SH, starter_share=_share,
                    width=WIDTH,
                    implied_points=env[t].get("implied_points"))
                # his completions for the volume chance (simulate_qb_completions: his receivers' catches
                # in this simulation, the depth bucket's targets caught, his share), stream 104: no price
                # reads them and no other draw moves
                sims[STARTER_QB[t]]["completions"] = MODEL.simulate_qb_completions(
                    team_stream(t, 104), N_SIM,
                    [sims[n_]["receptions"] for n_ in M[M.team == t].name if n_ != STARTER_QB[t] and n_ in sims],
                    other_t, P["other_receiver_rates"], starter_share=_share, width=WIDTH)
                if (WIDTH or {}).get("pass_implied_exp") and env[t].get("implied_points") is None:
                    # round 38 (pre-registered): a run without the spread/total says the scale is off
                    SOURCES.append((f"QB passing implied-points scale ({t})", "round 38's passing scale",
                                    "DATA MISSING", "no spread/total this run: the scale is off for this team's "
                                                    "passing price (DECISIONS #199)"))
    M["mu_rec"] = [max(env[r.team]["targets"] * r.ts * max(r.cr, 0.05), 0.02) for _, r in M.iterrows()]
    M["mu_car"] = [max(env[r.team]["carries"] * r.rs, 0.02) for _, r in M.iterrows()]

    # marginal-equivalence check: joint simulation means must match the closed-form means
    for _, m in M.iterrows():
        sm = sims[m["name"]]["receptions"].mean()
        if m.mu_rec > 0.5 and abs(sm - m.mu_rec) / m.mu_rec > 0.10:
            log(f"  WARNING joint-sim marginal drift: {m['name']} receptions mean {sm:.2f} vs closed-form {m.mu_rec:.2f}")

    # ---------- 6b. touchdown allocation ----------
    F_PASS_IN = P.get("pass_td_frac_inside10", 0.48); F_RUSH_IN = P.get("rush_td_frac_inside10", 0.74)
    def td_lambda(pr):
        """Expected TDs for a player. Goal-line TDs (plays starting inside the 10) are
        allocated by inside-the-10 share; the rest -- 52% of passing TDs and 26% of rushing
        TDs in 2025 -- are allocated by overall target/carry share, which is what a long
        touchdown actually depends on. Allocating everything by goal-line share (the
        earlier version) under-rated explosive and high-volume players and over-rated
        goal-line specialists."""
        e = env[pr.team]
        return (e["pass_td"] * (F_PASS_IN * pr.i10ts + (1 - F_PASS_IN) * pr.ts)
                + e["rush_td"] * (F_RUSH_IN * pr.i10rs + (1 - F_RUSH_IN) * pr.rs))

    def p_anytime(pr):
        """(P(at least one touchdown), model). anytime_td_v1 wherever it priced
        the player; anytime_td_v0 otherwise, and the second value says which,
        so a fallback row can never pass for a v1 one."""
        if V1TD is not None and pr.gsis_id in V1TD.index:
            return float(V1TD.loc[pr.gsis_id, "p"]), TDV1.LABEL
        return float(1 - np.exp(-td_lambda(pr))), "anytime_td_v0"

    # ---------- 6c. weather (NWS, Open-Meteo fallback) ----------
    # a roof NOT YET POSTED for a retractable stadium could open on the day: fetch anyway
    _fetch_wx = roof not in ("closed", "dome") or bool(ROOF_NOTE and "retractable" in ROOF_NOTE)
    weather = {"status": "skipped (closed roof)" if not _fetch_wx else "not attempted"}
    STADIUM_LL = {}   # filled from games.csv when available; else geocode by stadium is not attempted
    if _fetch_wx:
        import urllib.request
        # games.csv has no coordinates; use the bundled home-team stadium table. City-level
        # accuracy is enough for an NWS grid cell (2.5 km). Neutral-site games are the
        # exception; the table keys on the home team, so a London or Germany game will
        # get the wrong forecast -- games.csv `location` != "Home" flags those.
        lat = lon = None
        try:
            coords = pd.read_csv(RES / "stadium_coords.csv").set_index("team")
            if str(G.get("location", "Home")) != "Home":
                raise ValueError(f"neutral site ({G.get('location')}); no coordinates")
            if HOME in coords.index:
                lat, lon = float(coords.loc[HOME, "latitude"]), float(coords.loc[HOME, "longitude"])
            if lat is None:
                raise ValueError("no stadium coordinates for home team")
            req = urllib.request.Request(f"https://api.weather.gov/points/{lat},{lon}",
                                         headers={"User-Agent": "nfl-prop-research/1.0"})
            pts = json.load(urllib.request.urlopen(req, timeout=20))
            hurl = pts["properties"]["forecastHourly"]
            req = urllib.request.Request(hurl, headers={"User-Agent": "nfl-prop-research/1.0"})
            fc = json.load(urllib.request.urlopen(req, timeout=20))
            periods = fc["properties"]["periods"]
            win = [q for q in periods if abs((pd.Timestamp(q["startTime"]) - kick).total_seconds()) <= 3 * 3600]
            if win:
                winds = [int(str(q.get("windSpeed", "0")).split()[0]) for q in win]
                temps = [q["temperature"] for q in win]
                pops = [(q.get("probabilityOfPrecipitation") or {}).get("value") or 0 for q in win]
                weather = {"status": "ok", "provider": "NWS", "updated": fc["properties"].get("updateTime"),
                           "temp_f": f"{min(temps)}-{max(temps)}", "wind_mph_max": max(winds),
                           "precip_pct_max": max(pops), "wind_screen": max(winds) > 15}
            else:
                weather = {"status": "forecast window not covered", "provider": "NWS"}
        except Exception as ex:
            weather = {"status": f"failed ({type(ex).__name__})", "provider": "NWS"}

    SOURCES.append(("Weather (NWS)", "wind, temp, rain at kickoff", weather["status"],
                    (f"{weather.get('temp_f','')}F, wind to {weather.get('wind_mph_max','')} mph, "
                     f"rain {weather.get('precip_pct_max','')}%") if weather["status"] == "ok" else ""))

    # ---------- 7. odds ----------
    quote_meta, rows, consensus_rows, unmatched_odds_names = {}, [], [], set()
    _rn = rw[rw.team.isin([AWAY, HOME])].full_name
    roster_norm_global = {norm_name(n) for n in _rn}
    roster_loose_global = {name_key_loose(n) for n in _rn}
    if a.no_odds:
        SOURCES.append(("Sportsbook prices (The Odds API)", "the lines and odds being compared",
                        "skipped (--no-odds)", ""))
    data, eid, quote_meta = None, None, {}
    rows, unmatched_odds_names = [], set()
    sleeper_used = False
    td_two_sided = False
    oddsapi_is_fallback = False

    def pull_sleeper(is_fallback):
        """Pull Sleeper Picks lines for this event and shape them like an Odds API response.

        Returns {"data", "eid", "quote_meta"} or None when Sleeper has no lines for the game
        (so the caller can decide whether to spend Odds API credits). Sleeper is a pick'em
        product: prices are payout multipliers (2+ leg entries, ~12% overround per leg vs
        ~4.5% at DK/FD), converted to American for the join, so EV at these prices is lower
        than a sportsbook's for the same line. Anytime TD is two-sided here, unlike the
        Odds API feed, so it can be de-vigged properly."""
        nonlocal sleeper_used, td_two_sided
        if is_fallback:
            log("  Odds API prices unavailable; falling back to Sleeper Picks lines")
        import urllib.request as _ur
        try:
            _hdr = {"User-Agent": "Mozilla/5.0"}
            sl = cached_json(wd / "sleeper_lines.json", a.sleeper_cache_ttl, lambda: json.load(
                _ur.urlopen(_ur.Request("https://api.sleeper.app/lines/available?dynamic=true", headers=_hdr), timeout=60)))
            slp = cached_json(wd / "sleeper_players.json", 86400, lambda: json.load(
                _ur.urlopen(_ur.Request("https://api.sleeper.app/v1/players/nfl", headers=_hdr), timeout=120)))
            WT = {"receptions": "player_receptions", "receiving_yards": "player_reception_yds",
                  "rushing_yards": "player_rush_yds", "anytime_touchdowns": "player_anytime_td",
                  "passing_yards": "player_pass_yds", "rushing_and_receiving_yards": "player_rush_reception_yds"}
            def mult_to_amer(m):
                m = float(m)
                return int(round((m - 1) * 100)) if m >= 2 else int(round(-100 / (m - 1)))
            _teams = {SLEEPER_TEAM.get(AWAY, AWAY), SLEEPER_TEAM.get(HOME, HOME)}
            mkts, gid, n_lines, latest, pos_rank = {}, None, 0, 0, {}
            for m_ in sl:
                if m_.get("sport") != "nfl" or m_.get("wager_type") not in WT or m_.get("line_type", "normal") != "normal":
                    continue
                opts = m_.get("options") or []
                if not opts or opts[0].get("subject_team") not in _teams or opts[0].get("game_status") != "pre_game":
                    continue
                pinfo = slp.get(m_["subject_id"], {})
                nm_ = pinfo.get("full_name") or f'{pinfo.get("first_name","")} {pinfo.get("last_name","")}'.strip()
                if not nm_:
                    continue
                gid = m_.get("game_id"); latest = max(latest, int(m_.get("updated_at", 0)))
                if opts[0].get("subject_pos_rank"):
                    pos_rank[nm_] = opts[0]["subject_pos_rank"]
                over = next((o for o in opts if o["outcome"] == "over" and o.get("status") == "active"), None)
                under = next((o for o in opts if o["outcome"] == "under" and o.get("status") == "active"), None)
                if over is None:
                    continue
                key = WT[m_["wager_type"]]
                outs = mkts.setdefault(key, [])
                if key == "player_anytime_td":
                    outs.append({"name": "Yes", "description": nm_, "price": mult_to_amer(over["payout_multiplier"])})
                    if under is not None:
                        # Sleeper prices the "no TD" side too, so anytime-TD can be de-vigged
                        # properly instead of treating the Yes price as the market number.
                        outs.append({"name": "No", "description": nm_, "price": mult_to_amer(under["payout_multiplier"])})
                        td_two_sided = True
                else:
                    if under is None:
                        continue
                    outs.append({"name": "Over", "description": nm_, "point": float(over["outcome_value"]), "price": mult_to_amer(over["payout_multiplier"])})
                    outs.append({"name": "Under", "description": nm_, "point": float(under["outcome_value"]), "price": mult_to_amer(under["payout_multiplier"])})
                n_lines += 1
            if n_lines == 0:
                SOURCES.append(("Sportsbook prices (Sleeper Picks)", "the lines and odds being compared",
                                "no lines", "Sleeper has not posted this game yet"))
                log("  no Sleeper lines for this game")
                return None
            sleeper_used = True
            lu = datetime.fromtimestamp(latest / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if latest else now()
            data_ = {"bookmakers": [{"key": "sleeper", "markets": [{"key": k, "last_update": lu, "outcomes": v} for k, v in mkts.items()]}],
                     "sleeper_pos_rank": pos_rank,
                     # the book's longest-catch, longest-run and carries lines: read beside the
                     # priced lines (research.catch_yards_read / carry_yards_read, DECISIONS
                     # #164, #166), never priced, joined or archived
                     "sleeper_extra": RSCH.extra_lines(sl, slp, _teams)}
            eid_ = f"sleeper_{gid}"
            arch_rows = [{"retrieved_at_utc": now(), "snapshot_type": "decision", "season": SEASON, "week": WEEK,
                          "event_id": eid_, "commence_time": kick.isoformat(), "home_team": TEAM_NAMES.get(HOME), "away_team": TEAM_NAMES.get(AWAY),
                          "bookmaker": "sleeper", "market": mk_["key"], "player": o.get("description"), "outcome": o.get("name"),
                          "point": o.get("point"), "price_american": o.get("price"), "last_update": lu,
                          "requests_remaining": None, "requests_used": None, "requests_last": None, "source": "sleeper_lines_available"}
                         for mk_ in data_["bookmakers"][0]["markets"] for o in mk_["outcomes"]]
            with open(OUT / f"line_archive_nfl_{SEASON}.jsonl", "a") as fh:
                for r_ in arch_rows:
                    fh.write(json.dumps(r_) + "\n")
            SOURCES.append(("Sportsbook prices (Sleeper Picks)" + (" [automatic fallback]" if is_fallback else " [primary]"),
                            "the lines and odds being compared", "ok",
                            f"{n_lines} lines, multipliers converted to American, latest update {lu}; archived; ~12% overround"
                            + ("; anytime TD two-sided" if td_two_sided else "")))
            return {"data": data_, "eid": eid_, "quote_meta": {"quota": {}, "retrieved": now(), "event_id": eid_, "archive": None}}
        except Exception as ex:
            SOURCES.append(("Sportsbook prices (Sleeper Picks)", "the lines and odds being compared",
                            f"failed ({type(ex).__name__})", str(ex)[:120]))
            log(f"  Sleeper lines pull failed ({type(ex).__name__}: {ex})")
            return None

    if SNAP is not None:
        data, eid, quote_meta = SNAP["data"], SNAP["eid"], SNAP["quote_meta"]
        sleeper_used, td_two_sided = SNAP["sleeper_used"], SNAP["td_two_sided"]
        SOURCES.append(("Sportsbook prices", "the lines and odds being compared", "ok",
                        "the same lines as the main run (scenario; no fetch, no credits)"))
    if SNAP is None and not a.no_odds and not a.lines_file and a.source == "sleeper":
        _r = pull_sleeper(is_fallback=False)
        if _r:
            data, eid, quote_meta = _r["data"], _r["eid"], _r["quote_meta"]
        elif a.no_oddsapi_fallback:
            log("  --no-oddsapi-fallback set; continuing without prices")
        else:
            oddsapi_is_fallback = True
            log("  falling back to The Odds API (spends credits)")

    # ---------- 7a2. other books beside Sleeper (--compare-books, DECISIONS #146) ----------
    # DraftKings and FanDuel player lines for THIS game, appended to Sleeper's so the
    # research table and "Where the books disagree" show them. Opt-in, a few credits,
    # never the last ones; any failure is a sources note, never a lost run.
    if SNAP is None and not a.no_odds and not a.lines_file and a.compare_books and data is not None and sleeper_used:
        _q = last_oddsapi_quota()
        _src = ("Other books (The Odds API)", "DraftKings and FanDuel beside Sleeper")
        if _q is not None and _q < COMPARE_QUOTA_MIN:
            SOURCES.append((*_src, "skipped", f"{_q} credits left; needs {COMPARE_QUOTA_MIN}+"))
        else:
            try:
                home_name, away_name = TEAM_NAMES.get(HOME), TEAM_NAMES.get(AWAY)
                ev = run_odds("events", ["--home", home_name, "--away", away_name,
                                         "--key-file", str(RES / "credential.env")])
                evs = [e for e in ev.get("events", []) if e["home_team"] == home_name and e["away_team"] == away_name]
                if len(evs) != 1:
                    raise RuntimeError(f"{len(evs)} matching events")
                eid2 = evs[0]["id"]
                od = run_odds("odds", [eid2, "--key-file", str(RES / "credential.env"),
                                       "--markets", COMPARE_MARKETS, "--books", ",".join(COMPARE_BOOKS)])
                cf = ([HERE / "cache" / od["reused_cache"]] if od.get("reused_cache") else
                      sorted((HERE / "cache").glob(f"odds_{eid2}_*.json"), key=lambda f: f.stat().st_mtime))
                extra = []
                if od.get("class") == "OK" and cf:
                    extra = [b for b in json.load(open(cf[-1]))["data"].get("bookmakers", []) if b["key"] in COMPARE_BOOKS]
                data["bookmakers"] = list(data["bookmakers"]) + extra
                SOURCES.append((*_src, "ok" if extra else "no lines",
                                f"{', '.join(b['key'] for b in extra) or 'no book posted these markets'}; "
                                f"{(od.get('quota') or {}).get('x-requests-remaining')} credits left"))
            except Exception as ex:  # noqa: BLE001 -- a comparison must never cost the run
                SOURCES.append((*_src, "unavailable", f"{type(ex).__name__}: {str(ex)[:120]}"))

    if SNAP is None and not a.no_odds and not a.lines_file and (a.source == "oddsapi" or oddsapi_is_fallback):
        home_name, away_name = TEAM_NAMES.get(HOME), TEAM_NAMES.get(AWAY)
        if not home_name or not away_name:
            sys.exit(f"NO TEAM-NAME MAPPING for {AWAY}/{HOME}; add to TEAM_NAMES before pricing")
        try:
            ev = run_odds("events", ["--home", home_name, "--away", away_name,
                                     "--key-file", str(RES / "credential.env")])
        except RuntimeError as ex:
            if not oddsapi_is_fallback:
                raise
            # a fallback that cannot reach the Odds API (no key, no credits, network) must not
            # cost the game: continue without prices, exactly as an empty event match does
            log(f"  Odds API fallback unavailable ({ex}); continuing WITHOUT prices")
            ev = {"events": [], "fallback_failed": True}
        evs = ev.get("events", [])
        if ev.get("fallback_failed"):
            pass
        elif len(evs) != 1:
            # exactly one event must match by BOTH team names. Never fall back to date.
            log(f"  Odds API event match returned {len(evs)} events for {away_name} at {home_name}; "
                f"continuing WITHOUT prices (EVENT_MATCH_FAILED)")
            evs = []
        else:
            e = evs[0]
            assert e["home_team"] == home_name and e["away_team"] == away_name, \
                f"event teams {e['away_team']} at {e['home_team']} != requested {away_name} at {home_name}"
            kd = (pd.Timestamp(e["commence_time"]) - pd.Timedelta(hours=4)).strftime("%Y-%m-%d")
            assert kd == str(G.gameday), \
                f"event date {kd} != games.csv gameday {G.gameday}; refusing to price the wrong week"
        if not evs:
            log("  no matching Odds API event; continuing without prices")
            SOURCES.append(("Sportsbook prices (The Odds API)", "the lines and odds being compared",
                            *(("unavailable", "the fallback could not reach the API (key, credits or network)")
                              if ev.get("fallback_failed") else
                              ("no event found", "the API has not posted this game yet"))))
        else:
            eid = evs[0]["id"]
            books = "" if a.books == "all" else a.books
            args_ = [eid, "--key-file", str(RES / "credential.env"), "--archive",
                     "--snapshot", "decision", "--season", str(SEASON), "--week", str(WEEK),
                     "--markets", "spreads,totals,player_receptions,player_reception_yds,"
                                  "player_rush_yds,player_anytime_td"]
            if books:
                args_ += ["--books", books]
            else:
                args_ += ["--books", "draftkings,fanduel,betmgm,betrivers,bovada,fanatics,betonlineag"]
            od = run_odds("odds", args_)
            quote_meta = {"quota": od.get("quota"), "retrieved": od.get("retrieved_at_utc"),
                          "event_id": eid, "archive": od.get("archive")}
            def _has_props(f):
                r_ = json.load(open(f))
                return r_.get("class") == "OK" and any(m["key"].startswith("player_")
                                                       for b in r_["data"]["bookmakers"] for m in b["markets"])
            if od.get("reused_cache"):
                ok_caches = [HERE / "cache" / od["reused_cache"]]
            else:
                ok_caches = [f for f in sorted((HERE / "cache").glob(f"odds_{eid}_*.json")) if _has_props(f)]
            if od.get("class") == "OK" and ok_caches:
                data = json.load(open(ok_caches[-1]))["data"]
                SOURCES.append(("Sportsbook prices (The Odds API)", "the lines and odds being compared", "ok",
                                f"{len(data['bookmakers'])} books, captured {od.get('retrieved_at_utc')}, "
                                f"{od.get('quota',{}).get('x-requests-remaining')} API calls left"
                                + (f" (reused cache, {od.get('cache_age_s')} s old)" if od.get("reused_cache") else "")))
            else:
                data = None
                SOURCES.append(("Sportsbook prices (The Odds API)", "the lines and odds being compared",
                                od.get("class", "failed"), f"quota remaining {od.get('quota',{}).get('x-requests-remaining')}; no prices this run"))

    # ---------- 7b. Sleeper as the fallback when the Odds API was tried first ----------
    if SNAP is None and not a.no_odds and not a.lines_file and a.source == "oddsapi" and data is None:
        _r = pull_sleeper(is_fallback=True)
        if _r:
            data, eid, quote_meta = _r["data"], _r["eid"], _r["quote_meta"]
    if SNAP is None and not a.no_odds and not a.lines_file and data is None:
        log("  no prices from any source this run")

    # ---------- 7c. manual lines file (explicit only) ----------
    # CSV columns: player,market,line,over_price,under_price,book  (market in
    # player_receptions / player_reception_yds / player_rush_yds / player_anytime_td;
    # for anytime_td put the Yes price in over_price and leave line/under_price blank).
    # Built into the same shape the Odds API returns, so the join and card are identical.
    if a.lines_file:
        mf = pd.read_csv(a.lines_file)
        bks = {}
        for _, r in mf.iterrows():
            bk = str(r.get("book", "manual") or "manual")
            m = bks.setdefault(bk, {})
            outs = m.setdefault(r.market, [])
            if r.market == "player_anytime_td":
                outs.append({"name": "Yes", "description": r.player, "price": int(r.over_price)})
            else:
                outs.append({"name": "Over", "description": r.player, "point": float(r.line), "price": int(r.over_price)})
                outs.append({"name": "Under", "description": r.player, "point": float(r.line), "price": int(r.under_price)})
        data = {"bookmakers": [{"key": bk, "markets": [{"key": mk, "last_update": now(), "outcomes": o} for mk, o in ms.items()]} for bk, ms in bks.items()]}
        eid = f"manual_{SEASON}_wk{WEEK}_{AWAY}_{HOME}"
        quote_meta = {"quota": {}, "retrieved": now(), "event_id": eid, "archive": None}
        SOURCES.append(("Sportsbook prices (manual lines file)", "the lines and odds being compared", "ok",
                        f"{len(mf)} lines from {Path(a.lines_file).name}, entered {now()}; no archive row, no CLV"))
    # The lines this run priced, saved so the 'if he is out' runs price the SAME
    # lines without fetching again (no credits, no second archive row).
    snap_path = wd / f"odds_snapshot_{SEASON}_wk{WEEK:02d}_{AWAY}_{HOME}.json"
    snap_written = False
    if SNAP is None and data is None and snap_path.exists():
        snap_path.unlink()          # an earlier run's lines must never price this run's scenarios
    if SNAP is None and data is not None:
        snap_written = True
        snap_path.write_text(json.dumps({"market_env": market_env, "data": data, "eid": eid,
                                         "quote_meta": quote_meta, "sleeper_used": sleeper_used,
                                         "td_two_sided": td_two_sided}, default=str), encoding="utf-8")
    if data is not None:
        # consensus across all returned books (B)
        allrows = []
        for b in (data["bookmakers"] if data else []):
            for mk in b["markets"]:
                for o in mk["outcomes"]:
                    allrows.append({"book": b["key"], "market": mk["key"],
                                    "player": o.get("description"), "name": o["name"],
                                    "point": o.get("point"), "price": o["price"],
                                    "last_update": mk["last_update"]})
        A = pd.DataFrame(allrows)
        for (mkey, player), grp in A[A.market.isin(list(YARD_MARKETS) + list(COUNT_MARKETS))
                                     & A.player.notna()].groupby(["market", "player"]):
            piv = grp.pivot_table(index="book", columns="name", values=["point", "price"],
                                  aggfunc="first")
            if ("price", "Over") not in piv or ("price", "Under") not in piv:
                continue
            lines = piv[("point", "Over")].astype(float)
            cons_line = float(np.nanmedian(lines.values))
            # No-vig probabilities are ONLY comparable between books posting the SAME
            # line. Comparing a 3.5 to a 4.5 as if both were "P(over)" is meaningless,
            # which is what produced NaN consensus rows in the first run.
            novigs = {}
            for bk in piv.index:
                if not np.isclose(lines.get(bk, np.nan), cons_line, equal_nan=False):
                    continue
                try:
                    io_ = amer_to_p(piv.loc[bk, ("price", "Over")])
                    iu_ = amer_to_p(piv.loc[bk, ("price", "Under")])
                    novigs[bk] = io_ / (io_ + iu_)
                except Exception:
                    pass
            cons_p = float(np.median(list(novigs.values()))) if novigs else np.nan
            for bk in piv.index:
                ln = lines.get(bk, np.nan)
                dev_line = float(ln) - cons_line if pd.notna(ln) else np.nan
                bp = novigs.get(bk, np.nan)
                dev_p = bp - cons_p if (pd.notna(bp) and pd.notna(cons_p)) else np.nan
                off_line = pd.notna(dev_line) and abs(dev_line) >= CONSENSUS_TOL[mkey]
                off_price = pd.notna(dev_p) and abs(dev_p) >= 0.04
                if off_line or off_price:
                    consensus_rows.append({
                        "market": mkey, "player": player, "book": bk, "book_line": ln,
                        "consensus_line": cons_line, "line_dev": dev_line,
                        "book_p_novig": bp, "consensus_p_novig": cons_p, "p_dev": dev_p,
                        "n_books_total": len(piv), "n_books_at_consensus_line": len(novigs),
                        "reason": "line off consensus" if off_line else "price off consensus"})

        # price every posted line for DK/FD against the model
        # Fix (round-5 review #4): match odds-API player descriptions to our
        # roster names via norm_name on BOTH sides. The previous version used
        # exact string equality, which is the same class of bug the snap-share
        # join had ("D.J. Moore" vs "DJ Moore") -- silently dropping a prop
        # instead of erroring is worse than erroring, so unmatched names are
        # now logged.
        name_by_norm = {norm_name(n): n for n in M.name}
        # Everyone on either roster this week, so we can tell a genuine name-join
        # failure from a player who is simply outside our eligible population
        # (TE2s, WR4s etc. get props posted but aren't in the top-7 + share proxy).
        # Reporting the latter as "name match failed" is a false alarm that would
        # mask a real join failure when one happens.
        loose_by_key = {}
        for n in M.name:
            loose_by_key.setdefault(name_key_loose(n), n)
        unmatched_odds_names = set()
        for b in (data["bookmakers"] if data else []):
            if b["key"] not in ("draftkings", "fanduel") and not a.lines_file and not sleeper_used:
                continue
            for mk in b["markets"]:
                if mk["key"] in YARD_MARKETS or mk["key"] in COUNT_MARKETS:
                    col = YARD_MARKETS.get(mk["key"]) or COUNT_MARKETS[mk["key"]]
                    by = {}
                    for o in mk["outcomes"]:
                        by.setdefault(o["description"], {})[o["name"]] = o
                    for nm_raw, oo in by.items():
                        nm = name_by_norm.get(norm_name(nm_raw)) or loose_by_key.get(name_key_loose(nm_raw))
                        if nm is None:
                            if not is_team_entry(nm_raw):
                                unmatched_odds_names.add((mk["key"], nm_raw))
                            continue
                        if nm not in sims or "Over" not in oo or "Under" not in oo:
                            continue
                        if col not in sims[nm]:
                            # passing yards: the starting QB only
                            if mk["key"] == "player_pass_yds" and PASS_ON:
                                tm_ = M[M.name == nm].team.iloc[0]
                                if (nm, tm_) not in pass_skipped:
                                    pass_skipped.add((nm, tm_))
                                    log(f"  passing line for {nm} not priced: the model's starter for {tm_} is "
                                        f"{STARTER_QB.get(tm_) or 'none'}")
                            continue
                        pr = M[M.name == nm].iloc[0]
                        if mk["key"] == "player_rush_yds" and pr.pos == "QB":
                            continue   # QB rushing is off the board (DECISIONS #188): the user does not bet
                                       # it; his carries stay in the team's pool, which the backs share
                        if mk["key"] == "player_rush_reception_yds" and pr.pos == "QB":
                            continue   # the combined line is checked on backs and receivers, not QBs
                        s = sims[nm][col]; L = oo["Over"]["point"]
                        p_o = float(np.mean(s > L))
                        p_push = float(np.mean(s == L)) if float(L).is_integer() else 0.0
                        io_, iu_ = amer_to_p(oo["Over"]["price"]), amer_to_p(oo["Under"]["price"])
                        nv = io_ / (io_ + iu_)
                        if p_o >= nv:
                            side, pw, px, pn = "Over", p_o, oo["Over"]["price"], nv
                        else:
                            side, pw, px, pn = "Under", 1 - p_o - p_push, oo["Under"]["price"], 1 - nv
                        er = pw * payout(px) - (1 - pw - p_push)
                        rows.append(dict(book=b["key"], market=mk["key"], player=nm,
                            team=pr.team, slot=pr.slot, line=L, model_mean=float(s.mean()),
                            side=side, p_model=pw, p_push=p_push, p_novig=pn, gap=pw - pn,
                            price=px, ER=er, last_update=mk["last_update"],
                            new_team=bool(pr.new_team), questionable=bool(pr.questionable),
                            price_over=oo["Over"]["price"], price_under=oo["Under"]["price"],
                            # round 23's factor on his target share, logged so the
                            # scorecard can grade the calls the rule moved (#145)
                            snap_react=float(pr.evidence.get("target_share", {}).get("snap_react") or 1.0),
                            # the reversal-check shadows beside the board (#204)
                            **({"p_over_board": p_o,
                                "p_over_hist_carries": float(np.mean(SHADOW_RUSH[nm][0] > L)),
                                "hist_carries": float(np.mean(SHADOW_RUSH[nm][1]))}
                               if mk["key"] == "player_rush_yds" and nm in SHADOW_RUSH else {}),
                            **({"p_over_board": p_o,
                                "p_over_spread40": float(np.mean(
                                    SHADOW_REC[nm][0 if mk["key"] == "player_receptions" else 1] > L))}
                               if mk["key"] in ("player_receptions", "player_reception_yds") and nm in SHADOW_REC
                               else {})))
                elif mk["key"] == "player_anytime_td":
                    no_price = {o["description"]: o["price"] for o in mk["outcomes"] if o["name"] == "No"}
                    for o in mk["outcomes"]:
                        if o["name"] != "Yes":
                            continue
                        nm = name_by_norm.get(norm_name(o["description"])) or loose_by_key.get(name_key_loose(o["description"]))
                        if nm is None:
                            if not is_team_entry(o["description"]):
                                unmatched_odds_names.add((mk["key"], o["description"]))
                            continue
                        if nm not in sims:
                            continue
                        pr = M[M.name == nm].iloc[0]
                        p_yes, td_model = p_anytime(pr)
                        two_sided = o["description"] in no_price
                        if two_sided:
                            # two-sided market (Sleeper): strip the hold like any O/U line
                            iy_, in_ = amer_to_p(o["price"]), amer_to_p(no_price[o["description"]])
                            p_imp = iy_ / (iy_ + in_)
                        else:
                            p_imp = amer_to_p(o["price"])
                        # LAYER 4: the de-vigged market and the blend at a PROVISIONAL weight,
                        # logged beside the model so the settled record can fit the real weight
                        p_mkt = TDM.market_prob(p_imp, two_sided)
                        p_bl = float(TDM.blend(p_yes, p_mkt))
                        rows.append(dict(book=b["key"], market="player_anytime_td",
                            player=nm, team=pr.team, slot=pr.slot, line=np.nan,
                            model_mean=np.nan, side="Yes", p_model=p_yes, p_push=0.0,
                            p_novig=p_imp, gap=p_yes - p_imp, price=o["price"],
                            ER=p_yes * payout(o["price"]) - (1 - p_yes),
                            last_update=mk["last_update"], new_team=bool(pr.new_team),
                            questionable=bool(pr.questionable), td_model=td_model,
                            two_sided=bool(two_sided), p_market=p_mkt, p_blend=p_bl,
                            blend_w=TDM.BLEND_W_MODEL))

    # Sleeper publishes its own depth rank per player (subject_pos_rank). Where it
    # disagrees with the nflverse depth chart we built the eligible set from, the book is
    # telling us its read on the role -- the single most common early-season model failure.
    # Logged, not acted on: it is one more opinion, not evidence.
    pos_rank_src = (data or {}).get("sleeper_pos_rank") or {}
    slot_gaps = []
    if pos_rank_src:
        _slot_by_norm = {norm_name(m_["name"]): (m_["name"], m_["slot"]) for _, m_ in M.iterrows()}
        for nm_, rk_ in pos_rank_src.items():
            hit = _slot_by_norm.get(norm_name(nm_))
            if hit and str(rk_) != str(hit[1]):
                slot_gaps.append(f"{hit[0]} ours {hit[1]} / Sleeper {rk_}")
        if slot_gaps:
            log("  depth-rank disagreements with Sleeper: " + "; ".join(slot_gaps))
            SOURCES.append(("Depth rank cross-check (Sleeper subject_pos_rank)",
                            "whether the book agrees with our depth-chart slot", "ok",
                            "; ".join(slot_gaps)))

    if MARKETS:
        rows = [r_ for r_ in rows if r_["market"] in MARKETS]
    R = pd.DataFrame(rows)
    # A row priced while a TEAMMATE is Questionable assumes he plays. If he sits,
    # his own props void but this row still grades -- against a line priced on
    # the wrong roster. Flagged so the scorecard can keep those rows apart.
    _q = pop[pop.questionable & ~pop.excluded]
    _q_by_team = {t: set(g["name"]) for t, g in _q.groupby("team")}
    if not R.empty:
        R["questionable_teammate"] = [bool(_q_by_team.get(t, set()) - {p}) for t, p in zip(R.team, R.player)]
    _bk_names ={"draftkings": "DraftKings", "fanduel": "FanDuel", "sleeper": "Sleeper Picks"}
    books_used_str = (", ".join(_bk_names.get(b, str(b).title()) for b in sorted(R.book.unique()))
                      if not R.empty else "no price source")
    if unmatched_odds_names:
        # Three distinct cases, which earlier versions collapsed into one misleading
        # "name match failed" label:
        #   - team D/ST entries: not players at all, filtered at collection time
        #   - rostered but outside our eligible set (TE2, WR4): expected, informational
        #   - not matchable to any rostered player even on the loose key: a REAL join bug
        # The loose key (first initial + surname) catches nickname splits such as the
        # book's "Joshua Palmer" vs the roster's "Josh Palmer".
        names_only = {n for _, n in unmatched_odds_names}
        truly = sorted({n for n in names_only
                        if norm_name(n) not in roster_norm_global
                        and name_key_loose(n) not in roster_loose_global})
        outside = sorted(names_only - set(truly))
        if outside:
            SOURCES.append(("Props on players outside our eligible set",
                            "priced by the book, not modeled here (depth-chart/usage rule)",
                            "ok", f"{len(outside)} skipped: " + ", ".join(outside[:8])))
        if truly:
            SOURCES.append(("Odds-to-roster name match", "matching sportsbook player names to our roster",
                            "FAILED", ", ".join(truly[:6])))
    if not R.empty:
        R["flag"] = np.where(R.new_team, "NEW TEAM - model role prior weak",
                    np.where(R.questionable, "QUESTIONABLE - regime unresolved",
                    np.where(R.gap.abs() > 0.10, "large gap - market likely holds info model lacks", "")))
        # ONE ELIGIBILITY TEST, here and on the betting card and the ladder.
        # `model_state` used to be assigned by matching market-name strings,
        # which is how it once claimed v1 for a v2 model; it now comes from
        # the same table that decides whether the market is validated at all.
        verdicts = [eligibility.evaluate(
            rr.market, p_win=float(rr.p_model), price=float(rr.price),
            gap=float(rr.gap), p_push=float(getattr(rr, "p_push", 0.0) or 0.0),
            new_team=bool(rr.new_team), questionable=bool(rr.questionable),
            min_gap=a.min_gap, min_er=a.min_er, er=float(rr.ER))
            for rr in R.itertuples()]
        R["model_state"] = [v.status for v in verdicts]
        R["decision"] = "PASS"
        R["eligible"] = [v.eligible for v in verdicts]
        R["ineligible_because"] = [v.why for v in verdicts]
        R["clears_edge_rule_if_validated"] = [v.priced for v in verdicts]
        R = R.sort_values("gap", ascending=False)
        R.insert(0, "logged_at_utc", now()); R.insert(1, "season", SEASON); R.insert(2, "week", WEEK)
        R.insert(3, "event_id", quote_meta.get("event_id"))

    # ---------- 8. merge prior persistence ----------
    slug = f"{SEASON}_wk{WEEK:02d}_{AWAY}_{HOME}"
    logf = OUT / f"shadow_log_{slug}.csv"
    if a.prior_log and Path(a.prior_log).exists() and not R.empty:
        prev = pd.read_csv(a.prior_log)
        R = pd.concat([prev, R], ignore_index=True).drop_duplicates(
            subset=["season", "week", "event_id", "book", "market", "player", "line", "side"],
            keep="last")
    if not R.empty:
        # --compare-books rows (DraftKings/FanDuel) are for reading, never for the
        # record: their quotes are not archived, so they stay out of the shadow log
        (R[~R.book.isin(COMPARE_BOOKS)] if a.compare_books else R).to_csv(logf, index=False)
        # anytime TD has its own board: the bet card leaves TD rows out
        TDB = R[R.market == "player_anytime_td"]
        if len(TDB):
            TDB[[c for c in ["player", "team", "book", "price", "p_model", "p_novig", "two_sided", "p_market",
                             "p_blend", "blend_w", "gap", "td_model", "questionable_teammate", "flag",
                             "decision"] if c in TDB.columns]] \
                .sort_values("p_model", ascending=False).to_csv(OUT / f"td_board_{slug}.csv", index=False)
    # LAYER 3: exact joint prices for every pair of anytime-TD legs priced 10%+,
    # all four candidate structures, logged for grading. The report renders
    # only the classes the committed gate opened (td_pairs_section).
    J_ = pd.DataFrame()
    try:
        J_ = joint_shadow(R, M, V1TD, AWAY, HOME, PRIOR)
        if len(J_):
            J_.insert(0, "event_id", quote_meta.get("event_id"))
            J_.insert(0, "week", WEEK); J_.insert(0, "season", SEASON)
            J_.insert(0, "logged_at_utc", now())
            J_.to_csv(OUT / f"joint_td_{slug}.csv", index=False)
    except Exception as exc:  # noqa: BLE001 -- shadow output must never cost the prop run
        log(f"  joint shadow skipped ({type(exc).__name__}: {exc})")
    arch = OUT / f"line_archive_nfl_{SEASON}.jsonl"
    if a.prior_archive and Path(a.prior_archive).exists() and arch.exists():
        seen, merged = set(), []
        for f in (a.prior_archive, arch):
            for line in Path(f).read_text().splitlines():
                if not line.strip():
                    continue
                r = json.loads(line)
                k = (r["event_id"], r["bookmaker"], r["market"], r.get("player"),
                     r["outcome"], r.get("point"), r["last_update"])
                if k not in seen:
                    seen.add(k); merged.append(line)
        arch.write_text("\n".join(merged) + "\n", encoding="utf-8")



    GATE = load_label_gate(wd)

    # ---------- 8a. research columns (props-v1.29, DECISIONS #142) ----------
    # What the line implies (the workload that makes it a fair 50/50), usage
    # last game against earlier weeks, and the flags. Own generators only
    # (research.py): no price moves.
    # USAGE / ROLE: computed before the share blend (section 5), which round 23 reads
    # teammates handled by the out rule, and key teammates back from a missed week
    OUT_NOTE = {t_: [] for t_ in (AWAY, HOME)}
    _flagged_out = set()      # gsis ids the out flag already names
    # WAS LAST WEEK A PREVIEW (DECISIONS #157)? Same starting QB, same key
    # absences. A mark built on last week's workload transfers when it was.
    PREVIEW_DIFF = {t_: [] for t_ in (AWAY, HOME)}
    _tg = passes[["posteam", "week"]].assign(pid=passes.receiver_player_id)
    _cr = rushes[["posteam", "week"]].assign(pid=rushes.rusher_player_id)
    _db_ = pbp[(pbp.play_type == "pass") & pbp.passer_player_id.notna()]
    _db = _db_[["posteam", "week"]].assign(pid=_db_.passer_player_id)
    for _, e_ in pop[pop.excluded].iterrows():
        pri_ = pri_players.loc[e_.gsis_id] if e_.gsis_id in pri_players.index else None
        _wk = ros[(ros.season == SEASON) & (ros.week < WEEK) & (ros.team == e_.team)
                  & (ros.gsis_id == e_.gsis_id) & (ros.status == "ACT")].week
        if RSCH.out_matters(e_.gsis_id, e_.team, _tg, _cr, _db,
                            None if pri_ is None else pri_.get("target_share"),
                            None if pri_ is None else pri_.get("rush_share"), weeks=set(_wk)):
            played_lw = _snp_w.get((e_.team, norm_name(e_["name"]), WEEK - 1), 0) > 0
            qb_tag = " (QB)" if str(e_.get("pos")) == "QB" else ""
            OUT_NOTE[e_.team].append(f"{e_['name']}{qb_tag} out, "
                                     + ("played last week" if played_lw else "also out last week"))
            _flagged_out.add(e_.gsis_id)
            if played_lw:
                PREVIEW_DIFF[e_.team].append(f"{e_['name']} newly out")
    # QUESTIONABLE TEAMMATES with a real role, priced or not (DECISIONS #163): a TE2 the
    # board does not price (Noah Fant, NO week 4) still moves the TE1 if he sits
    QWATCH = {t_: [] for t_ in (AWAY, HOME)}
    for _, j_ in iw[iw.team.isin([AWAY, HOME]) & iw.report_status.isin(["Questionable", "Doubtful"])].iterrows():
        if j_.gsis_id in _flagged_out:
            continue                    # the out flag already names him
        ts_j = RSCH.role_share(_tg, j_.gsis_id, j_.team)
        cs_j = RSCH.role_share(_cr, j_.gsis_id, j_.team)
        sn_j = snap_cur.get((j_.team, norm_name(j_.full_name)))
        if RSCH.worth_watching(ts_j, cs_j, sn_j):
            QWATCH[j_.team].append(dict(name=j_.full_name, pos=str(j_.position), status=str(j_.report_status),
                                        ts=ts_j, cs=cs_j, snap=sn_j, priced=j_.gsis_id in set(M.gsis_id)))
    BACK_NOTE = {}
    for _, m_ in M.iterrows():
        pri_ = pri_players.loc[m_.gsis_id] if m_.gsis_id in pri_players.index else None
        # a KEY teammate: 15%+ of the targets OR the carries last season, or this
        # season in the weeks he played (a back who returns matters too)
        if not RSCH.is_key_teammate(None if pri_ is None else pri_.get("target_share"),
                                    None if pri_ is None else pri_.get("rush_share"),
                                    RSCH.role_share(_tg, m_.gsis_id, m_.team),
                                    RSCH.role_share(_cr, m_.gsis_id, m_.team)):
            continue
        # BACK means he missed the game just played and plays today: a teammate
        # who missed week 2 but played last week is not returning (DECISIONS #157)
        if (m_.team, WEEK - 1) not in _tw_i.index:
            continue                       # the team was on a bye last week
        if _snp_w.get((m_.team, norm_name(m_["name"]), WEEK - 1), 0) > 0:
            continue
        if bool(m_.new_team) and not any(k_[0] == m_.team and k_[1] == norm_name(m_["name"]) for k_ in _snp_w.index):
            # never played for this team: he JOINS, he is not back
            BACK_NOTE[m_.team] = BACK_NOTE.get(m_.team, []) + [f"{m_['name']} joins (new this week)"]
            PREVIEW_DIFF[m_.team].append(f"{m_['name']} joins")
            continue
        BACK_NOTE[m_.team] = BACK_NOTE.get(m_.team, []) + [f"{m_['name']} back (missed last week)"]
        PREVIEW_DIFF[m_.team].append(f"{m_['name']} back")
    _lwp = pbp[(pbp.week == WEEK - 1) & (pbp.play_type == "pass") & pbp.passer_player_id.notna()]
    PREVIEW = {}
    for t_ in (AWAY, HOME):
        sq_ = STARTER_QB.get(t_)
        tid_ = M[(M.team == t_) & (M.name == sq_)].gsis_id if sq_ is not None else []
        qc_ = RSCH.qb_change(_lwp[_lwp.posteam == t_], tid_.iloc[0] if len(tid_) else None, sq_)
        if qc_:
            PREVIEW_DIFF[t_].insert(0, qc_)
        PREVIEW[t_] = RSCH.preview_note(PREVIEW_DIFF[t_])
    research_rows, _implied_cache, _edges_cache = [], {}, {}
    # THIS run's lines only: R has been merged with --prior-log above, and an
    # earlier capture's line (58.5 before it moved to 59.5) is not a line now
    _now = pd.DataFrame(rows)
    for _, r_ in (_now[_now.market != "player_anytime_td"] if len(_now) else _now).iterrows():
        if r_.player not in sims or not (M.name == r_.player).any():
            continue
        m_ = M[M.name == r_.player].iloc[0]
        si = sim_inputs[m_.team]
        # the posted prices: the break-even workload is read at the price this book shows
        px_ = (r_.get("price_over"), r_.get("price_under"))
        ck = (r_.player, r_.market, float(r_.line), str(px_))
        if ck not in _implied_cache and SCENARIO:
            _implied_cache[ck] = (None, None, None, None, None)     # scenario run: nobody reads its research
        if ck not in _implied_cache:
            if r_.market in ("player_receptions", "player_reception_yds"):
                _implied_cache[ck] = RSCH.implied_targets(
                    float(r_.line), "receptions" if r_.market == "player_receptions" else "rec_yards",
                    env[m_.team]["targets"], TVD["targets_r"], float(m_.ts), float(m_.cr), float(m_.ypt),
                    SH, width=WIDTH, prices=px_, role=MODEL.role_group(m_.slot))
                _implied_cache[ck] += ("targets",)
                _edges_cache[ck] = RSCH.edges_for()
            elif r_.market == "player_rush_yds":
                j_ = si["names"].index(r_.player)
                _implied_cache[ck] = RSCH.implied_carries(
                    float(r_.line), j_, env[m_.team]["carries"], TVD["carries_r"], si["rs"], si["ypc"], resid,
                    width=WIDTH, player_resid=si["p_resid"], player_kneel=si["p_kneel"], qb_index=si["qb_i"],
                    prices=px_)
                _implied_cache[ck] += ("carries",)
                _edges_cache[ck] = RSCH.edges_for()
            else:
                _implied_cache[ck] = (None, None, None, None, None)
        imp, proj, over_needs, under_needs, unit = _implied_cache[ck]
        p_over = r_.p_model if r_.side == "Over" else 1 - r_.p_model - (0.0 if pd.isna(r_.p_push) else r_.p_push)
        nv_over = r_.p_novig if r_.side == "Over" else 1 - r_.p_novig
        s_ = sims[r_.player][next(c for k, c in {**YARD_MARKETS, **COUNT_MARKETS}.items() if k == r_.market)]
        u_ = USAGE.get(r_.player) if r_.market != "player_pass_yds" else None
        flags_ = []
        if ROLE.get(r_.player) and r_.market != "player_rush_yds" and m_.pos != "QB":
            flags_.append(ROLE[r_.player][0])
        if r_.market == "player_rush_yds" and m_.pos != "QB":
            cf_ = RSCH.carry_flag(CARRY_U.get(r_.player), WEEK - 1)   # reports/rb_takeover_check.md
            if cf_:
                flags_.append(cf_[0])
        if bool(m_.new_team):
            flags_.append(f"new team (from {m_.prior_team})")
        if bool(m_.questionable):
            flags_.append("questionable")
        flags_ += OUT_NOTE.get(m_.team, [])
        flags_ += [f"{w_['name']} ({w_['pos']}) {w_['status'].lower()}" for w_ in QWATCH.get(m_.team, [])
                   if w_["name"] != r_.player and RSCH.watch_applies(w_["pos"], r_.market, m_.pos)]
        flags_ += [b_ for b_ in BACK_NOTE.get(m_.team, []) if not b_.startswith(r_.player + " ")]
        flags_ += RSCH.margin_flags(proj, over_needs, under_needs, unit)
        research_rows.append(dict(
            player=r_.player, team=r_.team, pos=m_.pos, market=r_.market, line=float(r_.line), book=r_.book,
            price_over=r_.get("price_over"), price_under=r_.get("price_under"),
            median=float(np.median(s_)), p10=float(np.quantile(s_, 0.1)), p90=float(np.quantile(s_, 0.9)),
            p_over_model=float(p_over), p_over_book=float(nv_over),
            p_push=float(r_.p_push) if pd.notna(r_.p_push) else None,
            implied=imp, projected=proj, unit=unit, over_needs=over_needs, under_needs=under_needs,
            be_over=RSCH.breakeven(px_[0]), be_under=RSCH.breakeven(px_[1]),
            **_edges_cache.get(ck, {}),
            usage_week=(u_ or {}).get("week"), preview=PREVIEW.get(m_.team),
            snap=(u_ or {}).get("snap"), snap_base=(u_ or {}).get("snap_base"),
            ts=(u_ or {}).get("ts"), ts_base=(u_ or {}).get("ts_base"),
            cs=(u_ or {}).get("cs"), cs_base=(u_ or {}).get("cs_base"),
            tn=(u_ or {}).get("tn"), tn_base=(u_ or {}).get("tn_base"),
            cn=(u_ or {}).get("cn"), cn_base=(u_ or {}).get("cn_base"),
            **{f"bf_{k}": v for k, v in (BACKFIELD.get(r_.player) or {}).items() if k != "week"},
            flags="; ".join(flags_)))
        lk_ = RSCH.worth_a_look(research_rows[-1], WEEK - 1)
        research_rows[-1]["look"] = lk_[0] if lk_ else None
        if lk_:
            research_rows[-1]["flags"] = "; ".join(
                [f"worth a look: {lk_[0]} ({lk_[1]})"] + ([research_rows[-1]["flags"]] if research_rows[-1]["flags"] else []))
    RESEARCH = pd.DataFrame(research_rows)
    if len(RESEARCH):
        RESEARCH = RESEARCH.drop_duplicates(["player", "market", "line", "book"])
        # WORTH A LOOK goes on the logged rows (DECISIONS #156): the scorecard grades every mark
        if not SCENARIO and not R.empty and RESEARCH["look"].notna().any():
            lk = {(r.player, r.market, float(r.line), r.book): r.look for r in RESEARCH.itertuples()
                  if isinstance(r.look, str)}
            this_run = set(_now.logged_at_utc) if "logged_at_utc" in _now else set()
            R["look"] = [lk.get((r.player, r.market, float(r.line), r.book))
                         if pd.notna(r.line) and r.logged_at_utc in this_run
                         else (getattr(r, "look", None) if "look" in R.columns else None)
                         for r in R.itertuples()]
            (R[~R.book.isin(COMPARE_BOOKS)] if a.compare_books else R).to_csv(logf, index=False)
    # FANTASY POINTS ALLOWED by each defence to RBs, WRs and TEs (DECISIONS #169): context only
    _pos_map = (ros.sort_values("week").drop_duplicates("gsis_id", keep="last").set_index("gsis_id").position.to_dict()
                if {"gsis_id", "position", "week"}.issubset(ros.columns) else {})
    PA = RSCH.points_allowed(pbp, _pos_map)
    # TEAM VOLUME (DECISIONS #172): every game this season beside our projection
    TEAM_VOL_LINES = {}
    TEAM_SPREAD = {t_: RSCH.team_line(None if market_env is None else market_env.get("home_spread"), t_ == HOME)
                   for t_ in (AWAY, HOME)}
    _league_script = RSCH.league_script_shares(pbp)
    _state_mix = RSCH.league_state_mix(pbp)
    _state_n = RSCH.league_state_sample(pbp)
    TEAM_VOL_CHK, TEAM_VOL_ROWS = {}, {}
    for t_ in (AWAY, HOME):
        _rows = RSCH.team_volume(pbp, t_)
        TEAM_VOL_ROWS[t_] = _rows
        TEAM_VOL_CHK[t_] = RSCH.team_volume_check(_rows, env[t_]["targets"], env[t_]["carries"],
                                                  team_spread=TEAM_SPREAD.get(t_), league=_league_script,
                                                  mix=_state_mix)
        TEAM_VOL_LINES[t_] = RSCH.team_volume_lines(t_, _rows, TEAM_VOL_CHK[t_])
    # the defences' EPA per play and points per drive allowed (user, 2026-10-06): context only
    DEF_LINE = RSCH.defense_line(RSCH.defense_metrics(pbp), (AWAY, HOME))
    OFF_LINE = RSCH.defense_line(RSCH.offense_metrics(pbp), (AWAY, HOME), verb="gains")
    # the offensive line: how many of each team's five regular linemen are out (#178)
    _pfr = (ros.dropna(subset=["pfr_id"]).drop_duplicates("pfr_id", keep="last")
               .set_index("pfr_id")["gsis_id"].to_dict() if "pfr_id" in ros else {})
    _ros_now = {g_: (t_, st_) for t_, g_, st_ in zip(rw.team, rw.gsis_id, rw.status)}
    # the same statuses the players are priced on: the official report, Sleeper's feed where it is silent
    _rep_now = {g_: s_ for (t_, g_), s_ in inj_status.items() if t_ in (AWAY, HOME)}
    _by_name = {(t_, norm_name(n_)): g_ for t_, n_, g_ in zip(rw.team, rw.full_name, rw.gsis_id)}
    LINE_STATUS = {t_: RSCH.line_status(RSCH.line_regulars(snp[snp.season == SEASON], t_, WEEK), t_, _pfr,
                                        _ros_now, _rep_now, NOT_PLAYING, name_to_gsis=_by_name)
                   for t_ in (AWAY, HOME)}
    LINE_LINES = [l_ for t_ in (AWAY, HOME) for l_ in [RSCH.line_sentence(
        t_, LINE_STATUS[t_], report_out=bool((iw.team == t_).any() or iw.team.nunique() >= 16),
        feed=SLP_PLAYERS is not None)] if l_]
    UNIT_EFF = RSCH.unit_efficiency(pbp)        # the brief's unit-vs-unit table (context only)
    # CATCHES, YARDS AND THE LONG ONE (DECISIONS #164): the book's three receiving lines
    # read together at the whole numbers that win them, against his yards a catch
    CATCH_READ, CARRY_READ, QB_READ, RUSH_REC = {}, {}, {}, {}
    if len(RESEARCH):
        _extra_rows = (data or {}).get("sleeper_extra")
        _extra = RSCH.extra_index(_extra_rows, SLEEPER_TEAM)
        _xl = lambda kind, p_, t_: (_extra.get((kind, norm_name(p_), t_)) or {})
        if _extra_rows is None:
            SOURCES.append(("Unpriced Sleeper lines (longest catch, longest run, carries)",
                            "read beside the priced lines: catches/carries and yards", "DATA MISSING",
                            "prices did not come from Sleeper this run, so the catches and carries reads "
                            "run without them"))
        else:
            SOURCES.append(("Unpriced Sleeper lines (longest catch, longest run, carries)",
                            "read beside the priced lines: catches/carries and yards", "ok",
                            RSCH.extra_summary(_extra_rows) + "; never priced"))
        _season = prec.groupby("gsis_id")[["receptions", "rec_yards"]].sum()
        # THE LUCK LINE per player (DECISIONS #167): his own 99th-percentile play for this
        # prop, last season's plays (resources) and this season's together
        _py_path = RES / f"priors_{PRIOR}_play_yards.csv"
        # the luck-free check reads his last LUCK_WINDOW games (DECISIONS #167): last season's
        # final games from resources, then this season's, game by game, oldest first
        import build_play_yards as _BPY
        _py = pd.read_csv(_py_path) if _py_path.exists() else pd.DataFrame(columns=["gsis_id", "kind", "games"])
        _prior_games = {(str(r.gsis_id), r.kind): _BPY.parse_games(r.games) for r in _py.itertuples()}
        _cur = {"catch": RSCH.games_by_player(passes[passes.complete_pass == 1], "receiver_player_id", "receiving_yards"),
                "run": RSCH.games_by_player(rushes, "rusher_player_id", "rushing_yards"),
                "pass": RSCH.games_by_player(passes[passes.complete_pass == 1], "passer_player_id", "receiving_yards")}
        _luck = lambda gid, kind: RSCH.luck_for(_prior_games, _cur[kind], str(gid), kind)

        if not _py_path.exists():
            SOURCES.append(("Last season's play yards (luck-free check)", "each player's last 10 games, play by play",
                            "DATA MISSING", f"{_py_path.name} not found; the check uses this season's games only"))
        for (p_, t_), g_ in RESEARCH[RESEARCH.market.isin(["player_receptions", "player_reception_yds"])].groupby(
                ["player", "team"]):
            # both lines from ONE book (Sleeper first): a ratio across two books is nobody's view
            by_book = {b_: dict(zip(x_.market, x_.line)) for b_, x_ in g_.groupby("book")}
            book_ = next((b_ for b_ in sorted(by_book, key=lambda b: b != "sleeper") if len(by_book[b_]) == 2),
                         next((b_ for b_ in sorted(by_book, key=lambda b: b != "sleeper")
                               if "player_reception_yds" in by_book[b_]), None))
            if book_ is None:
                continue
            m_ = M[(M.name == p_) & (M.team == t_)].iloc[0]
            sr_ = _season.loc[m_.gsis_id] if m_.gsis_id in _season.index else None
            _tg_proj = next((float(v_) for v_ in g_.projected if pd.notna(v_)), None)   # projected targets
            lk_, lfr_ = _luck(m_.gsis_id, "catch")
            CATCH_READ[(p_, t_)] = RSCH.catch_yards_read(
                luck=lk_, luckfree_ypc=lfr_,
                proj_catches=None if _tg_proj is None else _tg_proj * float(m_.cr),
                catches_line=by_book[book_].get("player_receptions"), yards_line=by_book[book_]["player_reception_yds"],
                season_rec=None if sr_ is None else float(sr_.receptions),
                season_yds=None if sr_ is None else float(sr_.rec_yards),
                model_ypc=float(m_.ypt) / float(m_.cr) if float(m_.cr) > 0 else None,
                longest_line=_xl("longest_reception", p_, t_).get("line"))
            _cr_row = g_[(g_.market == "player_receptions") & (g_.book == book_)]
            if CATCH_READ[(p_, t_)] is not None and len(_cr_row):
                CATCH_READ[(p_, t_)]["book_fair"] = RSCH.fair_volume(
                    float(_cr_row.line.iloc[0]),
                    RSCH.fair_over(price_over=_cr_row.price_over.iloc[0], price_under=_cr_row.price_under.iloc[0]),
                    float(np.std(sims[p_]["receptions"])) if p_ in sims else None)
        _cols = {"ypc_need": "need_ypc", "ypc_mid": "mid_ypc", "ypc_season": "season_ypc",
                 "ypc_luckfree_10g": "season_ypc_luckfree", "ypc_model": "model_ypc",
                 "long_line": "longest_line", "long_rest_ypc": "rest_ypc", "ypc_read": "read"}
        _rec = lambda r: r.market in ("player_receptions", "player_reception_yds")
        for c_, k_ in _cols.items():
            RESEARCH[c_] = [(CATCH_READ.get((r.player, r.team)) or {}).get(k_) if _rec(r) else None
                            for r in RESEARCH.itertuples()]
        # the sentence itself rides on both rows, so the chat answers carry it (core/props_ask)
        RESEARCH["catch_yards"] = [RSCH.catch_yards_sentence(CATCH_READ.get((r.player, r.team))) if _rec(r) else None
                                   for r in RESEARCH.itertuples()]
        # CARRIES, YARDS AND THE LONG RUN (DECISIONS #166): the runner's version, backs and
        # receivers only -- a QB's rushing line counts kneel-downs, which muddy a yards a carry
        _rs = rushes.groupby("rusher_player_id").rushing_yards.agg(car="size", yds="sum")
        _rush = RESEARCH[(RESEARCH.market == "player_rush_yds") & (RESEARCH.pos != "QB")]
        # one rushing line per player, Sleeper's first: its carries line is Sleeper's too
        _rush = _rush.sort_values("book", key=lambda b: b != "sleeper").drop_duplicates(["player", "team"])
        for r_ in _rush.itertuples():
            m_ = M[(M.name == r_.player) & (M.team == r_.team)].iloc[0]
            att_ = _xl("rushing_attempts", r_.player, r_.team)
            sr_ = _rs.loc[m_.gsis_id] if m_.gsis_id in _rs.index else None
            lk_, lfr_ = _luck(m_.gsis_id, "run")
            CARRY_READ[(r_.player, r_.team)] = RSCH.carry_yards_read(
                luck=lk_, luckfree_ypc=lfr_,
                carries_line=att_.get("line"), yards_line=float(r_.line),
                model_ypc=float(m_.ypc) if pd.notna(m_.ypc) else None, proj_carries=r_.projected,
                season_car=None if sr_ is None else float(sr_.car), season_yds=None if sr_ is None else float(sr_.yds),
                longest_line=_xl("longest_rush", r_.player, r_.team).get("line"),
                carries_fav=RSCH.favoured(att_.get("mult_over"), att_.get("mult_under")))
            if CARRY_READ[(r_.player, r_.team)] is not None and att_.get("line") is not None:
                CARRY_READ[(r_.player, r_.team)]["book_fair"] = RSCH.fair_volume(
                    att_["line"], RSCH.fair_over(att_.get("mult_over"), att_.get("mult_under")),
                    float(np.std(sims[r_.player]["carries"])) if r_.player in sims else None)
        _runcols = {"car_line": "carries_line", "car_fav": "carries_fav", "run_ypc_mid": "mid_ypc",
                    "run_ypc_model": "model_ypc", "run_ypc_season": "season_ypc",
                    "long_run_line": "longest_line", "run_read": "read"}
        for c_, k_ in _runcols.items():
            RESEARCH[c_] = [(CARRY_READ.get((r.player, r.team)) or {}).get(k_) if r.market == "player_rush_yds" else None
                            for r in RESEARCH.itertuples()]
        RESEARCH["carry_yards"] = [RSCH.carry_yards_sentence(CARRY_READ.get((r.player, r.team)))
                                   if r.market == "player_rush_yds" else None for r in RESEARCH.itertuples()]
        # RUSHING + RECEIVING YARDS (DECISIONS #173): the book's combined line against his touches
        for (k_, n_, tm_), x_ in _extra.items():
            if k_ != "rushing_and_receiving_yards":
                continue
            hit = M[(M.name.map(norm_name) == n_) & (M.team == tm_)]
            if hit.empty or hit.iloc[0]["name"] not in sims:
                continue
            m_ = hit.iloc[0]
            sm_ = sims[m_["name"]]
            lr_, rr_ = _luck(m_.gsis_id, "run")
            lc_, cr_ = _luck(m_.gsis_id, "catch")
            RUSH_REC[(m_["name"], tm_)] = RSCH.rush_rec_read(
                line=x_["line"], mult_over=x_.get("mult_over"), mult_under=x_.get("mult_under"),
                proj_carries=float(np.mean(sm_["carries"])), proj_catches=float(np.mean(sm_["receptions"])),
                run_rate=rr_ if rr_ is not None else (float(m_.ypc) if pd.notna(m_.ypc) else None),
                catch_rate=cr_ if cr_ is not None else (float(m_.ypt) / float(m_.cr) if float(m_.cr) > 0 else None),
                run_luck=lr_, catch_luck=lc_, rates_luck_free=rr_ is not None and cr_ is not None,
                sd=float(np.std(np.asarray(sm_["rush_yards"]) + np.asarray(sm_["rec_yards"]))),
                p_model_over=float(np.mean(np.asarray(sm_["rush_rec_yards"]) > float(x_["line"]))),
                book_carries=_xl("rushing_attempts", m_["name"], tm_).get("line"),
                book_catches=next((float(r.line) for r in RESEARCH[(RESEARCH.player == m_["name"])
                                                                   & (RESEARCH.market == "player_receptions")
                                                                   & (RESEARCH.book == "sleeper")].itertuples()), None))
        # on his rushing row, or on his receiving-yards row when he has no rushing line
        _has_rush = set(zip(RESEARCH.loc[RESEARCH.market == "player_rush_yds", "player"],
                            RESEARCH.loc[RESEARCH.market == "player_rush_yds", "team"]))
        RESEARCH["rush_rec"] = [RSCH.rush_rec_sentence(RUSH_REC.get((r.player, r.team)))
                                if (r.market == "player_rush_yds"
                                    or (r.market == "player_reception_yds" and (r.player, r.team) not in _has_rush))
                                else None for r in RESEARCH.itertuples()]
        # COMPLETIONS AND YARDS (DECISIONS #170): the quarterback's version
        _qbr = RESEARCH[RESEARCH.market == "player_pass_yds"]
        _qbr = _qbr.sort_values("book", key=lambda b: b != "sleeper").drop_duplicates(["player", "team"])
        for r_ in _qbr.itertuples():
            if r_.player not in sims or "pass_yards" not in sims[r_.player]:
                continue
            m_ = M[(M.name == r_.player) & (M.team == r_.team)].iloc[0]
            # our completions: the receivers' catches in this simulation plus the depth bucket's,
            # times the starter's usual share -- the mean of the draw simulate_qb_completions makes
            _team = [n_ for n_ in M[M.team == r_.team].name if n_ != r_.player and n_ in sims]
            _oth = pass_inputs.get(r_.team, (None, None))[1]
            _cr = float(P["other_receiver_rates"]["catch_rate"])
            _proj = RSCH.projected_completions([float(np.mean(sims[n_]["receptions"])) for n_ in _team],
                                               None if _oth is None else float(np.mean(_oth)), _cr,
                                               float(np.mean(P["qb_starter_pass_share_quantiles"])))
            lk_, lfr_ = _luck(m_.gsis_id, "pass")
            cp_ = _xl("pass_completions", r_.player, r_.team)
            QB_READ[(r_.player, r_.team)] = RSCH.qb_yards_read(
                completions_line=cp_.get("line"), yards_line=float(r_.line), proj_completions=_proj,
                model_ypc=float(np.mean(sims[r_.player]["pass_yards"])) / _proj if _proj > 0 else None,
                luck=lk_, luckfree_ypc=lfr_,
                longest_line=_xl("longest_passing_completion", r_.player, r_.team).get("line"),
                completions_fav=RSCH.favoured(cp_.get("mult_over"), cp_.get("mult_under")),
                attempts_line=_xl("passing_attempts", r_.player, r_.team).get("line"))
            if QB_READ[(r_.player, r_.team)] is not None and cp_.get("line") is not None:
                # the spread of the team's catches across the simulation, at the starter's share
                _sum = sum(np.asarray(sims[n_]["receptions"], dtype=float) for n_ in _team) if _team else None
                if _sum is not None and _oth is not None:
                    _sum = _sum + np.asarray(_oth, dtype=float) * _cr       # the depth bucket's catches (mean rate)
                QB_READ[(r_.player, r_.team)]["book_fair"] = RSCH.fair_volume(
                    cp_["line"], RSCH.fair_over(cp_.get("mult_over"), cp_.get("mult_under")),
                    None if _sum is None else float(np.std(_sum)) * float(np.mean(P["qb_starter_pass_share_quantiles"])))
        RESEARCH["qb_yards"] = [RSCH.qb_yards_sentence(QB_READ.get((r.player, r.team)))
                                if r.market == "player_pass_yds" else None for r in RESEARCH.itertuples()]
    RESEARCH.to_csv(OUT / f"research_{slug}.csv", index=False)

    # ---------- 8b/9. report, written for a casual reader ----------
    MKT = {"player_receptions": "catches", "player_reception_yds": "receiving yards",
           "player_rush_yds": "rushing yards", "player_anytime_td": "to score a touchdown",
           "player_pass_yds": "passing yards", "player_rush_reception_yds": "rushing + receiving yards"}

    def pct(x): return f"{100*x:.0f}%"
    def odds_words(a):
        a = int(a)
        return f"+{a} (bet $100 to win ${a})" if a > 0 else f"{a} (bet ${-a} to win $100)"
    def in_ten(x): return f"about {round(10*x)} in 10"
    def share_words(x): return f"{pct(x)} of the team's"

    def verdict_for(r, m):
        g = abs(r.gap)
        if m.questionable:
            return ("Injury question", "He's listed Questionable. This is priced as if he plays his normal role; "
                                       "if he sits, the prop voids. The 'if he's out' section shows what changes for "
                                       "everyone else. Your call.")
        if m.new_team:
            return ("New team, thin data", f"{m['name']} just moved from {m.prior_team}. We have one game with his new team; "
                    f"the sportsbook has watched practice, the depth chart and the game plan. When we disagree here, they're usually right.")
        if g > 0.10 and r.gap > 0:
            return ("Book probably knows something", "We like this side a lot more than the book does. A gap this big, from a model with "
                    "one week of this season's data, almost always means the book is pricing an injury, a reduced role or a matchup "
                    "we can't see. Not a bet.")
        if g > 0.10 and r.gap < 0:
            return ("Book expects more than his history", "The book is more bullish on him than his numbers alone justify. That usually "
                    "means they expect a bigger role or more scoring in this particular game than his averages show. "
                    "Our number is the cautious one here, and the price already reflects the book's view. Not a bet.")
        if g >= 0.03:
            return ("Small disagreement", "We lean the other way from the book, but by an amount our model can't tell apart from noise. Log it, don't bet it.")
        return ("Agree", "Our number and the book's are basically the same. Nothing here.")

    def explain(r, m):
        e = env[m.team]; ev = m.evidence; out = []
        withheld = False     # True for a v1 anytime price: no fair value is claimed
        book = {"draftkings": "DraftKings", "fanduel": "FanDuel", "sleeper": "Sleeper"}.get(r.book, str(r.book).title())
        if r.market == "player_anytime_td":
            out.append(f"**What the book says.** {book} pays {odds_words(r.price)} that he scores. "
                       f"That price implies {in_ten(r.p_novig)} ({pct(r.p_novig)}). "
                       + ("The 'won't score' side is priced too, so the book's cut is stripped out of that number."
                          if td_two_sided else
                          "No 'won't score' price is offered, so the book's cut is baked in and the true market number is a little lower."))
            if V1TD is not None and m.gsis_id in V1TD.index:
                v = V1TD.loc[m.gsis_id]
                out.append(f"**How we got our number ({TDV1.LABEL}, prototype).** {m.team} should score about "
                           f"{v['mu']:.1f} offensive touchdowns; the count runs slightly tighter than a Poisson "
                           f"because a drive can end in at most one. {m['name']}'s share of each of them is "
                           f"{pct(v['q'])}: his part of the carries from the 5 in, the other carries, and the "
                           f"red-zone and deeper targets, blended toward last season's role, with any absent "
                           f"teammate's share handed to the players who are active. That is "
                           f"{in_ten(r.p_model)} ({pct(r.p_model)}) to score at least once. No fair price is shown: "
                           "the model is not yet tested against posted lines.")
                withheld = True
            else:
                lam = td_lambda(m)
                t_ = ev.get("i10_target_share", {}); c_ = ev.get("i10_carry_share", {})
                hist = []
                if t_ and pd.notna(t_.get('own_prior')) and t_['own_prior'] > 0.02:
                    hist.append(f"last season {pct(t_['own_prior'])} of the goal-line throws")
                if c_ and pd.notna(c_.get('own_prior')) and c_['own_prior'] > 0.02:
                    hist.append(f"last season {pct(c_['own_prior'])} of the goal-line carries")
                if t_ and pd.notna(t_.get('cur_rate')) and t_['cur_den'] > 0 and (t_['cur_num'] > 0 or m.i10ts > 0.05):
                    hist.append(f"this season {int(t_['cur_num'])} of {int(t_['cur_den'])} goal-line throws")
                if c_ and pd.notna(c_.get('cur_rate')) and c_['cur_den'] > 0 and (c_['cur_num'] > 0 or m.i10rs > 0.05):
                    hist.append(f"this season {int(c_['cur_num'])} of {int(c_['cur_den'])} goal-line carries")
                gl = e["pass_td"]*F_PASS_IN*m.i10ts + e["rush_td"]*F_RUSH_IN*m.i10rs
                lg = lam - gl
                out.append(f"**How we got our number.** {m.team} should score about {e['pass_td']:.1f} passing and {e['rush_td']:.1f} rushing TDs "
                           f"in a typical game. About half of passing TDs and a quarter of rushing TDs are long plays from outside the 10, "
                           f"the rest are punched in from the goal line, and the two get shared out differently. "
                           f"Goal line: we expect {m['name']} to get {pct(m.i10ts)} of the throws and {pct(m.i10rs)} of the carries there"
                           + (f" ({'; '.join(hist)})" if hist else "")
                           + f", worth {gl:.2f} TDs. Long plays: his overall share of the offense ({pct(m.ts)} of throws, {pct(m.rs)} of runs) "
                           f"is worth another {lg:.2f}. Total {lam:.2f} expected TDs, which is {in_ten(r.p_model)} ({pct(r.p_model)}) to score at least once.")
                out.append(f"**Fallback.** This is the FALLBACK model ({TDV1.LABEL} could not run here), and it runs low: in the "
                           "2024-25 backtest it predicted a 13.5% scoring rate against 14.8% actual, about 1.3 "
                           "points too low on average, so a gap in the book's favour is partly ours.")
        elif r.market in ("player_receptions", "player_reception_yds"):
            thing = "catches" if r.market == "player_receptions" else "receiving yards"
            out.append(f"**What the book says.** {book} sets the line at **{r.line} {thing}**, {r.side.lower()} priced at {odds_words(r.price)}. "
                       f"With the book's cut removed, that's {in_ten(r.p_novig)} ({pct(r.p_novig)}) on the {r.side.lower()}.")
            ts_ = ev.get("target_share", {}); cr_ = ev.get("catch_rate", {})
            parts = [f"{m.team} should throw about {e['targets']:.0f} times."]
            hist = []
            if ts_ and pd.notna(ts_.get("own_prior")):
                hist.append(f"last season he got {pct(ts_['own_prior'])} of his team's throws over {int(ts_['n_prior'])} games")
            if ts_ and pd.notna(ts_.get("cur_rate")) and ts_["cur_den"] > 0:
                hist.append(f"this season he has {int(ts_['cur_num'])} of {int(ts_['cur_den'])} ({pct(ts_['cur_rate'])})")
            if hist:
                parts.append("His share: " + "; ".join(hist) + f". A typical {m.slot} gets {pct(ts_['slot_prior'])}.")
            if ts_ and ts_.get("scaled"):
                parts.append("Because he changed teams, we scaled that by how many snaps he's playing now versus last year.")
            f_sr = ts_.get("snap_react") if ts_ else None
            u_ex = USAGE.get(m["name"])
            if f_sr and abs(f_sr - 1.0) > 0.005 and u_ex:
                parts.append(f"Last week he played {pct(u_ex['snap'])} of the snaps against {pct(u_ex['snap_base'])} "
                             f"in his earlier weeks, which moves that share by x{f_sr:.2f} (the snap-change rule, "
                             f"reports/snap_react.md).")
            parts.append(f"Blending those, we project **{pct(m.ts)}** of the throws = about **{e['targets']*m.ts:.1f} targets**, "
                         f"and he catches roughly {pct(m.cr)} of his targets, so about **{m.mu_rec:.1f} catches**"
                         + (f" for about **{r.model_mean:.0f} yards**" if r.market == "player_reception_yds" else "") + ".")
            parts.append(f"Run that 20,000 times with normal game-to-game swings and he lands **{r.side.lower()} {r.line}** {in_ten(r.p_model)} ({pct(r.p_model)}).")
            out.append("**How we got our number.** " + " ".join(parts))
        elif r.market == "player_pass_yds":
            out.append(f"**What the book says.** {book} sets the line at **{r.line} passing yards**, {r.side.lower()} priced at {odds_words(r.price)}. "
                       f"With the book's cut removed, that's {in_ten(r.p_novig)} ({pct(r.p_novig)}) on the {r.side.lower()}.")
            out.append(f"**How we got our number.** {m.team} should throw about {e['targets']:.0f} times. His passing yards are "
                       f"his receivers' yards in the same simulated games -- each receiver's share, catch rate and yards per "
                       f"target, plus the throws to depth players -- times the share of the team's passing yards a starter "
                       f"usually keeps (an injury or a benching counts against him, as the book settles it): about "
                       f"**{r.model_mean:.0f} yards**. He lands **{r.side.lower()} {r.line}** {in_ten(r.p_model)} ({pct(r.p_model)}).")
        else:
            out.append(f"**What the book says.** {book} sets the line at **{r.line} rushing yards**, {r.side.lower()} priced at {odds_words(r.price)}. "
                       f"With the book's cut removed, that's {in_ten(r.p_novig)} ({pct(r.p_novig)}) on the {r.side.lower()}.")
            rs_ = ev.get("rush_share", {}); yp_ = ev.get("ypc", {})
            parts = [f"{m.team} should run about {e['carries']:.0f} times."]
            hist = []
            if rs_ and pd.notna(rs_.get("own_prior")):
                hist.append(f"last season he took {pct(rs_['own_prior'])} of his team's carries over {int(rs_['n_prior'])} games")
            if rs_ and pd.notna(rs_.get("cur_rate")) and rs_["cur_den"] > 0:
                hist.append(f"this season {int(rs_['cur_num'])} of {int(rs_['cur_den'])} ({pct(rs_['cur_rate'])})")
            if hist:
                parts.append("His share: " + "; ".join(hist) + ".")
            parts.append(f"We project **{pct(m.rs)}** of the carries = about **{m.mu_car:.1f} carries** at about {m.ypc:.1f} yards each "
                         f"= about **{r.model_mean:.0f} yards**. Individual carries are drawn from last season's real distribution, so "
                         f"breakaway runs and stuffs are both in there.")
            parts.append(f"He lands **{r.side.lower()} {r.line}** {in_ten(r.p_model)} ({pct(r.p_model)}).")
            out.append("**How we got our number.** " + " ".join(parts))
        label, text = verdict_for(r, m)
        if label in ("Injury question", "New team, thin data"):
            out.append(f"**Caution: {label.lower()}.** {text.replace(' Your call.', '')}")
        return out

    # WHAT THE USER READS (DECISIONS #190): anytime TDs are deferred -- priced, logged and
    # graded (R keeps them; the shadow log is written from R), but every table the user
    # reads is built from RD, which drops them unless the run asked for them (--markets td)
    show_td = bool(MARKETS) and "player_anytime_td" in MARKETS
    RD = R if (show_td or R.empty) else R[R.market != "player_anytime_td"]
    top = pd.DataFrame()
    if not RD.empty:
        top = (RD.sort_values("gap", key=abs, ascending=False)
                .drop_duplicates(subset=["market", "player", "side"]).head(12))

    hrs = (kick - pd.Timestamp.now(tz="UTC")).total_seconds() / 3600
    kick_local = kick.tz_convert("US/Pacific") if False else None   # avoid tz dependency

    # ---------- 8c. THE BETTING CARD: explicit line thresholds ----------
    # For every prop, the line at which the simulated probability at standard -110 pricing
    # clears the edge rule (ER >= min_er, i.e. p_win >= (1+min_er)/(1+100/110) ~ 0.541 at 3%).
    # Above the Under threshold, take the Under; below the Over threshold, take the Over;
    # in between, no play. This is the "if the line is at X" rule the report exists to give.
    # Still exploratory per the registry, stated once at the top, not on every row.
    P_NEEDED = (1 + a.min_er) / (1 + 100 / 110)
    CARD_MARKETS = [("player_receptions", "receptions", "catches", 0.5),
                    ("player_reception_yds", "rec_yards", "rec yds", 0.5),
                    ("player_rush_yds", "rush_yards", "rush yds", 0.5),
                    ("player_pass_yds", "pass_yards", "pass yds", 0.5)]
    if MARKETS:
        CARD_MARKETS = [c for c in CARD_MARKETS if c[0] in MARKETS]

    def thresholds(samples, step):
        """Smallest half-integer line where P(under) >= P_NEEDED, and largest where
        P(over) >= P_NEEDED. Returns (under_at_or_above, over_at_or_below), either may be None."""
        lo = float(np.floor(np.percentile(samples, 2))) - 0.5
        hi = float(np.ceil(np.percentile(samples, 98))) + 0.5
        grid = np.arange(max(lo, 0.5), hi + step, 1.0)
        under_thr = over_thr = None
        for Lx in grid:
            if (samples < Lx).mean() >= P_NEEDED:
                under_thr = float(Lx); break
        for Lx in grid[::-1]:
            if (samples > Lx).mean() >= P_NEEDED:
                over_thr = float(Lx); break
        return under_thr, over_thr

    # The whole priced row is carried, not just the number. The card used to
    # keep only (book, line) and then decide playability from the sample
    # distribution against an ASSUMED -110, while the real price sat unused in
    # R. That is the defect `eligibility` exists to remove.
    book_lines = {}
    if not R.empty:
        for rr in R[R.market.isin([m for m, _, _, _ in CARD_MARKETS])].itertuples():
            book_lines.setdefault((rr.player, rr.market), []).append(
                (rr.book, rr.line, rr))

    card_rows = []
    for _, m in M.iterrows():
        for mkey, col, label, step in CARD_MARKETS:
            if mkey == "player_rush_yds" and m.pos == "QB" and (
                    not QB_RUSH_ON or STARTER_QB.get(m.team) != m["name"]):
                continue
            if col not in sims[m["name"]]:
                continue           # passing yards: the starting QB only
            samp = sims[m["name"]][col]
            if samp.mean() < 0.3:
                continue
            u_thr, o_thr = thresholds(samp, step)
            lines = book_lines.get((m["name"], mkey), [])
            bl = None; bk = ""; brow = None
            if lines:
                bk, bl, brow = sorted(lines, key=lambda x: x[0] != "draftkings")[0]
            call, why, eligible, priced = "no line posted", "", False, False
            if brow is not None:
                # The side comes from the priced row, which chose it by
                # p_model against the no-vig probability. Deriving it here
                # from the distribution thresholds instead could name the
                # opposite side to the one the record logged.
                v = eligibility.evaluate(
                    mkey, p_win=float(brow.p_model), price=float(brow.price),
                    gap=float(brow.gap),
                    p_push=float(getattr(brow, "p_push", 0.0) or 0.0),
                    new_team=bool(m.new_team), questionable=bool(m.questionable),
                    min_gap=a.min_gap, min_er=a.min_er, er=float(brow.ER))
                eligible, priced, why = v.eligible, v.priced, v.why
                call = f"{str(brow.side).upper()} {bl}" if priced else "no play"
            card_rows.append(dict(player=m["name"], team=m.team, prop=label, book=bk, book_line=bl,
                                  our_median=float(np.median(samp)),
                                  under_at=u_thr, over_at=o_thr, call=call, why=why,
                                  price=float(brow.price) if brow is not None else None,
                                  er=float(brow.ER) if brow is not None else None,
                                  eligible=eligible, would_play_if_validated=priced,
                                  strength=abs((samp < bl).mean() - 0.5) if bl is not None else 0))
    # the columns are fixed so an empty card (a --markets td run prices no yardage) still has them
    CARD = pd.DataFrame(card_rows, columns=["player", "team", "prop", "book", "book_line", "our_median",
                                            "under_at", "over_at", "call", "why", "price", "er",
                                            "eligible", "would_play_if_validated", "strength"])
    if not CARD.empty:
        # `is_play` was a string-prefix test on rendered display text. It is
        # now the enforced verdict, and the price-aware "would play if the
        # model were validated" is kept beside it.
        CARD["is_play"] = CARD.eligible
        CARD = CARD.sort_values(["would_play_if_validated", "strength"],
                                ascending=[False, False])
        CARD.to_csv(OUT / f"betting_card_{slug}.csv", index=False)

    L = []
    L.append(f"# {AWAY} at {HOME}")
    L.append(f"### {SEASON} Week {WEEK} · {G.gameday} {G.gametime} ET · {G.stadium}\n")
    for aq_ in AUTO_QB:
        L.append(f"**{aq_['team']}'s starting quarterback: {aq_['starter']}.** {aq_['out']} is out"
                 + (f" ({aq_['why']})" if aq_['why'] else "") + f", so the next quarterback on the depth chart "
                 f"is priced as the starter (his kneel-downs, passing share and rushing).\n")
    if ROLE_OVERRIDES:
        L.append("**Role what-if, not the board:** " + "; ".join(
            f"{ro['name']} ({ro['team']}) priced as {ro['slot']}"
            + (f" (the depth chart has him at {ro['was']})" if ro["was"] else " (no depth-chart slot)")
            + "".join(f"; {o_['name']} still holds {ro['slot']} too" for _, o_ in
                      pop[(pop.team == ro["team"]) & (pop.slot == ro["slot"]) & ~pop.excluded
                          & (pop.gsis_id != ro["gsis_id"])].iterrows())
            for ro in ROLE_OVERRIDES)
            + ". His prior is that slot's role average, blended with his own games; nobody else moves. "
              "Never recorded.\n")
    L.append(research_statement(RESEARCH, GATE) + "\n")

    # ---------- player-by-player research rows, in depth-chart order ----------

    SLOT_ORDER = {"QB1": 0, "RB1": 1, "WR1": 2, "WR2": 3, "TE1": 4, "WR3": 5, "RB2": 6, "PROXY": 7}
    def pct(x): return f"{100*x:.0f}%"
    def odds_str(a): a = int(a); return f"+{a}" if a > 0 else f"{a}"
    td_book = {}
    if not R.empty and show_td:
        for _, rr in R[R.market == "player_anytime_td"].iterrows():
            td_book.setdefault(rr.player, []).append((rr.book, rr.price, rr.p_novig))

    # his games this season, per team and week, for the volume chance's "games he beat it" (attempts as
    # research.qb_workload counts them: no sacks, no spikes)
    _tg_g = passes.groupby(["receiver_player_id", "posteam", "week"]).agg(
        tg=("play_type", "size"), cat=("complete_pass", "sum"), ryd=("receiving_yards", "sum"),
        lng=("receiving_yards", "max"))
    _ru_g = rushes.groupby(["rusher_player_id", "posteam", "week"]).agg(car=("play_type", "size"),
                                                                       uyd=("rushing_yards", "sum"),
                                                                       lng=("rushing_yards", "max"))
    _pa = pbp[(pbp.play_type == "pass") & pbp.passer_player_id.notna()] if "passer_player_id" in pbp else pbp.iloc[0:0]
    if "sack" in _pa:
        _pa = _pa[_pa["sack"].fillna(0) != 1]
    if "pass_attempt" in _pa:
        _pa = _pa[_pa["pass_attempt"].fillna(0) == 1]
    _pa_g = _pa.groupby(["passer_player_id", "posteam", "week"]).agg(att=("play_type", "size"),
                                                                     pyd=("passing_yards", "sum"),
                                                                     cmp=("complete_pass", "sum"),
                                                                     lng=("passing_yards", "max"))

    def games_of(gid, t, kind):
        """[(volume, outcome)] for his games this season with team t, oldest first."""
        def by_week(frame, cols):
            try:
                x = frame.xs((gid, t), level=(0, 1))[cols].fillna(0)
            except KeyError:
                return {}
            return {w: tuple(float(v) for v in r) for w, r in zip(x.index, x.to_numpy())}
        parts = {"player_reception_yds": [(_tg_g, ["cat", "ryd"])], "player_receptions": [(_tg_g, ["tg", "cat"])],
                 "player_rush_yds": [(_ru_g, ["car", "uyd"])], "player_pass_yds": [(_pa_g, ["cmp", "pyd"])],
                 "player_rush_reception_yds": [(_ru_g, ["car", "uyd"]), (_tg_g, ["cat", "ryd"])]}.get(kind, [])
        tot = {}
        for frame, cols in parts:               # combined: carries and catches added week by week
            for w, (v, y) in by_week(frame, cols).items():
                a_ = tot.get(w, (0.0, 0.0))
                tot[w] = (a_[0] + v, a_[1] + y)
        return [tot[w] for w in sorted(tot)]

    def season_facts(gid, t, frame):
        """(games, longest play) for his games this season with team t in one per-game frame."""
        try:
            x = frame.xs((gid, t), level=(0, 1))
        except KeyError:
            return 0, None
        return len(x), (float(x.lng.max()) if x.lng.notna().any() else None)

    def book_lines_of(mk, nm, t):
        """The book's lines read beside a priced one (DECISIONS #164, #166, #170): what the catches and
        yards lines ask together, the carries line and the side it favours, the longest-play lines."""
        g = lambda v: f"{float(v):g}" if v is not None and v == v else None
        bits = []
        if mk == "player_reception_yds":
            cr_ = CATCH_READ.get((nm, t)) or {}
            if g(cr_.get("catches_line")) and cr_.get("mid_ypc"):
                bits.append(f"catches {g(cr_['catches_line'])}: {float(cr_['mid_ypc']):.1f} a catch asked")
            if g(cr_.get("longest_line")):
                bits.append(f"longest catch {g(cr_['longest_line'])}")
        elif mk == "player_rush_yds":
            cy_ = CARRY_READ.get((nm, t)) or {}
            if g(cy_.get("carries_line")):
                bits.append(f"carries {g(cy_['carries_line'])}" + (f", {cy_['carries_fav']} favoured"
                                                                   if cy_.get("carries_fav") else ""))
            if g(cy_.get("longest_line")):
                bits.append(f"longest run {g(cy_['longest_line'])}")
        elif mk == "player_pass_yds":
            q_ = QB_READ.get((nm, t)) or {}
            if g(q_.get("longest_line")):
                bits.append(f"longest completion {g(q_['longest_line'])}")
        return "; ".join(bits) or None

    def volume_inputs(m, t, rows, nm):
        """The volume chance for his priced markets (research.volume_cells, shown in the card's table). The engine's volume
        (catches, carries, completions; targets for receptions) against the efficiency the reader judges
        (yards a catch, a carry, a completion). Every row names the games behind its rate: the
        luck-capped window (last season's games and this season's), this season uncapped with its
        longest play, the engine's own rate."""
        s_ = sims.get(nm) or {}
        out, seen = [], set()
        cap = lambda luck, play, word: RSCH.capped_label(luck, play, word, PRIOR, SEASON)
        mean_ = lambda k: float(np.mean(s_[k])) if k in s_ else 0.0
        per = lambda num, den: num / den if den > 0 else None

        def season_label(frame, play):
            n_, lng_ = season_facts(m.gsis_id, t, frame)
            longest = f", longest {play} {lng_:.0f}" if lng_ is not None else ""
            return f"{SEASON} so far, uncapped ({n_} games{longest})"

        def season_rate(frame, vol, yds):
            try:
                x = frame.xs((m.gsis_id, t), level=(0, 1))
            except KeyError:
                return None
            return per(float(x[yds].fillna(0).sum()), float(x[vol].sum()))

        for r in rows:
            mk = r["market"]
            if mk in seen or mk not in RSCH.VOLUME_UNIT:
                continue
            seen.add(mk)
            games = games_of(m.gsis_id, t, mk)
            tot = lambda i: sum(g[i] for g in games)
            season = (tot(1) / tot(0)) if games and tot(0) > 0 else None
            mvol, rates, draws, vtext = None, [], None, None
            if mk == "player_reception_yds" and "receptions" in s_:
                cr_ = CATCH_READ.get((nm, t)) or {}
                rates = [("capped", cap(cr_.get("luck"), "catches", "catches"), cr_.get("season_ypc_luckfree")),
                         ("season", season_label(_tg_g, "catch"), season),
                         ("engine", None, per(mean_("rec_yards"), mean_("receptions")))]
                draws = s_["receptions"]
                vtext = f"{mean_('targets'):.1f} targets -> {mean_('receptions'):.1f} catches"
            elif mk == "player_receptions" and "targets" in s_:
                rates = [("season", f"{SEASON} so far ({season_facts(m.gsis_id, t, _tg_g)[0]} games)", season),
                         ("engine", None, float(m.cr))]
                draws = s_["targets"]
                vtext = f"{mean_('targets'):.1f} targets"
            elif mk == "player_rush_yds" and "carries" in s_:
                cy_ = CARRY_READ.get((nm, t)) or {}
                rates = [("capped", cap(cy_.get("luck"), "runs", "carries"), cy_.get("season_ypc_luckfree")),
                         ("season", season_label(_ru_g, "run"), season),
                         ("engine", None, per(mean_("rush_yards"), mean_("carries")))]
                draws, mvol = s_["carries"], cy_.get("carries_line")
                vtext = f"{mean_('carries'):.1f} carries"
            elif mk == "player_rush_reception_yds" and "carries" in s_ and "receptions" in s_:
                # two efficiencies: yards a carry and yards a catch, on the engine's carries and catches
                rr_ = RUSH_REC.get((nm, t)) or {}
                capped = (rr_.get("run_rate"), rr_.get("catch_rate")) if rr_.get("rates_luck_free") else None
                rates = [("capped", cap(rr_.get("run_luck"), "runs", "carries") + "; "
                          + cap(rr_.get("catch_luck"), "catches", "catches")[0].lower()
                          + cap(rr_.get("catch_luck"), "catches", "catches")[1:], capped),
                         ("season", f"{SEASON} so far, uncapped ({len(games)} games)",
                          (season_rate(_ru_g, "car", "uyd"), season_rate(_tg_g, "cat", "ryd"))),
                         ("engine", None, (per(mean_("rush_yards"), mean_("carries")),
                                           per(mean_("rec_yards"), mean_("receptions"))))]
                draws = (s_["carries"], s_["receptions"])
                vtext = f"{mean_('carries'):.1f} carries + {mean_('receptions'):.1f} catches"
            elif mk == "player_pass_yds" and "completions" in s_ and "pass_yards" in s_:
                # the simulated starter only. QB luck cap (user, 2026-10-07): his capped yards a
                # completion over his last 10 games
                q_ = QB_READ.get((nm, t)) or {}
                rates = [("capped", cap(q_.get("luck"), "completions", "completions"), q_.get("luckfree_ypc")),
                         ("season", season_label(_pa_g, "completion"), season),
                         ("engine", None, per(mean_("pass_yards"), mean_("completions")))]
                draws = s_["completions"]
                vtext = f"{mean_('completions'):.1f} completions"
                mvol = _xl("pass_completions", nm, t).get("line")      # the market's completions line, if posted
            if draws is None and not book_lines_of(mk, nm, t):
                continue
            out.append({"market": mk, "line": r["line"], "volume_text": vtext, "book_lines": book_lines_of(mk, nm, t),
                        "cells": RSCH.volume_cells(mk, r["line"], draws, rates, games, mvol) if draws is not None
                        else None})
        return out

    def card_inputs(m, t, mine, rr_read):
        """Everything one player's card shows, from what this run already built."""
        nm = m["name"]
        mine = mine.sort_values("book", key=lambda b: b != "sleeper", kind="stable")
        rows = mine.to_dict("records")
        book = rows[0]["book"] if rows else ("sleeper" if rr_read else None)
        quoted = None
        if len(R) and "last_update" in R and book:
            lu_ = R[(R.player == nm) & (R.book == book)].last_update.dropna()
            quoted = str(lu_.max())[:16].replace("T", " ") + " UTC" if len(lu_) else None
        ev = m.evidence
        ts_, rs_ = ev.get("target_share", {}), ev.get("rush_share", {})
        prior = {"ts": ts_.get("own_prior"), "rs": rs_.get("own_prior"), "games": ts_.get("n_prior") or rs_.get("n_prior"),
                 "team": m.prior_team, "new_team": bool(m.new_team)}
        cr_ = CATCH_READ.get((nm, t)) or {}
        season = {"games": len(WEEK_SH.get(nm, [])),
                  "targets": ts_.get("cur_num") if pd.notna(ts_.get("cur_num")) else None,
                  "catches": cr_.get("season_rec"),
                  "carries": rs_.get("cur_num") if m.pos in ("RB", "FB", "HB") and pd.notna(rs_.get("cur_num")) else None}
        u_ = USAGE.get(nm)
        qbs = None
        if u_:
            by_w = {r_["week"]: r_["qb"] for r_ in TEAM_VOL_ROWS.get(t, [])}
            earlier = [w_[0] for w_ in WEEK_SH.get(nm, [])][:-1]
            qbs = (list(dict.fromkeys(by_w[w_] for w_ in earlier if by_w.get(w_))), by_w.get(u_["week"]))
        qb = None
        if m.pos == "QB":
            q_ = QB_READ.get((nm, t)) or {}
            att_ = _xl("passing_attempts", nm, t)
            qb = {"team_passes": (TEAM_VOL_CHK.get(t) or {}).get("our_att"),
                  "games": RSCH.qb_workload(pbp, m.gsis_id), "proj_cmp": q_.get("proj"),
                  "cmp_line": q_.get("completions_line"), "cmp_fav": q_.get("completions_fav"),
                  "att_line": att_.get("line"), "att_fav": RSCH.favoured(att_.get("mult_over"), att_.get("mult_under")),
                  "gauge": q_.get("gauge"), "gauge_rate": q_.get("gauge_rate"),
                  "luck_games": (q_.get("luck") or {}).get("games")}
        shadow = []
        if nm in SHADOW_RUSH and len(R) and "p_over_hist_carries" in R:
            for _, x_ in R[(R.player == nm) & (R.market == "player_rush_yds")
                           & R.p_over_hist_carries.notna()].drop_duplicates("line").iterrows():
                shadow.append({"line": x_.line, "p_board": x_.p_over_board, "p_mkt": x_.p_over_hist_carries,
                               "car_from": float(np.mean(sims[nm]["carries"])), "car_to": x_.hist_carries})
        watch = []
        if m.new_team:
            watch.append(f"changed teams ({m.prior_team} to {t}); his role here has few games behind it")
        if m.questionable:
            watch.append("listed Questionable; priced as if he plays his normal role; whether his own prop voids "
                         "if he sits depends on the provider's rules")
        if m.role_scale != 1.0:
            watch.append(f"snap share on the new team scaled his projection by {m.role_scale:.2f}")
        rf_ = ROLE.get(nm)
        if rf_ and m.pos != "QB":
            watch.append(f"receiving {rf_[0]}: {rf_[1]}")
        for f_ in "; ".join(str(x) for x in mine.get("flags", pd.Series(dtype=object)).dropna().unique()).split("; "):
            if f_ and f_ != "questionable" and not f_.startswith(("new team", "thin:")) and f_ not in watch \
                    and not (rf_ and f_ == rf_[0]):
                watch.append(f_)
        return {"name": nm, "team": t, "slot": m.slot, "pos": m.pos, "rows": rows, "book": book, "quoted": quoted,
                "volume": volume_inputs(m, t, rows, nm),
                "unpriced_read": RSCH.rush_rec_sentence(rr_read) if not rows and rr_read else None,
                "usage": u_, "backfield": BACKFIELD.get(nm), "qbs": qbs, "prior": prior, "season": season,
                "qb": qb, "shadow": shadow,
                "matchup": RSCH.matchup_sentence(PA, HOME if t == AWAY else AWAY, m.pos), "watch": watch}

    L.append(RSCH.CARD_LEGEND + "\n")
    # the live record and the backtest calibration, once (they were the same on every card)
    _cal = RSCH.calibration_block(set(RESEARCH.market) if len(RESEARCH) else set(),
                                  {t_: env[t_]["implied_points"] for t_ in (AWAY, HOME)
                                   if env[t_].get("implied_points") is not None},
                                  list(M[M.name.isin(set(RESEARCH.player))].slot) if len(RESEARCH) else [])
    if _cal:
        L.append("\n".join(_cal) + "\n")
    for t, side_label in [(AWAY, "away"), (HOME, "home")]:
        L.append(f"## {t} ({side_label})\n")
        e = env[t]
        td_note = (f" (anchored to the market's implied {e['implied_points']:.1f} points; history blend said {e['td_total_history']:.1f})"
                   if e.get("td_anchor") == "market" else " (history blend; market anchor unavailable)")
        L.append(f"Offense projects about {e['targets']:.0f} throws, {e['carries']:.0f} runs, "
                 f"{e['pass_td']+e['rush_td']:.1f} offensive touchdowns{td_note}.\n")
        Mt = M[M.team == t].copy()
        Mt["_ord"] = Mt.slot.map(SLOT_ORDER).fillna(9)
        Mt = Mt.sort_values(["_ord", "mu_rec"], ascending=[True, False])
        for _, m in Mt.iterrows():
            mine = RESEARCH[RESEARCH.player == m["name"]] if len(RESEARCH) else RESEARCH
            tdq = td_book.get(m["name"], [])
            rr_read = RUSH_REC.get((m["name"], t))
            if mine.empty and not tdq and not rr_read:
                continue
            L += RSCH.player_card(card_inputs(m, t, mine, rr_read))
            if tdq:
                bk, price, p_imp = sorted(tdq, key=lambda x: x[0] != "draftkings")[0]
                p_yes, td_src = p_anytime(m)
                # anytime TD: the two chances only; no fair odds from a prototype
                L.append(f"Anytime touchdown ({td_src}, prototype; not part of the research): {odds_str(price)}, "
                         f"engine {pct(p_yes)} / market {pct(p_imp)}.\n")
    L.append(RSCH.CARD_FOOTNOTE + "\n")

    # ---------- 8d. confidence tiers + parlay candidates ----------
    # Confidence is NOT gap size. In early season a big gap almost always means the model
    # is stale on a role change. Tier by role stability first, gap second.
    def stability(m):
        ev = m.evidence; ts_ = ev.get("target_share", {}); rs_ = ev.get("rush_share", {})
        if m.new_team or m.questionable: return "weak"
        own = ts_.get("own_prior"); cur = ts_.get("cur_rate")
        if pd.notna(own) and pd.notna(cur) and own > 0.05 and abs(cur - own) > 0.10: return "weak"
        return "stable"
    conf_rows = []
    if not R.empty:
        best = R.sort_values("gap", ascending=False).drop_duplicates(["player", "market", "side"])
        for _, rr in best.iterrows():
            if rr.gap < 0.03: continue
            mm = M[M.name == rr.player].iloc[0]
            st = stability(mm)
            if st == "weak" or rr.gap > 0.15: tier = "WEAK (book likely knows something)"
            elif rr.gap >= 0.05: tier = "STRONG"
            else: tier = "MODERATE"
            if rr.market == "player_anytime_td":
                et = env[rr.team]
                if et.get("td_anchor") != "market" and tier == "STRONG":
                    tier = "MODERATE (team TD total not market-anchored)"
                elif et.get("td_anchor") == "market" and et.get("td_total_history", 0) > 0:
                    drift = abs(et["td_total_history"] - et["td_total_market"]) / et["td_total_market"]
                    if drift > 0.20 and tier == "STRONG":
                        tier = f"STRONG (note: history had this team at {et['td_total_history']:.1f} TDs vs market {et['td_total_market']:.1f}; anchored to market)"
            conf_rows.append(dict(player=rr.player, team=rr.team, market=rr.market, side=rr.side,
                                  line=rr.line, price=rr.price, p_model=rr.p_model, p_novig=rr.p_novig,
                                  gap=rr.gap, tier=tier))
    CONF = pd.DataFrame(conf_rows)
    if not CONF.empty:
        CONF.to_csv(OUT / f"confidence_{slug}.csv", index=False)

    # Parlays: joint probability from the JOINT simulation (teammates share one team-volume
    # draw, so within-team correlation is real). Cross-team legs are independent draws.
    # TD legs are not simulated per draw and are excluded from joint pricing.
    def leg_hits(row):
        col = {**COUNT_MARKETS, **YARD_MARKETS}.get(row["market"])
        if col is None or row["player"] not in sims or col not in sims[row["player"]]: return None
        sv = sims[row["player"]][col]
        return (sv > row["line"]) if row["side"] == "Over" else (sv < row["line"])
    parlay_rows = []
    # JOINT OUTCOMES ARE NOT VALIDATED, SO THEY ARE NOT PRICED.
    # The simulation does induce real within-team correlation (one team-volume
    # draw, multinomial split), and that is exactly why a parlay number built
    # from it looks authoritative. Nothing has ever checked whether the
    # simulated joint distribution matches realised joint outcomes -- the
    # backtest scores each market marginally and never looks at pairs. A
    # correlation factor that is wrong in the second decimal place turns a
    # +450 fair price into a losing bet, and the marginal CRPS that has been
    # measured cannot detect it. Singles are recorded prospectively; joint
    # pricing waits on its own holdout. See DECISIONS #77.
    if ENABLE_PARLAYS and not CONF.empty:
        legs = CONF[CONF.tier == "STRONG"].head(5)
        legs = legs[legs.market != "player_anytime_td"]
        from itertools import combinations
        for k in (2, 3):
            for combo in combinations(legs.index, k):
                if len({CONF.loc[i, "player"] for i in combo}) < k:
                    continue   # same-player legs: books price these as correlated SGPs, not parlays
                hits = [leg_hits(CONF.loc[i]) for i in combo]
                if any(h is None for h in hits): continue
                joint = float(np.mean(np.logical_and.reduce(hits)))
                indep = float(np.prod([h.mean() for h in hits]))
                if joint <= 0: continue
                fair_dec = 1 / joint
                fair_amer = (fair_dec - 1) * 100 if fair_dec >= 2 else -100 / (fair_dec - 1)
                need_dec = (1 + a.min_er) / joint
                need_amer = (need_dec - 1) * 100 if need_dec >= 2 else -100 / (need_dec - 1)
                parlay_rows.append(dict(legs=" + ".join(f"{CONF.loc[i,'player']} {CONF.loc[i,'side']} {CONF.loc[i,'line']:g} {CONF.loc[i,'market'].replace('player_','')}" for i in combo),
                                        n_legs=k, p_joint=joint, p_if_independent=indep,
                                        correlation_effect=joint / indep if indep > 0 else np.nan,
                                        fair_price=int(round(fair_amer)), take_at_or_longer=int(round(need_amer / 5) * 5)))
    PARLAY = pd.DataFrame(parlay_rows).sort_values("p_joint", ascending=False) if parlay_rows else pd.DataFrame()
    # The confidence tiers used to be logged INSIDE the parlay block, so a
    # slate with no parlay candidates printed no tiers either. Gating parlays
    # off would have made that permanent; they are independent outputs and
    # are logged independently.
    if not CONF.empty:
        log("\n=== Model vs book (information, not advice) ===")
        for _, c in CONF.iterrows():
            log(f"  {c.player} {c.side} {c.line if pd.notna(c.line) else ''} {c.market.replace('player_','')}  model {c.p_model:.0%} book {c.p_novig:.0%}")
    if not PARLAY.empty:
        PARLAY.to_csv(OUT / f"parlays_{slug}.csv", index=False)
        log("\n=== Parlay candidates (STRONG legs only, joint sim) ===")
        for _, pr in PARLAY.head(8).iterrows():
            log(f"  {pr.legs}: joint {pr.p_joint:.1%} (indep {pr.p_if_independent:.1%}, corr x{pr.correlation_effect:.2f}) fair {pr.fair_price:+d}, take at {pr.take_at_or_longer:+d} or longer")
    elif not ENABLE_PARLAYS:
        log("\n=== Parlay candidates: DISABLED ===")
        log("  joint outcomes have never been checked against realised joint")
        log("  outcomes; marginal CRPS cannot detect a wrong correlation factor.")

    L.append("<details><summary>Everything else: how the numbers were built, sources, per-line arithmetic</summary>\n")

    # ---- plain-English summary box ----
    L.append("> **Read this first.** This report puts the sportsbook's numbers next to ours so you can research a prop. "
             "It does **not** recommend bets: the model has not shown it adds anything beside the book's price (the first "
             "line gives the graded record), and "
             "its biggest disagreements were mostly the model missing something. Use it to test a workload story -- what the "
             "line implies, what the player has been getting, and what changed -- then log any bet you make in the journal "
             "so the process is graded.\n")
    if not R.empty:
        dist = R.drop_duplicates(subset=["market", "player", "line", "side"])
        n_big = int((dist.gap.abs() > 0.10).sum()); n_mid = int(((dist.gap.abs() >= 0.03) & (dist.gap.abs() <= 0.10)).sum())
        n_flag = int(dist.new_team.sum() + dist.questionable.sum())
        L.append(f"**Tonight in one paragraph.** We priced **{len(dist)} player props** across {books_used_str}. "
                 f"On **{n_big}** of them our number is more than 10 points away from the book's, and on **{n_mid}** it's "
                 f"3 to 10 points away. {n_flag} of the disagreements involve a player who changed teams or is on the injury "
                 f"report, which is exactly where a model with one week of data is weakest. "
                 f"The big gaps are much more likely to be the book knowing something than a mispriced line.\n")

    # ---------- 8e. BET CARD: one table a bettor can size from ----------
    # Reviewer feedback (2026-09-17): tiers without price, EV and correlation are not
    # actionable. Every line here carries book, price, model %, no-vig %, edge (points),
    # EV per $100 at that price, Kelly fraction, the best line/price across all books,
    # what it is correlated with, the backtest hit rate for its probability bucket, and
    # a tier. Edge floor: below EDGE_FLOOR points a call is "LEAN, no bet" regardless of
    # tier, because a few points is inside model noise on two or three weeks of data.
    EDGE_FLOOR = 0.06
    CAL = None
    try:
        CAL = pd.read_csv(RES / "calibration_2025.csv")
    except Exception:
        pass
    def cal_lookup(market, side, p):
        """Distributional self-check, NOT a betting track record.

        The 2025 table behind this was built by placing lines at FIXED OFFSETS
        FROM THE MODEL'S OWN MEDIAN and asking whether the model's stated
        probability matched the realised frequency. That measures whether the
        distribution is self-consistent near its own centre. It does not
        measure anything about beating a sportsbook, for two reasons:

          - the lines are not book lines, so no book's opinion is in it; and
          - it covers every player-week symmetrically, whereas a real call
            only happens where model and book DISAGREE. That is a different
            population, and the selection is the whole point of betting.

        It also reuses each of the 1,895 player-weeks at 8-10 offsets, so the
        per-bucket `n` is not 1,895 independent observations -- it overstates
        the evidence by roughly an order of magnitude.

        Kept because self-consistency is worth knowing and it is honest about
        what it is. Never presented as a realised hit rate on calls."""
        if CAL is None: return np.nan
        mk = {"player_receptions": "receptions", "player_reception_yds": "rec_yards"}.get(market)
        if mk is None or pd.isna(p) or p < 0.5: return np.nan
        b = "50-60" if p < 0.6 else "60-70" if p < 0.7 else "70-80" if p < 0.8 else "80-90" if p < 0.9 else "90+"
        r = CAL[(CAL.market == mk) & (CAL.side == side) & (CAL.bucket == b)]
        return float(r.hit_rate.iloc[0]) if len(r) else np.nan
    def kelly(p, price, push=0.0):
        b = payout(price); q = 1 - p - push
        return max(0.0, (b * p - q) / b)
    MKT_SHORT = {"player_receptions": "catches", "player_reception_yds": "rec yds",
                 "player_rush_yds": "rush yds", "player_anytime_td": "anytime TD", "player_pass_yds": "pass yds",
                 "player_rush_reception_yds": "rush+rec yds"}
    SIM_COL = {**COUNT_MARKETS, **YARD_MARKETS}
    tier_of = {}
    if not CONF.empty:
        for _, c in CONF.iterrows():
            tier_of[(c.player, c.market, c.side)] = c.tier
    bet_rows = []
    if not R.empty:      # all markets: the card's final tier is what the shadow log records
        Rd = R[R.season.eq(SEASON) & R.week.eq(WEEK)].copy()
        Rd["ER"] = Rd["ER"].astype(float)
        # one row per (player, market, side): the best PRICE at the book's own line
        for (pl, mk, sd), g in Rd.groupby(["player", "market", "side"]):
            best = g.sort_values("ER", ascending=False).iloc[0]
            if best.gap < 0.03: continue
            # best available LINE for this side across books (for yardage/count markets)
            if mk != "player_anytime_td":
                bl = g.sort_values("line", ascending=(sd == "Over")).iloc[0]
                best_line_txt = f"{bl.line:g} @ {bl.book} {int(bl.price):+d}"
            else:
                bl = g.sort_values("price", ascending=False).iloc[0]
                best_line_txt = f"{bl.book} {int(bl.price):+d}"
            tier = tier_of.get((pl, mk, sd), "")
            if not tier:
                mm = M[M.name == pl].iloc[0]
                tier = "WEAK (book likely knows something)" if (stability(mm) == "weak" or best.gap > 0.15) else "MODERATE"
            # edge floor: 6 points for count/yardage props (a few points is model noise on
            # 2-3 weeks of data); for TD props, which live at +150 to +800 where 5 points
            # can be a 40% relative edge, the floor is relative edge >= 25% of the book's number
            under_floor = (best.gap < EDGE_FLOOR) if mk != "player_anytime_td" else (best.gap / max(best.p_novig, 1e-6) < 0.25)
            if not tier.startswith("WEAK") and under_floor:
                tier = "LEAN (no bet: edge under floor)"
            # Reviewer (2026-09-17): a STRONG gap can have the same cause as a WEAK one, just
            # smaller. If the player's current-season share is ABOVE his blended share and we
            # call Under (or below and we call Over), the gap exists because the model trusts
            # the prior more than the market does. Flag it and demote STRONG to MODERATE.
            prior_driven = False
            if mk not in ("player_anytime_td", "player_pass_yds"):   # a QB's own share is not the driver
                mm = M[M.name == pl].iloc[0]
                key = "rush_share" if mk == "player_rush_yds" else "target_share"
                ev_ = mm.evidence.get(key, {}) if isinstance(mm.evidence, dict) else {}
                cur_, fin_ = ev_.get("cur_rate"), ev_.get("final")
                if pd.notna(cur_) and pd.notna(fin_) and fin_ > 0:
                    rel = (cur_ - fin_) / fin_
                    prior_driven = (rel > 0.10 and sd == "Under") or (rel < -0.10 and sd == "Over")
            if prior_driven and tier.startswith("STRONG"):
                tier = "MODERATE (gap is prior-vs-market: this-season share runs " + ("above" if sd == "Under" else "below") + " the blend)"
            # correlation: same-player props and team-volume direction
            same_player = [f"{MKT_SHORT[m2]} {s2}" for (p2, m2, s2) in tier_of if p2 == pl and m2 != mk]
            corr_note = ""
            col = SIM_COL.get(mk)
            if col is not None and pl in sims:
                sv = sims[pl][col]
                hit = (sv > best.line) if sd == "Over" else (sv < best.line)
                tv = team_targets_draw.get(best.team) if mk != "player_rush_yds" else team_carries_draw.get(best.team)
                if tv is not None and len(tv) == len(hit):
                    rho = float(np.corrcoef(hit.astype(float), tv)[0, 1])
                    vol = "throws" if mk != "player_rush_yds" else "runs"
                    if abs(rho) >= 0.10:
                        corr_note = f"{best.team} {vol} {'low' if rho < 0 else 'high'} (r={rho:+.2f})"
            corr_txt = "; ".join(([f"same player: {', '.join(same_player)}"] if same_player else []) + ([corr_note] if corr_note else []))
            bet_rows.append(dict(
                player=pl, team=best.team, prop=MKT_SHORT[mk], side=sd,
                line=best.line if mk != "player_anytime_td" else np.nan,
                book=best.book, price=int(best.price), model_p=round(best.p_model, 3),
                novig_p=round(best.p_novig, 3), edge_pts=round(100 * best.gap, 1),
                ev_per_100=round(100 * best.ER, 1), kelly_frac=round(kelly(best.p_model, best.price, best.p_push), 3),
                stake_qkelly_per_1000=round(250 * kelly(best.p_model, best.price, best.p_push), 0),
                ladder=(lambda col_: "" if (col_ is None or pl not in sims) else " ".join(
                    (f"<={k}:{np.mean(sims[pl][col_] <= k):.0%}" for k in range(max(0, int(min(np.median(sims[pl][col_]), best.line)) - 2), int(max(np.median(sims[pl][col_]), best.line)) + 3))
                    if mk == "player_receptions" else
                    (f"<{L_}.5:{np.mean(sims[pl][col_] < L_ + 0.5):.0%}" for L_ in range(max(5, int(min(np.median(sims[pl][col_]), best.line) // 5 * 5) - 10), int(max(np.median(sims[pl][col_]), best.line) // 5 * 5) + 11, 5))))(SIM_COL.get(mk)),
                best_line=best_line_txt, correlated_with=corr_txt,
                dist_selfcheck=cal_lookup(mk, sd, best.p_model), tier=tier,
                # THE SAME VERDICT AS EVERYWHERE ELSE. This is the table that
                # carries a Kelly stake, so it is the last place that may keep
                # its own private notion of what is bettable.
                **(lambda v: dict(eligible=v.eligible,
                                  would_play_if_validated=v.priced,
                                  ineligible_because=v.why))(
                    eligibility.evaluate(
                        mk, p_win=float(best.p_model), price=float(best.price),
                        gap=float(best.gap), p_push=float(best.p_push or 0.0),
                        new_team=bool(best.new_team),
                        questionable=bool(best.questionable),
                        min_gap=a.min_gap, min_er=a.min_er, er=float(best.ER))),
                note="; ".join([x for x in [("new team" if best.new_team else "questionable" if best.questionable else ""),
                                            ("prior-vs-market gap" if prior_driven else ""),
                                            ("rush model unvalidated" if mk == "player_rush_yds" else "TD model unvalidated" if mk == "player_anytime_td" else "")] if x]),
                book_last_update=best.last_update, snapshot_utc=now(), market=mk))
    BET = pd.DataFrame(bet_rows)
    tier_rank = {"STRONG": 0, "MODERATE": 1, "LEAN": 2, "WEAK": 3}
    if not BET.empty:
        BET["tier_rank"] = BET.tier.str.split(" ").str[0].map(tier_rank).fillna(4)
        BET = BET.sort_values(["tier_rank", "ev_per_100"], ascending=[True, False]).drop(columns="tier_rank")
        BET.to_csv(OUT / f"bet_card_{slug}.csv", index=False)

    # ladder: P(stat <= k) for every modeled player, so alternate lines can be priced
    lad = []
    for pl, sd in sims.items():
        tm = M[M.name == pl].team.iloc[0]
        rec = sd.get("receptions"); ry = sd.get("rec_yards"); ru = sd.get("rush_yards"); pa = sd.get("pass_yards")
        if rec is not None and rec.mean() > 0.3:
            for k in range(0, 12):
                lad.append(dict(player=pl, team=tm, stat="catches", threshold=k, p_at_or_below=float(np.mean(rec <= k)), p_over_half=float(np.mean(rec > k + 0.5))))
        if ry is not None and ry.mean() > 5:
            m = float(np.median(ry))
            for L_ in range(max(5, int(m - 30) // 5 * 5), int(m + 45) // 5 * 5 + 1, 5):
                lad.append(dict(player=pl, team=tm, stat="rec yds", threshold=L_ + 0.5, p_at_or_below=float(np.mean(ry < L_ + 0.5)), p_over_half=float(np.mean(ry > L_ + 0.5))))
        if ru is not None and ru.mean() > 5:
            m = float(np.median(ru))
            for L_ in range(max(5, int(m - 40) // 5 * 5), int(m + 50) // 5 * 5 + 1, 5):
                lad.append(dict(player=pl, team=tm, stat="rush yds", threshold=L_ + 0.5, p_at_or_below=float(np.mean(ru < L_ + 0.5)), p_over_half=float(np.mean(ru > L_ + 0.5))))
        if pa is not None:
            m = float(np.median(pa))
            for L_ in range(max(100, int(m - 90) // 10 * 10), int(m + 100) // 10 * 10 + 1, 10):
                lad.append(dict(player=pl, team=tm, stat="pass yds", threshold=L_ + 0.5, p_at_or_below=float(np.mean(pa < L_ + 0.5)), p_over_half=float(np.mean(pa > L_ + 0.5))))
    LADDER = pd.DataFrame(lad)
    if not LADDER.empty:
        LADDER.to_csv(OUT / f"ladder_{slug}.csv", index=False)

    # shadow log: carry the tier so WEAK-tier calls grade as their own bucket. The CARD's final
    # tier (after the edge floor and the prior-vs-market demotion), not the pre-floor confidence
    # tier: logging the pre-floor one recorded "MODERATE" for rows the card calls LEAN.
    if not R.empty:
        final_tier = {(b.player, b.market, b.side): b.tier for b in BET.itertuples()} if not BET.empty else {}
        R["tier"] = [final_tier.get((r.player, r.market, r.side), tier_of.get((r.player, r.market, r.side), ""))
                     for _, r in R.iterrows()]
        R.to_csv(logf, index=False)

    # THE MATCHUP BRIEF goes at the top whether or not the card has rows (code review)
    BRIEF = brief_section(AWAY=AWAY, HOME=HOME, market_env=market_env, M=M, pop=pop, iw=iw, pbp=pbp,
                          STARTER_QB=STARTER_QB, AUTO_QB=AUTO_QB, LINE_STATUS=LINE_STATUS,
                          TEAM_VOL_CHK=TEAM_VOL_CHK, UNIT_EFF=UNIT_EFF, PA=PA, weather=weather, roof=roof,
                          ROOF_NOTE=ROOF_NOTE, R=R, G=G, WEEK=WEEK, TEAM_VOL_ROWS=TEAM_VOL_ROWS, STATE_N=_state_n)
    if BET.empty:
        L[3:3] = BRIEF
    # put the card at the top of the report, right after the header rule
    if not BET.empty:
        T = []
        # game header: frame, weather, injury designations, data cutoff
        ME_ = market_env or {}
        frame = (f"DK {HOME} {ME_['home_spread']:+g}, total {ME_['total_line']}, implied {HOME} {(ME_['total_line'] - ME_['home_spread'])/2:.1f} / {AWAY} {(ME_['total_line'] + ME_['home_spread'])/2:.1f}"
                 if ME_ else "spread/total unavailable")
        wx = (f"{weather.get('temp_f','')}F, wind to {weather.get('wind_mph_max','')} mph, rain {weather.get('precip_pct_max','')}% (NWS {weather.get('updated','')})"
              if weather.get("status") == "ok" else f"weather {weather.get('status')}")
        desig = [f"{r['name']} {r.report_status}" for _, r in pop.iterrows() if isinstance(r.get("report_status"), str) and r.report_status]
        T += BRIEF
        T += ["## Game header\n",
              f"- **Frame:** {frame}. Team TD totals, all touchdowns incl. defence and special teams (the yardage "
              f"model's anchor): " + ", ".join(f"{t} {env[t].get('pass_td',0)+env[t].get('rush_td',0):.1f} ({'market-anchored' if env[t].get('td_anchor')=='market' else 'history'})" for t in (AWAY, HOME))
              + ("" if V1TD is None or V1TD.empty else
                 ". Offensive touchdowns only, the mean the anytime-TD model prices from: "
                 + ", ".join(f"{t} {float(V1TD[V1TD.team == t]['mu'].iloc[0]):.1f}" for t in (AWAY, HOME)
                             if (V1TD.team == t).any()) + ". The two differ by design, not by error."),
              f"- **Weather:** {wx}. 15 mph sustained-wind screen {'HIT' if (weather.get('wind_mph_max') or 0) > 15 else 'not hit'}.",
              *([f"- **Offence:** {OFF_LINE}"] if OFF_LINE else []),
              *([f"- **Defence:** {DEF_LINE}"] if DEF_LINE else
                [f"- **Defence:** no EPA or drive data in this season's play-by-play yet (DATA MISSING)."]
                if WEEK > 1 else []),
              *([f"- **Offensive line (the five linemen with the most snaps this season):** " + " ".join(LINE_LINES)
                 + " Context only: line absences do not change any price."] if LINE_LINES else
                [f"- **Offensive line:** no lineman snap counts yet this season (DATA MISSING)."] if WEEK > 1 else []),
              f"- **Injury designations (week {WEEK} report):** " + (", ".join(desig) if desig else "none on the eligible set") + ". Out/Doubtful removed; their share goes mostly to the replacement, a quarter to the priced teammates; Questionable priced as if playing, with a separate 'if he's out' pricing. Re-run inside 90 minutes of kickoff: a late scratch changes every share on that team.",
              f"- **Data cutoff:** 2026 weeks 1-{WEEK-1} play-by-play, week {WEEK} roster/injury/depth chart; prices snapshot {now()}; kickoff in {hrs:.1f} h.",
              "",
              *(["## Team volume\n"] + [l_ for t_ in (AWAY, HOME) for l_ in TEAM_VOL_LINES.get(t_, [])]
                if any(TEAM_VOL_LINES.values()) else []),
              "<details><summary>Method in six lines</summary>\n",
              f"1. Data: nflverse play-by-play/rosters/injuries/snaps through week {WEEK-1}, 2025 priors bundled, prices from {books_used_str}, NWS weather.",
              "2. Model: receiving_hier_v2 (receptions, rec yds), rush_yds_v0, pass_yds_v0 (the starting QB), anytime_td_v1 (anytime TD; v0 only as a labelled fallback); methodology v1.0 in resources/methodology.md.",
              "3. Validated against sportsbook lines: NOTHING. The 2025 walk-forward shows the model beats a naive baseline on CRPS and that its distribution is internally consistent (calibration_2025.csv places lines at fixed offsets from the model\u2019s own median, not at book numbers, across all player-weeks rather than the ones worth betting). No market has been tested against posted lines, so every prop is ineligible and the record is being built prospectively.",
              "4. Team TD totals are market-anchored, so a TD gap is a share disagreement only.",
              "5. Line implies: the targets (or carries) per game at which the posted line is a fair 50/50, from the same simulation with only his share moved; 'pays at this price' is the same search at each side's break-even win rate (vig included).",
              "6. No bet labels. " + gate_sentence(GATE),
              "\n</details>\n"]
        T += ["## Research table\n",
              f"*Every priced line, snapshot {now()}, grouped by team. {RESEARCH_NOTE.strip('*')}*\n",
              "| Player | Prop | Line | Price | Our projection | Over: model / book | Line implies | "
              "Pays at this price if you expect | Last game | Flags |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        if len(RESEARCH):
            for _, x in RESEARCH.sort_values(["team", "player", "market", "line"]).iterrows():
                cells = research_cells(x, MKT).strip("|").split("|")
                ul_ = usage_line(None if x.market == "player_pass_yds" else USAGE.get(x.player), rush=x.market == "player_rush_yds", short=True) or "—"
                T.append(f"| {x.player} ({x.team}) |{'|'.join(cells)}| {ul_} | {x['flags'] if isinstance(x['flags'], str) and x['flags'] else '—'} |")
        T.append("")
        L[3:3] = T

    # ---- how this works, for a non-technical reader ----
    L.append("## How this works, in plain English\n")
    L.append("**Step 1, the starting point.** For every player we begin with what he did last season: what share of his team's "
             "throws or carries he got, how often he caught the ball, how many yards each touch went for, and how much of the "
             "goal-line work was his. A rookie or a player with no history starts from what a typical player in his role does.\n")
    L.append(f"**Step 2, this season.** We layer in what has actually happened so far ({n_weeks} week{'s' if n_weeks!=1 else ''}). "
             "One game counts for a little; by mid-season it counts for most of it. A player who changed teams gets his old "
             "numbers discounted, because his old role is weak evidence for his new one.\n")
    L.append("**Step 3, the game.** We estimate how many times each team will throw and run, and how many touchdowns it should "
             "score, from its own recent games. Players who are out are removed and their share of the ball is handed to teammates.\n")
    L.append("**Step 4, the simulation.** We play the game out 20,000 times on a computer with realistic randomness: some games "
             "a player gets 4 catches, some 9, some he breaks a long one. From those 20,000 outcomes we read off how often he "
             "clears each line the book has posted.\n")
    L.append("**Step 5, the comparison.** We turn the book's odds into a probability, strip out its built-in cut, and put our "
             "number next to it. The gap is what the report is about. A big gap does not mean a good bet; it usually means "
             "one side knows something the other doesn't, and the book is the one watching practice.\n")

    L.append("## What we pulled, and whether it worked\n")
    L.append("| Source | Used for | Status | Detail |")
    L.append("|---|---|---|---|")
    for nm, use, st, det in SOURCES:
        badge = "OK" if st == "ok" else ("skipped" if "skipped" in st else "**" + st + "**")
        L.append(f"| {nm} | {use} | {badge} | {det} |")
    failed = [nm for nm, _, st, _ in SOURCES if st not in ("ok",) and "skipped" not in st]
    if failed:
        L.append(f"\n**Heads up:** {', '.join(failed)} did not come through. The numbers below are built without that input.\n")
    else:
        L.append("\nEverything the report needs came through.\n")

    # ---- cheat sheet ----
    if not top.empty:
        L.append("## Where the model and the book differ most\n")
        L.append("Information, not advice. Through week 3 a big difference was usually the model missing something "
                 "(an injury, a role change, a game plan), so these are the lines to check for a reason first. "
                 "\"Model\" and \"Book\" are the chance of that side.\n")
        L.append("| Player | Prop | Line / Price | Side | Model | Book |")
        L.append("|---|---|---|---|---|---|")
        for _, r in top.iterrows():
            m = M[M.name == r.player].iloc[0]
            ln = f"{int(r.price):+d}" if pd.isna(r.line) else r.line
            side = "Yes" if r.market == "player_anytime_td" else r.side
            L.append(f"| **{r.player}** ({m.team}) | {MKT[r.market]} | {ln} | {side} | {pct(r.p_model)} | {pct(r.p_novig)} |")
        L.append("")

    # ---- context ----
    L.append("## The setup\n")
    L.append(f"- **Kickoff:** {G.gameday} {G.gametime} ET at {G.stadium} ({'indoors' if roof in ('closed','dome') else 'outdoors' if roof in ('open', 'outdoors') else 'roof unknown'}"
             + (f"; {ROOF_NOTE}" if ROOF_NOTE else "") + ").")
    L.append(f"- **What we're working with:** {n_weeks} week{'s' if n_weeks!=1 else ''} of this season, plus each player's full {PRIOR} season as a starting point.")
    for t in (AWAY, HOME):
        e = env[t]
        src = e.get("source") or "history"
        src_note = (" (anchored to the market's spread and total; unvalidated option)" if src == "market" else
                    f" (the team's own recent games plus last season, the throws {100 * MODEL.MARKET_PASS_WEIGHT:.0f}% "
                    "from the market's spread/total fit)" if src.startswith("history + market pass") else
                    " (from the team's own recent games, plus last season -- no spread/total this run, so the "
                    "market's share of the throws was not applied)" if src.startswith("history (no spread") else
                    " (from the team's own recent games, plus last season)")
        L.append(f"- **{t}'s offense, typical game{src_note}:** about {e['targets']:.0f} throws, {e['carries']:.0f} runs, "
                 f"{e['pass_td']+e['rush_td']:.1f} offensive touchdowns.")
    L.append("- **Matchup (opponent defense):** included at the team level, weighted by how much real "
             "between-team difference last season's data could actually detect (roughly a 4% swing in "
             "efficiency, weighted about half). Position-specific matchups ('good against tight ends') were "
             "tested and are too noisy to use. Expect this to move a projection by a point or two, not more.")
    excl = pop[pop.excluded]
    if len(excl):
        _src = lambda r: (f", {INJ_SOURCE[(r.team, r.gsis_id)]}" if (r.team, r.gsis_id) in INJ_SOURCE else "")
        L.append(f"- **Out:** " + ", ".join(f"{r['name']} ({r.report_status or r.status}{_src(r)})"
                                            for _, r in excl.iterrows())
                 + ". Most of their usual share goes to whoever replaces them, not to the priced teammates: a quarter of their targets is handed on in our numbers, mostly to their position; for carries, a quarter of their carry share this season, and to each teammate only the part of the absence not already in his own numbers (round 35).")
        for f_ in SC.missing_replacements(pop):
            left = ("nobody" if not f_["priced_left"] else "only " + ", ".join(f_["priced_left"]))
            L.append(f"- **No priced replacement for {f_['name']} ({f_['team']} {f_['slot']}):** the depth chart "
                     f"before kickoff has not promoted anyone, so {f_['team']} prices {left} at {f_['pos']}. "
                     + (f"No {f_['team']} passing lines are priced, and the receivers' numbers carry no "
                        f"adjustment for the backup. " if f_["pos"] == "QB" else
                        f"The player who takes his snaps is not priced; most of the absent player's share "
                        f"stays with the unpriced depth pool. ")
                     + f"A role what-if prices whoever replaces him: "
                     f"--role \"PLAYER={f_['slot']}\".")
    if "was_inactive" in rw:
        # provisional roster: last week's inactives with no report yet this week are priced as playing
        reported = {k for k, v in inj_status.items() if isinstance(v, str)}
        prov_ina = [r_ for _, r_ in rw[rw.was_inactive].iterrows()
                    if (r_.team, r_.gsis_id) not in reported and r_.gsis_id in set(pop.gsis_id)]
        if prov_ina:
            L.append("- **Inactive last week, no injury report yet this week:** "
                     + ", ".join(f"{r_.full_name} ({r_.team})" for r_ in prov_ina)
                     + ". Priced as playing his normal role until this week's report says otherwise; if he "
                       "sits again, his lines are void and his teammates' move.")
    # the book's quarterbacks: its extra QB lines and its passing-yards line (the commonest
    # QB line; outcomes carry no team, so the team comes from this week's roster)
    _qb_team = {norm_name(n_): t_ for t_, n_, p_ in zip(rw.team, rw.full_name, rw.position)
                if p_ == "QB" and t_ in (AWAY, HOME)}
    _book_qbs = list((data or {}).get("sleeper_extra") or [])
    for b_ in ((data or {}).get("bookmakers") or []):
        for mk_ in b_.get("markets", []):
            if mk_.get("key") == "player_pass_yds":
                for o_ in mk_.get("outcomes", []):
                    t_ = _qb_team.get(norm_name(o_.get("description", "")))
                    if t_:
                        _book_qbs.append({"name": o_["description"], "team": t_, "kind": "passing_yards"})
    for mm_ in RSCH.book_qb_mismatch(_book_qbs, STARTER_QB, SLEEPER_TEAM):
        L.append(f"- **The book's quarterback is not ours ({mm_['team']}):** Sleeper posts passing lines for "
                 f"{', '.join(mm_['book'])} and none for {mm_['engine']}, the depth chart's starter, whom this "
                 f"board prices as the starter (his kneel-downs and passing share; his receivers' numbers do not "
                 f"depend on who throws). The depth chart may be stale. To price the book's quarterback: "
                 f"--role \"{mm_['book'][0]}=QB1\".")
    q = pop[pop.questionable]
    if len(q):
        L.append(f"- **Questionable:** " + ", ".join(r["name"] for _, r in q.iterrows()) + ". Priced as if they play their normal role; see 'If a Questionable player is out' for the other case.")
    unpriced_q = [w_ for t_ in (AWAY, HOME) for w_ in QWATCH.get(t_, []) if not w_["priced"]]
    if unpriced_q:
        pc_ = lambda v: "—" if v is None or v != v else f"{100 * v:.0f}%"
        L.append("- **Questionable, not priced here:** " + "; ".join(
            f"{w_['name']} ({w_['pos']}, {w_['status']}: {pc_(w_['ts'])} of targets and {pc_(w_['cs'])} of carries "
            f"in the weeks he played, {pc_(w_['snap'])} of snaps)" for w_ in unpriced_q)
                 + ". If one sits, his work goes mostly to the teammates at his position: their rows carry his flag.")
    if excl.empty and q.empty and not unpriced_q:
        L.append("- **Injuries:** no one relevant is out or questionable on the current report.")
    if roof in ("closed", "dome"):
        L.append("- **Weather:** indoors, not a factor.")
    elif weather["status"] == "ok":
        w = weather
        L.append(f"- **Weather (NWS, updated {str(w.get('updated',''))[:16]}Z):** {w['temp_f']}°F, wind up to {w['wind_mph_max']} mph, "
                 f"{w['precip_pct_max']}% chance of rain. "
                 + ("**Wind is above the 15 mph line where passing numbers start to suffer.** We do not adjust for it automatically; treat passing props with extra caution."
                    if w["wind_screen"] else "Nothing here that changes the numbers."))
    else:
        L.append(f"- **Weather:** could not be retrieved ({weather['status']}). Only matters if sustained wind tops 15 mph.")
    L.append("")

    # ---- explained lines ----
    L.append("## How the model got its numbers (biggest differences first)\n")
    if top.empty:
        L.append("_No prices were retrieved for this game._\n")
    else:
        for i, (_, r) in enumerate(top.iterrows(), 1):
            m = M[M.name == r.player].iloc[0]
            side = "Yes" if r.market == "player_anytime_td" else f"{r.side} {r.line}"
            L.append(f"### {i}. {r.player} · {MKT[r.market]} · {side}")
            L.append(f"**Model {pct(r.p_model)} · Book {pct(r.p_novig)}**\n")
            for line in explain(r, m):
                L.append(line + "\n")

    # ---- consensus ----
    L.append("## Where the books disagree with each other\n")
    L.append("This part doesn't use our model at all. It just checks whether one sportsbook is out of step with the others "
             "on the same player. When a book is a full catch or several yards off the pack, that's worth a look on its own.\n")
    if consensus_rows:
        C = pd.DataFrame(consensus_rows)
        C["_s"] = C.p_dev.abs().fillna(0) + C.line_dev.abs().fillna(0)/10
        C = C.sort_values("_s", ascending=False).drop(columns="_s")
        C.to_csv(OUT / f"consensus_outliers_{slug}.csv", index=False)
        L.append("| Player | Prop | This book | Its line | Most books say | Off by |")
        L.append("|---|---|---|---|---|---|")
        for _, r in C.head(12).iterrows():
            off = f"{r.line_dev:+.1f}" if pd.notna(r.line_dev) and abs(r.line_dev) >= 0.5 else (f"{r.p_dev:+.0%} on price" if pd.notna(r.p_dev) else "")
            L.append(f"| {r.player} | {MKT.get(r.market, r.market)} | {r.book} | {r.book_line} | {r.consensus_line} | {off} |")
        L.append("")
    else:
        L.append("_All books are within normal range of each other tonight._\n")

    # ---- glossary ----
    L.append("## Reading the numbers\n")
    L.append("- **Our number** is the chance our model gives that side. 60% means it happens about 6 games in 10.")
    L.append("- **Book** is what the odds imply once the sportsbook's built-in cut is removed. A book's two prices on one line "
             "always add to more than 100%; we strip that out so it's a fair comparison.")
    L.append("- **Line implies** is the workload (targets or carries per game) at which the posted line is a fair 50/50, "
             "holding his catch rate and yards per touch. Compare it with what he has been getting.")
    L.append("- **Pays at this price if you expect** is the same search at each side's own price: the Over beats its price only "
             "above the first number, the Under only at or below the second. The gap between them is the book's cut. It "
             "tells you how much role your view needs, not whether the view is right; the model's chances are not shown "
             "to be calibrated within 3 points (reports/calibration_bar_v2.md).")
    if not td_two_sided:
        if (RD.market == "player_anytime_td").any() if len(RD) else False:
            L.append("- **Touchdown prices** have no 'won't score' side to remove the cut from, so the book's number there is a bit high.")
    L.append("- **Why there are no bet labels:** the model beats simple baselines on past seasons, but it has not shown it "
             "adds anything beside the book's price (the report's first line gives the current graded record). Every run "
             "still logs every line, the Tuesday scorecard keeps measuring, and bets you make are graded in the journal.")
    L.append("")

    # ---- touchdown pairs: only the classes the committed gate opened (deferred, #190) ----
    if show_td:
        L += td_pairs_section(J_)

    # ---- housekeeping ----
    L.append("## Housekeeping\n")
    if quote_meta:
        _q = (quote_meta.get("quota") or {}).get("x-requests-remaining")
        src_ = ("priced from Sleeper" if sleeper_used else
                "priced from the manual lines file" if a.lines_file else "no quota header returned")
        L.append(f"- Prices captured {quote_meta['retrieved']} UTC. Odds API calls remaining this month: "
                 + (f"n/a ({src_})" if sleeper_used or a.lines_file or _q is None else f"{_q}") + ".")
    L.append(f"- Routes run and route participation: not available from any verified source, so not used.")
    if QB_RUSH_ON:
        L.append("- QB rushing yards (the starter only) include kneel-downs, which the book counts, drawn by the "
                 "team's pregame spread. The newest yardage market: its graded record, including where it runs "
                 "high or low, is in the repo's reports/yardage_harness.md.")
    else:
        L.append(f"- QB rushing yards left out on purpose: kneel-downs count against the prop and we don't model them yet.")
    if PASS_ON:
        L.append("- QB passing yards (the starter only) are his receivers' yards in the same simulation, times a "
                 "starter's usual share of the team's passing yards. Graded 2022-25 in reports/yardage_harness.md: "
                 "right on average and the right width; it beats the unshrunk version early in the season and ties it "
                 "from week 5.")
        if pass_skipped:
            L.append("- Passing lines posted for a QB the model does not start, not priced: "
                     + "; ".join(f"{nm} ({tm}; the model's starter is {STARTER_QB.get(tm) or 'none'})"
                                 for nm, tm in sorted(pass_skipped)) + ".")
        if (a.source == "oddsapi" or oddsapi_is_fallback) and not sleeper_used and not a.lines_file:
            L.append("- QB passing yards were not priced this run: Sleeper Picks carries them, and the Odds API "
                     "fallback request does not include them.")
    if hrs > 1:
        L.append(f"- **Kickoff is in {hrs:.1f} hours.** To track how these lines moved, open a chat inside the last hour and ask for a closing capture.")
    elif hrs > 0:
        L.append(f"- **Candidate closing snapshot:** kickoff in {hrs * 60:.0f} minutes, inside the closing window. The "
                 "scheduled capture records the official close; this run is a reference copy.")
    L.append(f"- Full technical detail (every line, every book, model parameters) is in the attached CSV files.")
    L.append("")

    # ---- technical appendix ----
    L.append("---\n<details><summary>Technical appendix: all lines</summary>\n")
    if not RD.empty:
        L.append("| Book | Market | Player | Line | Model mean | Side | p_model | p_novig | Gap | Price | ER |")
        L.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for _, r in RD.iterrows():
            L.append(f"| {r.book} | {r.market.replace('player_','')} | {r.player} | {'' if pd.isna(r.line) else r.line} | "
                     f"{'' if pd.isna(r.model_mean) else round(r.model_mean,1)} | {r.side} | {r.p_model:.3f} | {r.p_novig:.3f} | "
                     f"{r.gap:+.3f} | {r.price} | {r.ER:+.3f} |")
    # the evidence per market, as measured (outside review 2026-10-06: the blanket "calibrated"
    # outlived a corrected FAIL on passing width); reports/rush_rec_calibration.md, yardage_harness.md
    L.append(f"\nModel states (none tested against posted lines): receptions and receiving yards `receiving_hier_v2` PROTOTYPE "
             f"(2022-25 harness: width within the bar; at the main line the Over hits more often than the engine says -- receiving yards by 2.9 points, receptions 1.4, tight ends most, DECISIONS #197-#198); rushing yards `rush_yds_v0` and rushing + receiving PROTOTYPE "
             f"(near the main line on average, leaning by implied points -- backs on teams implied 27+ hit the Over 59% against 49%; too narrow in the tails: 23-25% of games outside the 80% range, so a "
             f"line far from the median reads too confident; reports/current_settings_check_2026-10-06.md); QB passing yards "
             f"`pass_yds_v0` PROTOTYPE (scaled by implied points since round 38, DECISIONS #199: at the main line the Over hit 39% at 18 or fewer implied points against an engine 45%, 66% at 27+ against 57%; too WIDE: 12% of "
             f"games outside the 80% range against a 17-23% bar, so its chances sit too close to 50%); "
             f"anytime TD `anytime_td_v1` PROTOTYPE (outcome-backtested, no posted-line test; no fair odds). All MODEL_UNVALIDATED. Dispersion: receptions log r = "
             f"{P['receptions_dispersion']['a']:.3f} + {P['receptions_dispersion']['b']:.3f}·log μ; carries "
             f"{P['carries_dispersion']['a']:.3f} + {P['carries_dispersion']['b']:.3f}·log μ; per-catch Gamma shape {SH:.3f}; "
             f"K0={K0}; {N_SIM} draws, seed 20260917. Early-season prior-season blend is not the form validated in the 2025 backtest.")
    L.append("</details>")

    L.append("\n</details>")       # closes 'Everything else', which is opened unconditionally
    # encoding is explicit: the report contains "≥" and Windows defaults to
    # cp1252, which cannot encode it. The Linux runner never saw this because
    # it defaults to UTF-8, so the bug was invisible in CI and fatal locally.
    (OUT / f"report_{slug}.md").write_text("\n".join(L), encoding="utf-8")
    M.drop(columns=["evidence"]).to_csv(OUT / f"player_params_{slug}.csv", index=False)
    try:
        FP = fantasy_table(M, sims, V1TD, td_lambda, parse_scoring(a.fantasy_scoring),
                           np.random.default_rng(20260922), N_SIM)
        FP.to_csv(OUT / f"fantasy_points_{slug}.csv", index=False)
    except Exception as exc:  # noqa: BLE001 -- the export must never cost the prop run
        log(f"  fantasy export skipped ({type(exc).__name__}: {exc})")
    log(f"\nwrote {OUT}/report_{slug}.md")
    if hrs > 0 and hrs <= 1:
        log(f"  CANDIDATE CLOSING SNAPSHOT: kickoff in {hrs * 60:.0f} minutes")
    SCEN_L = []
    if RULES and not SCENARIO:
        snap_ = Path(a.odds_snapshot) if a.odds_snapshot else (snap_path if snap_written else None)
        if any(r_.get("auto") for r_ in RULES):
            # the automatic range (#179): our projection +/- one standard error of his
            # share over his last 10 games; this season only after a team change or a takeover
            import build_play_yards as _BPY
            _sg_path = RES / f"priors_{PRIOR}_share_games.csv"
            _sg = ({str(r_.gsis_id): _BPY.parse_share_games(r_.games)
                    for r_ in pd.read_csv(_sg_path).itertuples()} if _sg_path.exists() else {})
            _ranges = {}
            for r_ in RULES:
                if not r_.get("auto"):
                    continue
                m_ = M[M.name == r_["who"]].iloc[0]
                j_ = 2 if r_["key"] == "targets" else 3            # target / carry share in WEEK_SH rows
                vol_ = env[m_.team]["targets" if r_["key"] == "targets" else "carries"]
                proj_ = (vol_ * float(m_.ts) if r_["key"] == "targets"
                         else float(np.mean(sims[m_["name"]]["carries"])))
                # a role change: a new team, or the validated flag for this volume (the
                # takeover flag for carries, the role-shift flag for targets)
                changed_ = bool(m_.new_team) or bool(RSCH.carry_flag(CARRY_U.get(m_["name"]), WEEK - 1)
                                                     if r_["key"] == "carries" else ROLE.get(m_["name"]))
                _ranges[(r_["who"], r_["key"])] = RSCH.auto_range(
                    [w_[j_] for w_ in WEEK_SH.get(m_["name"], [])],
                    [g_[j_ - 1] for g_ in _sg.get(str(m_.gsis_id), [])], proj_, vol_, this_season_only=changed_)
            try:
                RULES = SC.fill_auto(RULES, _ranges)
                auto_err = None
            except ValueError as exc:
                auto_err = str(exc)
        else:
            auto_err = None
        # THIS run's lines only, never the --prior-log merge (an earlier capture's chance is not the board's)
        SCEN_L = (["", "## Your scenario (experimental)", "", f"Not priced: {auto_err}."] if auto_err else
                  run_user_scenario(pd.DataFrame(rows) if rows else R.iloc[0:0], RESEARCH, slug, snap_, RULES))
        L += SCEN_L
        (OUT / f"report_{slug}.md").write_text("\n".join(L), encoding="utf-8")
    if not SCENARIO and not a.no_scenarios:
        q = pop[pop.questionable & ~pop.excluded]
        if len(q) and snap_written:
            L += run_scenarios(q, RD, slug, snap_path)
            (OUT / f"report_{slug}.md").write_text("\n".join(L), encoding="utf-8")
        elif len(q):
            L += ["", "## If a Questionable player is out", "",
                  "Not priced: this run had no lines to price against."]
            (OUT / f"report_{slug}.md").write_text("\n".join(L), encoding="utf-8")
    if MARKETS:
        S_ = short_summary(R, AWAY, HOME, SEASON, WEEK, books_used_str, hrs, sorted(MARKETS), gate=GATE) + SCEN_L
        (OUT / f"summary_{slug}.md").write_text("\n".join(S_), encoding="utf-8")
        print("\n".join(S_))
        print(f"\n(full report: {OUT / f'report_{slug}.md'})")
    else:
        print("\n".join(L))


def short_summary(R, away, home, season, week, books, hrs, markets, gate=None) -> list[str]:
    """The --markets fast path: just the asked-for markets, one table."""
    out = [f"# {away} at {home}, {season} week {week}: {', '.join(m.replace('player_', '') for m in markets)}", "",
           f"Prices: {books}." + (f" Candidate closing snapshot (kickoff in {hrs * 60:.0f} min)." if 0 < hrs <= 1 else ""),
           "", "**No bet labels**: a research view. " + gate_sentence(gate), ""]
    if R.empty:
        return out
    out += ["| player | market | side / line | book | price | model | market | gap |", "|---|---|---|---|---|---|---|---|"]
    for r in R.sort_values(["market", "p_model"], ascending=[True, False]).itertuples():
        ln = "" if pd.isna(r.line) else f" {r.line:g}"
        out.append(f"| {r.player} ({r.team}) | {r.market.replace('player_', '')} | {r.side}{ln} | {r.book} | "
                   f"{int(r.price):+d} | {r.p_model:.0%} | {r.p_novig:.0%} | {r.gap:+.0%} |")
    return out


def carry_handoff_inputs(rushes, passes, act_weeks, team, absent, mates):
    """Round 35 (reports/round35_out_rule.md, DECISIONS #192): for the CARRY handoff,
    the absent player's carry share THIS season in the games he had a carry, and for each
    priced teammate the fraction of his own active games this season in which the absent
    player had a carry -- the part of the absence NOT already in that teammate's share.
    Exactly the tested definition (out_rule_test.py V2, carries kind: two-point tries out).
    rushes / passes: this season's plays before the game (posteam, week, rusher_player_id /
    receiver_player_id); act_weeks: {gsis_id: set of weeks ACTIVE for this team}. Returns
    (share or None when he has not carried this season, {mate: fraction})."""
    r = rushes[rushes.posteam == team]
    if "two_point_attempt" in r:
        r = r[r.two_point_attempt.fillna(0) != 1]
    p = passes[passes.posteam == team]
    played = set(r.loc[r.rusher_player_id == absent, "week"])
    if not played:
        return None, {}
    team_c = r.groupby("week").size()
    den = float(team_c.reindex(sorted(played)).fillna(0).sum())
    share = float((r.rusher_player_id == absent).sum()) / den if den > 0 else None
    team_weeks = set(team_c.index) | set(p.week)
    frac = {}
    for j in mates:
        wj = act_weeks.get(j, set()) & team_weeks
        frac[j] = (len(wj & played) / len(wj)) if wj else 1.0
    return share, frac


def apply_out_rule(M: pd.DataFrame, E: pd.DataFrame, teams, rule=None, mult=None):
    """Hand each excluded player's share on under OUT_RULE. M: priced players
    (team, pos, ts, rs, i10ts, i10rs); E: excluded players (team, pos, and the
    same share columns). mult: {col: {E row index: {teammate gsis_id: factor}}} --
    round 35's carries: only the part of the absence not yet in a teammate's share is
    handed to him. Returns (M, {team: {col: share handed on}})."""
    rule = OUT_RULE if rule is None else rule
    M = M.copy()
    grp = M["pos"].map(lambda x: POS_GROUP.get(x, x))
    redistributed = {}
    for t in teams:
        m = M.team == t
        redistributed[t] = {}
        for col in ["ts", "rs", "i10ts", "i10rs"]:
            x, y = rule[col]
            kept = 0.0
            for _, e in (E[E.team == t].iterrows() if len(E) else []):
                f = float(e[col]) * y
                if f <= 0:
                    continue
                base = M.loc[m, col].clip(lower=0)
                same = m & (grp == e["pos"])
                base_same = M.loc[same, col].clip(lower=0)
                add = pd.Series(0.0, index=M.index)
                if base.sum() > 0:
                    add[m] += x * f * base / base.sum()
                if base_same.sum() > 0:
                    add[same] += (1 - x) * f * base_same / base_same.sum()
                fac = ((mult or {}).get(col) or {}).get(e.name)
                if fac:
                    add = add * M["gsis_id"].map(fac).fillna(1.0)
                M.loc[m, col] = M.loc[m, col].clip(lower=0) + add[m]
                kept += float(add.sum())
            redistributed[t][col] = kept
    return M, redistributed


# Out path (A2): (x, y) per share column. y = the fraction of an excluded
# player's share that stays with the priced teammates; x = of that, the part
# spread over all of them (the rest goes to his position). Tuned on 2022-23
# absence games, scored as-is on 2024-25 (reports/absence_tune.md); test loss
# vs the shipped (1, 1): targets -14.9 (-21.5, -9.7), carries -96 (-136, -62),
# inside-10 targets -90 (-121, -62), inside-10 carries -375 (-617, -206).
OUT_RULE = {"ts": (0.2, 0.25), "i10ts": (0.0, 0.0), "rs": (0.0, 0.25), "i10rs": (0.0, 0.25)}
POS_GROUP = {"FB": "RB", "HB": "RB"}
JOINT_LEG_MIN = 0.10


def joint_shadow(R, M, V1TD, away, home, prior) -> pd.DataFrame:
    """Every pair of anytime-TD legs priced JOINT_LEG_MIN+ by anytime_td_v1:
    the leg-by-leg product and ALL FOUR candidate joint prices -- plain joint
    (teammates share their team's count), + mix shift, + mix shift + copula,
    + copula. Shadow logging costs nothing, and the graded record is what will
    settle which structure is right (DECISIONS #89). Nothing renders."""
    if R.empty or V1TD is None or V1TD.empty:
        return pd.DataFrame()
    td = R[(R.market == "player_anytime_td") & (R.td_model == TDV1.LABEL) & (R.p_model >= JOINT_LEG_MIN)]
    td = td.sort_values("p_model", ascending=False).drop_duplicates("player")
    gsis = dict(zip(M["name"], M["gsis_id"]))
    td = td[td.player.map(gsis).isin(V1TD.index)]
    if len(td) < 2:
        return pd.DataFrame()
    # THE GATED SPECIFICATION: when the committed gate exists, the shadow and the
    # rendered pairs use exactly the mix shift, copula r and Dirichlet c it
    # validated -- a table estimated on other seasons would render a model the
    # gate never scored. Without the gate file, the bundled table and constants
    # feed the shadow log only (nothing renders then).
    gf = RES / TDJ.GATE_FILE
    spec = json.loads(gf.read_text(encoding="utf-8")) if gf.exists() else {}
    if spec.get("mix_shift"):
        shift = pd.DataFrame(spec["mix_shift"]["rows"], columns=spec["mix_shift"]["channels"])[TDJ.CH]
    else:
        mf = RES / f"priors_{prior}_td_mixshift.csv"
        shift = pd.read_csv(mf, index_col=0)[TDJ.CH] if mf.exists() else None
    r_cop = float(spec.get("copula_r", TDJ.R_PROVISIONAL))
    c_dir = spec.get("dirichlet_c", TDJ.DIRICHLET_C)
    mu = {t: float(V1TD[V1TD.team == t]["mu"].iloc[0]) for t in (away, home) if (V1TD.team == t).any()}
    if len(mu) < 2:
        return pd.DataFrame()
    P0 = TDJ.joint_counts(mu[away], mu[home])
    Pr = TDJ.joint_counts(mu[away], mu[home], r=r_cop)
    axis = {away: 0, home: 1}
    q0, q1 = {}, {}
    for t in (away, home):
        v = V1TD[V1TD.team == t]
        shares = v[[f"s_{c}" for c in TDJ.CH]].set_axis(TDJ.CH, axis=1)
        mix = pd.Series([float(v[f"w_{c}"].iloc[0]) for c in TDJ.CH], index=TDJ.CH)
        m0 = TDJ.q_by_opp(shares, TDJ.mixes_by_opp(mix, None))
        m1 = TDJ.q_by_opp(shares, TDJ.mixes_by_opp(mix, shift))
        q0.update({g: m0[i] for i, g in enumerate(v.index)})
        q1.update({g: m1[i] for i, g in enumerate(v.index)})
    empty = np.zeros((0, TDJ.OPP_BUCKETS))
    rows = []
    legs = list(td.itertuples())
    for i in range(len(legs)):
        for j in range(i + 1, len(legs)):
            a_, b_ = legs[i], legs[j]
            ga, gb = gsis[a_.player], gsis[b_.player]

            def pj(q, P):
                on_a = [q[g] for g, t in ((ga, a_.team), (gb, b_.team)) if axis[t] == 0]
                on_b = [q[g] for g, t in ((ga, a_.team), (gb, b_.team)) if axis[t] == 1]
                return TDJ.p_all(np.array(on_a) if on_a else empty, np.array(on_b) if on_b else empty, P, c_dir)
            rows.append({"player_a": a_.player, "team_a": a_.team, "player_b": b_.player, "team_b": b_.team,
                         "kind": "teammates" if a_.team == b_.team else "opponents",
                         "p_a": float(a_.p_model), "p_b": float(b_.p_model),
                         "p_indep": float(a_.p_model * b_.p_model),
                         "p_joint_plain": pj(q0, P0), "p_joint_shift": pj(q1, P0),
                         "p_joint_shift_copula": pj(q1, Pr), "p_joint_copula": pj(q0, Pr),
                         "joint_model": f"td_joint_v0 shadow, four candidates, copula r {r_cop:g}, "
                                        f"Dirichlet c {c_dir}, spec {'gate' if spec else 'bundled'}"})
    return pd.DataFrame(rows)


PAIR_COL = {"joint": "p_joint_plain", "joint + mix shift": "p_joint_shift",
            "joint + mix shift + copula": "p_joint_shift_copula", "joint + copula": "p_joint_copula"}
PAIR_CLASS = {"opponents": "cross-team pair", "teammates": "teammate pair"}


def td_pairs_section(J_: pd.DataFrame, top: int = 6) -> list[str]:
    """Anytime-TD pairs for the parlay classes the committed gate OPENED
    (resources/td_parlay_gate.json, written by td_joint_backtest.py -- never a
    hand-written verdict). Each class uses its own tune-chosen model. A class
    that is unresolved or failing never renders, and neither does anything
    when the gate file is missing."""
    gf = RES / TDJ.GATE_FILE
    if J_ is None or J_.empty or not gf.exists():
        return []
    gate = json.loads(gf.read_text(encoding="utf-8"))
    out = []
    for kind, cls in PAIR_CLASS.items():
        if cls not in gate.get("open_classes", []):
            continue
        col = PAIR_COL[gate["picks"][cls]]
        g = J_[J_["kind"] == kind].sort_values(col, ascending=False).head(top)
        if g.empty:
            continue
        v = gate["b_prime"][cls]
        out += ["", f"### Touchdown pairs: {cls} (layer 3, PROTOTYPE -- no fair odds)", "",
                f"*Open by the committed gate: pooled actual/predicted {v['ratio']:.3f} "
                f"({v['ci'][0]:.3f}-{v['ci'][1]:.3f}) over {v['games']} games. Model: {gate['picks'][cls]}. "
                "Both legs are PROTOTYPE, so neither is a fair price; the lift is how far scoring together "
                "differs from multiplying the two legs.*", "",
                "| pair | P(both) | legs multiplied | lift |", "|---|---|---|---|"]
        for r in g.itertuples():
            out.append(f"| {r.player_a} ({r.team_a}) + {r.player_b} ({r.team_b}) | {getattr(r, col):.1%} | "
                       f"{r.p_indep:.1%} | {getattr(r, col) / r.p_indep:.2f} |")
    if out:
        out = ["", "## Touchdown pairs"] + out + ["", "Three teammates together is not shown: its class is not open."]
    return out


RESEARCH_NOTE = ("*Each line: the book's line and price, our projection (median, with the 10th-90th percentile "
                 "range), the chance of the Over by our model and by the book's price (its cut removed), and what the "
                 "line implies: the targets or carries per game at which the line is a fair 50/50, next to what we "
                 "project; then the workload each side needs to beat its own price. A **bold** prop is worth a "
                 "look, not a bet: a role story plus last game's workload already past that side's break-even "
                 "(DECISIONS #156; the scorecard grades every one). 'Carries up / down' marks a back whose "
                 "carry share moved 20+ points last week (reports/rb_takeover_check.md). Flags mark a teammate out or back, a new team, a Questionable tag, and the receiving "
                 "role-shift pattern (reports/role_shift_check.md).*")


GATE_URL = "https://raw.githubusercontent.com/gabjew90/Fantasy-football/main/props/record/model_weight.json"


def load_label_gate(wd=None):
    """The label gate the Tuesday scorecard writes (props/record/model_weight.json,
    DECISIONS #144): the repo copy when the engine runs inside the repo, else the
    published copy (chat), cached six hours. None when neither can be read --
    the report then says so instead of quoting a number."""
    local = Path(__file__).resolve().parents[2] / "record" / "model_weight.json"
    try:
        if local.exists():
            return json.loads(local.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    try:
        import urllib.request as _ur
        loader = lambda: json.load(_ur.urlopen(_ur.Request(GATE_URL, headers={"User-Agent": "Mozilla/5.0"}),
                                               timeout=15))
        return cached_json(Path(wd) / "model_weight.json", 6 * 3600, loader) if wd else loader()
    except Exception:  # noqa: BLE001 -- the gate is context, never a reason to fail a run
        return None


def gate_sentence(gate) -> str:
    """One sentence on the graded record. The gate opens only on the CURRENT
    pricing model's own calls (two engines are not one sample); the pooled fit
    across every model is quoted as context."""
    if not isinstance(gate, dict) or "pooled" not in gate:
        return ("The graded record could not be read on this run, so no line carries a bet label "
                "(props/record/scorecard.md has it).")
    cur, pool = gate.get("current"), gate.get("pooled") or {}
    wk = lambda g: f"weeks {min(g['weeks'])}-{max(g['weeks'])}" if g.get("weeks") else "no weeks yet"
    ci = lambda g: f"{g['w_model']:+.2f} (95% {g['lo']:+.2f} to {g['hi']:+.2f})"
    ctx = (f" Across every pricing model ({wk(pool)}, {pool['n_calls']} calls) it is {ci(pool)}."
           if pool.get("estimated") else "")
    if not cur:
        return "No call has been graded yet, so no line carries a bet label." + ctx
    name = cur.get("engine", "latest")
    nxt = cur.get("next_review")
    rule = ("Labels return only at a review (after weeks 8, 12 and 18) where the model's weight beside the "
            "book AND the top-tier calls' profit at Sleeper's recorded prices both sit wholly above zero"
            + (f"; the next is after week {nxt}." if nxt else "."))
    ar = cur.get("at_review")
    if ar:
        w, pr = ar["weight"], ar["profit"]
        wtxt = (f"carried a weight of {ci(w)} beside the book's price" if w.get("estimated")
                else f"had too few calls ({ar['n_calls']}) to estimate its weight")
        ptxt = (f"its top-tier calls made {pr['net_per_100']:+.1f} per $100 at Sleeper's recorded prices "
                f"(95% {pr['lo']:+.1f} to {pr['hi']:+.1f}, {pr['n_bets']} bets)" if pr.get("estimated")
                else f"its top-tier calls ({pr['n_bets']} bets) were too few to judge profit")
        head = f"At the week-{ar['week']} review the current pricing model ({name}) {wtxt}, and {ptxt}"
        if cur.get("gate_open"):
            return (head + " -- both wholly above zero, so the label gate is OPEN until the next review; the "
                    "scorecard says so and labels are the user's call." + ctx)
        return head + ". " + rule + ctx
    if not cur.get("estimated"):
        return (f"The current pricing model ({name}) has {cur['n_calls']} graded calls ({wk(cur)}), too few to "
                "estimate whether its numbers add anything beside the book's price, so no line carries a bet "
                "label. " + rule + ctx)
    return (f"Graded so far, the current pricing model ({name}, {wk(cur)}, {cur['n_calls']} calls) carries a "
            f"running weight of {ci(cur)} beside the book's price; no review has been reached, so no line carries "
            "a bet label. " + rule + ctx)


def research_statement(RESEARCH: pd.DataFrame, gate=None) -> str:
    """The report's first line: what this sheet is, what it is not, and the
    graded record behind that."""
    if RESEARCH is None or not len(RESEARCH):
        return "**No yardage or catch lines were priced for this game.**"
    n = RESEARCH.drop_duplicates(["player", "market", "line"]).shape[0]
    return f"**{n} lines priced.** A research sheet, not a bet list. " + gate_sentence(gate)


BOOK_NAME = {"sleeper": "Sleeper", "draftkings": "DraftKings", "fanduel": "FanDuel"}


break_even_cell = RSCH.break_even_cell


def first_passers(pbp):
    """{(game_id, team): the QB who threw the team's first pass} -- the starts."""
    if pbp is None or not len(pbp) or "passer_player_id" not in pbp:
        return pd.Series(dtype=object)
    p_ = pbp[pbp.passer_player_id.notna() & pbp.posteam.notna()]
    if "play_id" in p_:
        p_ = p_.sort_values(["game_id", "play_id"])
    return p_.groupby(["game_id", "posteam"]).passer_player_id.first()


def qb_starts(pbp, gsis_id, first=None) -> int:
    """Games this season in which this QB threw his team's first pass (the start)."""
    first = first_passers(pbp) if first is None else first
    return int((first == gsis_id).sum()) if len(first) else 0


BRIEF_ARGS = ("AWAY", "HOME", "market_env", "M", "pop", "iw", "pbp", "STARTER_QB", "AUTO_QB", "LINE_STATUS",
              "TEAM_VOL_CHK", "UNIT_EFF", "PA", "weather", "roof", "ROOF_NOTE", "R", "G", "WEEK", "TEAM_VOL_ROWS",
              "STATE_N")


def brief_section(**V) -> list[str]:
    """The team matchup section, to the user's format and voice guide (2026-10-06): the header and
    sources line, then 1 the market, 2 expected volume, 3 unit against unit, 4 who plays, 5
    production allowed by position, 6 weather and venue, 7 where the baseline could miss -- one
    compact table each, home team first. The opening thesis, every narration and section 8 (game
    flow) are chat's to write (SKILL.md). Every input is a named argument (BRIEF_ARGS); a missing
    one is an error, never a silently empty table. Context only: nothing here moves a price."""
    missing = [k for k in BRIEF_ARGS if k not in V]
    if missing:
        raise TypeError(f"brief_section is missing {missing}")
    AWAY, HOME, ME_ = V["AWAY"], V["HOME"], V.get("market_env") or {}
    M, pop, iw, pbp, G, WEEK = V["M"], V["pop"], V["iw"], V["pbp"], V["G"], V["WEEK"]
    R = V.get("R")
    wx = V.get("weather") or {}
    roof, note = V.get("roof"), V.get("ROOF_NOTE")
    chk = V.get("TEAM_VOL_CHK") or {}
    # ---- header ----
    kick = eastern_to_utc(G.gameday, G.gametime) if pd.notna(G.get("gametime")) else None
    dst = kick is not None and (kick - pd.Timestamp(f"{G.gameday} {G.gametime}").tz_localize("UTC")) == pd.Timedelta(hours=4)
    when = RSCH.kickoff_words(G.get("weekday"), G.gameday, G.gametime, HOME, dst,
                              neutral=str(G.get("location", "Home")) == "Neutral")
    rest = ({HOME: int(G.home_rest), AWAY: int(G.away_rest)}
            if pd.notna(G.get("home_rest")) and pd.notna(G.get("away_rest")) else None)
    quoted = None
    if R is not None and len(R) and "last_update" in R:
        lu_ = R.last_update.dropna()
        books_ = ", ".join(sorted(BOOK_NAME.get(b_, b_) for b_ in set(R.book.dropna()))) if "book" in R else ""
        quoted = (f"player prices ({books_}) " if books_ else "player prices ") + \
            str(lu_.max())[:16].replace("T", " ") + " UTC" if len(lu_) else None
    reported = set(iw.team) if len(iw) and "team" in iw else set()
    inj = (f"injury report: week {WEEK} published for " + " and ".join(sorted({AWAY, HOME} & reported))
           if {AWAY, HOME} & reported else f"injury report: week {WEEK} not yet published")
    srcs = [(f"spread and total ({ME_.get('book') or 'book not recorded'}) "
             f"{str(ME_.get('as_of'))[:16].replace('T', ' ')} UTC") if ME_.get("as_of") else "spread and total: time not recorded",
            *([quoted] if quoted else []), inj,
            f"performance through week {WEEK - 1}",
            (f"weather forecast {str(wx.get('updated') or '')[:16].replace('T', ' ')} UTC" if wx.get("status") == "ok"
             else "weather forecast not included in this run")]
    L = ["## Team matchup\n",
         *RSCH.matchup_header(AWAY, HOME, when, G.stadium, roof, note, rest, srcs), "",
         "### 1. The market's view of the game\n",
         *RSCH.market_table(AWAY, HOME, ME_.get("home_spread"), ME_.get("total_line"), ME_.get("book"),
                            (str(ME_.get("as_of"))[:16].replace("T", " ") + " UTC") if ME_.get("as_of") else None), ""]
    gs = RSCH.game_state_table(chk, AWAY, HOME, V.get("STATE_N"))
    if gs:
        L += [*gs, ""]
    # ---- 2. expected volume ----
    ot = RSCH.outlook_table(chk, AWAY, HOME)
    L += ["### 2. Expected volume and how the teams have been playing\n",
          *(ot or ["Team volume: not included in this run."]), ""]
    # a QB change makes the starts behind the season average worth seeing apart
    starters = V.get("STARTER_QB") or {}
    auto = {a_["team"]: a_ for a_ in (V.get("AUTO_QB") or [])}
    FP = first_passers(pbp)
    sid = {t: (lambda g_: g_.iloc[0] if len(g_) else None)(M[(M.team == t) & (M.name == starters[t])].gsis_id)
           for t in (AWAY, HOME) if starters.get(t) is not None}
    qb_change = {}
    for t in (AWAY, HOME):
        if t in auto:
            qb_change[t] = f"{auto[t]['starter']} starts for {auto[t]['out']}"
        elif sid.get(t):
            mine = qb_starts(pbp, sid[t], FP)
            team_fp = FP[[k[1] == t for k in FP.index]] if len(FP) else FP
            others = int((team_fp != sid[t]).sum()) if len(team_fp) else 0
            if others and mine <= 1:          # another QB started for this team: a real change
                qb_change[t] = f"{starters[t]}, start {mine + 1} this season after {others} by another QB"
    for t in (HOME, AWAY):
        if t in qb_change and (V.get("TEAM_VOL_ROWS") or {}).get(t):
            L += [f"{t}'s games, quarterback change ({qb_change[t]}):", "",
                  *RSCH.recent_games_table(t, V["TEAM_VOL_ROWS"][t]), ""]
    # ---- 3. unit against unit ----
    ut = RSCH.unit_table(V.get("UNIT_EFF") or {}, AWAY, HOME, window=f"weeks 1-{WEEK - 1}" if WEEK > 2 else "week 1")
    L += ["### 3. Unit performance and matchup: scores and tiers\n",
          *(ut or ["Unit scores: not included in this run (no EPA in this season's play-by-play yet)."]), ""]
    # ---- 4. who plays ----
    cells = {}
    prac = (iw.set_index("gsis_id")["practice_status"].to_dict()
            if len(iw) and {"gsis_id", "practice_status"}.issubset(iw.columns) else {})
    for t in (AWAY, HOME):
        c = {}
        qn = starters.get(t)
        if qn is not None:
            n_ = qb_starts(pbp, sid[t], FP) + 1 if sid.get(t) else None
            st_ = pop[(pop.team == t) & (pop.name == qn)].report_status
            st_ = st_.iloc[0] if len(st_) and isinstance(st_.iloc[0], str) else None
            if t in auto:
                c["Quarterback"] = (f"{qn} starts" + (f" ({RSCH.ordinal(n_)} start this season)" if n_ else "")
                                    + f"; {auto[t]['out']} out" + (f" ({auto[t]['why']})" if auto[t]["why"] else ""))
            else:
                c["Quarterback"] = f"{qn} starts; {st_ if st_ else 'no injury designation'}" + (
                    f"; {RSCH.ordinal(n_)} start this season" if n_ and n_ <= 3 else "")
        ls = (V.get("LINE_STATUS") or {}).get(t) or []
        if len(ls) >= 5:
            word = {"out": "out", "questionable": "questionable", "playing": "available", "unmatched": "status unknown"}
            avail = sum(1 for x in ls if x["state"] != "out")
            c["Offensive line"] = (f"{avail} of 5 regulars available: "
                                   + ", ".join(f"{x['name']} ({x['pos']}, {word.get(x['state'], x['state'])})"
                                               for x in ls))
        sk = pop[(pop.team == t) & pop.report_status.apply(lambda v: isinstance(v, str) and v != "")]
        c["Receivers, tight ends and backs"] = "; ".join(
            f"{r['name']} ({r.pos}, {r.report_status}"
            + (f", practice: {prac[r.gsis_id]}" if isinstance(prac.get(r.gsis_id), str) and prac.get(r.gsis_id) else "")
            + ")" for _, r in sk.iterrows() if r.pos != "QB") or "no designations"
        if len(iw) and "position" in iw and (iw.team == t).any():
            dfn = iw[(iw.team == t) & iw.position.isin(RSCH.DEF_POS)
                     & iw.report_status.isin(["Out", "Doubtful", "Questionable"])]
            c["Pass rush and coverage"] = "; ".join(f"{r.full_name} ({r.position}, {r.report_status})"
                                                    for r in dfn.itertuples()) or "no designations"
        else:
            c["Pass rush and coverage"] = "no injury report yet this week"
        cells[t] = c
    who_note = (f"Official report: week {WEEK} " + ("published for " + " and ".join(sorted({AWAY, HOME} & reported))
                                                   if {AWAY, HOME} & reported else "not yet published")
                + ". Before it, a quarterback's status can come from Sleeper's injury feed, labelled where used; "
                  "statuses not yet published stay unknown. Offensive line = the five linemen with the most snaps "
                  "this season.")
    L += ["### 4. Who plays: injuries and replacements\n", *RSCH.personnel_table(cells, AWAY, HOME, who_note), ""]
    # ---- 5. production allowed ----
    pt = RSCH.positional_table(V.get("PA"), (HOME, AWAY))
    if pt:
        L += ["### 5. Production allowed by position\n", *pt, ""]
    # ---- 6. weather and venue ----
    L += ["### 6. Weather and venue\n", RSCH.weather_line(wx, roof, note), ""]
    # ---- 7. where the baseline could miss ----
    mk = set(R.market) if R is not None and len(R) else set()
    spread = ME_.get("home_spread")
    fav = (HOME if spread < 0 else AWAY) if spread is not None else None
    priced = set(R.player) if R is not None and len(R) else set()
    ctx = {"qb_change": qb_change, "fav": fav, "dog": (AWAY if fav == HOME else HOME) if fav else None,
           "spread": abs(spread) if spread is not None else None,
           "new_team": sorted(n for n in M[M.new_team.astype(bool)].name if n in priced),
           "questionable": sorted(n for n in M[M.questionable.astype(bool)].name if n in priced),
           "has_pass_lines": "player_pass_yds" in mk,
           "has_rush_lines": bool({"player_rush_yds", "player_rush_reception_yds"} & mk),
           "markets": mk,
           "implied": ({HOME: (ME_["total_line"] - ME_["home_spread"]) / 2, AWAY: (ME_["total_line"] + ME_["home_spread"]) / 2}
                       if ME_.get("home_spread") is not None and ME_.get("total_line") is not None else {}),
           "oline_out": {t: sum(1 for x in ((V.get("LINE_STATUS") or {}).get(t) or []) if x["state"] == "out")
                         for t in (AWAY, HOME)},
           "wind_mph": wx.get("wind_mph_max") if wx.get("status") == "ok" else None,
           "roof": roof, "roof_note": note}
    L += ["### 7. Where the baseline could miss this game\n", *RSCH.known_gaps_table(RSCH.known_gaps(ctx)), ""]
    return L


def research_cells(x, MKT) -> str:
    """One research row's cells: | prop | line | price | projection | Over model / book | line implies |
    break-even workload |."""
    def odds(a):
        try:
            a = int(a)
        except (TypeError, ValueError):
            return "—"
        return f"+{a}" if a > 0 else f"{a}"
    unit_ = x.unit if isinstance(x.unit, str) else ""
    if pd.notna(x.implied) and pd.notna(x.projected):
        imp = f"{x.implied:.1f} {unit_} (we project {x.projected:.1f})"
    elif pd.notna(x.projected):
        imp = f"outside the search range (we project {x.projected:.1f} {unit_})"
    else:
        imp = "—"
    n0 = lambda v: f"{int(round(float(v))) + 0}"
    book = str(x.get("book", "sleeper"))
    label = MKT.get(x.market, x.market) + ("" if book == "sleeper" else f" ({BOOK_NAME.get(book, book)})")
    if isinstance(x.get("look"), str):       # worth a look (research.worth_a_look): bold, never a bet label
        label = f"**{label}**"
    return (f"| {label} | {x.line:g} | O {odds(x.price_over)} / U {odds(x.price_under)} | "
            f"{n0(x['median'])} ({n0(x['p10'])} to {n0(x['p90'])}) | {100*x.p_over_model:.0f}% / {100*x.p_over_book:.0f}% | {imp} | "
            f"{break_even_cell(x)} |")


def usage_line(u, rush=False, short=False):
    """Last game's snap and target (or carry) share against his earlier weeks."""
    if not u:
        return None
    pc = lambda v: "—" if v is None or pd.isna(v) else f"{100*v:.0f}%"
    blank = lambda v: v is None or (isinstance(v, float) and np.isnan(v))
    # share / count: '19% / 6' last game, '25% / 8.3' a game before it (the user's format)
    n, nb = (u.get("cn"), u.get("cn_base")) if rush else (u.get("tn"), u.get("tn_base"))
    last_n = "" if blank(n) else f" / {float(n):.0f}"
    base_n = "" if blank(nb) else f" / {float(nb):.1f}"
    share = ("carries", u["cs"], u["cs_base"]) if rush else ("targets", u["ts"], u["ts_base"])
    if short:
        return (f"wk{u['week']}: snaps {pc(u['snap'])} ({pc(u['snap_base'])}), "
                f"{share[0]} {pc(share[1])}{last_n} ({pc(share[2])}{base_n})")
    return (f"Week {u['week']}: snaps {pc(u['snap'])} (earlier weeks {pc(u['snap_base'])}), "
            f"{share[0]} {pc(share[1])} of the team's{last_n.replace(' / ', ', ')} "
            f"(earlier {pc(share[2])}{base_n.replace(' / ', ', ') + ' a game' if base_n else ''}).")


SCEN_KEY = ["book", "market", "player", "side", "line"]
MARKET_WORDS = {"player_receptions": "catches", "player_reception_yds": "receiving yards",
                "player_rush_yds": "rushing yards", "player_pass_yds": "passing yards",
                "player_rush_reception_yds": "rushing + receiving yards"}


def run_scenarios(q: pd.DataFrame, R: pd.DataFrame, slug: str, snap_path: Path) -> list[str]:
    """For each Questionable player, price the game again with him OUT: a full
    run of this script with --assume-out, on the lines this run saved. The
    main run already priced the 'he plays' case at his normal share. Nothing
    here is blended; the report shows both and the user decides. Scenario
    outputs go to OUT/scenarios, which record_run never reads."""
    L = ["", "## If a Questionable player is out", "",
         "Every line above is priced as if the Questionable players play their normal role. Below, "
         "the same lines priced with each one OUT, the way an Out player is handled: most of his share "
         "goes to his replacement; a quarter of his targets and carries stays with the priced teammates, "
         "mostly at his position (measured on 2024-25 absences). His own props void if he sits. Only lines whose probability moves by at least "
         "1 point are listed. Neither case is weighted by how likely he is to play: that call is yours."]
    # the scenario compares against THIS run's lines only: no merge with earlier logs
    argv = _scenario_argv(("--prior-log", "--prior-archive", "--assume"))
    for _, pl in q.iterrows():
        cmd = [sys.executable, str(Path(__file__).resolve()), *argv, "--assume-out", pl.gsis_id,
               "--odds-snapshot", str(snap_path), "--no-scenarios"]
        f = OUT / "scenarios" / f"shadow_log_{slug}.csv"
        f.unlink(missing_ok=True)   # never read a leftover from an earlier scenario
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        L += ["", f"### If {pl['name']} ({pl.team} {pl.pos}) is out", ""]
        if r.returncode != 0 or not f.exists():
            L.append(f"Scenario failed (exit {r.returncode}): {r.stderr.strip().splitlines()[-1][:200] if r.stderr.strip() else 'no output'}.")
            continue
        S = pd.read_csv(f)
        dest = OUT / "scenarios" / f"shadow_log_{slug}_out_{pl.gsis_id}.csv"
        f.replace(dest)
        if R.empty:
            L.append("No priced lines to compare.")
            continue
        j = R.merge(S[SCEN_KEY + ["p_model"]], on=SCEN_KEY, how="left", suffixes=("", "_out"))
        j = j[j.player != pl["name"]]
        j["move"] = j["p_model_out"] - j["p_model"]
        j = j[j["move"].abs() >= 0.01].sort_values("move", key=lambda x: -x.abs())
        if j.empty:
            L.append("No other line moves by 1 point or more.")
            continue
        L += ["| player | line | book | market says | if he plays | if he's out | change |",
              "|---|---|---|---|---|---|---|"]
        for _, x in j.iterrows():
            what = ("scores a TD" if x.market == "player_anytime_td" else
                    f"{x.side} {x.line:g} {MARKET_WORDS.get(x.market, x.market)}")
            L.append(f"| {x.player} ({x.team}) | {what} | {x.book} | {x.p_novig:.0%} | {x.p_model:.0%} | "
                     f"{x.p_model_out:.0%} | {x.move:+.0%} |")
    return L


def _sides(x):
    """(P(Over), P(Under), P(push)) from a shadow-log row, which carries the
    model's favoured side only."""
    push = 0.0 if pd.isna(x.p_push) else float(x.p_push)
    p = float(x.p_model)
    over = p if x.side == "Over" else 1 - p - push
    return over, 1 - over - push, push


def _scenario_argv(drop=("--prior-log", "--prior-archive")):
    """This run's arguments minus the given flags and their values. A scenario
    compares against THIS run's lines only (no earlier-log merges); an 'if he
    is out' run also drops --assume (it prices the board as it stands)."""
    argv, skip = [], False
    for x in sys.argv[1:]:
        if skip:
            skip = False
        elif x in drop:
            skip = True
        elif not x.startswith(tuple(f"{d}=" for d in drop)):
            argv.append(x)
    return argv


def _price_scenario(slug, snap, assume, label):
    """One scenario pricing in a subprocess. assume None keeps this run's own --assume
    flags; a list replaces them (one end of a range). Returns (lines, None) or (None, why)."""
    drop = ("--prior-log", "--prior-archive") + (() if assume is None else ("--assume",))
    extra = [] if assume is None else [y for a in assume for y in ("--assume", a)]
    cmd = [sys.executable, str(Path(__file__).resolve()), *_scenario_argv(drop), *extra, "--scenario-run",
           "--odds-snapshot", str(snap), "--no-scenarios"]
    f = OUT / "scenarios" / f"shadow_log_{slug}.csv"
    f.unlink(missing_ok=True)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0 or not f.exists():
        tail = r.stderr.strip().splitlines()[-1][:300] if r.stderr.strip() else "no output"
        return None, f"exit {r.returncode}: {tail}"
    S = pd.read_csv(f)
    f.replace(OUT / "scenarios" / f"shadow_log_{slug}_assume{'' if assume is None else '_' + label}.csv")
    return S, None


def run_user_scenario(R: pd.DataFrame, RESEARCH: pd.DataFrame, slug: str, snap: Path | None, rules) -> list[str]:
    """YOUR scenario (scenario.py, DECISIONS #153): the same lines priced again
    with the user's workload assumptions, beside the board's own numbers, the
    break-even at each side's price and what each side would return IF the
    assumptions are right. Written to OUT/scenarios, never recorded."""
    L = ["", "## Your scenario (experimental)", "",
         f"**Your assumptions:** {SC.describe(rules)}. "
         + ("An auto range is one standard error of his recent share around our projection: how sure we are "
            "of his average workload, not a forecast of this game. " if any(r_.get("auto") for r_ in rules)
            else "These are assumptions, not confidence intervals. ") + "Every "
         "line below is priced again from the same simulation with only those inputs changed: what one player "
         "gains in targets or carries his teammates give up in proportion, receptions and receiving yards move "
         "together, and the starting QB's passing yards follow his receivers. The model's chances are not shown "
         "to be calibrated within 3 points (reports/calibration_bar_v2.md), so a return of a few dollars per $100 "
         "sits inside that error. Touchdown prices are not adjusted.", ""]
    if snap is None or not Path(snap).exists():
        return L + ["Not priced: this run saved no lines to price against."]
    if R.empty:
        return L + ["No priced lines to compare."]
    variants = SC.range_variants(rules)
    runs = {}
    for lab, assume in (variants or [("expected", None)]):
        S, err = _price_scenario(slug, snap, assume, lab)
        if err:
            return L + [f"Scenario failed{'' if variants is None else f' ({lab} run)'}: {err}"]
        runs[lab] = S
    S = runs["expected"]
    key = ["book", "market", "player", "line"]
    base = R[R.market != "player_anytime_td"].drop_duplicates(key)
    j = base.merge(S[key + ["side", "p_model", "p_push"]].drop_duplicates(key), on=key, how="left",
                   suffixes=("", "_sc"))
    for lab, suf in (("low", "_lo"), ("high", "_hi")):
        if lab in runs:
            E = runs[lab][key + ["side", "p_model", "p_push"]].drop_duplicates(key)
            j = j.merge(E.rename(columns={c: c + suf for c in ("side", "p_model", "p_push")}), on=key, how="left")
    pays = ({(r.player, r.market, float(r.line), r.book): RSCH.break_even_cell(r)
             for _, r in RESEARCH.iterrows()} if len(RESEARCH) else {})
    named = {x["who"] for x in rules if not x["team"]}
    teams_named = {x["who"] for x in rules if x["team"]}
    rows = []
    for _, x in j.iterrows():
        if pd.isna(x.get("p_model_sc")):
            continue
        o0, u0, _p0 = _sides(x)
        o1, u1, p1 = _sides(pd.Series({"p_model": x.p_model_sc, "side": x.side_sc, "p_push": x.p_push_sc}))
        moved = [o1] + [_sides(pd.Series({"p_model": x["p_model" + suf], "side": x["side" + suf],
                                          "p_push": x["p_push" + suf]}))[0]
                        for suf in ("_lo", "_hi") if variants and pd.notna(x.get("p_model" + suf))]
        if max(abs(v - o0) for v in moved) < 0.005 and x.player not in named and x.team not in teams_named:
            continue
        po, pu = x.get("price_over"), x.get("price_under")
        ev_o = SC.net_per_100(po, o1, u1) if pd.notna(po) else None
        ev_u = SC.net_per_100(pu, u1, o1) if pd.notna(pu) else None
        row = dict(player=x.player, team=x.team, market=x.market, line=float(x.line), book=x.book,
                   price_over=po, price_under=pu, be_over=RSCH.breakeven(po), be_under=RSCH.breakeven(pu),
                   over_model=o0, over_scenario=o1, under_scenario=u1, push_scenario=p1,
                   net_over=ev_o, net_under=ev_u,
                   pays_if=pays.get((x.player, x.market, float(x.line), x.book), "—"),
                   named=x.player in named)
        if variants:
            ends = {}
            for suf in ("_lo", "_hi"):
                ends[suf] = ((None, None) if pd.isna(x.get("p_model" + suf)) else
                             _sides(pd.Series({"p_model": x["p_model" + suf], "side": x["side" + suf],
                                               "p_push": x["p_push" + suf]}))[:2])
            row.update(over_low=ends["_lo"][0], over_high=ends["_hi"][0],
                       verdict_over=SC.range_verdict(ends["_lo"][0], o1, ends["_hi"][0], row["be_over"]),
                       verdict_under=SC.range_verdict(ends["_lo"][1], u1, ends["_hi"][1], row["be_under"]))
        rows.append(row)
    if not rows:
        return L + ["No line moves by half a point or more under these assumptions."]
    T = pd.DataFrame(rows)
    T["move"] = (T.over_scenario - T.over_model).abs()
    T = T.sort_values(["named", "move"], ascending=[False, False])
    odds = lambda v: "—" if v is None or pd.isna(v) else (f"+{int(v)}" if v > 0 else f"{int(v)}")
    pc = lambda v: "—" if v is None or pd.isna(v) else f"{100 * v:.0f}%"
    money = lambda v: "—" if v is None or pd.isna(v) else f"{v:+.1f}"
    if variants:
        def verdict(x):
            v = [f"{side} {x[f'verdict_{side.lower()}']}" for side in ("Over", "Under")
                 if x[f"verdict_{side.lower()}"] not in (None, "does not pay in your range")]
            return "; ".join(v) or "neither side pays in your range"
        L += ["| Player | Prop | Line | Price (O / U) | Break-even (O / U) | Over: board / your low / expected / high | "
              "Your range | Net per $100 at your expected: Over / Under | Pays at this price if you expect |",
              "|---|---|---|---|---|---|---|---|---|"]
        for _, x in T.iterrows():
            L.append(f"| {x.player} ({x.team}) | {MARKET_WORDS.get(x.market, x.market)} | {x.line:g} | "
                     f"O {odds(x.price_over)} / U {odds(x.price_under)} | {pc(x.be_over)} / {pc(x.be_under)} | "
                     f"{pc(x.over_model)} / {pc(x.over_low)} / {pc(x.over_scenario)} / {pc(x.over_high)} | "
                     f"{verdict(x)} | {money(x.net_over)} / {money(x.net_under)} | {x.pays_if} |")
        L += ["", "Your range is priced three times: every range at its low, then at its expected, then at its "
              "high (fixed assumptions stay put). 'Pays across your range' means the side clears its break-even "
              "at your low, expected and high alike; 'pays only at your high' means it needs that end of what you "
              "assumed. A teammate's line can run the other way: his Over may pay only at your low."]
    else:
        L += ["| Player | Prop | Line | Price (O / U) | Break-even (O / U) | Over: board / your scenario | "
              "If your scenario is right, net per $100: Over / Under | Pays at this price if you expect |",
              "|---|---|---|---|---|---|---|---|"]
        for _, x in T.iterrows():
            L.append(f"| {x.player} ({x.team}) | {MARKET_WORDS.get(x.market, x.market)} | {x.line:g} | "
                     f"O {odds(x.price_over)} / U {odds(x.price_under)} | {pc(x.be_over)} / {pc(x.be_under)} | "
                     f"{pc(x.over_model)} / {pc(x.over_scenario)} | {money(x.net_over)} / {money(x.net_under)} | "
                     f"{x.pays_if} |")
    L += ["", "Lines are listed for the players and teams you named, then any other line whose Over moves by half "
          "a point or more. 'Pays at this price' is the board's break-even workload: compare it with the "
          "workload you assumed."]
    out = {"logged_at_utc": now(), "assumptions": [x["text"] for x in rules], "rules": rules,
           "range_runs": None if variants is None else {lab: a_ for lab, a_ in variants},
           "lines": T.drop(columns=["move"]).to_dict(orient="records")}
    (OUT / "scenarios" / f"scenario_{slug}.json").write_text(json.dumps(out, indent=1, default=str) + "\n",
                                                            encoding="utf-8")
    return L


if __name__ == "__main__":
    main()
