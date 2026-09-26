"""Question tools: the engine's numbers for one question at a time.

Chat answers a conversation, not a report. These tools give it the pieces --
one player's week, a head-to-head, a what-if swap, a roster -- each printed
as a few plain lines (or JSON with --json), read from the session's league
snapshot (fantasy.snapshot) so a follow-up takes a second, not ten.

Every number is the decision commands' own: weekly_blend_v0 projections with
their dispersion_v0 range, fantasy.winprob for any probability, fantasy.
evidence for usage, the lineup command's injury watch and FantasyPros lookup.
Nothing here computes a new kind of number. What the tools add is SHAPE: the
question decides which numbers are printed, and chat decides what to say.

Each answer carries the data's age and the league data gate, because a
snapshot can be up to snapshot.TTL_MIN minutes old and an injury can change
inside that.
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field

import numpy as np

from core import ids as IDS
from core.manifest import Manifest
from draftkit.lineup import optimal_lineup

from . import environment as E
from . import evidence as EV
from . import lineup as LU
from . import winprob as WP
from .snapshot import Snapshot

MAX_CANDIDATES = 6


class AskError(ValueError):
    """The question cannot be answered as asked: a name matching nobody or
    several players, or a swap no legal lineup allows. The message says which."""


@dataclass
class AskResult:
    text: str
    data: dict
    record: dict = field(default_factory=dict)      # gate + manifest, for the session log
    report_path: None = None

    def render(self, as_json: bool) -> str:
        return json.dumps(self.data, indent=1, default=str) if as_json else self.text


# ------------------------------------------------------------------ names

def resolve(snap: Snapshot, name: str, notes: list | None = None) -> str:
    """A Sleeper id from an id, a full name, a last name or a defense's team.

    Exact names go through core.ids.NameIndex (fantasy eligibility, live
    players first). A partial name ("Kelce", "Bijan") is matched as a whole
    word inside the full name. Several matches are an error listing them -- a
    guess would answer about the wrong player -- unless exactly one of them is
    on the user's roster: then that one, with a note naming the others."""
    s = str(name).strip()
    if s in snap.players:
        return s
    defs = {str(p.get("team") or "").upper(): sid for sid, p in snap.players.items()
            if p.get("position") == "DEF"}
    if s.upper() in defs:
        return defs[s.upper()]
    idx = IDS.NameIndex(snap.players)
    pid = idx.resolve(s)
    if pid:
        return pid
    want = IDS.normalize_name(s)
    if not want:
        raise AskError("empty player name")
    hits = []
    for sid, p in snap.players.items():
        full = IDS.normalize_name(p.get("full_name") or f"{p.get('first_name', '')} {p.get('last_name', '')}")
        words = full.split()
        if want == full or (want in words) or (len(want.split()) > 1 and want in full):
            hits.append(sid)
    if not hits:
        # a defense by nickname or city ("Bengals", "Cincinnati")
        hits = [sid for sid, p in snap.players.items() if p.get("position") == "DEF"
                and want in IDS.normalize_name(f"{p.get('first_name', '')} {p.get('last_name', '')}").split()]
    if len(hits) > 1:
        # the rostered and projected are the ones a question is about
        hits = [h for h in hits if snap.owner_rid(h) is not None or h in snap.projections] or hits
    if len(hits) > 1:
        # a partial name in the user's own league chat means the user's player
        # when exactly one match is his -- said out loud, never silently
        mine = [h for h in hits if snap.owner_rid(h) == snap.my_rid]
        if len(mine) == 1 and notes is not None:
            notes.append(f"'{s}' read as {_label(snap, mine[0])}, on your roster; it also matches "
                         + ", ".join(_label(snap, h) for h in hits if h != mine[0])[:300])
            return mine[0]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise AskError(f"no player named '{s}' on an NFL roster this week")
    opts = ", ".join(f"{_label(snap, h)} (id {h})" for h in hits[:MAX_CANDIDATES])
    raise AskError(f"'{s}' matches more than one player: {opts}. Use the full name or the id.")


