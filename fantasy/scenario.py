"""`nfl fantasy scenario`: how does a player project if a teammate is out?

Three answers, side by side and never blended:

  MODEL      the props engine priced twice -- as posted, and with the teammate
             removed (`--assume-out`), whose measured absence rule hands his
             targets, carries and inside-10 work to the rest of the offence
             (tuned on 2022-23 absences, scored on 2024-25). Fantasy points are
             scored from the engine's joint simulation in the league's scoring.
  OBSERVED   the games the teammate actually missed this season and last,
             against the games he played: the player's points, targets and
             carries, labelled PRIOR-SEASON DATA for last season's rows.
  MARKET     the player's market-implied points from the lines posted now;
             whether those lines already price the absence is not knowable
             from here, and the report says so.

What the model cannot do, stated in every report:
  * a QUARTERBACK absence changes the team's passing volume and efficiency,
    not only who gets the ball; the absence rule redistributes shares and was
    not tuned for it, so a QB-out model row is PROVISIONAL;
  * a QUARTERBACK's own row is rushing only (passing is not modelled by the
    engine), so a QB as the subject has no model answer.

Players are joined by id (Sleeper id -> gsis id through core.ids), never by name.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from core import fetch as F
from core import ids as IDS
from core.manifest import Manifest
from core.scoring import NFLVERSE_BASE, nflverse_weights, score_frame

from . import gate as G
from . import league as LG
from .contract import QUANTILES, fantasy_position
from .sources import market_points as MP

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "props" / "engine" / "scripts" / "score_game.py"
OUT = Path(os.environ.get("NFL_OUT", "/mnt/user-data/outputs"))
SLEEPER_TO_NFLVERSE = {"LAR": "LA"}
ENGINE_KEYS = ("rec", "rec_yd", "rush_yd", "rush_td", "rec_td")


class ScenarioError(ValueError):
    """The request cannot be answered as asked (unknown player, not teammates)."""


@dataclass
class ScenarioResult:
    markdown: str
    record: dict
    report_path: Path | None = None
    record_path: Path | None = None


# ---------------------------------------------------------------- identity

def resolve(name_or_id: str, players: dict) -> str:
    """A Sleeper id from an id or a name. An ambiguous name is an error that
    lists the candidates -- a guess would price the wrong player."""
    s = str(name_or_id).strip()
    if s in players:
        return s
    idx = IDS.NameIndex(players)
    pid = idx.resolve(s)
    if pid:
        return pid
    cands = idx.candidates(s)
    if cands:
        opts = ", ".join(f"{players[c].get('full_name')} ({players[c].get('team') or 'FA'}, id {c})" for c in cands)
        raise ScenarioError(f"'{s}' matches more than one player: {opts}. Pass the id.")
    raise ScenarioError(f"no player named '{s}'")


# --------------------------------------------------------------- the model

def engine_scoring(scoring: dict) -> str:
    """The props engine's --fantasy-scoring spec from the league scoring (it
    scores five keys; passing is not modelled)."""
    return ",".join(f"{k}={float(scoring.get(k, 0.0))}" for k in ENGINE_KEYS)


def run_engine(away: str, home: str, season: int, week: int, scoring: dict, out_dir: Path,
               workdir: Path, assume_out: str | None = None, snapshot: Path | None = None) -> Path:
    """One props-engine run; returns the fantasy_points CSV it wrote."""
    cmd = [sys.executable, str(ENGINE), "--away", away, "--home", home, "--season", str(season),
           "--week", str(week), "--workdir", str(workdir), "--fantasy-scoring", engine_scoring(scoring),
           "--no-scenarios", "--no-oddsapi-fallback"]
    if assume_out:
        cmd += ["--assume-out", assume_out]
    if snapshot is not None and snapshot.exists():
        cmd += ["--odds-snapshot", str(snapshot)]
    env = dict(os.environ, NFL_OUT=str(out_dir))
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    slug = f"{season}_wk{week:02d}_{away}_{home}"
    f = (out_dir / "scenarios" if assume_out else out_dir) / f"fantasy_points_{slug}.csv"
    if r.returncode != 0 or not f.exists():
        tail = (r.stderr or r.stdout or "").strip().splitlines()[-1:] or ["no output"]
        raise ScenarioError(f"props engine run failed ({'with ' + assume_out + ' out' if assume_out else 'as posted'}):"
                            f" {tail[0][:200]}")
    return f


def model_row(csv_path: Path, gsis: str) -> dict | None:
    df = pd.read_csv(csv_path)
    if "gsis_id" not in df.columns:
        raise ScenarioError("the props engine is older than props-v1.18 (no gsis_id in its fantasy table)")
    row = df[df["gsis_id"] == gsis]
    if row.empty:
        return None
    r = row.iloc[0]
    return {"mean": float(r["mean"]), "p_td": float(r["p_td"]),
            "quantiles": {q: float(r[c]) for q, c in zip(QUANTILES, ("p10", "p25", "median", "p75", "p90"))},
            "note": r.get("note") if isinstance(r.get("note"), str) else ""}


# ------------------------------------------------------------ observed

def _points(df: pd.DataFrame, scoring: dict) -> pd.Series:
    return score_frame(df, nflverse_weights(scoring, base=NFLVERSE_BASE))


def observed(stats_by_season: dict, gsis: str, out_gsis: str, team_nflverse: str, scoring: dict) -> list[dict]:
    """Per season: the player's weeks with the teammate on the field and
    without him, for the same team. A week the teammate appears in the team's
    box score is 'with'; a week he does not, after his first game for that
    team that season, is 'without' (injury, suspension or benching alike)."""
    out = []
    for season, df in sorted(stats_by_season.items(), reverse=True):
        if df is None or df.empty:
            continue
        df = df[df.get("season_type", "REG") == "REG"] if "season_type" in df.columns else df
        tcol = "team" if "team" in df.columns else "recent_team"
        me = df[(df["player_id"] == gsis) & (df[tcol] == team_nflverse)].copy()
        mate = df[(df["player_id"] == out_gsis) & (df[tcol] == team_nflverse)]
        if me.empty or mate.empty:
            continue
        me["pts"] = _points(me, scoring)
        with_w = set(mate["week"])
        # a week BEFORE the teammate's first game for the team (a trade, a
        # signing, a rookie not yet active) is not an absence
        first = min(with_w)
        split = {"with": me[me["week"].isin(with_w)],
                 "without": me[~me["week"].isin(with_w) & (me["week"] > first)]}
        row = {"season": int(season)}
        for k, g in split.items():
            row[k] = {"games": int(len(g)), "points": round(float(g["pts"].mean()), 1) if len(g) else None,
                      "targets": round(float(pd.to_numeric(g.get("targets", 0), errors="coerce").mean()), 1) if len(g) else None,
                      "carries": round(float(pd.to_numeric(g.get("carries", 0), errors="coerce").mean()), 1) if len(g) else None,
                      "weeks": sorted(int(w) for w in g["week"])}
        out.append(row)
    return out


# ------------------------------------------------------------------ run

def _current_week(games: pd.DataFrame, season: int) -> int:
    g = games[(games.season == season) & (games.game_type == "REG")]
    unplayed = g[g.result.isna()]
    return int(unplayed.week.min()) if not unplayed.empty else int(g.week.max())


def run(league: str, player: str, out: str, week: int | None = None, *, out_dir: Path | None = None,
        write: bool = True) -> ScenarioResult:
    m = Manifest(f"fantasy scenario {league}")
    yaml_sc, plat_sc = LG.load_scoring(league, m)      # scoring only: this command uses no roster
    scoring = {**yaml_sc, **plat_sc}
    players = json.loads(F.sleeper_players(manifest=m).read_text(encoding="utf-8"))
    pid, out_pid = resolve(player, players), resolve(out, players)
    p, o = players[pid], players[out_pid]
    if not p.get("team") or p.get("team") != o.get("team"):
        raise ScenarioError(f"{p.get('full_name')} ({p.get('team')}) and {o.get('full_name')} ({o.get('team')}) "
                            "are not teammates")
    gmap, _ = IDS.sleeper_gsis(IDS.load_id_map(F.DEFAULT_CACHE, manifest=m), players)
    gsis, out_gsis = gmap.get(pid), gmap.get(out_pid)
    if not gsis or not out_gsis:
        raise ScenarioError("no nflverse id for " + " and ".join(
            n for n, g in ((p.get("full_name"), gsis), (o.get("full_name"), out_gsis)) if not g))
    team = SLEEPER_TO_NFLVERSE.get(p["team"], p["team"])
    games = pd.read_csv(F.schedule(manifest=m), low_memory=False)
    season = F.current_season()
    wk = week or _current_week(games, season)
    g = games[(games.season == season) & (games.week == wk) & (games.game_type == "REG")
              & ((games.home_team == team) | (games.away_team == team))]
    if g.empty:
        raise ScenarioError(f"{team} has no game in {season} week {wk} (bye)")
    away, home = g.iloc[0].away_team, g.iloc[0].home_team
    pos, out_pos = fantasy_position(p), fantasy_position(o)

    # MODEL: the engine twice, the second with the teammate out
    tmp = Path(tempfile.mkdtemp(prefix="nfl_scenario_"))
    workdir = F.DEFAULT_CACHE / "props_wd"
    workdir.mkdir(parents=True, exist_ok=True)
    notes = []
    try:
        base_csv = run_engine(away, home, season, wk, scoring, tmp, workdir)
        snap = workdir / f"odds_snapshot_{season}_wk{wk:02d}_{away}_{home}.json"
        scen_csv = run_engine(away, home, season, wk, scoring, tmp, workdir, assume_out=out_gsis, snapshot=snap)
        base, scen = model_row(base_csv, gsis), model_row(scen_csv, gsis)
        # did the as-posted run already leave the teammate out? (the engine
        # excludes Out/Doubtful from ITS injury report, which can lag Sleeper's)
        out_in_base = model_row(base_csv, out_gsis) is not None
    except ScenarioError as ex:
        base = scen = None
        out_in_base = True
        notes.append(str(ex))
    m.record("props engine (as posted, and with the teammate out)", source="props/engine score_game.py",
             status="fresh" if base else "failed", fetched_at=dt.datetime.now(dt.timezone.utc) if base else None,
             detail="" if base else (notes[-1] if notes else "no model row")[:200])

    # OBSERVED: games the teammate missed, this season and last
    stats = {}
    for s in (season, season - 1):
        try:
            stats[s] = pd.read_csv(F.nflverse("player_stats_week", s, manifest=m), low_memory=False)
        except Exception as ex:  # noqa: BLE001 -- a missing season is a gap, reported
            notes.append(f"player stats {s} unavailable ({type(ex).__name__})")
    obs = observed(stats, gsis, out_gsis, team, scoring)

    # MARKET: what the posted lines say now
    try:
        mk = MP.project(scoring, manifest=m).projections.get(pid)
    except Exception as ex:  # noqa: BLE001
        mk = None
        notes.append(f"market_points unavailable ({type(ex).__name__})")

    gate = G.scoring_only(yaml_sc, plat_sc)
    md = markdown(league, season, wk, p, o, pos, out_pos, away, home, base, scen, obs, mk, gate, m, notes,
                  out_in_base=out_in_base)
    rec = {"command": "fantasy scenario", "league": league, "season": season, "week": wk,
           "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
           "player": {"sleeper_id": pid, "gsis_id": gsis, "name": p.get("full_name"), "pos": pos, "team": p.get("team")},
           "out": {"sleeper_id": out_pid, "gsis_id": out_gsis, "name": o.get("full_name"), "pos": out_pos},
           "game": f"{away}@{home}", "model": {"as_posted": base, "teammate_out": scen},
           "observed": obs, "market": None if mk is None else {"mean": mk.mean, "detail": mk.detail},
           "gate": gate.to_dict(), "manifest": m.to_dict(), "notes": notes}
    res = ScenarioResult(md, rec)
    if write:
        d = Path(out_dir or OUT)
        d.mkdir(parents=True, exist_ok=True)
        slug = f"{league}_{season}_wk{wk:02d}_{pid}_without_{out_pid}"
        res.report_path, res.record_path = d / f"scenario_{slug}.md", d / f"scenario_{slug}.json"
        res.report_path.write_text(md, encoding="utf-8")
        res.record_path.write_text(json.dumps(rec, indent=1, default=str), encoding="utf-8")
    return res


def _q(d, q):
    return "—" if not d else f"{d['quantiles'][q]:.1f}"


def markdown(league, season, wk, p, o, pos, out_pos, away, home, base, scen, obs, mk, gate, m, notes,
             out_in_base: bool = True) -> str:
    pn, on = p.get("full_name"), o.get("full_name")
    L = [f"# {pn} if {on} is out -- {away}@{home}, {season} week {wk}", "",
         f"*League scoring: {league}. {gate.line().replace('LEAGUE DATA GATE', 'Scoring check')}*", ""]
    L += ["## Model: the props engine priced as posted and with him out", ""]
    if pos == "QB":
        L += ["No model answer: the engine does not model passing, so a quarterback's own row is rushing only.", ""]
    elif base and scen:
        L += ["| | Mean | p10 | p25 | Median | p75 | p90 | P(TD) |", "|---|---|---|---|---|---|---|---|"]
        for lab, d in (("as posted", base), (f"{on} out", scen)):
            L.append(f"| {lab} | {d['mean']:.1f} | {_q(d, 0.1)} | {_q(d, 0.25)} | {_q(d, 0.5)} | {_q(d, 0.75)} | "
                     f"{_q(d, 0.9)} | {d['p_td']:.0%} |")
        L += ["", f"**Change: {scen['mean'] - base['mean']:+.1f} points** ({(scen['mean'] / base['mean'] - 1) if base['mean'] else 0:+.0%})."]
        if not out_in_base:
            tag = o.get("injury_status")
            L += ["", f"**The engine's as-posted run already leaves {on} out**"
                  + (f" (he is {tag} on the injury report)" if tag else "")
                  + f", so both rows price the no-{on} game and the change is zero by construction -- not evidence "
                  "that his absence does not matter. The engine has no with-him number here; the observed and "
                  "market rows below are the comparison."]
        if out_pos == "QB":
            L += ["", "**PROVISIONAL.** The absence rule moves targets and carries between teammates; it was not tuned "
                  "for a quarterback, whose absence changes the team's passing volume and efficiency as well. "
                  "Weight the observed rows below more heavily."]
        L += [""]
    else:
        L += ["No model answer: " + ("; ".join(notes) or f"{pn} is not in the engine's priced roster for this game."), ""]

    L += ["## Observed: the games he actually missed", ""]
    if not obs:
        L += [f"No week this season or last in which {pn} played for this team without {on}.", ""]
    else:
        L += ["| Season | Split | Games | Points | Targets | Carries | Weeks |", "|---|---|---|---|---|---|---|"]
        for r in obs:
            lab = f"{r['season']}" + (" (PRIOR-SEASON DATA)" if r["season"] < season else "")
            for k in ("with", "without"):
                x = r[k]
                L.append(f"| {lab} | {k} {on} | {x['games']} | {x['points'] if x['points'] is not None else '—'} | "
                         f"{x['targets'] if x['targets'] is not None else '—'} | "
                         f"{x['carries'] if x['carries'] is not None else '—'} | {', '.join(map(str, x['weeks'])) or '—'} |")
        L += ["", "*A 'without' week is any week he played for the team and the teammate did not appear in the box "
              "score -- injury, suspension or benching alike. A handful of games is a small sample.*", ""]

    L += ["## Market: the lines posted now", ""]
    if mk is None:
        L += ["No two-sided lines posted for him.", ""]
    else:
        L += [f"Market-implied {mk.mean:.1f} points" + (" (partial board: " + ", ".join(mk.detail.get("missing_markets") or [])
                                                          + " missing)" if mk.detail.get("partial") else "")
              + f". Whether these lines already price {on}'s absence cannot be told from here: check when the news "
              "broke against the book's last update.", ""]
    L += [f"*{m.summary_line()}*"] + ([f"*Notes: {'; '.join(notes)}*"] if notes else [])
    return "\n".join(L) + "\n"
