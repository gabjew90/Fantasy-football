"""`nfl fantasy waiver`: acquisition targets, compared with my bench.

The user's waiver framework (docs/plans/2026-09-24-consolidation-plan.md, s6):

  Step zero, the horizon (`--horizon`):
    stream   the weeks I need -- this week. An add is worth the rise in this
             week's P(win) with him in my best lineup and my weakest cut gone.
    season   a league-winner candidate. An add is worth the points he adds to
             my best lineup over the remaining weeks, counting only weeks he
             would start (byes included), with the fantasy-playoff weeks
             shown on their own.
  1. Role vs output     the evidence table: usage and whether the role changed
                        beyond noise (noise_bands_v0), never points scored.
  2. Role duration      WHY the role changed: a same-position teammate absent
                        in the weeks the role grew is named, with his status.
                        The PROBABILITY the role lasts is not modelled yet --
                        the report says so rather than guess.
  3. Lineup improvement computed against the specific cut, as above.
  Standing              a contender (top half of the standings) ranks season
                        adds by points added; a team behind ranks them by
                        rest-of-season upside among the adds that improve it.

Drops obey the blocking rule: a player with an established role (60%+ of
snaps, role not falling) is never proposed as a cut on production alone.

Candidates are UNROSTERED in the league; whether one is claimable now (waiver
period, add limits) is not checked, and the report says so. FAAB is out of
scope by the user's decision.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from core import fetch as F
from core.manifest import Manifest
from draftkit.lineup import optimal_lineup

from . import evidence as EV
from . import gate as G
from . import league as LG
from . import weekly as W
from . import winprob as WP
from .contract import fantasy_position

OUT = Path(os.environ.get("NFL_OUT", "/mnt/user-data/outputs"))
POOL_SIZE = 60              # unrostered players considered, by rest-of-season value
USAGE_ADDS = 20             # plus this many by last-week usage, so a fresh role is not missed
SEASON_GAMES = 17
# Weeks a player is assumed to miss from his status, where no return date is
# known: Out/Doubtful this week; IR/PUP/NFI the NFL's four-week minimum.
# Assumptions, stated in every report -- not a model of injury duration.
MISS_WEEKS = {"out": 1, "doubtful": 1, "ir": 4, "pup": 4, "nfi": 4, "sus": 1, "suspended": 1}
# Yahoo's status codes, read as the same statuses (Sleeper spells them out)
STATUS_ALIAS = {"o": "out", "d": "doubtful", "ir-r": "ir", "ir+": "ir", "pup-r": "pup", "pup-p": "pup",
                "nfi-r": "nfi", "nfi-a": "nfi", "susp": "sus"}


def miss_weeks(status: str | None) -> int:
    """Weeks a player is assumed to miss from his platform status (0 = none)."""
    s = (status or "").strip().lower()
    return MISS_WEEKS.get(STATUS_ALIAS.get(s, s), 0)
ESTABLISHED_SNAP = 0.60
STAND_PAT = {"stream": 0.01, "season": 5.0}     # P(win) points / season points below which: stand pat


@dataclass
class WaiverResult:
    markdown: str
    record: dict
    report_path: Path | None = None
    record_path: Path | None = None


# ------------------------------------------------------------------ pieces

standing = LG.standing          # moved to league.py; every command reads it


def byes_by_team(games: pd.DataFrame, season: int, weeks) -> dict:
    """team (nflverse code) -> set of weeks in `weeks` it has no game."""
    g = games[(games.season == season) & (games.game_type == "REG")]
    plays = {}
    for _, r in g.iterrows():
        plays.setdefault(r.home_team, set()).add(int(r.week))
        plays.setdefault(r.away_team, set()).add(int(r.week))
    return {t: {w for w in weeks if w not in ws} for t, ws in plays.items()}


def season_gain(roster_rates: dict, pos: dict, team: dict, slots, flex_slots, weeks, byes: dict,
                add: str | None = None, drop: str | None = None, out_until: dict | None = None,
                starts_of: str | None = None, starts: list | None = None) -> tuple[float, dict]:
    """Points of my best lineup summed over `weeks`, with `add` in and `drop`
    out, each week's lineup chosen from the players who have a game and are
    not expected to miss it (`out_until`: player -> first week he plays).
    Returns (total, points by week). Given `starts_of` and a `starts` list,
    appends each week that player is in the best lineup -- what makes a
    season gain checkable ("+14.9 over weeks 3-9")."""
    ids = [p for p in roster_rates if p != drop] + ([add] if add else [])
    back = out_until or {}
    by_week, total = {}, 0.0
    for w in weeks:
        rows = [{"sleeper_id": p, "pos": pos.get(p),
                 "weekly": 0.0 if (w in byes.get(team.get(p), set()) or w < back.get(p, 0))
                 else roster_rates.get(p, 0.0)} for p in ids]
        lineup = optimal_lineup(rows, slots, flex_slots=flex_slots)
        pts = sum(r["weekly"] for r in lineup)
        if starts is not None and starts_of is not None and any(r["sleeper_id"] == starts_of for r in lineup):
            starts.append(w)
        by_week[w] = pts
        total += pts
    return total, by_week


CONSENSUS_TTL_S = 12 * 3600


def _consensus(ctx, league: str, season: int, store):
    """The manager's consensus, cached under the core cache for 12 hours: the
    manager's own store is read-only for a decision command (it is committed
    state), so without this every run refetched Sleeper, ESPN and FantasyPros."""
    import time
    from manager import consensus as CON
    f = F.DEFAULT_CACHE / "consensus" / f"{league}_{season}.json"
    if f.exists() and time.time() - f.stat().st_mtime < CONSENSUS_TTL_S:
        blob = json.loads(f.read_text(encoding="utf-8"))
        return blob["data"], blob["notes"] + ["consensus from the local 12-hour cache"]
    con, notes = CON.build(ctx, store)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"data": con, "notes": notes}), encoding="utf-8")
    return con, notes


def record_consensus_failures(m, notes) -> None:
    """A rest-of-season source that could not be read (FantasyPros refuses the
    chat container) goes into the manifest as a FAILED input, so the session
    log's command table shows it -- a note alone never reached the log."""
    for n in notes or []:
        if "unavailable" in n and ":" in n:
            name = n.split(":", 1)[0].strip()
            m.record(f"{name} (rest-of-season consensus)", source="manager/consensus.py", status="failed",
                     detail=n[:200])