def _label(snap: Snapshot, sid: str) -> str:
    i = snap.info.get(sid) or {}
    return f"{i.get('name') or sid} ({i.get('pos') or '?'}, {i.get('team') or 'FA'})"


# ------------------------------------------------------------------ facts

def owner(snap: Snapshot, sid: str) -> dict:
    rid = snap.owner_rid(sid)
    if rid is None:
        return {"rid": None, "who": "free agent", "starting": False}
    t = snap.teams[rid]
    who = "you" if rid == snap.my_rid else ("your opponent" if rid == snap.opp_rid else "another team")
    return {"rid": rid, "who": who, "team_name": t["name"], "starting": sid in t["starters"]}


def _game(snap: Snapshot, team: str | None) -> dict | None:
    e = snap.env.get(team or "")
    if not e:
        return None
    k = LU._kick(e)
    return dict(e, kickoff_pt=LU._pt(k) if k else None, team=team)


def projection(snap: Snapshot, sid: str) -> dict:
    p = snap.projections.get(sid)
    if p is None:
        return {"mean": None, "why": "no projection this week (not in Sleeper's weekly projections)"}
    d = p.detail or {}
    out = {"mean": round(p.mean, 1), "range_from": p.range_from or None,
           "p10": _r(p.q(0.10)), "p25": _r(p.q(0.25)), "p50": _r(p.q(0.50)), "p75": _r(p.q(0.75)), "p90": _r(p.q(0.90)),
           "sleeper": _r(d.get("sleeper")), "market": _r(d.get("market")), "market_partial": d.get("market_partial"),
           "market_weight": d.get("market_weight"), "zero_reason": d.get("zero_reason"), "flag": d.get("flag"),
           "final": bool(d.get("final")), "projected_before_kickoff": _r(d.get("projected"))}
    return {k: v for k, v in out.items() if v is not None}


def _r(v, d=1):
    return None if v is None else round(float(v), d)


def usage(ev: dict | None) -> dict:
    e = ev or {}
    if not e.get("weeks"):
        return {"weeks": 0, "note": e.get("note") or "no usage this season"}
    ser, mean = e.get("series") or {}, e.get("mean") or {}
    changed = {m: {"earlier": f.get("earlier"), "recent": f.get("recent")}
               for m, f in (e.get("role_change") or {}).items() if f.get("changed")}
    return {"weeks": e["weeks"], "week_list": e.get("week_list"), "snap_pct_by_week": ser.get("snap_pct"),
            "snap_pct": mean.get("snap_pct"), "target_share": mean.get("tgt_share"),
            "carry_share": mean.get("carry_share"), "wopr": mean.get("wopr"),
            "targets": (e.get("totals") or {}).get("targets"), "carries": (e.get("totals") or {}).get("carries"),
            "inside10_targets": (e.get("totals") or {}).get("i10_tgt"),
            "inside10_carries": (e.get("totals") or {}).get("i10_car"),
            "role": e.get("trajectory"), "role_changed": changed or None,
            "partial_weeks": e.get("partial_weeks") or None}


def _record(snap: Snapshot, m: Manifest) -> dict:
    """The session log's view of a tool call: the snapshot's gate, and every
    input the snapshot and this call read (the call's own reads last)."""
    entries = list((snap.manifest or {}).get("entries") or []) + list(m.entries)
    return {"gate": snap.gate, "manifest": {"entries": entries}, "snapshot_age_min": round(snap.age_min(), 1)}


def header(snap: Snapshot) -> str:
    g = snap.gate or {}
    check = "PASS" if g.get("passed") else "FAIL -- " + "; ".join(
        f"{c.get('name')} ({c.get('detail')})" for c in g.get("checks") or [] if not c.get("passed"))
    built = dt.datetime.fromisoformat(snap.built_at_utc)
    return (f"{snap.league}, {snap.season} week {snap.week} -- league read {snap.age_min():.0f} min ago "
            f"({LU._pt(built)}; `--fresh` re-reads) -- league data check: {check}")


