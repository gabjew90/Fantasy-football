"""`nfl status`: is it too early to run?

One call that says what is posted for a week before anything is priced: the
schedule and what has kicked off, the spread and total per game, the injury
report, Sleeper's weekly projections, the Sleeper Picks board per game, and --
for a league -- how old its roster data is. The fantasy skill's Tuesday run
(2026-09-22) priced a slate five days out without knowing any of this.

Facts first, then a verdict line per use; the verdict never refuses to run
anything, it says what an early run will be missing.
"""

from __future__ import annotations

import datetime as dt
import json

import pandas as pd

from . import fetch as F
from .manifest import Manifest

ESPN_TO_SLEEPER = {"WSH": "WAS"}
SLEEPER_TO_NFLVERSE = {"LAR": "LA"}
NFLVERSE_TO_SLEEPER = {v: k for k, v in SLEEPER_TO_NFLVERSE.items()}
# the injury table's order: game designations first, worst first; then practice-only rows
STATUS_ORDER = {"Out": 0, "Doubtful": 1, "Questionable": 2}
PRACTICE_SHOWN = ("Did Not Participate", "Limited")


def team_code(t: str) -> str:
    """A team as status prints it (ESPN's WSH and nflverse's LA read as WAS and LAR)."""
    t = str(t).strip().upper()
    return ESPN_TO_SLEEPER.get(t, NFLVERSE_TO_SLEEPER.get(t, t))


def pick_game(games: list[dict], game: str) -> dict:
    """The one game `game` (AWAY@HOME) names. Raises ValueError listing the week's games."""
    away, _, home = str(game).partition("@")
    want = (team_code(away), team_code(home))
    hit = [g for g in games if (g["away"], g["home"]) == want]
    if not hit:
        raise ValueError(f"no game {want[0]}@{want[1]} this week; the games are: "
                         + ", ".join(g["game"] for g in games))
    return hit[0]


def game_injuries(df: pd.DataFrame, week: int, teams: tuple[str, str]) -> list[dict]:
    """Both teams' injury-report rows for the week, from nflverse's official report as published:
    every player with a game designation (Out / Doubtful / Questionable), and every player who
    missed or was limited in practice without one yet. Names as the report prints them."""
    nv = {SLEEPER_TO_NFLVERSE.get(t, t): t for t in teams}
    wk = df[(df["week"] == week) & df["team"].isin(list(nv))]
    out = []
    for _, r in wk.iterrows():
        status = r.get("report_status") if isinstance(r.get("report_status"), str) else None
        practice = r.get("practice_status") if isinstance(r.get("practice_status"), str) else None
        if not status and not (practice and practice.startswith(PRACTICE_SHOWN)):
            continue
        injury = next((r.get(c) for c in ("report_primary_injury", "practice_primary_injury")
                       if isinstance(r.get(c), str)), None)
        out.append({"team": nv[r["team"]], "player": r.get("full_name"), "position": r.get("position"),
                    "status": status, "practice": practice, "injury": injury})
    out.sort(key=lambda x: (teams.index(x["team"]), STATUS_ORDER.get(x["status"], 3), str(x["player"])))
    return out


def _lines_by_team(lines: list, players: dict) -> dict:
    out = {}
    for m in lines or []:
        opts = m.get("options") or []
        if m.get("sport") != "nfl" or not opts or opts[0].get("game_status") != "pre_game":
            continue
        team = opts[0].get("subject_team") or (players.get(str(m.get("subject_id"))) or {}).get("team")
        if team and len(opts) >= 2:
            out[team] = out.get(team, 0) + 1
    return out