def protected_cuts(drops, ev: dict) -> set:
    """THE BLOCKING RULE: an established role (60%+ of snaps, role not
    falling) is never a cut on production alone. Applied BEFORE a cut is
    chosen: applied after, bench players who never start all cost zero, the
    tie fell to a protected backup QB, and every pairing was refused -- a
    false STAND PAT (first run, 2026-09-24)."""
    out = set()
    for p in drops:
        e = ev.get(p) or {}
        snap = (e.get("mean") or {}).get("snap_pct")
        falling = any(f.get("changed") and f.get("diff", 0) < 0 for f in (e.get("role_change") or {}).values())
        if snap is not None and snap >= ESTABLISHED_SNAP and not falling:
            out.add(p)
    return out


def cut_order(drops, protected: set, rate: dict) -> list:
    """The cuts a pairing may use, cheapest first (by rest-of-season rate), so
    an add that gains the same against several cuts takes the cheapest."""
    return sorted((d for d in drops if d not in protected), key=lambda d: rate.get(d, 0.0))


def role_cause(gsis: str, usage: pd.DataFrame, positions: dict) -> str | None:
    """If a player's recent weeks came while a same-team, same-position
    teammate who played earlier was absent, name the teammate(s)."""
    d = usage[usage["gsis_id"] == gsis].sort_values("week")
    if len(d) < 3:
        return None
    team, recent = d["team"].iloc[-1], set(d["week"].iloc[-2:])
    earlier = set(d["week"].iloc[:-2])
    mates = usage[(usage["team"] == team) & (usage["gsis_id"] != gsis)]
    names = []
    for g, md in mates.groupby("gsis_id"):
        if positions.get(g) != positions.get(gsis):
            continue
        weeks = set(md["week"])
        if weeks & earlier and not (weeks & recent) and float(md["snap_pct"].fillna(0).mean()) >= 0.3:
            names.append(g)
    return ",".join(sorted(names)) or None