# ------------------------------------------------------------------ tools

def players(snap: Snapshot, names: list[str], *, with_usage: bool = True, with_fp: bool = True) -> AskResult:
    """One or more players' week: owner, game, status, projection and range,
    usage and role, designated teammates. Two or more: who outscores whom."""
    if not names:
        raise AskError("name at least one player")
    notes: list = []
    sids = list(dict.fromkeys(resolve(snap, n, notes) for n in names))
    m = Manifest(f"fantasy player {snap.league}")
    ev = EV.for_sleeper(sids, snap.info, snap.season, manifest=m) if with_usage else {}
    watch = LU.injury_watch(sids, snap.info, snap.players, snap.league)
    # when his status settles, and which of MY players at his position lock
    # before then -- the "do I have to choose before the news?" question
    LU.lock_order(watch, snap.my_players, snap.info, snap.env, dt.datetime.now(dt.timezone.utc))
    fp, fp_note = (LU.fp_practice(watch, snap.season, snap.week, m) if (watch and with_fp) else ({}, ""))
    by_pid = {w["pid"]: w for w in watch}
    rows = []
    for sid in sids:
        i, raw = snap.info.get(sid) or {}, snap.players.get(sid) or {}
        w = by_pid.get(sid) or {}
        row = {"id": sid, "name": i.get("name"), "pos": i.get("pos"), "team": i.get("team"),
               "owner": owner(snap, sid), "game": _game(snap, i.get("team")),
               "status": i.get("status") or raw.get("injury_status") or "",
               "injury": raw.get("injury_body_part"), "practice_sleeper": raw.get("practice_participation"),
               "fantasypros": fp.get(sid), "projection": projection(snap, sid),
               "status_settles_pt": w.get("status_known_pt") if w.get("own") else None,
               "my_players_locking_first": (w.get("locks_before") or None) if w.get("own") else None,
               "usage": usage(ev.get(sid)) if with_usage else None,
               "designated_teammates": [{k: t.get(k) for k in ("name", "pos", "status", "part", "scenario")}
                                        | {"fantasypros": fp.get(t["sid"])} for t in w.get("teammates") or []]}
        rows.append(row)
    data = {"league": snap.league, "season": snap.season, "week": snap.week, "players": rows,
            "fantasypros_note": fp_note or None, "name_notes": notes or None}
    if len(sids) >= 2:
        data["head_to_head"] = head_to_head(snap, sids)
    L = [header(snap), ""] + [f"({n}.)" for n in notes] + ([""] if notes else [])
    for r in rows:
        L += _player_lines(r) + [""]
    if fp_note and not fp:
        L.append(f"(No FantasyPros practice reports: {fp_note}.)")
    if data.get("head_to_head"):
        L += _h2h_lines(snap, data["head_to_head"])
    return AskResult("\n".join(L).rstrip() + "\n", data, _record(snap, m))


def head_to_head(snap: Snapshot, sids: list[str]) -> dict:
    """P(A outscores B) for two players; for three or more, each one's chance
    of being the top scorer. Draws come from fantasy.winprob (independent
    players: two in the same game are drawn as if unrelated)."""
    draws = {s: WP.draws(snap.projections.get(s), WP.N_DRAWS, WP._seed(s, 7)) for s in sids}
    same_game = sorted({(snap.info.get(a) or {}).get("name") for a in sids for b in sids if a < b
                        and _same_game(snap, a, b)} - {None})
    if len(sids) == 2:
        a, b = sids
        p = float(np.mean(draws[a] > draws[b]) + 0.5 * np.mean(draws[a] == draws[b]))
        mean = {s: (snap.projections[s].mean if s in snap.projections else 0.0) for s in sids}
        out = {"p_first_outscores_second": round(p, 3), "first": a, "second": b,
               "mean_gap": round(mean[a] - mean[b], 1)}
    else:
        stack = np.vstack([draws[s] for s in sids])
        top = np.argmax(stack, axis=0)
        out = {"p_top_scorer": {s: round(float(np.mean(top == k)), 3) for k, s in enumerate(sids)}}
    out["same_game"] = bool(same_game)
    return out


