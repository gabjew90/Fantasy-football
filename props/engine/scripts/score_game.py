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
(outcome-backtested, not tested against posted lines); rush_yds_v0 is PROTOTYPE too. The
2022-25 yardage harness (reports/yardage_harness.md) finds all three yardage markets unbiased
but too NARROW, so probabilities far from 50% run high.
Nothing is a fair price or an entry threshold.
Recommendation is PASS on every line, per the model registry.
"""
import argparse, json, os, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

import re
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eligibility
import model as MODEL
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
        return json.load(open(p))
    obj = loader()
    p.parent.mkdir(parents=True, exist_ok=True)
    json.dump(obj, open(p, "w"))
    return obj
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
YARD_MARKETS = {"player_reception_yds": "rec_yards", "player_rush_yds": "rush_yards"}
COUNT_MARKETS = {"player_receptions": "receptions"}
CONSENSUS_TOL = {"player_receptions": 1.0, "player_reception_yds": 4.0, "player_rush_yds": 5.0}


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
        raise RuntimeError(f"odds_client {stage} returned no JSON (exit {r.returncode}): {r.stderr.strip()[-300:]}")


# ---------------------------------------------------------------- CLI conveniences
# Abbreviations people type that games.csv spells differently.
CLI_ALIASES = {"LAR": "LA", "WSH": "WAS", "JAC": "JAX", "LVR": "LV"}
MARKET_ALIASES = {"receptions": "player_receptions", "rec": "player_receptions",
                  "rec_yds": "player_reception_yds", "receiving_yards": "player_reception_yds",
                  "rush_yds": "player_rush_yds", "rushing_yards": "player_rush_yds",
                  "td": "player_anytime_td", "anytime_td": "player_anytime_td", "atd": "player_anytime_td"}
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
    if ASSUME_OUT:
        OUT = OUT / "scenarios"

    AWAY, HOME = resolve_team(a.away), resolve_team(a.home)
    wd = Path(a.workdir); wd.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20260917)

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
    roof = str(G.roof).lower()
    log(f"verified: {AWAY} at {HOME}, {SEASON} week {WEEK}, {G.gameday} {G.gametime} ET, "
        f"{G.stadium}, roof={roof}")

    PRIOR = a.prior_season or SEASON - 1
    P = json.load(open(RES / f"priors_{PRIOR}_params.json"))
    K0 = P["K0"]                              # fallback flat constant, kept for any rate not in k0_per_rate
    K0R = P.get("k0_per_rate", MODEL.DEFAULT_K0)   # per-rate constants, tuned by build_priors.py (round 5)
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
                    market_env = {"home_spread": home_spread, "total_line": total_line}   # TD anchor always; plays/pass-rate only with --env market
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
                    market_env = {"home_spread": float(o_["spread"]), "total_line": float(o_["overUnder"])}
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
    for t in (AWAY, HOME):
        d = dcf[(dcf.team == t) & (dcf.dt < kick) & dcf.pos_abb.isin(["QB", "RB", "WR", "TE"])]
        if d.empty:
            continue
        d = d[d.dt == d.dt.max()]
        for pos, mx in [("QB", 1), ("RB", 2), ("WR", 3), ("TE", 1)]:
            for _, r in d[(d.pos_abb == pos) & (d.pos_rank <= mx)].iterrows():
                roles.append({"team": t, "gsis_id": r.gsis_id, "slot": f"{pos}{int(r.pos_rank)}",
                              "dc_dt": d.dt.max()})
    roles = pd.DataFrame(roles).drop_duplicates(["team", "gsis_id"])

    rw = ros[(ros.season == SEASON) & (ros.week == WEEK)][
        ["team", "gsis_id", "full_name", "position", "status"]].drop_duplicates(["team", "gsis_id"])
    if rw.empty:
        rw = ros[(ros.season == SEASON) & (ros.week == ros.week.max())][
            ["team", "gsis_id", "full_name", "position", "status"]].drop_duplicates(["team", "gsis_id"])
        log(f"  WARNING: no week {WEEK} roster rows; using week {ros.week.max()} as provisional")

    iw = inj[(inj.season == SEASON) & (inj.week == WEEK)]
    inj_status = iw.set_index(["team", "gsis_id"])["report_status"].to_dict()
    inj_practice = iw.set_index(["team", "gsis_id"])["practice_status"].to_dict()

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
            if r.empty or r.status.iloc[0] not in ("ACT", "INA"):
                continue
            pop.append({"team": t, "gsis_id": pid, "name": r.full_name.iloc[0],
                        "pos": r.position.iloc[0], "status": r.status.iloc[0]})
    pop = pd.DataFrame(pop)
    if roles.empty:
        pop["slot"] = "PROXY"
    else:
        pop = pop.merge(roles[["team", "gsis_id", "slot"]], on=["team", "gsis_id"], how="left")
        pop["slot"] = pop["slot"].fillna("PROXY")
    pop["report_status"] = [inj_status.get((t, p)) for t, p in zip(pop.team, pop.gsis_id)]
    pop["practice_status"] = [inj_practice.get((t, p)) for t, p in zip(pop.team, pop.gsis_id)]

    # A2: Out/Doubtful removed; Questionable flagged for regime treatment
    pop["excluded"] = pop.report_status.isin(["Out", "Doubtful"]) | (pop.status == "INA")
    pop["questionable"] = pop.report_status.eq("Questionable")
    if ASSUME_OUT:
        _ao = pop.gsis_id.isin(ASSUME_OUT)
        pop.loc[_ao, "report_status"] = "Out (scenario)"
        pop["excluded"] = pop["excluded"] | _ao
        pop["questionable"] = pop["questionable"] & ~_ao
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
        env[t]["source"] = "history"
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
            "team": p.team, "pos": POS_GROUP.get(p.pos, p.pos),
            "ts": float(pri.target_share) if pri is not None and pd.notna(pri.target_share)
                  else slot_val(sl, "target_share", 0.0),
            "rs": float(pri.rush_share) if pri is not None and pd.notna(pri.rush_share)
                  else slot_val(sl, "rush_share", 0.0),
            "i10ts": float(pri.i10_target_share) if pri is not None and pd.notna(pri.i10_target_share)
                     else slot_val(sl, "i10_target_share", 0.0),
            "i10rs": float(pri.i10_carry_share) if pri is not None and pd.notna(pri.i10_carry_share)
                     else slot_val(sl, "i10_carry_share", 0.0)})
    E = pd.DataFrame(excl_rates)
    M, redistributed = apply_out_rule(M, E, (AWAY, HOME))
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

    # ---------- 6. simulate: JOINT per-team draws (round 5, review item 6) ----------
    # One team-targets draw and one team-carries draw per simulation, shared by every
    # player on that team, then a multinomial split across the eligible set plus an
    # "other" bucket. Teammates are negatively correlated within a simulation (a fixed
    # total means more for A is less for B) and every player shares the team's own
    # play-count variance. Independent per-player draws had neither property, which
    # made same-game-parlay probabilities impossible to state.
    SH = P["shape_ypc_per_catch"]
    TVD = P.get("team_volume_dispersion", {"targets_r": 30.0, "carries_r": 30.0})
    sims = {}
    team_targets_draw, team_carries_draw = {}, {}
    for t in (AWAY, HOME):
        Mt = M[M.team == t]
        names = list(Mt.name)
        shares_t = {n: float(v) for n, v in zip(Mt.name, Mt.ts)}
        crs_t = {n: float(v) for n, v in zip(Mt.name, Mt.cr)}
        ypt_t = {n: float(v) for n, v in zip(Mt.name, Mt.ypt)}
        out_rec, tt_draw = MODEL.simulate_team_game(rng, N_SIM, env[t]["targets"], TVD["targets_r"],
                                                    shares_t, crs_t, ypt_t, SH, other_bucket=True)
        team_targets_draw[t] = tt_draw
        # carries: same joint structure, per-carry yards from the empirical league residual grid
        car_t, rush_t, tc_draw = MODEL.simulate_team_rush(rng, N_SIM, env[t]["carries"], TVD["carries_r"],
                                                          [float(v) for v in Mt.rs], [float(v) for v in Mt.ypc], resid)
        team_carries_draw[t] = tc_draw
        for j, (_, m) in enumerate(Mt.iterrows()):
            rec, yds = out_rec[m["name"]]
            sims[m["name"]] = {"receptions": rec, "rec_yards": yds, "rush_yards": rush_t[j], "carries": car_t[j]}
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
    weather = {"status": "skipped (closed roof)" if roof in ("closed", "dome") else "not attempted"}
    STADIUM_LL = {}   # filled from games.csv when available; else geocode by stadium is not attempted
    if roof not in ("closed", "dome"):
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
                  "rushing_yards": "player_rush_yds", "anytime_touchdowns": "player_anytime_td"}
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
                     "sleeper_pos_rank": pos_rank}
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
                        pr = M[M.name == nm].iloc[0]
                        if mk["key"] == "player_rush_yds" and pr.pos == "QB":
                            continue   # kneels not modelled; prop settles incl. kneels
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
                            new_team=bool(pr.new_team), questionable=bool(pr.questionable)))
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
        R.to_csv(logf, index=False)
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



    # ---------- 8b/9. report, written for a casual reader ----------
    MKT = {"player_receptions": "catches", "player_reception_yds": "receiving yards",
           "player_rush_yds": "rushing yards", "player_anytime_td": "to score a touchdown"}

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
            parts.append(f"Blending those, we project **{pct(m.ts)}** of the throws = about **{e['targets']*m.ts:.1f} targets**, "
                         f"and he catches roughly {pct(m.cr)} of his targets, so about **{m.mu_rec:.1f} catches**"
                         + (f" for about **{r.model_mean:.0f} yards**" if r.market == "player_reception_yds" else "") + ".")
            parts.append(f"Run that 20,000 times with normal game-to-game swings and he lands **{r.side.lower()} {r.line}** {in_ten(r.p_model)} ({pct(r.p_model)}).")
            out.append("**How we got our number.** " + " ".join(parts))
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
        dollars = 100 * r.ER
        if r.market == "player_anytime_td":
            book_side = "you lose roughly the book's cut, typically $5 to $8 per $100 on this kind of market"
        else:
            book_side = f"it loses about ${100*(1-r.p_novig*(1+payout(r.price))):.0f} (that's the book's cut)"
        if withheld:
            pass     # a prototype with no posted-line test makes no claim about what a bet is worth
        elif dollars >= 0:
            out.append(f"**If our number is right:** a $100 bet here makes about **${dollars:.0f}** on average over many games. "
                       f"If the book's number is right, {book_side}.")
        else:
            out.append(f"**If our number is right:** a $100 bet here still loses about **${-dollars:.0f}** on average. "
                       f"The price is worse than even our number.")
        label, text = verdict_for(r, m)
        out.append(f"**Bottom line: {label}.** {text}")
        return out

    top = pd.DataFrame()
    if not R.empty:
        top = (R.sort_values("gap", key=abs, ascending=False)
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
                    ("player_rush_yds", "rush_yards", "rush yds", 0.5)]
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
            if mkey == "player_rush_yds" and m.pos == "QB":
                continue
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
    L.append(ev_statement(R) + "\n")

    # ---------- player-by-player card, in depth-chart order ----------
    L.append("*Model opinion, not yet tested against sportsbooks; six weeks of logged results decide whether to trust it. "
             "Rule for each prop: take the UNDER if the book's line is at or above our Under number, the OVER if it's at "
             "or below our Over number, otherwise no play. Yardage thresholds assume standard -110 pricing.*\n")

    SLOT_ORDER = {"QB1": 0, "RB1": 1, "WR1": 2, "WR2": 3, "TE1": 4, "WR3": 5, "RB2": 6, "PROXY": 7}
    def pct(x): return f"{100*x:.0f}%"
    def odds_str(a): a = int(a); return f"+{a}" if a > 0 else f"{a}"
    td_book = {}
    if not R.empty:
        for _, rr in R[R.market == "player_anytime_td"].iterrows():
            td_book.setdefault(rr.player, []).append((rr.book, rr.price, rr.p_novig))

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
            props = CARD[(CARD.player == m["name"]) & (CARD.call != "no line posted")]
            tdq = td_book.get(m["name"], [])
            if props.empty and not tdq:
                continue
            ev = m.evidence
            L.append(f"### {m['name']} — {m.slot}\n")

            # role summary, built from the evidence chain
            ts_ = ev.get("target_share", {}); rs_ = ev.get("rush_share", {})
            bits = []
            if pd.notna(ts_.get("own_prior")) and ts_["own_prior"] >= 0.04:
                bits.append(f"{pct(ts_['own_prior'])} of his team's throws last season over {int(ts_['n_prior'])} games")
            if pd.notna(ts_.get("cur_rate")) and ts_.get("cur_den", 0) > 0 and ts_["cur_num"] > 0:
                bits.append(f"{int(ts_['cur_num'])} of {int(ts_['cur_den'])} ({pct(ts_['cur_rate'])}) this season")
            if pd.notna(rs_.get("own_prior")) and rs_["own_prior"] >= 0.08:
                bits.append(f"{pct(rs_['own_prior'])} of the carries last season")
            if pd.notna(rs_.get("cur_rate")) and rs_.get("cur_den", 0) > 0 and rs_["cur_num"] > 0 and rs_["cur_rate"] >= 0.08:
                bits.append(f"{int(rs_['cur_num'])} of {int(rs_['cur_den'])} carries this season")
            if m.pos == "QB":
                L.append("**Role.** Starting quarterback. Passing props are not modeled here; rushing yards are "
                         "excluded because kneel-downs count against the prop and are not simulated.\n")
            else:
                role = "; ".join(bits) if bits else "little usage history"
                # medians, not means: yardage is right-skewed and the thresholds below key off
                # the median, so quoting the mean here made a 92-yard projection sit next to an
                # 87.5 line that read "no play"
                rec_med = float(np.median(sims[m['name']]['receptions']))
                yds_med = float(np.median(sims[m['name']]['rec_yards']))
                proj = f"typical game about {e['targets']*m.ts:.1f} targets, {rec_med:.0f} catches"
                if yds_med >= 8: proj += f", {yds_med:.0f} receiving yards"
                if m.mu_car >= 3: proj += f", {m.mu_car:.0f} carries for {float(np.median(sims[m['name']]['rush_yards'])):.0f} yards"
                L.append(f"**Role.** {role}. Blending that, {proj} (medians; upside games run higher).\n")
            flags = []
            if m.new_team: flags.append(f"changed teams ({m.prior_team} to {t}); one game of new-team data, so the book knows his role better than we do")
            if m.questionable: flags.append("listed Questionable; priced as if he plays his normal role; if he sits the prop voids")
            if m.role_scale != 1.0: flags.append(f"snap share on the new team scaled his projection by {m.role_scale:.2f}")
            if flags:
                L.append("**Watch.** " + " ".join(f + "." for f in flags) + "\n")

            # props table
            L.append("| Call | Prop | Book | Take UNDER if ≥ | Take OVER if ≤ |")
            L.append("|---|---|---|---|---|")
            for _, c in props.iterrows():
                u = f"{c.under_at:g}" if pd.notna(c.under_at) else "—"
                o = f"{c.over_at:g}" if pd.notna(c.over_at) else "—"
                bl = f"{c.book_line:g}" if pd.notna(c.book_line) else "—"
                call = f"**{c.call}**" if c.is_play else c.call
                if c.why and "far from us" in c.why: call += " *(book far from us; likely knows something)*"
                L.append(f"| {call} | {c.prop} | {bl} | {u} | {o} |")
            if tdq:
                bk, price, p_imp = sorted(tdq, key=lambda x: x[0] != "draftkings")[0]
                p_yes, td_src = p_anytime(m)
                # NO FAIR ODDS for anytime touchdowns until logged lines have
                # tested the model. A "take YES at +X" threshold IS a fair price,
                # and quoting one would present a prototype as a pricing edge.
                L.append(f"| no fair odds ({td_src}, prototype) | anytime TD | {odds_str(price)} "
                         f"(book {pct(p_imp)}, us {pct(p_yes)}) | — | |")
            L.append("")

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
        col = {"player_receptions": "receptions", "player_reception_yds": "rec_yards", "player_rush_yds": "rush_yards"}.get(row["market"])
        if col is None or row["player"] not in sims: return None
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
        log("\n=== Confidence tiers ===")
        for _, c in CONF.iterrows():
            log(f"  {c.tier:36s} {c.player} {c.side} {c.line if pd.notna(c.line) else ''} {c.market.replace('player_','')}  us {c.p_model:.0%} book {c.p_novig:.0%} gap {c.gap:+.0%}")
    if not PARLAY.empty:
        PARLAY.to_csv(OUT / f"parlays_{slug}.csv", index=False)
        log("\n=== Parlay candidates (STRONG legs only, joint sim) ===")
        for _, pr in PARLAY.head(8).iterrows():
            log(f"  {pr.legs}: joint {pr.p_joint:.1%} (indep {pr.p_if_independent:.1%}, corr x{pr.correlation_effect:.2f}) fair {pr.fair_price:+d}, take at {pr.take_at_or_longer:+d} or longer")
    elif not ENABLE_PARLAYS:
        log("\n=== Parlay candidates: DISABLED ===")
        log("  joint outcomes have never been checked against realised joint")
        log("  outcomes; marginal CRPS cannot detect a wrong correlation factor.")

    shown = CARD[CARD.call != "no line posted"]
    if not shown.empty:
        n_play = int(shown.would_play_if_validated.sum())
        n_under = int(shown.call.str.startswith("UNDER").sum())
        n_elig = int(shown.is_play.sum())
        L.append(f"*{n_play} of {len(shown)} posted yardage/reception props clear the edge rule at the price actually "
                 f"posted, {n_under} of them Unders. **{n_elig} are eligible to bet**, because no market's model has "
                 f"passed a holdout against real sportsbook lines yet — that gate is enforced, not advisory. "
                 f"The card leans Under overall; whether that is the model running low or the books shading toward the Over "
                 f"is what the logged results will settle.*\n")
    L.append("<details><summary>Everything else: how the numbers were built, sources, per-line arithmetic</summary>\n")

    # ---- plain-English summary box ----
    L.append("> **Read this first.** This report compares what the sportsbooks are charging on player props with what "
             "our own numbers say should happen. It does **not** recommend bets. Every line below is marked **no bet** "
             "because the model behind it has not yet proven it can beat the market. What it *is* useful for: seeing "
             "where the book and the numbers disagree, understanding why, and building a track record so we can find out "
             "over the season whether the numbers are worth trusting.\n")
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
                 "player_rush_yds": "rush yds", "player_anytime_td": "anytime TD"}
    SIM_COL = {"player_receptions": "receptions", "player_reception_yds": "rec_yards", "player_rush_yds": "rush_yards"}
    tier_of = {}
    if not CONF.empty:
        for _, c in CONF.iterrows():
            tier_of[(c.player, c.market, c.side)] = c.tier
    bet_rows = []
    if not R.empty:
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
            if mk != "player_anytime_td":
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

    # portfolio exposure: how many card legs ride on each team's pass/run volume, and the
    # joint probability that the whole cluster hits (from the joint simulation)
    EXPO = []
    if not BET.empty:
        for (tm, vol), g in BET[BET.correlated_with.str.contains("throws|runs", regex=True, na=False)].assign(
                vol=lambda d: d.correlated_with.str.extract(r"(throws (?:low|high)|runs (?:low|high))")[0]).groupby(["team", "vol"]):
            g2 = g[~g.tier.str.startswith("WEAK") & ~g.tier.str.startswith("LEAN")]
            hits = []
            for _, r in g2.iterrows():
                col = SIM_COL.get(r.market)
                if col and r.player in sims:
                    sv = sims[r.player][col]; hits.append((sv > r.line) if r.side == "Over" else (sv < r.line))
            joint = float(np.mean(np.logical_and.reduce(hits))) if hits else np.nan
            indep = float(np.prod([h.mean() for h in hits])) if hits else np.nan
            EXPO.append(dict(team=tm, thesis=f"{tm} {vol}", legs_total=len(g), legs_bettable=len(g2),
                             players=", ".join(g.player.unique()), p_all_bettable_hit=joint, p_if_independent=indep))
    EXPO = pd.DataFrame(EXPO)
    if not EXPO.empty:
        EXPO.to_csv(OUT / f"exposure_{slug}.csv", index=False)

    # ladder: P(stat <= k) for every modeled player, so alternate lines can be priced
    lad = []
    for pl, sd in sims.items():
        tm = M[M.name == pl].team.iloc[0]
        rec = sd.get("receptions"); ry = sd.get("rec_yards"); ru = sd.get("rush_yards")
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
        T += ["## Game header\n",
              f"- **Frame:** {frame}. Team TD totals, all touchdowns incl. defence and special teams (the yardage "
              f"model's anchor): " + ", ".join(f"{t} {env[t].get('pass_td',0)+env[t].get('rush_td',0):.1f} ({'market-anchored' if env[t].get('td_anchor')=='market' else 'history'})" for t in (AWAY, HOME))
              + ("" if V1TD is None or V1TD.empty else
                 ". Offensive touchdowns only, the mean the anytime-TD model prices from: "
                 + ", ".join(f"{t} {float(V1TD[V1TD.team == t]['mu'].iloc[0]):.1f}" for t in (AWAY, HOME)
                             if (V1TD.team == t).any()) + ". The two differ by design, not by error."),
              f"- **Weather:** {wx}. 15 mph sustained-wind screen {'HIT' if (weather.get('wind_mph_max') or 0) > 15 else 'not hit'}.",
              f"- **Injury designations (week {WEEK} report):** " + (", ".join(desig) if desig else "none on the eligible set") + ". Out/Doubtful removed; their share goes mostly to the replacement, a quarter to the priced teammates; Questionable priced as if playing, with a separate 'if he's out' pricing. Re-run inside 90 minutes of kickoff: a late scratch changes every share on that team.",
              f"- **Data cutoff:** 2026 weeks 1-{WEEK-1} play-by-play, week {WEEK} roster/injury/depth chart; prices snapshot {now()}; kickoff in {hrs:.1f} h.",
              "",
              "<details><summary>Method in six lines</summary>\n",
              f"1. Data: nflverse play-by-play/rosters/injuries/snaps through week {WEEK-1}, 2025 priors bundled, prices from {books_used_str}, NWS weather.",
              "2. Model: receiving_hier_v2 (receptions, rec yds), rush_yds_v0, anytime_td_v1 (anytime TD; v0 only as a labelled fallback); methodology v1.0 in resources/methodology.md.",
              "3. Validated against sportsbook lines: NOTHING. The 2025 walk-forward shows the model beats a naive baseline on CRPS and that its distribution is internally consistent (calibration_2025.csv places lines at fixed offsets from the model\u2019s own median, not at book numbers, across all player-weeks rather than the ones worth betting). No market has been tested against posted lines, so every prop is ineligible and the record is being built prospectively.",
              "4. Team TD totals are market-anchored, so a TD gap is a share disagreement only.",
              "5. Thresholds, not bets: 'take at X' is where the edge rule clears at -110; no call is a validated betting edge until logged closing lines say so.",
              "6. Tiers: STRONG = stable role, edge at/above floor, not prior-driven. LEAN = under floor. WEAK = role change or gap > 15 pts.",
              "\n</details>\n"]
        if not EXPO.empty:
            expo_top = EXPO[EXPO.legs_bettable > 0].sort_values("legs_total", ascending=False)
            if len(expo_top):
                e = expo_top.iloc[0]
                T.append(f"**Game-script thesis.** {e.legs_total} of the card's legs ride on '{e.thesis}' ({e.players}); the {e.legs_bettable} bettable ones have P(all hit) {e.p_all_bettable_hit:.0%} vs {e.p_if_independent:.0%} if independent. Size them as one bet.\n")
        n_elig_bet = int(BET.eligible.sum())
        T += ["## Bet card\n",
             (f"> **{n_elig_bet} of {len(BET)} rows are eligible to bet.** Eligibility is enforced by one shared test "
              f"(`scripts/eligibility.py`) covering model status, expected return at the price actually posted, and role. "
              f"No market has passed a holdout against real sportsbook lines, so none is eligible. **The Kelly and stake "
              f"columns below are what the arithmetic would say if it were — not a recommendation to stake anything.**\n"
              if n_elig_bet < len(BET) else ""),
             f"*Best price per line across books, snapshot {now()}. Edge in probability points; EV per $100 at the listed price; "
             "Kelly is the full-Kelly fraction of bankroll. STRONG = stable role and edge at or above the floor (6 pts, or 25% relative on TD). "
             "LEAN = below the floor, no bet. WEAK = role changed or gap over 15 pts, treat as the book knowing something. "
             "Self-check column: the 2025 distributional self-check for this probability bucket -- lines placed at fixed offsets from "
             "the model\u2019s OWN median, not book lines, over every player-week rather than the ones worth betting. It says the "
             "distribution is internally consistent. It is not a track record against a sportsbook, and no market has one yet.*\n",
             "| Tier | Player | Prop | Line | Book | Odds | Model | No-vig | Edge | EV/$100 | Kelly | 1/4-Kelly per $1k | Self-check | Ladder | Correlated with | Note |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for _, b in BET.iterrows():
            ln = "" if pd.isna(b.line) else f"{b.line:g}"
            cal = "" if pd.isna(b.dist_selfcheck) else f"{b.dist_selfcheck:.0%}"
            T.append(f"| {b.tier.split(' ')[0]} | {b.player} ({b.team}) | {b.side} {b.prop} | {ln} | {b.book} | {b.price:+d} | {b.model_p:.0%} | {b.novig_p:.0%} | {b.edge_pts:+.0f} | {b.ev_per_100:+.0f} | {b.kelly_frac:.2f} | ${b.stake_qkelly_per_1000:.0f} | {cal} | {b.ladder} | {b.correlated_with} | {b.note} |")
        if not EXPO.empty:
            T.append("\n**Exposure.** " + " ".join(
                f"{e.thesis}: {e.legs_bettable} bettable of {e.legs_total} legs ({e.players}); P(all bettable hit) "
                f"{e.p_all_bettable_hit:.0%} vs {e.p_if_independent:.0%} if independent." for _, e in EXPO.iterrows() if e.legs_bettable > 0))
        T.append("")
        L[3:3] = T
    if not BET.empty:
        log("\n=== BET CARD (best price per line; sorted tier then EV) ===")
        for _, b in BET.iterrows():
            ln = "" if pd.isna(b.line) else f"{b.line:g} "
            cal = "" if pd.isna(b.dist_selfcheck) else f" sc {b.dist_selfcheck:.0%}"
            log(f"  {b.tier.split(' ')[0]:8s} {b.player:20s} {b.side:5s} {ln}{b.prop:10s} {b.book:10s} {b.price:+5d} "
                f"us {b.model_p:.0%} book {b.novig_p:.0%} edge {b.edge_pts:+.0f} EV {b.ev_per_100:+.0f}/100 kelly {b.kelly_frac:.2f}{cal}  {b.correlated_with}")
    if not EXPO.empty:
        log("\n=== Exposure ===")
        for _, e in EXPO.iterrows():
            log(f"  {e.thesis}: {e.legs_bettable} bettable of {e.legs_total} legs ({e.players}); P(all bettable hit) {e.p_all_bettable_hit:.1%} vs {e.p_if_independent:.1%} if independent")

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
        L.append("## The cheat sheet\n")
        L.append("Biggest disagreements first. \"Our number\" and \"Book\" are the chance of that side hitting.\n")
        L.append("| Player | Prop | Line / Price | Side | Our number | Book | Verdict |")
        L.append("|---|---|---|---|---|---|---|")
        for _, r in top.iterrows():
            m = M[M.name == r.player].iloc[0]
            label, _ = verdict_for(r, m)
            ln = f"{int(r.price):+d}" if pd.isna(r.line) else r.line
            side = "Yes" if r.market == "player_anytime_td" else r.side
            L.append(f"| **{r.player}** ({m.team}) | {MKT[r.market]} | {ln} | {side} | {pct(r.p_model)} | {pct(r.p_novig)} | {label} |")
        L.append("")

    # ---- context ----
    L.append("## The setup\n")
    L.append(f"- **Kickoff:** {G.gameday} {G.gametime} ET at {G.stadium} ({'indoors' if roof in ('closed','dome') else 'outdoors'}).")
    L.append(f"- **What we're working with:** {n_weeks} week{'s' if n_weeks!=1 else ''} of this season, plus each player's full {PRIOR} season as a starting point.")
    for t in (AWAY, HOME):
        e = env[t]
        src_note = " (anchored to the market's spread and total; unvalidated option)" if e.get("source") == "market" else " (from the team's own recent games, plus last season)"
        L.append(f"- **{t}'s offense, typical game{src_note}:** about {e['targets']:.0f} throws, {e['carries']:.0f} runs, "
                 f"{e['pass_td']+e['rush_td']:.1f} offensive touchdowns.")
    L.append("- **Matchup (opponent defense):** included at the team level, weighted by how much real "
             "between-team difference last season's data could actually detect (roughly a 4% swing in "
             "efficiency, weighted about half). Position-specific matchups ('good against tight ends') were "
             "tested and are too noisy to use. Expect this to move a projection by a point or two, not more.")
    excl = pop[pop.excluded]
    if len(excl):
        L.append(f"- **Out:** " + ", ".join(f"{r['name']} ({r.report_status or r.status})" for _, r in excl.iterrows())
                 + ". Most of their usual share goes to whoever replaces them, not to the priced teammates: a quarter of their targets and carries is handed on in our numbers, mostly to their position.")
    q = pop[pop.questionable]
    if len(q):
        L.append(f"- **Questionable:** " + ", ".join(r["name"] for _, r in q.iterrows()) + ". Priced as if they play their normal role; see 'If a Questionable player is out' for the other case.")
    if not excl.empty is False and q.empty:
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
    L.append("## The lines that matter, explained\n")
    if top.empty:
        L.append("_No prices were retrieved for this game._\n")
    else:
        for i, (_, r) in enumerate(top.iterrows(), 1):
            m = M[M.name == r.player].iloc[0]
            side = "Yes" if r.market == "player_anytime_td" else f"{r.side} {r.line}"
            L.append(f"### {i}. {r.player} · {MKT[r.market]} · {side}")
            L.append(f"**Our number {pct(r.p_model)} · Book {pct(r.p_novig)} · Gap {r.gap:+.0%}**\n")
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
    L.append("- **Gap** is our number minus the book's. Positive means we like that side more than the book does.")
    if not td_two_sided:
        L.append("- **Touchdown prices** have no 'won't score' side to remove the cut from, so the book's number there is a bit high.")
    L.append("- **Why everything is 'no bet':** the receiving model beats simple baselines in a 2025 backtest, but no model here "
             "has been tested against real sportsbook prices yet. Until it is, a disagreement is a curiosity, not an edge.")
    L.append("- **What builds the case:** every run logs every line. After enough games, we compare our numbers to where the "
             "lines closed. If we consistently beat the close, the numbers are real. If not, they aren't.")
    L.append("")

    # ---- touchdown pairs: only the classes the committed gate opened ----
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
    L.append(f"- QB rushing yards left out on purpose: kneel-downs count against the prop and we don't model them yet.")
    if hrs > 1:
        L.append(f"- **Kickoff is in {hrs:.1f} hours.** To track how these lines moved, open a chat inside the last hour and ask for a closing capture.")
    elif hrs > 0:
        L.append(f"- **Candidate closing snapshot:** kickoff in {hrs * 60:.0f} minutes, inside the closing window. The "
                 "scheduled capture records the official close; this run is a reference copy.")
    L.append(f"- Full technical detail (every line, every book, model parameters) is in the attached CSV files.")
    L.append("")

    # ---- technical appendix ----
    L.append("---\n<details><summary>Technical appendix: all lines</summary>\n")
    if not R.empty:
        L.append("| Book | Market | Player | Line | Model mean | Side | p_model | p_novig | Gap | Price | ER |")
        L.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for _, r in R.iterrows():
            L.append(f"| {r.book} | {r.market.replace('player_','')} | {r.player} | {'' if pd.isna(r.line) else r.line} | "
                     f"{'' if pd.isna(r.model_mean) else round(r.model_mean,1)} | {r.side} | {r.p_model:.3f} | {r.p_novig:.3f} | "
                     f"{r.gap:+.3f} | {r.price} | {r.ER:+.3f} |")
    L.append(f"\nModel states: receptions/receiving yards `receiving_hier_v2` and rushing yards `rush_yds_v0` PROTOTYPE (2022-25 harness: unbiased but too narrow, so probabilities far from 50% run high); "
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
    if not ASSUME_OUT and not a.no_scenarios:
        q = pop[pop.questionable & ~pop.excluded]
        if len(q) and snap_written:
            L += run_scenarios(q, R, slug, snap_path)
            (OUT / f"report_{slug}.md").write_text("\n".join(L), encoding="utf-8")
        elif len(q):
            L += ["", "## If a Questionable player is out", "",
                  "Not priced: this run had no lines to price against."]
            (OUT / f"report_{slug}.md").write_text("\n".join(L), encoding="utf-8")
    if MARKETS:
        S_ = short_summary(R, AWAY, HOME, SEASON, WEEK, books_used_str, hrs, sorted(MARKETS))
        (OUT / f"summary_{slug}.md").write_text("\n".join(S_), encoding="utf-8")
        print("\n".join(S_))
        print(f"\n(full report: {OUT / f'report_{slug}.md'})")
    else:
        print("\n".join(L))


def short_summary(R, away, home, season, week, books, hrs, markets) -> list[str]:
    """The --markets fast path: just the asked-for markets, one table."""
    out = [f"# {away} at {home}, {season} week {week}: {', '.join(m.replace('player_', '') for m in markets)}", "",
           f"Prices: {books}." + (f" Candidate closing snapshot (kickoff in {hrs * 60:.0f} min)." if 0 < hrs <= 1 else ""),
           "", ev_statement(R), ""]
    if R.empty:
        return out
    out += ["| player | market | side / line | book | price | model | market | gap |", "|---|---|---|---|---|---|---|---|"]
    for r in R.sort_values(["market", "p_model"], ascending=[True, False]).itertuples():
        ln = "" if pd.isna(r.line) else f" {r.line:g}"
        out.append(f"| {r.player} ({r.team}) | {r.market.replace('player_', '')} | {r.side}{ln} | {r.book} | "
                   f"{int(r.price):+d} | {r.p_model:.0%} | {r.p_novig:.0%} | {r.gap:+.0%} |")
    out += ["", "No row is eligible to bet: no market is validated against sportsbook lines."]
    return out


def apply_out_rule(M: pd.DataFrame, E: pd.DataFrame, teams, rule=None):
    """Hand each excluded player's share on under OUT_RULE. M: priced players
    (team, pos, ts, rs, i10ts, i10rs); E: excluded players (team, pos, and the
    same share columns). Returns (M, {team: {col: share handed on}})."""
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


def ev_statement(R: pd.DataFrame) -> str:
    """Say plainly whether any priced row has positive expected value at the
    price actually posted -- the first thing a reader wants to know."""
    if R.empty:
        return "**No lines were priced for this game.**"
    pos = R[pd.to_numeric(R["ER"], errors="coerce") > 0]
    if pos.empty:
        return "**No row has positive expected value at the posted prices.**"
    return (f"**{len(pos)} of {len(R)} priced rows have positive expected value at the posted price** "
            "-- none is eligible to bet (no market is validated against sportsbook lines).")


SCEN_KEY = ["book", "market", "player", "side", "line"]
MARKET_WORDS = {"player_receptions": "catches", "player_reception_yds": "receiving yards",
                "player_rush_yds": "rushing yards"}


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
    argv, skip = [], False
    for x in sys.argv[1:]:
        if skip:
            skip = False
        elif x in ("--prior-log", "--prior-archive"):
            skip = True
        elif not x.startswith(("--prior-log=", "--prior-archive=")):
            argv.append(x)
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


if __name__ == "__main__":
    main()