# --------------------------------------------------------------------- run

def run(league: str, positions=("RB", "WR", "TE"), horizon: str = "season", week: int | None = None, *,
        out_dir: Path | None = None, write: bool = True) -> WaiverResult:
    if horizon not in ("stream", "season"):
        raise ValueError("horizon is stream or season")
    m = Manifest(f"fantasy waiver {league}")
    view = LG.load(league, week, m)
    ctx, cfg = view.ctx, view.ctx["cfg"]
    players = json.loads(F.sleeper_players(manifest=m).read_text(encoding="utf-8"))
    rostered = {str(p) for r in ctx["rosters"] for p in (r.get("players") or [])}

    # the rest-of-season rate: the manager's consensus (Sleeper, ESPN, FantasyPros)
    from manager import consensus as CON
    from manager.context import state_dir
    from manager.store import Store
    con, con_notes = _consensus(ctx, league, view.season, Store(state_dir(), read_only=True))
    record_consensus_failures(m, con_notes)
    rate = {p: v["mean"] / SEASON_GAMES for p, v in con.items()}
    upside = {p: max((v.get("per_source") or {}).values(), default=v["mean"]) / SEASON_GAMES for p, v in con.items()}

    pool = [p for p, d in players.items() if isinstance(d, dict) and d.get("active") and d.get("team")
            and fantasy_position(d) in positions and p not in rostered]
    by_value = sorted(pool, key=lambda p: -rate.get(p, 0.0))[:POOL_SIZE]
    usage = EV.season_usage(view.season, manifest=m)
    gmap = {}
    try:
        from core import ids as IDS
        gmap, _ = IDS.sleeper_gsis(IDS.load_id_map(F.DEFAULT_CACHE, manifest=m), players)
    except Exception:  # noqa: BLE001
        pass
    last_wk = int(usage["week"].max()) if len(usage) else 0
    recent = usage[usage["week"] == last_wk].assign(opp=lambda d: d["tgt_share"] + d["carry_share"])
    inv = {g: s for s, g in gmap.items()}
    by_usage = [inv[g] for g in recent.sort_values("opp", ascending=False)["gsis_id"]
                if g in inv and inv[g] in pool and inv[g] not in by_value][:USAGE_ADDS]
    cands = by_value + by_usage

    info = dict(view.info)
    for p in cands:
        d = players.get(p) or {}
        info[p] = {"name": d.get("full_name"), "pos": fantasy_position(d), "team": d.get("team"),
                   "status": d.get("injury_status") or ""}
    pids = list(dict.fromkeys(view.my_players + view.opp_players + cands))
    projs, env, notes = W.project_players(pids, info, view.season, view.week, view.scoring, league, m,
                                          (cfg.get("fantasy") or {}).get("market_weight"))
    ev = EV.for_sleeper(view.my_players + cands, info, view.season, manifest=m)
    gate = G.evaluate(m, view.scoring_yaml, view.scoring_platform, view.my_players, projs)
    stand = standing(ctx["rosters"], view.my_rid)
    # the bench is who is not starting: the lineup set on the platform, or --
    # when none is set -- the best-by-mean lineup, never the whole roster
    from .lineup import candidates as _cands
    starting = view.my_starters or _cands(view.my_players, info, projs, view.slots, view.flex_slots)[0][1]
    drops = [p for p in view.my_players if p not in starting]
    protected = protected_cuts(drops, ev)
    eligible = cut_order(drops, protected, rate)

    rows = []
    if horizon == "stream":
        theirs = view.opp_starters or []
        base = _cands(view.my_players, info, projs, view.slots, view.flex_slots)[0][1]
        pw0 = WP.p_win(base, theirs, projs) if theirs else None
        for c in cands:
            best = None
            for d in eligible:                                               # cheapest cut first: ties go to it
                roster = [p for p in view.my_players if p != d] + [c]
                lineup = _cands(roster, info, projs, view.slots, view.flex_slots)[0][1]
                if c not in lineup:
                    continue
                gain = (WP.p_win(lineup, theirs, projs) - pw0) if theirs else \
                    (sum(projs[p].mean for p in lineup) - sum(projs[p].mean for p in base))
                if best is None or gain > best[1]:
                    best = (d, gain)
            rows.append({"add": c, "drop": best[0] if best else None, "gain": best[1] if best else 0.0})
    else:
        games = pd.read_csv(F.schedule(manifest=m), low_memory=False)
        last = int(ctx.get("last_week") or 17)
        weeks = list(range(view.week, last + 1))
        byes = byes_by_team(games, view.season, weeks)
        team_nv = {p: {"LAR": "LA"}.get((info.get(p) or {}).get("team"), (info.get(p) or {}).get("team"))
                   for p in pids}
        pos = {p: (info.get(p) or {}).get("pos") for p in pids}
        mine = {p: rate.get(p, 0.0) for p in view.my_players}
        playoff = int(((ctx.get("league") or {}).get("settings") or {}).get("playoff_week_start") or 15)
        out_until = {p: view.week + miss_weeks((info.get(p) or {}).get("status")) for p in pids}
        base_total, base_wk = season_gain(mine, pos, team_nv, view.slots, view.flex_slots, weeks, byes,
                                          out_until=out_until)
        for c in cands:
            best = None
            for d in eligible:                                               # cheapest cut first: ties go to it
                st: list = []
                tot, wk = season_gain(dict(mine, **{c: rate.get(c, 0.0)}), pos, team_nv, view.slots,
                                      view.flex_slots, weeks, byes, drop=d, out_until=out_until,
                                      starts_of=c, starts=st)
                gain = tot - base_total
                po = sum(wk[w] - base_wk[w] for w in weeks if w >= playoff)
                if best is None or gain > best[1]:
                    best = (d, gain, po, st)
            rows.append({"add": c, "drop": best[0] if best else None, "gain": best[1] if best else 0.0,
                         "playoff_gain": best[2] if best else 0.0, "start_weeks": best[3] if best else []})

    # EVERY player's position, not only the ones in this report: the teammate who
    # explains a role change is almost never a candidate or on my roster
    pos_map = {g: fantasy_position(players.get(s)) for s, g in gmap.items()}
    for r in rows:
        c = r["add"]
        e = ev.get(c) or {}
        r["ceiling"] = projs[c].ceiling if c in projs else None
        r["ros_upside"] = round(upside.get(c, rate.get(c, 0.0)), 2)
        r["trajectory"] = e.get("trajectory")
        g = gmap.get(c)
        cause = role_cause(g, usage, pos_map) if g else None
        r["cause"] = None if not cause else ", ".join(
            f"{(info.get(inv.get(x)) or {}).get('name') or (players.get(inv.get(x)) or {}).get('full_name') or x}"
            f" ({(players.get(inv.get(x)) or {}).get('injury_status') or 'active'})" for x in cause.split(","))
    ranked, stand_pat = rank_adds(rows, horizon, stand["contender"])

    md = markdown(league, view, horizon, positions, stand, gate, ranked, drops, protected, projs, ev, info,
                  rate, stand_pat, m, notes + con_notes)
    rec = {"command": "fantasy waiver", "league": league, "season": view.season, "week": view.week,
           "horizon": horizon, "positions": list(positions), "standing": stand, "gate": gate.to_dict(),
           "stand_pat": stand_pat, "adds": ranked[:15], "protected_cuts": sorted(protected),
           "drops": [{"player": p, "ros_rate": round(rate.get(p, 0.0), 2), "protected": p in protected}
                     for p in drops],
           "manifest": m.to_dict(), "notes": notes}
    res = WaiverResult(md, rec)
    if write:
        d = Path(out_dir or OUT)
        d.mkdir(parents=True, exist_ok=True)
        slug = f"{league}_{view.season}_wk{view.week:02d}_{horizon}_{'-'.join(positions)}"
        res.report_path, res.record_path = d / f"waiver_{slug}.md", d / f"waiver_{slug}.json"
        res.report_path.write_text(md, encoding="utf-8")
        res.record_path.write_text(json.dumps(rec, indent=1, default=str), encoding="utf-8")
    return res