def _same_game(snap: Snapshot, a: str, b: str) -> bool:
    ta, tb = (snap.info.get(a) or {}).get("team"), (snap.info.get(b) or {}).get("team")
    ea = snap.env.get(ta or "") or {}
    return bool(ta) and (ta == tb or ea.get("opp") == tb)


def swap(snap: Snapshot, start: list[str], bench: list[str] | None = None) -> AskResult:
    """P(win) with the lineup you have set, and with START in its place.

    With --bench the named players sit and nothing else moves. Without it,
    each legal replacement is tried (every current starter START could take
    the seat of) and all are listed best first -- "if I start X, who sits?".
    A player whose game has kicked off cannot move in or out."""
    m = Manifest(f"fantasy swap {snap.league}")
    notes: list = []
    ins = [resolve(snap, n, notes) for n in start]
    outs = [resolve(snap, n, notes) for n in (bench or [])]
    mine = set(snap.my_players)
    for s in ins + outs:
        if s not in mine:
            raise AskError(f"{_label(snap, s)} is not on your roster ({owner(snap, s)['who']})")
    now = dt.datetime.now(dt.timezone.utc)
    locked = {p for p in snap.my_players if E.started(snap.env.get((snap.info.get(p) or {}).get("team")), now)}
    base, base_how = _baseline(snap)
    for s in ins:
        if s in base:
            raise AskError(f"{_label(snap, s)} is already in {base_how}")
        if s in locked:
            raise AskError(f"{_label(snap, s)}'s game has kicked off: he cannot move into the lineup")
    for s in outs:
        if s not in base:
            raise AskError(f"{_label(snap, s)} is not in {base_how}")
        if s in locked:
            raise AskError(f"{_label(snap, s)}'s game has kicked off: he cannot move out of the lineup")
    theirs, their_how = _opponent(snap)

    def pw(ids):
        return WP.p_win(ids, theirs, snap.projections) if theirs else None

    def total(ids):
        return round(sum(snap.projections[p].mean for p in ids if p in snap.projections), 1)

    if outs:
        options = [outs]
    else:
        movable = [p for p in base if p not in locked]
        options = [[o] for o in movable]
        if len(ins) > 1:
            import itertools
            options = [list(c) for c in itertools.combinations(movable, len(ins))]
    rows = []
    for o in options:
        ids = _legal(snap, [p for p in base if p not in o] + ins)
        if ids is None:
            continue
        rows.append({"bench": o, "lineup": ids, "p_win": pw(ids), "projected_total": total(ids)})
    if not rows:
        what = f"benching {', '.join(_label(snap, o) for o in outs)}" if outs else "any current starter"
        raise AskError(f"no legal lineup starts {', '.join(_label(snap, s) for s in ins)} in place of {what} "
                       "(the league's slots do not allow it)")
    rows.sort(key=lambda r: (-(r["p_win"] if r["p_win"] is not None else r["projected_total"])))
    base_pw = pw(base)
    data = {"league": snap.league, "week": snap.week, "baseline": {"from": base_how, "lineup": base,
            "p_win": base_pw, "projected_total": total(base)},
            "opponent": {"name": snap.teams[snap.opp_rid]["name"] if snap.opp_rid is not None else None,
                         "lineup_from": their_how, "projected_total": total(theirs) if theirs else None},
            "start": ins, "options": rows, "noise": LU.MIN_GAIN, "name_notes": notes or None,
            "players": {s: projection(snap, s) for s in ins + sorted({x for r in rows for x in r["bench"]})}}
    L = [header(snap), ""] + [f"({n}.)" for n in notes] + ([""] if notes else [])
    opp = data["opponent"]
    if base_pw is not None:
        L.append(f"Now ({base_how}): projects {total(base)} vs {opp['name']} {opp['projected_total']} "
                 f"({their_how}); P(win) {base_pw:.1%}.")
    else:
        L.append(f"Now ({base_how}): projects {total(base)}; no opponent this week, so only points are compared.")
    for r in rows:
        who = ", ".join(_label(snap, x) for x in r["bench"])
        d = "" if r["p_win"] is None or base_pw is None else f" ({(r['p_win'] - base_pw) * 100:+.1f} percentage points)"
        L.append(f"- Start {', '.join(_label(snap, s) for s in ins)}, sit {who}: projects {r['projected_total']}"
                 + ("" if r["p_win"] is None else f"; P(win) {r['p_win']:.1%}{d}") + ".")
    L += ["", "The players:"] + [f"- {_label(snap, s)}: {_proj_text(data['players'][s])}" for s in data["players"]]
    L += ["", f"P(win) differences under {LU.MIN_GAIN * 100:.1f} percentage points are simulation noise. Players are drawn "
              "independently (a same-game pair's swing is understated)."]
    return AskResult("\n".join(L) + "\n", data, _record(snap, m))


