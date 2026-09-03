"""Run the REAL engine for a Yahoo draft. The page only actuates.

Why this exists
---------------
The browser driver started as a JavaScript reimplementation of
draftkit/tracker.py, because Chrome's Private Network Access blocks the page
from calling a local Python server, so it looked like the decision loop had
to live in the page. Measured against the engine it was reimplementing, that
driver agreed on 25% of top picks and lost at 8 of 10 slots
(scripts/engine_bakeoff.py).

The premise was wrong. The page never needed to *think* -- only to *act*. Our
turn is preceded by roughly `teams` rival picks, which is minutes of wall
clock, so the ranked list can be computed ahead of time by the real engine
and handed to the page. The page walks the list and clicks.

So: this is the brain, `draft_driver.js` is the hands, and there is exactly
one ranking implementation in the repo again.

    python scripts/yahoo_bridge.py --league keefamania --state state.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import polars as pl  # noqa: E402

from draftkit import snake  # noqa: E402
from draftkit.config import Config  # noqa: E402
from draftkit.tracker import Tracker, TrackerState  # noqa: E402


def norm(n: str) -> str:
    s = unicodedata.normalize("NFKD", n or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return "".join(c for c in s.lower() if c.isalnum() or c == " ").strip()


def key(n: str) -> str:
    """first-initial + surname, matching how Yahoo renders a row."""
    parts = [p for p in norm(n).split() if p not in
             ("jr", "sr", "ii", "iii", "iv", "v")] or norm(n).split()
    if not parts:
        return ""
    return parts[0] if len(parts) == 1 else parts[0][0] + " " + parts[-1]


def pkey(name: str, pos: str | None) -> str:
    """Identity key for matching the page's text to the board.

    Team defenses have no first name: the board says "Houston Texans" and the
    roster panel says "DEF Texans", which key() turns into "h texans" and
    "d texans" -- so in mock 11 our drafted defense was never attributed and
    the engine kept a DEF slot open all draft. Defenses match on the nickname.
    """
    if str(pos or "").upper() in ("DEF", "DST"):
        parts = norm(name).split()
        return parts[-1] if parts else ""
    return key(name)


class PlayerIndex:
    """Resolve a name the page hands us to ONE board player.

    Yahoo renders "A. Brown" for Amon-Ra St. Brown and for A.J. Brown, and
    "B. Robinson" for Bijan and Brian Robinson Jr. -- same position, and for
    the Robinsons the same team. A dict keyed on first-initial + surname kept
    whichever came first by VORP, so in mock 13 (2026-09-02) A.J. Brown went
    at pick 17 and led the engine's plan for the next thirty picks: he could
    never be marked drafted.

    The store feed carries full names, so those match exactly. The panel's
    abbreviated text falls back to the initial key and, among namesakes,
    resolves to one not already accounted for (the caller passes what it has
    seen) -- a second "A. Brown" after Amon-Ra left is A.J., never a second
    Amon-Ra.
    """

    def __init__(self, players: list[dict]):
        self.full: dict[tuple[str, str], list[dict]] = {}
        self.short: dict[tuple[str, str], list[dict]] = {}
        for p in players:
            pos = str(p["pos"]).upper()
            self.full.setdefault((norm(p["name"]), pos), []).append(p)
            self.short.setdefault((pkey(p["name"], pos), pos), []).append(p)

    def resolve(self, name: str, pos: str | None, exclude: set[str] = frozenset()) -> dict | None:
        pos = str(pos or "").upper()
        cands = self.full.get((norm(name), pos)) or self.short.get((pkey(name, pos), pos)) or []
        fresh = [p for p in cands if p["sleeper_id"] not in exclude]
        # every namesake already accounted for: it is a repeat view of one of
        # them, and the highest-VORP one is the conventional reading
        return (fresh or cands or [None])[0]


FLEX_NAMES = {"W/R/T", "WRT", "W/R", "FLEX", "W/T", "R/W/T"}


def slots_from_yahoo_roster(roster: list[str]) -> dict[str, int]:
    """Starter slots from a Yahoo roster list. BN and IR are not starters."""
    out = {"QB": 0, "RB": 0, "WR": 0, "TE": 0, "FLEX": 0, "K": 0, "DEF": 0, "BN": 0}
    for raw in roster:
        s = str(raw).strip().upper()
        if s in ("BN", "BENCH"):
            out["BN"] += 1
        elif s in ("IR", "IR+", "NA"):
            continue
        elif s in FLEX_NAMES:
            out["FLEX"] += 1
        elif s in out:
            out[s] += 1
    return out


def load_players(cfg: Config) -> list[dict]:
    df = pl.read_csv(cfg.scoped(cfg.root / "tiers.csv"), infer_schema_length=2000)
    out = []
    for i, r in enumerate(df.iter_rows(named=True)):
        pos = (r.get("pos") or "").upper()
        if pos not in ("QB", "RB", "WR", "TE", "K", "DEF"):
            continue
        out.append({
            "sleeper_id": str(i + 1), "name": r["player"], "pos": pos,
            "team": (r.get("team") or "").upper(),
            "vorp": float(r.get("vorp") or 0.0),
            "vorp_flex": float(r.get("vorp_flex") or r.get("vorp") or 0.0),
            "proj_pts": float(r.get("proj_pts") or 0.0),
            "adp": float(r["adp"]) if r.get("adp") not in (None, "") else None,
            "adp_delta": float(r.get("adp_delta") or 0.0),
            "tier": int(r.get("tier") or 9),
            "pos_rank": int(r.get("pos_rank") or 99),
            "value_rank": int(r.get("value_rank") or 999),
            "cliff_flag": bool(r.get("cliff_flag")),
            "upside_flag": bool(r.get("upside_flag")),
            "upside_why": r.get("upside_why") or "",
            "proj_source": r.get("proj_source") or "blend",
            "backs_up": r.get("backs_up") or "",
            "backs_up_pos": r.get("backs_up_pos") or "",
            "starter_fragility_label": r.get("starter_fragility_label") or "",
            "starter_exp_games": r.get("starter_exp_games"),
            "starter_avail": r.get("starter_avail"),
            # plan A1/A3: dispersion across projection sources (None when absent)
            "proj_sd": float(r["proj_sd"]) if r.get("proj_sd") not in (None, "") else None,
            "proj_hi": float(r["proj_hi"]) if r.get("proj_hi") not in (None, "") else None,
            "proj_lo": float(r["proj_lo"]) if r.get("proj_lo") not in (None, "") else None,
            "n_sources": int(r.get("n_sources") or 0),
            # DECISIONS #35: Yahoo default rank (o_rank); the tracker reads it
            # as `yrank` for the list-walking autopick component. None when absent.
            "yahoo_rank": float(r["yahoo_rank"]) if r.get("yahoo_rank") not in (None, "") else None,
        })
    out.sort(key=lambda p: -p["vorp"])
    return out


def build_tracker(cfg: Config, players: list[dict], state: dict) -> Tracker:
    """A Tracker over Yahoo state. No Sleeper API is involved."""
    exp = cfg.get("expected") or {}
    teams = int(state.get("teams") or exp.get("teams") or 10)
    rounds = int(state.get("rounds") or exp.get("rounds") or 15)

    t = object.__new__(Tracker)
    t.teams, t.rounds = teams, rounds
    # Yahoo names its slots differently from Sleeper: the flex is "W/R/T" and
    # IR is a roster slot never filled during a draft.
    # roster_slots_from_draft_settings() reads Sleeper's slots_* keys, so
    # feeding it the Yahoo list silently produced an EMPTY slot map -- which
    # makes my_needs() all zeros and quietly disables every need-aware
    # guardrail. Build the map from the league yaml's own roster list.
    t.slots = slots_from_yahoo_roster(exp.get("roster") or [])
    t.my_slot = int(state["my_slot"])
    t.draft_id = "yahoo"
    t.poll_seconds, t.fall_alert = 5.0, 12

    # Engine knobs come from the SAME config the Sleeper tracker reads, so the
    # Yahoo draft is run by an identically-configured engine rather than by
    # defaults that merely look similar.
    t.apply_engine_cfg(cfg.get("engine") or {})   # the one knob list (Tracker.ENGINE_KNOBS)
    t.local = True

    g = cfg.get("guardrails") or {}
    t.qb2_round = int(g.get("qb2_earliest_round", 10))
    t.te2_fall = int(g.get("te2_fall_picks", 12))
    t._urgency_cache = None
    t.rival_seeds, t.slot_to_user = {}, {}
    t.players = players
    t.by_id = {p["sleeper_id"]: p for p in players}

    index = PlayerIndex(players)

    # SECOND source of "whose pick was it": the roster panel. The page sends
    # my_roster (name + pos read off "YOUR TEAM"), and a drafted entry whose
    # name+pos appears there is ours whether or not the Picks panel labelled
    # it "You". Mock 11 (2026-09-01) drafted a THIRD tight end at pick 28
    # after a plan that saw no roster at all -- the panel's label was not
    # readable at our turn, every pick came through unattributed, and with an
    # empty roster the TE market was open and urgent.
    #
    # Resolve the roster to player ids FIRST, so a drafted entry is ours when
    # it is the same player -- not when it merely renders the same way.
    mine_ids: set[str] = set()
    for r in state.get("my_roster") or []:
        p = index.resolve(r.get("name", ""), r.get("pos", ""), exclude=mine_ids)
        if p:
            mine_ids.add(p["sleeper_id"])

    picks = []
    seen: set[str] = set()
    unresolved: list[dict] = []          # drafted entries no board player matched (logged, not dropped silently)
    mine_snake_slots: set[int] = set()   # where OUR flagged picks actually fell
    flagged_ids: set[str] = set()        # the players those flags named
    for d in sorted(state.get("drafted", []), key=lambda x: int(x.get("pick_no") or 0)):
        p = index.resolve(d["name"], d.get("pos", ""), exclude=seen)
        if not p:
            unresolved.append({"pick_no": d.get("pick_no"), "name": d.get("name"), "pos": d.get("pos")})
            continue
        if d.get("mine") and d.get("pick_no"):
            mine_snake_slots.add(snake.pick_to_round_slot(int(d["pick_no"]), teams)[1])
            flagged_ids.add(p["sleeper_id"])
        seen.add(p["sleeper_id"])
        pick_no = int(d["pick_no"])
        if p["sleeper_id"] in mine_ids:
            d = dict(d, mine=True)
        # Whose pick was it?
        #
        # Yahoo's pick feed names the player and the pick number but not the
        # slot. Reading d["slot"] defaulted every pick to 0, so NONE were
        # attributed to us, my_pos_counts() came back empty, and the engine
        # recommended a second QB in round 4 against a round-10 gate.
        #
        # The panel does label our own picks "You", and that flag beats snake
        # arithmetic: a mock reshuffled us from slot 3 to slot 10 seconds
        # before it started, which would have mis-attributed every pick. Trust
        # the flag when present, fall back to the snake position otherwise.
        rnd, snake_slot = snake.pick_to_round_slot(pick_no, teams)
        if d.get("mine"):
            slot = t.my_slot
        else:
            slot = int(d.get("slot") or snake_slot)
            if slot == t.my_slot:
                slot = 0        # not ours: never let the snake claim it for us
        picks.append({
            "pick_no": pick_no, "player_id": p["sleeper_id"],
            "draft_slot": slot, "round": rnd,
        })
    # RECONCILE the three views the page sends (see draft_driver.refreshPlan).
    # 1. Roster panel players missing from the feed are still OUR picks. After
    #    a mid-draft reload the Picks panel shows only the last few picks, so
    #    without this the engine sees an empty roster, every slot open, and
    #    the TE market urgent again.
    have_ids = {x["player_id"] for x in picks}
    next_filler = (max((x["pick_no"] for x in picks), default=0) + 1)
    for pid in sorted(mine_ids - have_ids):
        picks.append({"pick_no": next_filler, "player_id": pid,
                      "draft_slot": t.my_slot,
                      "round": snake.pick_to_round_slot(next_filler, teams)[0]})
        have_ids.add(pid)
        next_filler += 1
    # 2. The header's pick number is authoritative for WHERE we are. Pad with
    #    anonymous rival picks so current_pick, the survival window and the
    #    round-gated guardrails line up, even when the feed is partial. The
    #    fillers remove nobody from the board, so the sim errs toward "still
    #    available" -- which the driver's own row lookup then corrects.
    warnings: list[str] = []
    # Seat check (review 2026-09-02): the URL/config slot is what the room
    # said before the bell; a reshuffle moves us. Our own flagged picks say
    # where we really sit. One consistent snake slot that disagrees wins.
    if len(mine_snake_slots) == 1 and next(iter(mine_snake_slots)) != t.my_slot:
        real = next(iter(mine_snake_slots))
        warnings.append(f"my_slot {t.my_slot} disagrees with my picks (snake slot {real}); using {real}")
        t.my_slot = real
        # one rule for every pick, re-applied: ours (flagged or on the roster
        # panel) sit on the real seat; anyone else sits on his snake slot,
        # except that the real seat's unflagged picks are "not ours" (0)
        mine_all = mine_ids | flagged_ids
        for x in picks:
            if x["player_id"] in mine_all:
                x["draft_slot"] = real
            else:
                s = snake.pick_to_round_slot(x["pick_no"], teams)[1]
                x["draft_slot"] = 0 if s == real else s
    elif len(mine_snake_slots) > 1:
        warnings.append(f"my flagged picks fall on several snake slots {sorted(mine_snake_slots)}; keeping my_slot {t.my_slot}")
    cur = state.get("current_pick")
    if cur:
        cur = int(cur)
        while len(picks) + 1 < cur:
            n = len(picks) + 1
            rnd, slot = snake.pick_to_round_slot(n, teams)
            picks.append({"pick_no": n, "player_id": f"unknown{n}",
                          "draft_slot": 0 if slot == t.my_slot else slot,
                          "round": rnd})
        # RECONCILE DOWN too (review 2026-09-02). The header is authoritative
        # for where we are; an entry numbered AT or past the pick on the clock
        # cannot have happened (a spurious panel line, a namesake resolved
        # twice). It used to stay, current_pick ran one ahead of the header
        # for the rest of the room, and the page's gate refused every click.
        # Our own flagged picks are never dropped.
        before = len(picks)
        picks = [x for x in picks if x["pick_no"] < cur or x["draft_slot"] == t.my_slot]
        if len(picks) != before:
            warnings.append(f"dropped {before - len(picks)} feed entries numbered >= header pick {cur}")
        if len(picks) + 1 > cur:
            warnings.append(f"feed over-count: {len(picks)} picks but header says pick {cur} is on the clock")
    picks.sort(key=lambda x: x["pick_no"])
    t.state = TrackerState(picks=picks,
                           drafted_ids={x["player_id"] for x in picks},
                           status="drafting")
    t.away_slots = away_slots_from_state(state, teams)
    # DATA MISSING, said aloud: we are past our first turn and the engine sees
    # no roster of ours -- every slot open, QB/TE gates off (mock 11)
    first_turn = snake.slot_pick_numbers(t.my_slot, teams, rounds)[0] if t.my_slot else None
    if first_turn and cur and cur > first_turn and not t.picks_for_slot(t.my_slot):
        warnings.append("MY ROSTER UNKNOWN: past my first turn with no pick attributed to me (no mine flags, no roster panel)")
    if unresolved:
        warnings.append(f"{len(unresolved)} drafted entries matched no board player: "
                        + ", ".join(f"{u['pick_no']} {u['name']}" for u in unresolved[:5]))
    t.unresolved = unresolved
    t.warnings = warnings
    return t


def away_slots_from_state(state: dict, teams: int) -> frozenset:
    """Plan B5: the draft slots whose manager Yahoo has flagged `away`
    (autopick). The page reports away TEAM ids; a team id maps to a slot
    through any drafted entry that carries both a pick number and a team id
    (store path). The DOM path has no team ids, so the mapping is empty and
    the sim models every rival as human -- DATA MISSING, never a guess that
    team id equals slot (mock 10 reshuffled us from slot 3 to 10 at the bell)."""
    away = {str(x) for x in (state.get("away_teams") or [])}
    if not away:
        return frozenset()
    team_to_slot: dict[str, int] = {}
    for d in state.get("drafted") or []:
        tid, no = d.get("team_id"), d.get("pick_no")
        if tid is None or not no:
            continue
        team_to_slot.setdefault(str(tid), snake.pick_to_round_slot(int(no), teams)[1])
    return frozenset(team_to_slot[t] for t in away if t in team_to_slot)


def merge_feed(memory: dict, drafted: list[dict]) -> list[dict]:
    """Union the page's current view of the Picks panel into what the bridge
    has already seen, keyed by pick number.

    The panel virtualises and, after a page reload, shows only the last few
    picks. In mock 11 a reload at pick 133 left the engine believing
    McCaffrey was still available. The bridge is long-lived and has seen
    every pick go by, so it keeps the union; a later view never REMOVES a
    pick, it can only add or relabel one (a "You" flag learned later wins).
    """
    for d in drafted or []:
        try:
            n = int(d.get("pick_no"))
        except (TypeError, ValueError):
            continue
        prev = memory.get(n)
        if prev is None:
            memory[n] = dict(d)
            continue
        # the store's view (carries team_id) beats a panel-parsed one at the
        # same number (review 2026-09-02: first-view-wins let a DOM misread
        # shadow the real pick for the rest of the room); a `mine` flag
        # learned later is kept either way
        replace = (d.get("team_id") is not None and prev.get("team_id") is None) \
            or (d.get("mine") and not prev.get("mine"))
        if replace:
            merged = dict(d)
            if prev.get("mine") and not merged.get("mine"):
                merged["mine"] = True
            memory[n] = merged
    return [memory[k] for k in sorted(memory)]


def depth_tail(t: Tracker, plan: list[dict], depth: int) -> list[dict]:
    """Pad a plan past the engine's named candidates -- under the SAME
    guardrails the engine applies.

    The tail exists so the page still has somewhere to go when everything the
    engine named is gone by our turn. It used to be raw VORP order with only
    drafted/no_market removed, which is how mock 11 (2026-09-01) took FOUR
    tight ends: once the page had wrongly marked the real recommendations as
    gone, the next entries were TE3, TE4 and a defense in round 3, and nothing
    in the tail said no. _pos_allowed is the single source of those rules;
    the tail goes through it like every other candidate.
    """
    if len(plan) >= depth:
        return plan
    named = {(x["n"], x["p"]) for x in plan}
    rnd, _ = snake.pick_to_round_slot(
        min(t.current_pick, t.teams * t.rounds), t.teams)
    counts = t._my_pos_counts()
    needs = t.my_needs()
    picks_left = t.rounds - len(t.picks_for_slot(t.my_slot))
    top6_te_fell = any(
        q["pos_rank"] <= 6 and q.get("adp") is not None
        and t.current_pick - q["adp"] >= t.te2_fall
        for q in t.remaining("TE"))
    out = list(plan)
    for p in t.players:
        if len(out) >= depth:
            break
        if p["sleeper_id"] in t.state.drafted_ids:
            continue
        if (p["name"], p["pos"]) in named or p.get("proj_source") == "no_market":
            continue
        # Position caps AND must-fill, but NOT Python's one-stash rule: with 3
        # picks left, K/DEF open and every remaining RB/WR below replacement,
        # the full _guardrail_ok refused everyone and the tail came back EMPTY
        # (stress mock 2026-09-02, pick 126: two engine rows, nothing behind
        # them, the page's local ranker took over). The must-fill rule is
        # what stopped the QB2-before-the-kicker case; the stash rule is the
        # engine's ranking opinion, and the tail exists for when the engine's
        # named rows are gone.
        if not t._pos_allowed(p["pos"], rnd, counts, picks_left, top6_te_fell):
            continue
        open_starters = sum(v for k, v in needs.items() if k not in ("BN", "BENCH", "IR"))
        if picks_left <= open_starters and not snake.needs_position(needs, p["pos"]):
            continue
        out.append({"n": p["name"], "p": p["pos"], "t": p["team"],
                    "v": round(float(p["vorp"] or 0.0), 1), "a": p["adp"],
                    "why": "depth fallback (engine list exhausted)",
                    "s": None, "sr": None, "e": None, "b": None})
    return out


def plan_rows(t: Tracker, recs, report=None) -> list[dict]:
    """The plan rows the page consumes -- ONE spelling for the CLI and the
    bridge server. Besides name/pos/team/vorp/adp/why, each row carries the
    engine's numbers for the candidate's market so the trail keeps them
    structured (plan 2026-09-02 B1): s = shown (calibrated) survival to my
    next pick, sr = raw survival, e = expected best at my next turn, b = best
    now."""
    from draftkit.planner import market_for
    needs = t.my_needs()
    rows = []
    for _score, why, p in recs:
        s = sr = e = b = None
        if report:
            mkt = market_for(p["pos"], needs)
            u = report.get(mkt) or report.get(p["pos"])
            if u:
                sid = str(p.get("sleeper_id"))
                s = (u.get("survival") or {}).get(sid)
                sr = (u.get("survival_raw") or {}).get(sid)
                e, b = u.get("e_best_next"), u.get("best_now")
        rows.append({"n": p["name"], "p": p["pos"], "t": p["team"],
                     "v": round(float(p["vorp"] or 0.0), 1), "a": p["adp"], "why": why,
                     "s": None if s is None else round(float(s), 3),
                     "sr": None if sr is None else round(float(sr), 3),
                     "e": None if e is None else round(float(e), 1),
                     "b": None if b is None else round(float(b), 1)})
    return rows


def room_of(draft_key) -> str:
    """The Yahoo room id inside the page's draft key (its pathname)."""
    m = re.search(r"(\d{5,})", str(draft_key or ""))
    return m.group(1) if m else "room"


