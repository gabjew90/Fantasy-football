"""`nfl fantasy trade`: a trade is a waiver move with players on both sides.

The waiver command already answers "what does this add do for my lineup over
the rest of the season": the points my best lineup gains, counting only the
weeks a player would start, with byes and expected missed weeks, and the
fantasy-playoff weeks on their own. A trade is the same question with more
than one player moving -- and it has a second roster, so the same arithmetic
runs for the partner too: a trade that only helps me is an offer they refuse.

  --give "A.J. Brown"            players leaving my roster (comma list)
  --get "Courtland Sutton"       players arriving, all from one other roster
  --back "A.J. Brown:8"          a return week, when the news says more than the
                                 status does (IR alone assumes the NFL minimum)

Roster size: a side that ends up over its roster size drops its cheapest
bench player by rest-of-season rate, never one with an established role (the
waiver blocking rule); a side that ends up short fills the open spot with the
free agent who adds most to that side's lineup over the season (replacement
level) -- scoring the spot empty would charge a 2-for-1 for a hole nobody would
leave, and the best free agent by rate is often a QB who never starts -- and
the report names him.

Standing adjusts the reading, as in waivers: a contender goes by points
added; a team behind also sees the upside (the most optimistic source's rate).
"""

from __future__ import annotations

import datetime as dt
import json
import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from core import fetch as F
from core.ids import normalize_name
from core.manifest import Manifest

from . import evidence as EV
from . import gate as G
from . import league as LG
from . import weekly as W
from . import waiver as WV
from .contract import fantasy_position
from .lineup import record_line

OUT = Path(os.environ.get("NFL_OUT", "/mnt/user-data/outputs"))
WORTH_IT = 5.0          # season points: the waiver command's season stand-pat line, for the same reason
FREE_AGENTS_PER_POS = 4  # replacement candidates per position for an open roster spot


class TradeError(ValueError):
    """A name that matches nobody, several players, or the wrong roster."""


@dataclass
class TradeResult:
    markdown: str
    record: dict
    report_path: Path | None = None
    record_path: Path | None = None


# ------------------------------------------------------------------ pieces

def resolve(names: list[str], rosters: dict[int, list[dict]], within: set[int] | None = None) -> dict[str, int]:
    """Player names -> {sleeper_id: roster_id}, searched on the given rosters.
    A name must match exactly one player once punctuation and suffixes are
    stripped ('AJ Brown' finds 'A.J. Brown'); otherwise it is an error the
    user sees, never a guess."""
    out = {}
    for raw in names:
        want = normalize_name(raw)
        hits = [(str(p["sleeper_id"]), rid) for rid, ps in rosters.items() if within is None or rid in within
                for p in ps if normalize_name(p.get("name") or "") == want]
        if not hits:
            raise TradeError(f"no rostered player named '{raw}'" + (" on that side of the trade" if within else ""))
        if len({h[0] for h in hits}) > 1:
            raise TradeError(f"'{raw}' matches more than one rostered player; use the full name")
        out[hits[0][0]] = hits[0][1]
    return out


def parse_back(specs: list[str]) -> dict[str, int]:
    """'A.J. Brown:8' -> {'aj brown': 8}: the first week the player plays."""
    out = {}
    for s in specs:
        name, _, wk = s.rpartition(":")
        if not name or not wk.strip().isdigit():
            raise TradeError(f"--back wants NAME:WEEK, got '{s}'")
        out[normalize_name(name)] = int(wk)
    return out


def settle_roster(ids: list[str], size: int, rate: dict, protected: set, locked: set,
                  free_agents: list[str] = (), value=None, reserve: set = frozenset()) -> tuple[list[str], list[str], list[str]]:
    """Fit a roster to its ACTIVE size after a trade (`reserve` = players in IR
    slots, who do not count): over, and the cheapest droppable players go
    (never protected, never the players just received, never an IR stash);
    under, and each open spot takes the free agent that raises `value(roster)`
    the most (by rate when no value function is given).
    Returns (roster, dropped, added)."""
    ids = list(ids)
    dropped, added = [], []
    active = lambda: sum(1 for p in ids if p not in reserve)
    while active() > size:
        cands = [p for p in ids if p not in protected and p not in locked and p not in reserve]
        if not cands:
            break
        # the drop that costs the lineup least -- not the lowest rate: the lowest
        # rate on a roster is often its only defense or kicker, whose loss empties
        # a starting slot all season (first run: -97 for the partner)
        cut = (max(cands, key=lambda p: (value([q for q in ids if q != p]), -rate.get(p, 0.0)))
               if value is not None else min(cands, key=lambda p: rate.get(p, 0.0)))
        dropped.append(cut)
        ids.remove(cut)
    pool = [fa for fa in free_agents if fa not in ids]
    while active() < size and pool:
        best = (max(pool, key=lambda fa: value(ids + [fa])) if value is not None
                else max(pool, key=lambda fa: rate.get(fa, 0.0)))
        ids.append(best); added.append(best); pool.remove(best)
    return ids, dropped, added