def _n(p, info):
    i = info.get(p) or {}
    return f"{i.get('name') or p} ({i.get('team') or 'FA'}, {i.get('pos')})"


def _pct(v):
    return "—" if v is None else f"{100 * v:.0f}%"


def week_spans(weeks) -> str:
    """[3, 4, 5, 9] -> "3-5, 9"; nothing -> "none"."""
    ws = sorted(set(weeks or []))
    if not ws:
        return "none"
    spans, start = [], ws[0]
    for a, b in zip(ws, ws[1:] + [None]):
        if b != a + 1:
            spans.append(f"{start}-{a}" if a != start else f"{a}")
            start = b
    return ", ".join(spans)


def rank_adds(rows: list[dict], horizon: str, contender: bool) -> tuple[list[dict], bool]:
    """(ranked adds, stand pat?). Only adds that improve the lineup and come
    with a cut are ranked. A team behind ranks season adds by rest-of-season
    UPSIDE (the most optimistic source's rate) -- not this week's p90, which
    an injured stash reads as zero -- but only AMONG THE ADDS THAT CLEAR THE
    THRESHOLD, which come first; stand pat means no add clears it. (The first
    version tested only the upside leader's gain: Keefamania, 2026 week 3,
    printed STAND PAT on Courtland Sutton's +0.7 while its own table held five
    tight ends above +5.)"""
    limit = STAND_PAT[horizon]
    key = (lambda r: -r["gain"]) if horizon == "stream" or contender else (lambda r: -r["ros_upside"])
    ranked = sorted([r for r in rows if r["gain"] > 0.05 and r["drop"]],
                    key=lambda r: (r["gain"] < limit, key(r)))
    return ranked, (not ranked or ranked[0]["gain"] < limit)