def log_plan(t: Tracker, recs, report, draft_key, log_dir) -> Path:
    """One recs event per state into data/logs/yahoo_<room>.jsonl, the same
    shape as the Sleeper draft log, so scripts/fit_survival.py reads both."""
    from draftkit.draftlog import DraftLog
    path = Path(log_dir) / f"yahoo_{room_of(draft_key)}.jsonl"
    # the key names the STATE, not just the count: a `mine` label learned at
    # the same pick count changes needs and recs and must produce an event
    # (the old (current_pick, len(picks)) pair was a tautology)
    needs_key = "needs:" + ",".join(f"{k}{v}" for k, v in sorted(t.my_needs().items()))   # flat: the key round-trips through JSON
    DraftLog(path).snapshot(t, recs, report, key=(t.current_pick, len(t.picks_for_slot(t.my_slot)), needs_key))
    return path


def plan_detail(t: Tracker, recs, report, plan, state: dict, top_survival: int = 12,
                call: int | None = None, page_drafted: int | None = None) -> dict:
    """The scrutiny record for one plan (stress mocks, 2026-09-02): what the
    page handed the bridge, what the engine saw, and every market's numbers
    -- not just the candidates' rows. Pure; log_plan_detail appends it.
    `call` is the bridge's call counter (the page keeps it as plan_call, the
    bridge prints it), `page_drafted` the page's OWN drafted count before the
    bridge merged its memory in."""
    import datetime as dt
    import time
    drafted = state.get("drafted") or []
    markets = {}
    for mkt, u in (report or {}).items():
        if not isinstance(u, dict):
            continue
        surv = u.get("survival") or {}
        raw = u.get("survival_raw") or {}
        top = sorted(surv.items(), key=lambda kv: -float(kv[1] or 0.0))[:top_survival]
        names = {}
        for sid, _p in top:
            p = t.by_id.get(str(sid)) or {}
            names[str(sid)] = p.get("name") or p.get("player")
        markets[mkt] = {
            "best_now": u.get("best_now"), "e_best_next": u.get("e_best_next"),
            "e_best_next_carry": u.get("e_best_next_carry"), "urgency": u.get("urgency"),
            "pool": len(surv),
            "top_survival": [{"sleeper_id": str(sid), "name": names.get(str(sid)),
                              "s": round(float(surv[sid]), 3), "sr": round(float(raw.get(sid, surv[sid])), 3)}
                             for sid, _p in top],
        }
    return {
        "type": "plan_detail", "ts": dt.datetime.now().isoformat(timespec="seconds"),
        "ts_epoch": round(time.time(), 3), "call": call,
        "warnings": list(getattr(t, "warnings", []) or []),
        "unresolved": list(getattr(t, "unresolved", []) or []),
        "current_pick": t.current_pick, "my_slot": t.my_slot, "teams": t.teams, "rounds": t.rounds,
        "state_in": {"drafted": len(drafted), "page_drafted": page_drafted,
                     "mine": sum(1 for d in drafted if d.get("mine")),
                     "my_roster": [f"{x.get('name')} ({x.get('pos')})" for x in (state.get("my_roster") or [])],
                     "on_clock": state.get("on_clock"), "armed": state.get("armed"),
                     "roster_count": state.get("roster_count"), "current_pick": state.get("current_pick"),
                     "away_teams": state.get("away_teams"), "source": state.get("source")},
        "away_slots": sorted(int(s) for s in (getattr(t, "away_slots", None) or ())),
        "needs": t.my_needs(),
        "recs": [{"name": p.get("name"), "pos": p["pos"], "score": round(float(s), 2), "why": why}
                 for s, why, p in recs],
        "plan": plan,
        "markets": markets,
    }