def evaluate_side(before: list[str], out_ids: set, in_ids: set, *, limit: int, reserve: set, rate: dict,
                  protected: set, free: list[str], value, upside_value, weeks: list[int], playoff: int) -> dict:
    """One side of a trade: the roster after it (fitted to the limit), and what
    it does to that side's best lineup. `value(ids)` / `upside_value(ids)` give
    (season total, points by week) at the mean and at the upside rates."""
    after = [p for p in before if p not in out_ids] + list(in_ids)
    after, dropped, added = settle_roster(after, limit, rate, protected, set(in_ids), free,
                                          value=lambda ids: value(ids)[0], reserve=reserve - set(out_ids))
    b_tot, b_wk = value(before)
    a_tot, a_wk = value(after)
    return {"gain": a_tot - b_tot, "playoff_gain": sum(a_wk[w] - b_wk[w] for w in weeks if w >= playoff),
            "upside_gain": upside_value(after)[0] - upside_value(before)[0], "dropped": dropped, "added": added,
            "open_spots": max(sum(1 for p in before if p not in reserve)
                              - sum(1 for p in after if p not in reserve), 0) if not added else 0,
            "by_week": {w: round(a_wk[w] - b_wk[w], 2) for w in weeks}}


def verdict_for(me: dict, contender: bool) -> tuple[str, str]:
    """('worth it' | 'roughly even' | 'not worth it', the basis). A contender
    goes by points added; a team behind by UPSIDE (the user's framework: the
    standing adjusts the whole reading)."""
    gain, basis = (me["gain"], "points added") if contender else (me["upside_gain"], "upside (you are behind)")
    v = "worth it" if gain >= WORTH_IT else "not worth it" if gain <= -WORTH_IT else "roughly even"
    return v, basis


def side_value(ids: list[str], rate: dict, pos: dict, team: dict, slots, flex, weeks, byes, out_until) -> tuple[float, dict]:
    """Season points of this roster's best lineup week by week (waiver.season_gain)."""
    return WV.season_gain({p: rate.get(p, 0.0) for p in ids}, pos, team, slots, flex, weeks, byes,
                          out_until=out_until)


# --------------------------------------------------------------------- run