def roster(snap: Snapshot, which: str = "me") -> AskResult:
    """A roster with this week's numbers: yours (default), your opponent's
    ("opp"), or any team by its manager's name."""
    rid = _team_rid(snap, which)
    t = snap.teams[rid]
    m = Manifest(f"fantasy roster {snap.league}")
    order = {p: k for k, p in enumerate(("QB", "RB", "WR", "TE", "K", "DEF"))}
    rows = []
    for sid in t["players"]:
        i = snap.info.get(sid) or {}
        rows.append({"id": sid, "name": i.get("name"), "pos": i.get("pos"), "team": i.get("team"),
                     "status": i.get("status") or "", "starting": sid in t["starters"],
                     "game": _game(snap, i.get("team")), "projection": projection(snap, sid)})
    rows.sort(key=lambda r: (not r["starting"], order.get(r["pos"], 9), -(r["projection"].get("mean") or 0)))
    who = "you" if rid == snap.my_rid else ("your opponent" if rid == snap.opp_rid else "another team")
    data = {"league": snap.league, "week": snap.week, "team": t["name"], "who": who, "players": rows}
    if rid == snap.my_rid:
        data["standing"] = snap.standing
    L = [header(snap), "", f"{t['name']} ({who})" + (f" -- record {snap.standing['record']}, "
         f"{snap.standing['rank']} of {snap.standing['teams']}" if rid == snap.my_rid and snap.standing.get("rank")
         else "") + ":"]
    for label, keep in (("Starting", True), ("Bench", False)):
        part = [r for r in rows if r["starting"] == keep]
        if part:
            L += ["", f"{label}:"] + [f"- {r['pos']} {r['name']} ({r['team'] or 'FA'})"
                                      + (f" [{r['status']}]" if r["status"] else "")
                                      + f": {_proj_text(r['projection'], r['game'])}" for r in part]
    if not t["starters"]:
        L += ["", "(No lineup set on the platform.)"]
    return AskResult("\n".join(L) + "\n", data, _record(snap, m))


# ------------------------------------------------------------------ helpers

def _team_rid(snap: Snapshot, which: str) -> int:
    w = (which or "me").strip().lower()
    if w in ("me", "mine", "my", "you"):
        return snap.my_rid
    if w in ("opp", "opponent", "them"):
        if snap.opp_rid is None:
            raise AskError("no opponent this week")
        return snap.opp_rid
    hits = [rid for rid, t in snap.teams.items() if w in str(t["name"]).lower()]
    if len(hits) == 1:
        return hits[0]
    names = ", ".join(sorted(str(t["name"]) for t in snap.teams.values()))
    raise AskError(f"'{which}' {'matches several teams' if hits else 'matches no team'}; the managers are: {names}")