def log_plan_detail(t: Tracker, recs, report, plan, state: dict, draft_key, log_dir,
                    call: int | None = None, page_drafted: int | None = None) -> Path:
    """Append plan_detail to data/logs/yahoo_<room>.plans.jsonl (one line per
    bridge call, no dedupe: a re-request at the same state IS an event)."""
    path = Path(log_dir) / f"yahoo_{room_of(draft_key)}.plans.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(plan_detail(t, recs, report, plan, state, call=call, page_drafted=page_drafted)) + "\n")
    return path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", default=None)
    ap.add_argument("--state", required=True, help="JSON from the page")
    ap.add_argument("--out", default="data/draftrig/plan.json")
    ap.add_argument("--depth", type=int, default=25)
    a = ap.parse_args()

    cfg = Config.load(league=a.league)
    state = json.loads(Path(a.state).read_text(encoding="utf-8"))
    players = load_players(cfg)
    t = build_tracker(cfg, players, state)

    recs = t.recommendations(top_n=a.depth)
    plan = plan_rows(t, recs, t.urgency_report())

    # Depth beyond the engine's per-position candidates: if everything it
    # named is gone by the time we pick, the page still needs somewhere to go.
    plan = depth_tail(t, plan, a.depth)

    out = {
        "current_pick": t.current_pick,
        "my_slot": t.my_slot,
        "round": snake.pick_to_round_slot(
            min(t.current_pick, t.teams * t.rounds), t.teams)[0],
        "needs": t.my_needs(),
        "plan": plan,
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print(f"pick {out['current_pick']} · round {out['round']} · "
          f"needs {out['needs']}")
    for i, x in enumerate(plan[:8], 1):
        print(f"  {i:2}. {x['n']:24} {x['p']:3} v{x['v']:6.1f}  {x['why'][:70]}")
    print(f"-> {a.out} ({len(plan)} deep)")


if __name__ == "__main__":
    main()