def week_status(season: int, week: int, *, manifest: Manifest | None = None, league: dict | None = None,
                now: dt.datetime | None = None, game: str | None = None) -> dict:
    """`league` is fantasy.league.roster_freshness(cfg): core never imports the
    league code, which sits above it. `game` (AWAY@HOME): that game only, with its injury
    report (the chat's game read, DECISIONS #235); raises ValueError for a game not this week."""
    m = manifest or Manifest(f"status {season} wk{week}")
    now = now or dt.datetime.now(dt.timezone.utc)
    sb = json.loads(F.espn_scoreboard(season, week, manifest=m).read_text(encoding="utf-8"))
    games = []
    for ev in sb.get("events", []):
        comp = (ev.get("competitions") or [{}])[0]
        t = {c.get("homeAway"): ESPN_TO_SLEEPER.get(c["team"]["abbreviation"], c["team"]["abbreviation"])
             for c in comp.get("competitors", []) if c.get("team")}
        odds = (comp.get("odds") or [{}])[0]
        kick = dt.datetime.fromisoformat(ev["date"].replace("Z", "+00:00"))
        games.append({"game": f"{t.get('away')}@{t.get('home')}", "away": t.get("away"), "home": t.get("home"),
                      "kickoff_utc": kick.isoformat(), "started": now >= kick,
                      "hours_to_kickoff": round((kick - now).total_seconds() / 3600, 1),
                      "spread": odds.get("details"), "total": odds.get("overUnder")})
    try:
        lines = json.loads(F.sleeper_lines(manifest=m).read_text(encoding="utf-8"))
        players = json.loads(F.sleeper_players(manifest=m).read_text(encoding="utf-8"))
        by_team = _lines_by_team(lines, players)
    except Exception:  # noqa: BLE001 -- reported as unavailable, not raised
        by_team = None
    for g in games:
        g["lines"] = None if by_team is None else by_team.get(g["away"], 0) + by_team.get(g["home"], 0)
    one = pick_game(games, game) if game else None
    if one is not None:
        games = [one]

    inj = {"rows": 0, "designations": 0}
    game_inj = None
    try:
        # the file has no report date; what matters is whether the final game
        # designations (Out / Doubtful / Questionable, released Friday) are in
        df = pd.read_csv(F.nflverse("injuries", season, manifest=m), low_memory=False)
        wk = df[df["week"] == week]
        inj = {"rows": int(len(wk)),
               "designations": int(wk["report_status"].notna().sum()) if "report_status" in wk else 0}
        if one is not None:
            game_inj = game_injuries(df, week, (one["away"], one["home"]))
    except Exception as ex:  # noqa: BLE001
        inj["error"] = type(ex).__name__

    proj = {"published": False, "players": 0}
    try:
        rows = json.loads(F.sleeper_projections(season, week, manifest=m).read_text(encoding="utf-8"))
        real = [r for r in rows if any(not k.startswith(("adp_", "pos_adp_")) and k != "gp"
                                       for k in (r.get("stats") or {}))]
        proj = {"published": bool(real), "players": len(real)}
    except Exception as ex:  # noqa: BLE001
        proj["error"] = type(ex).__name__

    return {"season": season, "week": week, "checked_at_utc": now.isoformat(), "games": games,
            "injuries": inj, "projections": proj, "league": league, "manifest": m.to_dict(),
            "game": one["game"] if one is not None else None, "game_injuries": game_inj}


def verdicts(st: dict) -> list[str]:
    games = [g for g in st["games"] if not g["started"]]
    out = []
    n_spread = sum(1 for g in games if g["spread"])
    lines = [g["lines"] for g in games if g["lines"] is not None]
    thin = sum(1 for n in lines if n < 24)
    soonest = min((g["hours_to_kickoff"] for g in games), default=None)
    out.append(f"PROPS: {len(games)} games to play; spread and total posted for {n_spread}; "
               + (f"Sleeper board thin (<24 lines) for {thin} of {len(lines)}; " if lines else "Sleeper board unavailable; ")
               + (f"next kickoff in {soonest:.0f} h. " if soonest is not None else "")
               + ("" if soonest is None else
                  "More than a day out: lines will move; re-run inside 90 minutes of kickoff for the closing read."
                  if soonest > 24 else
                  "Lines settle through the day; the closing read is inside 90 minutes of kickoff."
                  if soonest > 1.5 else "Inside the closing window."))
    inj, proj = st["injuries"], st["projections"]
    out.append("FANTASY: " + ("weekly projections published for "
                              f"{proj['players']} players; " if proj.get("published") else
                              "Sleeper is still serving placeholders (no weekly projections yet); ")
               + ("no injury report for this week yet (the first practice report comes Wednesday)."
                  if not inj.get("rows") else
                  f"practice reports in ({inj['rows']} entries); game designations "
                  + (f"out for {inj['designations']} players." if inj.get("designations")
                     else "not yet (they come Friday; Thursday's game gets them Wednesday).")))
    lg = st.get("league")
    if lg:
        age = lg.get("roster_age_h")
        out.append(f"LEAGUE {lg['name']} ({lg['platform']}): roster from the {lg['source']}"
                   + ("" if age in (None, 0.0) else f", {age:.0f} h old")
                   + (" -- STALE: a personal verdict will be CONDITIONAL until it is refreshed."
                      if age is None or age > 6 else "."))
    return out


def markdown(st: dict) -> str:
    L = [f"# Status -- {st['season']} week {st['week']}", "", *[f"- {v}" for v in verdicts(st)], "",
         "| Game | Kickoff (UTC) | Hours | Spread | Total | Sleeper lines |", "|---|---|---|---|---|---|"]
    for g in st["games"]:
        L.append(f"| {g['game']} | {g['kickoff_utc'][:16]} | {'started' if g['started'] else g['hours_to_kickoff']} | "
                 f"{g['spread'] or '—'} | {g['total'] or '—'} | {'—' if g['lines'] is None else g['lines']} |")
    if st.get("game"):
        rows = st.get("game_injuries")
        L += ["", f"## Injury report -- {st['game']}", ""]
        if rows is None:
            L.append(f"The injury report could not be read ({st['injuries'].get('error', 'unknown error')}).")
        elif not rows:
            L.append("No player on either team has a game designation or a missed or limited practice yet.")
        else:
            L += ["| Team | Player | Pos | Game status | Practice | Injury |", "|---|---|---|---|---|---|"]
            L += [f"| {r['team']} | {r['player']} | {r['position'] or '—'} | {r['status'] or 'no designation yet'} | "
                  f"{r['practice'] or '—'} | {r['injury'] or '—'} |" for r in rows]
            L += ["", "nflverse's copy of the official report, as published (a status and a practice entry can "
                      "disagree there, e.g. Out with full participation)."]
    return "\n".join(L) + "\n"