def run(league: str, give: list[str], get: list[str], back: list[str] | None = None, week: int | None = None, *,
        out_dir: Path | None = None, write: bool = True) -> TradeResult:
    if not give or not get:
        raise TradeError("a trade needs --give and --get")
    m = Manifest(f"fantasy trade {league}")
    view = LG.load(league, week, m)
    ctx, cfg = view.ctx, view.ctx["cfg"]
    rosters = {int(k): v for k, v in ctx["roster_players"].items()}
    my = view.my_rid
    gave = resolve(give, rosters, within={my})
    got = resolve(get, rosters, within=set(rosters) - {my})
    partners = set(got.values())
    if len(partners) != 1:
        raise TradeError("the players you get must all come from one other roster")
    partner = partners.pop()
    names_back = parse_back(back or [])

    players = json.loads(F.sleeper_players(manifest=m).read_text(encoding="utf-8"))
    from manager.context import state_dir
    from manager.store import Store
    con, con_notes = WV._consensus(ctx, league, view.season, Store(state_dir(), read_only=True))
    WV.record_consensus_failures(m, con_notes)
    rate = {p: v["mean"] / WV.SEASON_GAMES for p, v in con.items()}
    upside = {p: max((v.get("per_source") or {}).values(), default=v["mean"]) / WV.SEASON_GAMES
              for p, v in con.items()}

    mine = [str(p["sleeper_id"]) for p in rosters.get(my, [])]
    theirs = [str(p["sleeper_id"]) for p in rosters.get(partner, [])]
    info = {}
    for rid in (my, partner):
        for p in rosters.get(rid, []):
            raw = players.get(str(p["sleeper_id"])) or {}
            info[str(p["sleeper_id"])] = {"name": p.get("name"), "pos": fantasy_position(raw) or p.get("pos"),
                                          "team": p.get("team"), "status": p.get("status") or ""}
    # replacement level: the best unrostered players by rest-of-season rate
    rostered = {str(p["sleeper_id"]) for ps in rosters.values() for p in ps}
    # (the top few AT EACH POSITION: the top ten overall are mostly quarterbacks,
    # who never start for a team that already has one)
    free = []
    for fpos in ("QB", "RB", "WR", "TE"):
        free += sorted((p for p, d in players.items() if isinstance(d, dict) and d.get("active") and d.get("team")
                        and fantasy_position(d) == fpos and p not in rostered and p in rate),
                       key=lambda p: -rate.get(p, 0.0))[:FREE_AGENTS_PER_POS]
    for p in free:
        d = players.get(p) or {}
        info[p] = {"name": d.get("full_name"), "pos": fantasy_position(d), "team": d.get("team"),
                   "status": d.get("injury_status") or ""}
    pids = list(dict.fromkeys(mine + theirs + free))
    # the league's ACTIVE roster limit (IR slots excluded) and who sits in IR:
    # inferring the size from roster lengths let a stashed IR player make a
    # 2-for-1 look free
    lg = ctx.get("league") or {}
    limit = sum(1 for p in (lg.get("roster_positions") or []) if str(p).upper() not in ("IR", "IR+")) or None
    reserve = {int(r["roster_id"]): {str(x) for x in (r.get("reserve") or [])} for r in ctx["rosters"]}

    games = pd.read_csv(F.schedule(manifest=m), low_memory=False)
    last = int(ctx.get("last_week") or 17)
    weeks = list(range(view.week, last + 1))
    byes = WV.byes_by_team(games, view.season, weeks)
    team_nv = {p: {"LAR": "LA"}.get((info.get(p) or {}).get("team"), (info.get(p) or {}).get("team")) for p in pids}
    pos = {p: (info.get(p) or {}).get("pos") for p in pids}
    playoff = int(((ctx.get("league") or {}).get("settings") or {}).get("playoff_week_start") or 15)
    # --back applies to the players in the trade only, so a namesake elsewhere
    # is never benched by it
    trade_ids = set(gave) | set(got)
    back_for = {}
    for nm, wk in names_back.items():
        hits = [p for p in trade_ids if normalize_name((info.get(p) or {}).get("name") or "") == nm]
        if not hits:
            raise TradeError(f"--back names '{nm}', who is not in this trade")
        back_for.update({p: wk for p in hits})
    out_until, assumed = {}, {}
    for p in pids:
        status = (info.get(p) or {}).get("status") or ""
        if p in back_for:
            out_until[p] = back_for[p]
            assumed[p] = f"back week {back_for[p]} (as given)"
        elif WV.miss_weeks(status):
            out_until[p] = view.week + WV.miss_weeks(status)
            assumed[p] = f"back week {out_until[p]} (assumed from '{status}': the NFL minimum, not a prognosis)"

    ev = EV.for_sleeper(pids, info, view.season, manifest=m)
    # the gate covers BOTH rosters: the verdict rests on the partner's side too
    both = list(dict.fromkeys(mine + theirs))
    info_both = {**dict(view.info), **{p: info[p] for p in both if p in info}}
    projs, _env, notes = W.project_players(both, info_both, view.season, view.week, view.scoring,
                                           league, m, (cfg.get("fantasy") or {}).get("market_weight"))
    gate = G.evaluate(m, view.scoring_yaml, view.scoring_platform, both, projs)

    value = lambda ids: side_value(ids, rate, pos, team_nv, view.slots, view.flex_slots, weeks, byes, out_until)
    upside_value = lambda ids: side_value(ids, upside, pos, team_nv, view.slots, view.flex_slots, weeks, byes,
                                          out_until)

    def side(before, rid, out_ids, in_ids, pool):
        # never blame a trade for an overflow the roster already had
        active_now = sum(1 for p in before if p not in reserve.get(rid, set()))
        lim = max(limit or 0, active_now)
        return evaluate_side(before, set(out_ids), set(in_ids), limit=lim, reserve=reserve.get(rid, set()),
                             rate=rate, protected=WV.protected_cuts([p for p in before if p not in out_ids], ev),
                             free=pool, value=value, upside_value=upside_value, weeks=weeks, playoff=playoff)

    me = side(mine, my, gave, got, free)
    them = side(theirs, partner, got, gave, [p for p in free if p not in me["added"]])
    stand = view.standing
    verdict, basis = verdict_for(me, bool(stand.get("contender", True)))
    realistic = ("they gain too" if them["gain"] > 0 else
                 "they lose little" if them["gain"] > -WORTH_IT else "they lose clearly -- unlikely to be accepted")

    md = markdown(league, view, stand, gate, gave, got, info, rate, upside, ev, me, them, verdict, basis, realistic,
                  assumed, playoff, ctx["users_by_rid"].get(partner, "partner"), m, notes + con_notes)
    rec = {"command": "fantasy trade", "league": league, "season": view.season, "week": view.week,
           "give": sorted(gave), "get": sorted(got), "partner_rid": partner, "standing": stand,
           "gate": gate.to_dict(), "me": me, "them": them, "verdict": verdict, "verdict_basis": basis,
           "realistic": realistic, "roster_limit": limit,
           "assumed_returns": assumed, "manifest": m.to_dict(), "notes": notes}
    res = TradeResult(md, rec)
    if write:
        d = Path(out_dir or OUT)
        d.mkdir(parents=True, exist_ok=True)
        slug = f"{league}_{view.season}_wk{view.week:02d}_" + "-".join(
            normalize_name((info.get(p) or {}).get("name") or p).replace(" ", "_") for p in list(gave) + list(got))
        res.report_path, res.record_path = d / f"trade_{slug[:120]}.md", d / f"trade_{slug[:120]}.json"
        res.report_path.write_text(md, encoding="utf-8")
        res.record_path.write_text(json.dumps(rec, indent=1, default=str), encoding="utf-8")
    return res