def markdown(league, view, horizon, positions, stand, gate, ranked, drops, protected, projs, ev, info,
             rate, stand_pat, m, notes) -> str:
    unit = "P(win) this week" if horizon == "stream" else "season points added (weeks he would start)"
    L = [f"# Waiver -- {league}, {view.season} week {view.week}: {', '.join(positions)}, {horizon} horizon", "",
         f"**{gate.line()}**", "",
         (f"*Standings unavailable (every team 0-0 with no points) -- ranked as a contender. " if stand.get("unavailable")
          else f"*Standing: {stand['record']}, {stand['rank']} of {stand['teams']} -- "
          + ("a contender: adds ranked by what they add." if stand["contender"] or horizon == "stream" else
             "behind: season adds ranked by rest-of-season UPSIDE (the most optimistic source) among those that "
             "improve the lineup."))
         + " Candidates are UNROSTERED in the league; whether one is claimable right now (waiver period, "
           "add limits) is not checked.*", ""]
    if stand_pat:
        limit = (f"{STAND_PAT[horizon] * 100:g} percentage point of this week's P(win)" if horizon == "stream"
                 else f"{STAND_PAT[horizon]:g} season points")
        best = max(ranked, key=lambda r: r["gain"]) if ranked else None
        L += [f"**STAND PAT -- DO NOT CUT.** No add improves the lineup by the threshold ({limit})"
              + (f"; the best, {_n(best['add'], info)}, adds {_gain(best, horizon)}." if best else "."), ""]
    L += [f"## Adds, ranked ({unit})", "",
          "| Add | Drop | Gain | " + ("Starts (weeks) | Playoff wks | " if horizon == "season" else "") +
          "This week (mean / p10 / p90) | ROS rate | Snap % | Tgt / carry share | Role | Why the role changed |",
          "|---|---|---|" + ("---|---|" if horizon == "season" else "") + "---|---|---|---|---|---|"]
    for r in ranked[:12]:
        c, e = r["add"], ev.get(r["add"]) or {}
        mean = e.get("mean") or {}
        pr = projs.get(c)
        wk = "—" if pr is None else f"{pr.mean:.1f} / {pr.floor if pr.floor is not None else 0:.1f} / " \
                                    f"{pr.ceiling if pr.ceiling is not None else 0:.1f}"
        L.append(f"| {_n(c, info)} | {_n(r['drop'], info) if r['drop'] else '—'} | {_gain(r, horizon)} | "
                 + (f"{week_spans(r.get('start_weeks'))} | {r.get('playoff_gain', 0):+.1f} | "
                    if horizon == "season" else "")
                 + f"{wk} | {rate.get(c, 0):.1f} | {_pct(mean.get('snap_pct'))} | "
                 f"{_pct(mean.get('tgt_share'))} / {_pct(mean.get('carry_share'))} | {r.get('trajectory') or '—'} | "
                 f"{('teammate out: ' + r['cause']) if r.get('cause') else '—'} |")
    if protected:
        L += ["", "**Never proposed as a cut** (an established role -- 60%+ of snaps, role not falling -- is not "
              "dropped on production alone): " + ", ".join(_n(p, info) for p in sorted(protected)) + ".", ""]
    L += ["", "## Your bench, as cut candidates", "",
          "| Player | ROS rate | Snap % | Tgt / carry share | Role | Cut? |", "|---|---|---|---|---|---|"]
    for p in sorted(drops, key=lambda x: rate.get(x, 0.0)):
        e = ev.get(p) or {}
        mean = e.get("mean") or {}
        L.append(f"| {_n(p, info)} | {rate.get(p, 0):.1f} | {_pct(mean.get('snap_pct'))} | "
                 f"{_pct(mean.get('tgt_share'))} / {_pct(mean.get('carry_share'))} | {e.get('trajectory') or '—'} | "
                 f"{'NO -- established role' if p in protected else 'eligible'} |")
    L += ["", "## How to read this", "",
          "- **ROS rate** is the rest-of-season consensus (Sleeper, ESPN, FantasyPros) per game; the season gain "
          "counts only the weeks the player would start in your best lineup, byes included.",
          "- **Role** is usage judged against its measured noise (noise_bands_v0); fewer than four games is "
          "INSUFFICIENT_SAMPLE. **Why the role changed** names a same-position teammate who played earlier and "
          "has been absent since.",
          "- **Missed weeks are assumed from status**, not modelled: Out or Doubtful misses this week; IR, PUP or "
          "NFI the NFL's four-week minimum.",
          "- **Not modelled yet:** the PROBABILITY a changed role lasts (role duration), and claim eligibility. "
          "Weigh a role built on a teammate's absence by when that teammate returns.",
          "", f"*{m.summary_line()}*"] + ([f"*Notes: {'; '.join(notes)}*"] if notes else [])
    return "\n".join(L) + "\n"


def _gain(r, horizon):
    return f"{r['gain'] * 100:+.1f} pts" if horizon == "stream" else f"{r['gain']:+.1f}"