def _baseline(snap: Snapshot) -> tuple[list, str]:
    """The lineup a swap is measured against: the one set on the platform
    when it is full, else the best by mean (what the lineup command starts from)."""
    t = snap.teams[snap.my_rid]
    best = _best(snap, snap.my_players)
    if len(t["starters"]) >= len(best):
        return list(t["starters"]), "the lineup you have set"
    return best, "the best-by-mean lineup (no full lineup set)"


def _opponent(snap: Snapshot) -> tuple[list, str]:
    if snap.opp_rid is None:
        return [], "no opponent this week"
    t = snap.teams[snap.opp_rid]
    best = _best(snap, t["players"])
    if len(t["starters"]) >= len(best):
        return list(t["starters"]), "the lineup they have set"
    return best, "their best-by-mean lineup (they have not set a full one)"


def _best(snap: Snapshot, pids) -> list:
    return [r["sleeper_id"] for r in optimal_lineup(LU._rows(pids, snap.info, snap.projections),
                                                    snap.slots, flex_slots=snap.flex_slots)]


def _legal(snap: Snapshot, ids: list) -> list | None:
    """`ids` seated as one lineup, or None when the slots cannot hold them all."""
    rows = [dict(r, weekly=r["weekly"] + LU.BOOST) for r in LU._rows(ids, snap.info, snap.projections)]
    seated = [r["sleeper_id"] for r in optimal_lineup(rows, snap.slots, flex_slots=snap.flex_slots)]
    return seated if set(seated) == set(ids) and len(seated) == len(ids) else None


def _proj_text(p: dict, game: dict | None = None) -> str:
    if p.get("mean") is None:
        return p.get("why") or "no projection"
    if p.get("final"):
        s = f"{p['mean']} pts, final (projected {p.get('projected_before_kickoff')})"
    elif p.get("zero_reason"):
        s = f"0 -- {p['zero_reason']}"
    elif p.get("p10") is not None:
        s = f"{p['mean']} pts (bad week {p['p10']}, good week {p['p90']})"
    else:
        s = f"{p['mean']} pts (no measured range)"
    if game and not p.get("final"):
        s += f"; {'vs' if game.get('home') else 'at'} {game.get('opp')} {game.get('kickoff_pt') or ''}".rstrip()
    return s


def _pct(v):
    return "--" if v is None else f"{100 * v:.0f}%"