def _n(p, info):
    d = info.get(p) or {}
    return f"{d.get('name') or p} ({d.get('pos') or '?'}, {d.get('team') or 'FA'})"


def markdown(league, view, stand, gate, gave, got, info, rate, upside, ev, me, them, verdict, basis, realistic,
             assumed, playoff, partner_name, m, notes) -> str:
    L = [f"# Trade -- {league}, {view.season} week {view.week}", "", f"**{gate.line()}**", "",
         record_line(stand), "",
         f"**Give** {', '.join(_n(p, info) for p in gave)}  **for** {', '.join(_n(p, info) for p in got)} "
         f"(from {partner_name}).", "",
         f"**For you: {verdict}** (on {basis}) -- {me['gain']:+.1f} season points to your best lineup "
         f"({me['playoff_gain']:+.1f} in the fantasy playoffs, week {playoff} on). "
         f"**For them:** {them['gain']:+.1f} ({realistic}).", ""]
    if not stand.get("contender", True):
        L += [f"*You are behind, so upside counts: on the most optimistic source, {me['upside_gain']:+.1f} "
              "season points.*", ""]
    L += ["| Player | Side | Rest-of-season points/game | Upside/game | Status | Snap share | Role trend |",
          "|---|---|---|---|---|---|---|"]
    for p, side in [(p, "you give") for p in gave] + [(p, "you get") for p in got]:
        e = ev.get(p) or {}
        snap = (e.get("mean") or {}).get("snap_pct")
        L.append(f"| {_n(p, info)} | {side} | {rate.get(p, 0.0):.1f} | {upside.get(p, rate.get(p, 0.0)):.1f} | "
                 f"{(info.get(p) or {}).get('status') or 'active'}"
                 + (f"; {assumed[p]}" if p in assumed else "") + " | "
                 + (f"{snap:.0%}" if snap is not None else "--") + f" | {e.get('trajectory') or '--'} |")
    for label, side in (("You", me), ("They", them)):
        if side["dropped"]:
            L += ["", f"{label} must drop to fit the roster: {', '.join(_n(p, info) for p in side['dropped'])} "
                  "(the drop that costs that lineup least; established roles are never dropped)."]
        if side["added"]:
            L += ["", f"{label} fill the open roster spot with the free agent who helps that lineup most: "
                  + ", ".join(f"{_n(p, info)} ({rate.get(p, 0.0):.1f}/game)" for p in side["added"]) + "."]
        if side["open_spots"]:
            L += ["", f"{label} end up {side['open_spots']} player(s) short; the open spot is played empty here."]
    L += ["", "## How to read this", "",
          "- **Season points** are what your best lineup gains or loses over the rest of the season, week by "
          "week, counting only weeks a player would start and not weeks he is on a bye or expected out -- the "
          "waiver command's arithmetic, run on both rosters.",
          f"- **Worth it** means at least {WORTH_IT:g} season points either way; inside that, the trade is "
          "roughly even and the reasons below the numbers decide it.",
          "- **Rates** are the rest-of-season consensus (Sleeper, ESPN, FantasyPros when reachable) per game. "
          "They carry no injury prognosis: a return week comes from `--back` or, failing that, the NFL minimum "
          "for the status, and the table says which.",
          "- **Not modelled:** how long a changed role lasts, trade-deadline and league rules, and the partner's "
          "own valuation beyond these numbers.", "",
          f"*{m.summary_line()}*"]
    if notes:
        L += ["", "*notes: " + "; ".join(str(n) for n in notes[:6]) + "*"]
    return "\n".join(L) + "\n"