def _player_lines(r: dict) -> list[str]:
    o, g, p, u = r["owner"], r["game"], r["projection"], r["usage"]
    own = {"you": "yours", "your opponent": f"your opponent's ({o.get('team_name')})",
           "another team": f"on {o.get('team_name')}'s roster", "free agent": "a free agent"}[o["who"]]
    if o["who"] in ("you", "your opponent"):
        own += ", starting" if o["starting"] else ", on the bench"
    L = [f"**{r['name']}** -- {r['pos']}, {r['team'] or 'no team'}; {own}."]
    if g:
        fav = "" if g.get("spread") is None else (f", favoured by {-g['spread']:g}" if g["spread"] < 0 else
                                                  f", {g['spread']:g}-point underdog" if g["spread"] > 0 else ", a pick'em")
        L.append(f"Game: {'vs' if g.get('home') else 'at'} {g.get('opp')}, {g.get('kickoff_pt') or 'kickoff unknown'}"
                 + ("" if g.get("implied") is None else f"; team implied {g['implied']:g} pts") + fav
                 + (f"; {g['status'].replace('STATUS_', '').lower()}" if g.get("status") not in (None, "STATUS_SCHEDULED") else "")
                 + ".")
    else:
        L.append("Game: none this week (bye, or no scheduled game).")
    st = r["status"] or "no designation"
    extra = [x for x in (r.get("injury"),) if x]
    fpt = LU._fp_text(r.get("fantasypros")) if r.get("fantasypros") else ""
    if r["status"]:
        L.append(f"Status: {st}" + (f" ({', '.join(extra)})" if extra else "")
                 + (f"; {fpt}" if fpt else (f"; practice (Sleeper): {r['practice_sleeper']}" if r.get("practice_sleeper") else ""))
                 + (f"; settles by {r['status_settles_pt']} (inactives)" if r.get("status_settles_pt") else "")
                 + (f"; your players at his position locking before then: {', '.join(r['my_players_locking_first'])}"
                    if r.get("my_players_locking_first") else "")
                 + ".")
    if p.get("mean") is None:
        L.append(f"Projection: {p.get('why')}.")
    elif p.get("final"):
        L.append(f"Scored {p['mean']} (final; projected {p.get('projected_before_kickoff')} before kickoff).")
    elif p.get("zero_reason"):
        L.append(f"Projection: 0 -- {p['zero_reason']}.")
    else:
        rng = (f" Range: bad week {p['p10']}, median {p['p50']}, good week {p['p90']} (10th/50th/90th percentile)."
               if p.get("p10") is not None else " No measured range for this position.")
        src = f"Sleeper {p.get('sleeper')}"
        if p.get("market") is not None:
            src += (f"; market {p['market']} from a partial prop board, not blended" if p.get("market_partial")
                    else f"; market {p['market']} at {100 * (p.get('market_weight') or 0):.0f}% weight")
        L.append(f"Projection: {p['mean']} pts.{rng} ({src}.)" + (f" Flagged {p['flag']}: projected as if he plays."
                                                                  if p.get("flag") else ""))
    if u is not None:
        if not u.get("weeks"):
            L.append(f"Usage: {u.get('note')}.")
        else:
            snaps = u.get("snap_pct_by_week") or []
            ch = "; ".join(f"{k.replace('_', ' ')} {_pct(v.get('earlier'))} -> {_pct(v.get('recent'))}"
                           for k, v in (u.get("role_changed") or {}).items())
            L.append(f"Usage ({u['weeks']} wk): snaps {', '.join(_pct(x) for x in snaps)} by week; target share "
                     f"{_pct(u.get('target_share'))}, carry share {_pct(u.get('carry_share'))}"
                     + ("" if u.get("wopr") is None else f", WOPR {u['wopr']:.2f}")
                     + f"; inside-10 {u.get('inside10_targets', 0)} tgt + {u.get('inside10_carries', 0)} car. "
                     f"Role: {u.get('role')}" + (f" ({ch})" if ch else "")
                     + (f"; partial game wk {', '.join(str(w) for w in u['partial_weeks'])} (an exit or benching, "
                        "not a role)" if u.get("partial_weeks") else "") + ".")
    for t in r["designated_teammates"]:
        fpt = LU._fp_text(t.get("fantasypros")) if t.get("fantasypros") else ""
        L.append(f"Teammate: {t['name']} ({t['pos']}) {t['status']}" + (f" ({t['part']})" if t.get("part") else "")
                 + (f" -- {fpt}" if fpt else "")
                 + (f". Price his absence: `{t['scenario']}`" if t.get("scenario") else "") + ".")
    return L


def _h2h_lines(snap: Snapshot, h: dict) -> list[str]:
    L = []
    if "p_first_outscores_second" in h:
        a, b = h["first"], h["second"]
        L.append(f"Head to head: {_label(snap, a)} outscores {_label(snap, b)} in "
                 f"{h['p_first_outscores_second']:.0%} of simulated weeks (projections differ by {h['mean_gap']:+.1f}).")
    else:
        L.append("Chance each is the top scorer: " + "; ".join(
            f"{_label(snap, s)} {p:.0%}" for s, p in sorted(h["p_top_scorer"].items(), key=lambda kv: -kv[1])) + ".")
    if h.get("same_game"):
        L.append("Two of them share a game; they are drawn independently, so that head-to-head is approximate.")
    return L
