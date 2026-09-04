"""Phase 4 — live draft tracker.

Single-process terminal app. Polls the Sleeper picks endpoint (default every
5s), diffs against last state, and renders a tier board + recommendations from
precomputed tiers.csv — no model or network work in the hot path, so the
on-clock render is instant. Resumable by construction: state is rebuilt from
the full picks list on every poll, so restarting mid-draft loses nothing.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import polars as pl
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import snake
from .shape import starting_slots
from .sleeper import SleeperClient, get_json, BASE

POS_ORDER = ["RB", "WR", "TE", "QB", "K", "DEF"]


@dataclass
class TrackerState:
    picks: list[dict] = field(default_factory=list)
    drafted_ids: set[str] = field(default_factory=set)
    last_poll_ok: float = 0.0
    last_error: str | None = None
    status: str = "unknown"


class Tracker:
    # v2 engine knobs as CLASS defaults: test fixtures (and the retro-recs
    # rewinder) construct Trackers via object.__new__, bypassing __init__
    sims = 1000
    sigma_early = 6.0
    sigma_late = 27.0
    reach_prob = 0.15
    reach_scale = 3.0
    run_window = 5
    run_min = 2
    run_boost = 1.5
    run_ratio = 0.0             # plan B4: run = count > run_ratio x expected; 0 = the absolute count rule (kept: DECISIONS #29)
    survival_shrink = 1.0       # retired 2026-09-02 (DECISIONS #26): the raw sim is calibrated; 0.55 was fitted to mis-scored data
    # rival need weighting (plan B3, hoisted from urgency.py constants at the
    # values that were in force; fitted in B7)
    need_damp = 0.15
    qb_filled_damp = 0.05
    qb_damp_until_round = 10
    kdef_early_damp = 0.02
    kdef_typical_round = 13
    autopick_sigma_scale = 0.5  # plan B5: an autopicking rival's ADP noise, x sigma
    autopick_need_damp = 0.02   # plan B5: autopick fills every starter slot first; a non-filling position while one is open
    autopick_list_prob = 0.0    # DECISIONS #35: P(an autopick seat walks Yahoo's default list this pick); 0 = today's behaviour
    rival_needs_update = True   # plan B6: a rival picking twice in my window consumes his needs
    away_slots = frozenset()    # plan B5: draft slots on autopick (Yahoo 'away'); empty on Sleeper
    upside_from_round = 8
    upside_mult = 1.15
    # plan A3 (DECISIONS #32): from upside_from_round, rank a candidate on
    # mean + dispersion_lambda x the spread of his projection across sources
    # (proj_sd) instead of the boolean upside multiplier -- only when the flag
    # is on AND the board carries a spread from >= 2 sources. Nothing here
    # enters VORP, tiers or the planner. OFF until its gate passes.
    late_round_dispersion = False
    dispersion_lambda = 0.5
    # Rank by unfilled roster SLOT rather than by position (_open_markets).
    # Kept as a knob so the ten-slot replay can A/B it; the A/B is the reason
    # it is on. Turning it off restores per-position urgency exactly.
    slot_markets = True
    # Cross-position comparison in the two-pick planner measures against the
    # player you would actually end up with, not against a yaml replacement
    # baseline (_fallback_points). Knob so the A/B stays runnable.
    adaptive_fallback = True
    # Bench rounds price candidates as INSURANCE -- weeks needed x edge over
    # the waiver wire, depth-aware (draftkit/bench.py) -- instead of VORP
    # against the starter baseline. ON since 2026-09-01: the season-level
    # replay (scripts/season_replay.py, no shared constants) has it beating
    # VORP bench selection on both leagues -- Keefamania +12.9 pts/season
    # (8 better, 0 worse, 2 tied), Omnibeta +23.9 (10 / 1 / 1). Knob kept so
    # the A/B stays runnable.
    bench_insurance = True
    pool_min = 40
    pool_lookback = 20
    pool_lookahead = 60
    local = False

    def __init__(
        self,
        cfg,
        tiers_path: Path,
        draft_id: str | None = None,
        my_slot: int | None = None,
    ):
        self.cfg = cfg
        self.client = SleeperClient(cfg.path("raw"))
        self.draft_id = str(draft_id or cfg.draft_id)
        # LOCAL mode (Yahoo leagues / no pollable API): draft facts come from
        # the league yaml's expected: block, picks from a local file fed by
        # the dashboard's manual entry or the browser poller.
        self.local = (self.draft_id.lower() in ("", "none", "null")
                      or self.draft_id.startswith("local"))
        if self.local:
            self.draft_id = f"local_{cfg.league_name or 'draft'}"
            exp = cfg.get("expected") or {}
            # one definition of "roster-position list -> starting slots", shared
            # with the in-season manager. The inline parse that used to live here
            # had its own flex vocabulary and silently kept anything it did not
            # recognise as a position of its own.
            sh = starting_slots(exp.get("roster") or [],
                                f"leagues/{cfg.league_name}.yaml expected.roster")
            counts = dict(sh.slots)
            counts["FLEX"] = len(sh.flex_slots)
            counts["BN"] = sh.bench
            self.draft = {
                "type": exp.get("type", "snake"), "status": "drafting",
                "draft_order": {},
                "settings": {
                    "teams": int(exp.get("teams", 10)),
                    "rounds": int(exp.get("rounds", 15)),
                    "pick_timer": int(exp.get("pick_timer", 60)),
                    "slots_qb": counts.get("QB", 0), "slots_rb": counts.get("RB", 0),
                    "slots_wr": counts.get("WR", 0), "slots_te": counts.get("TE", 0),
                    "slots_flex": counts.get("FLEX", 0), "slots_k": counts.get("K", 0),
                    "slots_def": counts.get("DEF", 0), "slots_bn": counts.get("BN", 0),
                },
            }
        else:
            self.draft = self.client.draft(self.draft_id)
        self.teams = int(self.draft["settings"]["teams"])
        self.rounds = int(self.draft["settings"]["rounds"])
        self.slots = snake.roster_slots_from_draft_settings(self.draft["settings"])
        self.my_slot = my_slot
        tcfg = cfg["tracker"]
        self.poll_seconds = float(tcfg["poll_seconds"])
        self.fall_alert = int(tcfg["fall_alert_picks"])
        self.apply_engine_cfg(cfg["engine"] if "engine" in cfg._data else {})
        self.waiver_k = None
        try:
            from .baselines import waiver_k
            self.waiver_k = waiver_k((cfg.get("expected") or {}).get("waivers"))
        except Exception:  # noqa: BLE001 — default k inside bench_rows
            pass
        gcfg = cfg["guardrails"] if "guardrails" in cfg._data else {}
        self.qb2_round = int(gcfg.get("qb2_earliest_round", 10))
        self.te2_fall = int(gcfg.get("te2_fall_picks", 12))
        self._urgency_cache: tuple[tuple, dict] | None = None
        from .rivals import load_seeds
        self.rival_seeds = load_seeds(cfg).get("users", {})
        order = self.draft.get("draft_order") or {}
        self.slot_to_user = {int(v): str(k) for k, v in order.items()}
        from .draftlog import DraftLog
        self.log = DraftLog(cfg.path("logs") / f"draft_{self.draft_id}.jsonl")

        tiers = pl.read_csv(tiers_path, infer_schema_length=2000)
        self.players = [r for r in tiers.iter_rows(named=True)]
        for p in self.players:
            p["sleeper_id"] = str(p["sleeper_id"])
        self.by_id = {p["sleeper_id"]: p for p in self.players}
        if self.local:
            from .picksource import LocalDraft
            self.source = LocalDraft(cfg.path("logs") / f"{self.draft_id}_picks.json",
                                     self.players, self.teams, self.rounds)
        self.state = TrackerState()

    # ---------- state ----------

    def poll(self) -> bool:
        """Fetch picks; returns True if the pick list changed. Retries with backoff."""
        if getattr(self, "local", False):
            picks = self.source.picks()
            # identity, not count: undo+re-add keeps the length but changes
            # the board (code review 2026-08-31)
            changed = ([p["player_id"] for p in picks]
                       != [p["player_id"] for p in self.state.picks])
            self.state.status = self.source.status()
            self.state.last_error = None
            self.state.last_poll_ok = time.time()
            self.state.picks = picks
            self.state.drafted_ids = {str(p["player_id"]) for p in picks}
            self.log.sync(self)
            return changed
        try:
            picks = get_json(f"{BASE}/draft/{self.draft_id}/picks", retries=3)
        except Exception as e:  # noqa: BLE001
            self.state.last_error = str(e)[:120]
            return False
        changed = len(picks) != len(self.state.picks)
        # Status only changes around pick activity; skipping the second round
        # trip mid-draft keeps a slow meta call from stalling the /state thread.
        if changed or self.state.status != "drafting":
            try:
                draft = get_json(f"{BASE}/draft/{self.draft_id}", retries=1)
                self.state.status = draft.get("status", "unknown")
            except Exception:  # noqa: BLE001 — picks succeeded; stale status is fine
                pass
        self.state.last_error = None
        self.state.last_poll_ok = time.time()
        self.state.picks = picks
        self.state.drafted_ids = {str(p["player_id"]) for p in picks}
        self.log.sync(self)
        return changed

    @property
    def current_pick(self) -> int:
        return len(self.state.picks) + 1

    def picks_for_slot(self, slot: int) -> list[dict]:
        return [p for p in self.state.picks if int(p.get("draft_slot") or 0) == slot]

    def _pick_pos(self, p: dict) -> str:
        """A pick's position: Sleeper's metadata when present, else the board
        (the Yahoo bridge and the replay harness send picks with no
        metadata -- the run detector read "" for every one of them until
        plan B4, so it never fired on real history there)."""
        pos = (p.get("metadata") or {}).get("position")
        if not pos:
            info = self.by_id.get(str(p.get("player_id")))
            pos = info["pos"] if info else "?"
        return {"DST": "DEF"}.get(pos, pos)

    def slot_positions(self, slot: int) -> list[str]:
        return [self._pick_pos(p) for p in self.picks_for_slot(slot)]

    def _recent_positions(self) -> list[str]:
        """Positions of the last run_window real picks, for the run detector
        (unknown players -> '' and are ignored there)."""
        out = []
        for p in self.state.picks[-self.run_window:]:
            pos = self._pick_pos(p)
            out.append(pos if pos != "?" else "")
        return out

    def remaining(self, pos: str | None = None) -> list[dict]:
        pool = [p for p in self.players if p["sleeper_id"] not in self.state.drafted_ids]
        if pos:
            pool = [p for p in pool if p["pos"] == pos]
        return sorted(pool, key=lambda p: -(p["vorp"] if p["vorp"] is not None else -999))

    # ---------- analysis ----------

    def my_needs(self) -> dict[str, int]:
        assert self.my_slot
        return snake.starter_needs(self.slot_positions(self.my_slot), self.slots)

    def intervening_slots(self) -> list[int]:
        """Rival slots picking between now and my NEXT turn. When I am on the
        clock the window starts at the pick after mine (the same off-by-one
        urgency_report fixes); before this the cliff report said "0 teams
        picking before you" exactly at decision time."""
        if not self.my_slot:
            return []
        cur = self.current_pick
        total = self.teams * self.rounds
        on_clock = cur <= total and snake.pick_to_round_slot(cur, self.teams)[1] == self.my_slot
        start = cur + 1 if on_clock else cur
        if start > total:
            return []
        nxt = snake.next_pick_for_slot(start, self.my_slot, self.teams, self.rounds)
        if nxt is None:
            return []
        return [
            s
            for s in snake.slots_picking_between(start, nxt, self.teams)
            if s != self.my_slot
        ]

    def cliff_report(self) -> dict[str, dict]:
        """Per position: picks of runway before the next cliff, vs. intervening demand."""
        inter = self.intervening_slots()
        demand: dict[str, int] = {}
        for s in inter:
            needs = snake.starter_needs(self.slot_positions(s), self.slots)
            for pos in POS_ORDER:
                if snake.needs_position(needs, pos):
                    demand[pos] = demand.get(pos, 0) + 1
        report = {}
        for pos in POS_ORDER:
            # no_market rows are engine-invisible; don't let them pad the
            # runway count or carry cliff flags into the urgency math
            rem = [p for p in self.remaining(pos) if p.get("proj_source") != "no_market"]
            before_cliff = None
            for i, p in enumerate(rem):
                if p["cliff_flag"]:
                    before_cliff = i + 1  # players available at/above the cliff edge
                    break
            report[pos] = {
                "before_cliff": before_cliff,
                "intervening_demand": demand.get(pos, 0),
                "urgent": before_cliff is not None
                and demand.get(pos, 0) >= before_cliff,
            }
        return report

    def fallers(self, limit: int = 5) -> list[dict]:
        out = []
        for p in self.remaining():
            adp = p.get("adp")
            if adp is not None and self.current_pick - adp >= self.fall_alert:
                out.append(p)
        return sorted(out, key=lambda p: -(self.current_pick - p["adp"]))[:limit]

    # ---------- decision engine (final spec §5-§6) ----------

    # every engine knob the config may set: (name, cast). The default is the
    # CLASS attribute, so a knob is added in exactly two places -- here and
    # the class default -- and every constructor (Sleeper __init__, the Yahoo
    # bridge, the replay harness) reads the same list (plan B3).
    ENGINE_KNOBS = (
        ("sims", int), ("pool_lookback", int), ("pool_lookahead", int),
        ("sigma_early", float), ("sigma_late", float),
        ("reach_prob", float), ("reach_scale", float),
        ("run_window", int), ("run_min", int), ("run_boost", float), ("run_ratio", float),
        ("survival_shrink", float),
        ("need_damp", float), ("qb_filled_damp", float), ("qb_damp_until_round", int),
        ("kdef_early_damp", float), ("kdef_typical_round", int),
        ("autopick_sigma_scale", float), ("autopick_need_damp", float), ("autopick_list_prob", float),
        ("rival_needs_update", bool),
        ("upside_from_round", int), ("upside_mult", float),
        ("late_round_dispersion", bool), ("dispersion_lambda", float),
        ("slot_markets", bool), ("adaptive_fallback", bool), ("bench_insurance", bool),
    )

    def _dispersion_for(self, q: dict) -> float | None:
        """The candidate's projection spread when the late-round dispersion
        objective applies to him: flag on, a spread present, from >= 2 sources.
        None otherwise (the boolean upside multiplier then applies)."""
        if not getattr(self, "late_round_dispersion", False):
            return None
        sd, n = q.get("proj_sd"), q.get("n_sources") or 0
        if sd is None or sd != sd or n < 2:
            return None
        return float(sd)

    def apply_engine_cfg(self, ecfg: dict | None) -> None:
        """Read the `engine:` block onto this tracker; absent keys keep the
        class defaults. pool_size is the legacy alias of pool_min."""
        ecfg = ecfg or {}
        for name, cast in self.ENGINE_KNOBS:
            setattr(self, name, cast(ecfg.get(name, getattr(Tracker, name))))
        # rolling ADP window for the rival sampling pool (post-v2 item 1);
        # pool_size is retained as the FLOOR so old configs stay meaningful
        self.pool_min = int(ecfg.get("pool_min", ecfg.get("pool_size", Tracker.pool_min)))

    def _rival_states(self, start: int, my_next: int) -> list[dict]:
        """Intervening pickers in order, with their open starter slots."""
        out = []
        for pick_no in range(start, my_next):
            _, slot = snake.pick_to_round_slot(pick_no, self.teams)
            if slot == self.my_slot:
                continue
            needs = snake.starter_needs(self.slot_positions(slot), self.slots)
            out.append({
                "slot": slot, "needs": needs,
                "user_id": self.slot_to_user.get(slot),
                # plan B5: a Yahoo manager flagged away is drafted by Yahoo's
                # autopick -- rank-following, starters first, no reaches
                "autopick": slot in (getattr(self, "away_slots", None) or ()),
            })
        return out

    def _sigma(self, rnd: int) -> float:
        e, late = self.sigma_early, self.sigma_late
        return e + (late - e) * (rnd - 1) / max(1, self.rounds - 1)

    def _open_markets(self, needs: dict) -> list[tuple[str, tuple[str, ...], str]]:
        """The markets I am still shopping in — one per UNFILLED roster slot.

        Position was only ever a proxy for "market I still need to buy from".
        Urgency asks what waiting costs, and that is a real question only in a
        market I have not yet left. So the pools are slots, not positions:

          * TE slot open  -> a TE market, priced on positional `vorp`. The
            TE2->TE3 cliff legitimately drives taking the elite tight end here.
          * TE slot FILLED -> there is no TE market any more. Remaining tight
            ends appear only inside the FLEX market, where they are priced on
            `vorp_flex` and have to beat the RB/WR competing for the same slot.

        That is what finally kills the double-elite-TE build, and for the right
        reason: the cliff is a fact about the TE market, and once your TE slot
        is full you have left it. Slot-conditional VORP alone could not do it --
        urgency is a DIFFERENCE, so shifting every tight end by the same 37.1
        points left every TE-to-TE gap intact (see DECISIONS.md 2026-09-01).

        Returns (market_name, member_positions, value_column). When every
        starter slot is filled we are shopping the bench, which stays
        per-position on `vorp` exactly as before.
        """
        out: list[tuple[str, tuple[str, ...], str]] = [
            (pos, (pos,), "vorp") for pos in POS_ORDER if needs.get(pos, 0) > 0
        ]
        if not getattr(self, "slot_markets", True):
            # the A/B control arm is PER-POSITION urgency: a FLEX-eligible
            # position with only the flex open still gets its own positional
            # row (review 2026-09-02: the off arm used to build the FLEX row
            # anyway and price it on a raw level, so it was not a control)
            if needs.get("FLEX", 0) > 0:
                have = {m for m, _members, _v in out}
                out += [(pos, (pos,), "vorp") for pos in POS_ORDER
                        if pos in snake.FLEX_ELIGIBLE and pos not in have]
            return out or [(pos, (pos,), "vorp") for pos in POS_ORDER]
        if needs.get("FLEX", 0) > 0:
            # Membership is ALL flex-eligible positions, not just the ones whose
            # dedicated slot is full: any of them can fill the flex, and pooling
            # them is the whole point -- a market containing only tight ends
            # would cancel the baseline shift all over again.
            out.append(("FLEX", snake.FLEX_ELIGIBLE, "vorp_flex"))
        if not out:
            out = [(pos, (pos,), "vorp") for pos in POS_ORDER]
        return out

    def _fallback_points(self, needs: dict) -> dict[str, float]:
        """Projected points of the player I would ACTUALLY END UP WITH at each
        position if I skip it now.

        This replaces the league yaml's replacement baseline as the reference
        for cross-position comparison in the two-pick planner, and it is the
        reason that baseline no longer has to be hand-fitted. A season-long
        constant has to answer "what is the alternative to a quarterback?" with
        one number for the whole draft. The real answer moves: in round 2 with
        thirteen picks left the alternative is a startable QB, so an early one
        is barely worth anything; in round 12 it is whoever is left.

        Method: find the LAST pick at which I could still fill my open starter
        slots -- if I have R picks remaining and S starters to fill, that is my
        S-th remaining pick. Then, per position, the best projected player
        whose ADP says he is likely to survive that long. No league constant
        enters; it adapts to teams, roster size, my remaining picks and the
        board.
        """
        remaining = [n for n in snake.slot_pick_numbers(
            self.my_slot, self.teams, self.rounds) if n >= self.current_pick]
        if not remaining:
            return {}
        open_starters = sum(needs.get(k, 0) for k in
                            ("QB", "RB", "WR", "TE", "FLEX", "K", "DEF"))
        # my last starter-filling pick; with no starters left to fill, the
        # question is what the bench could still get me, so use my final pick
        idx = min(max(open_starters, 1), len(remaining)) - 1
        deadline = remaining[idx]

        out: dict[str, float] = {}
        for pos in POS_ORDER:
            pool = [p for p in self.remaining(pos)
                    if p.get("proj_source") != "no_market"]
            if not pool:
                continue
            survivors = [p for p in pool
                         if p.get("adp") is not None and p["adp"] >= deadline]
            # nobody projected to last: the position will be picked clean, so
            # the fallback is the worst thing still on the board
            pick_from = survivors or pool
            # The fallback is priced at the LOWER of our blend and the market's
            # own projection. Taking the max of our projections over the ADP
            # survivors selects for the model's largest tail over-projections
            # (RJ Harvey: blend 155, market 136, consensus 118 -- user find,
            # 2026-09-03), which shrank every RB candidate's own value and
            # tilted pair coin-flips to WR. The market's number is the one
            # consistent with the ADP that made him a survivor.
            def _fb(p: dict) -> float:
                b = float(p.get("proj_pts") or 0.0)
                m = p.get("proj_market_pts")
                try:
                    m = float(m) if m not in (None, "") else None
                except (TypeError, ValueError):
                    m = None
                return min(b, m) if m is not None and m > 0 else b
            out[pos] = max(_fb(p) for p in pick_from) \
                if survivors else min(_fb(p) for p in pick_from)
        return out

    def _replacement_points(self) -> dict[str, float]:
        """Per-market replacement level in POINTS, recovered from the board.

        vorp = proj_pts - replacement, so replacement is proj_pts - vorp for
        any player at the position. Needed to convert the urgency report (which
        speaks VORP) back into points before comparing against a fallback.
        """
        out: dict[str, float] = {}
        for p in self.players:
            pos, pts, v = p.get("pos"), p.get("proj_pts"), p.get("vorp")
            if pos and pos not in out and pts is not None and v is not None:
                out[pos] = float(pts) - float(v)
            vf = p.get("vorp_flex")
            if (pos in snake.FLEX_ELIGIBLE and "FLEX" not in out
                    and pts is not None and vf is not None):
                out["FLEX"] = float(pts) - float(vf)
        return out

    def _my_starter_names(self) -> set[str]:
        """Names of my rostered players who would actually start (dedicated
        slot first, then FLEX) -- the ones a handcuff on my bench insures."""
        remaining = dict(self.slots)
        out: set[str] = set()
        for x in self.picks_for_slot(self.my_slot):
            q = self.by_id.get(str(x.get("player_id")))
            if not q:
                continue
            pos = q.get("pos")
            if remaining.get(pos, 0) > 0:
                remaining[pos] -= 1
            elif pos in snake.FLEX_ELIGIBLE and remaining.get("FLEX", 0) > 0:
                remaining["FLEX"] -= 1
            else:
                continue
            out.add(str(q.get("player") or q.get("name") or ""))
        return out

    def _bench_candidates(self, cands: list, needs: dict, counts: dict,
                          rnd: int, picks_left: int, top6_te_fell: bool) -> bool:
        """Append one insurance-priced row per bench position. Returns True
        when bench rows were produced (the caller then skips the planner).

        Only active once every non-K/DEF starter is filled, and never inside
        the must-fill window where remaining picks are owed to open starters.
        """
        from .bench import (BENCH_POSITIONS, insurance_value, starter_exposure,
                            waiver_ppw)
        open_skill = sum(needs.get(k, 0) for k in ("QB", "RB", "WR", "TE", "FLEX"))
        open_all = open_skill + needs.get("K", 0) + needs.get("DEF", 0)
        if open_skill > 0 or picks_left <= open_all:
            return False
        my_positions = self.slot_positions(self.my_slot)
        exposure = starter_exposure(my_positions, self.slots)
        # backups I already hold at each position: the next one covers the
        # NEXT simultaneous absence, not the first (bench.weeks_needed)
        depth_ahead = {pos: max(0, my_positions.count(pos) - exposure.get(pos, 0))
                       for pos in set(my_positions)}
        my_starters = self._my_starter_names()
        starter_ppw = {
            str(q.get("player") or q.get("name") or ""): float(q.get("proj_pts") or 0.0) / 17.0
            for q in self.players
            if str(q.get("player") or q.get("name") or "") in my_starters
        }
        k = getattr(self, "waiver_k", None) or 3
        last_pick = self.teams * self.rounds
        from .bench import predicted_undrafted
        rem_all = [p for p in self.remaining() if p.get("proj_source") != "no_market"]
        wire_names = predicted_undrafted(rem_all, self.current_pick, last_pick)
        added = False
        for pos in BENCH_POSITIONS:
            rem = [p for p in self.remaining(pos)
                   if p.get("proj_source") != "no_market"
                   and self._pos_allowed(pos, rnd, counts, picks_left, top6_te_fell)]
            if not rem:
                continue
            waiver, wname = waiver_ppw(rem, last_pick, k, wire_names=wire_names)
            best, best_iv = None, None
            for p in rem:
                hc = starter_ppw.get(str(p.get("backs_up") or ""))
                iv = insurance_value(p, waiver, exposure.get(pos, 0), hc,
                                     depth_ahead=depth_ahead.get(pos, 0))
                if best_iv is None or iv["value"] > best_iv["value"]:
                    best, best_iv = p, iv
            if best is None:
                continue
            n = exposure.get(pos, 0)
            d = depth_ahead.get(pos, 0)
            why = (f"bench insurance: covers {n} {pos} starter{'s' if n != 1 else ''}"
                   + (f" behind {d} reserve{'s' if d != 1 else ''} already held" if d else "")
                   + f" ~{best_iv['weeks']:.1f} wks/season · +{best_iv['edge']:.1f}/wk over "
                   f"the wire ({wname or 'nobody'}) ≈ {best_iv['value']:.0f} pts")
            if best_iv["handcuff"]:
                why += f" · HANDCUFF: backs up your {best.get('backs_up')}"
            cands.append((best_iv["value"], why, best))
            added = True
        if added:
            cands.sort(key=lambda t: -t[0])
        return added

    @staticmethod
    def _mval(p: dict, value_key: str) -> float:
        """A player's value in a given market's currency."""
        v = p.get(value_key)
        if v is None:
            v = p.get("vorp")
        return float(v or 0.0)

    def urgency_report(self) -> dict | None:
        """Cached per pick-state; None when unslotted or the draft is over."""
        if not self.my_slot:
            return None
        picks = self.state.picks
        # key includes the last pick's identity so an undo+redo at equal count
        # (commissioner reversal) invalidates the cache
        key = (len(picks), str(picks[-1].get("player_id")) if picks else "")
        if self._urgency_cache and self._urgency_cache[0] == key:
            return self._urgency_cache[1]
        import zlib

        import numpy as np

        from .urgency import simulate_survival

        cur = self.current_pick
        total = self.teams * self.rounds
        rnd, slot_on_clock = snake.pick_to_round_slot(min(cur, total), self.teams)
        # When I'M on the clock, the decision window is the rival picks between
        # now and my FOLLOWING turn (on pick 23, rivals pick 24-25 before my
        # 26) — next_pick_for_slot(cur) would return cur itself and zero out
        # every urgency exactly at decision time.
        start = cur + 1 if slot_on_clock == self.my_slot else cur
        my_next = snake.next_pick_for_slot(start, self.my_slot, self.teams, self.rounds)
        if my_next is None:
            return None
        # no_market rows are engine-invisible (guardrail) — keep them out of
        # the survival pool and best-available math too
        avail = sorted(
            (p for p in self.remaining() if p.get("proj_source") != "no_market"),
            key=lambda p: p["adp"] if p.get("adp") is not None else 999.0,
        )
        # ROLLING ADP WINDOW around the current pick, not a fixed top-N.
        # A fixed top-80-by-ADP starves in the late rounds (the board carries
        # every player with ADP inside 180, so by round 10 the top 80 are
        # nearly all gone) — rivals then had almost nobody to "take", which
        # understated competition and inflated survival exactly where the
        # round-8 upside switch is deciding (post-v2 item 1).
        # No LOWER bound (review 2026-09-02): a player 20+ picks past his ADP
        # is exactly the faller the engine exists to catch, and the old
        # `cur - pool_lookback` floor dropped him from the simulation -- so
        # his market's best_now/e_best/urgency were computed without him and
        # his "% chance he's still there" clause vanished. Fallers are few;
        # the pool grows by a handful. pool_lookback is kept in the knob list
        # for config compatibility and no longer bounds anything.
        hi = cur + self.pool_lookahead
        window = [p for p in avail
                  if p.get("adp") is not None and p["adp"] <= hi]
        if len(window) < self.pool_min:
            # floor: never starve — extend by ADP proximity to the window
            window = avail[: max(self.pool_min, len(window))]
        # DECISIONS #35: the list-walking autopick component reads `yrank`
        # (Yahoo default rank). Rows without a yahoo_rank are passed through
        # untouched so the engine's fallback to adp applies.
        pool = [dict(p, yrank=p["yahoo_rank"]) if p.get("yahoo_rank") is not None else p
                for p in window]
        # crc32, not hash(): string hash is per-process randomized and would
        # let a mid-draft restart silently flip near-tie recommendations
        seed = zlib.crc32(f"{self.draft_id}:{key[0]}:{key[1]}".encode())
        rng = np.random.default_rng(seed)
        recent_pos = self._recent_positions()
        # Pooled markets alongside the per-position report. Only the FLEX
        # market differs from a position group; dedicated slots ARE their
        # position. Computed on the same simulation -- rival behavior does not
        # change, only how the survivors are aggregated into "what did waiting
        # cost me".
        markets = None
        if self.slot_markets and self.my_needs().get("FLEX", 0) > 0:
            markets = {"FLEX": {"members": snake.FLEX_ELIGIBLE,
                                "value": "vorp_flex"}}
        report = simulate_survival(
            pool, start, my_next, self._rival_states(start, my_next), self.rival_seeds,
            rng, sims=self.sims, sigma=self._sigma(rnd), teams=self.teams,
            history_end=cur,   # the real history ends at the pick on the clock, not at `start`
            reach_prob=self.reach_prob, reach_scale=self.reach_scale,
            run_window=self.run_window, run_min=self.run_min,
            run_boost=self.run_boost, survival_shrink=self.survival_shrink,
            recent_pos=recent_pos, markets=markets,
            need_damp=self.need_damp, qb_filled_damp=self.qb_filled_damp,
            kdef_early_damp=self.kdef_early_damp,
            qb_damp_until_round=self.qb_damp_until_round,
            kdef_typical_round=self.kdef_typical_round, run_ratio=self.run_ratio,
            autopick_sigma_scale=self.autopick_sigma_scale,
            autopick_need_damp=self.autopick_need_damp,
            autopick_list_prob=self.autopick_list_prob,
            rival_needs_update=self.rival_needs_update,
        )
        self._urgency_cache = (key, report)
        return report

    def _my_pos_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for pos in self.slot_positions(self.my_slot):
            counts[pos] = counts.get(pos, 0) + 1
        return counts

    def _pos_allowed(self, pos: str, rnd: int, counts, picks_left,
                     top6_te_fell: bool) -> bool:
        """Position-level guardrails (spec §6) — the SINGLE source of truth,
        used by _guardrail_ok for this pick and by the two-pick planner for
        the next pick (code review 2026-08-30: the planner's hand copy had
        silently diverged)."""
        if pos in ("K", "DEF"):
            if picks_left > 2:
                return False
            if counts.get(pos, 0) >= 1:
                return False
        if pos == "QB":
            if counts.get("QB", 0) >= 2:  # never a 3rd QB in a 1-QB league
                return False
            if counts.get("QB", 0) >= 1 and rnd < self.qb2_round:
                return False
        if pos == "TE":
            if counts.get("TE", 0) >= 2:  # spec allows at most a 2nd TE
                return False
            if counts.get("TE", 0) >= 1 and not top6_te_fell:
                return False
        return True

    def _guardrail_ok(self, p: dict, rnd: int, needs, counts, picks_left,
                      top6_te_fell: bool) -> bool:
        """Final spec §6 — hard rules, override the engine."""
        # no_market rows are board-visible only: the stats model's lone opinion
        # with no market corroboration. An overrides.csv entry (proj_source
        # becomes "override") is the switch that activates them for the engine.
        if p.get("proj_source") == "no_market":
            return False
        pos = p["pos"]
        if not self._pos_allowed(pos, rnd, counts, picks_left, top6_te_fell):
            return False
        # max one zero-role stash: proxy = negative-VORP player already rostered
        if (p["vorp"] or 0) <= 0 and not snake.needs_position(needs, pos):
            have_stash = any(
                (self.by_id[pid].get("vorp") or 1) <= 0
                for pid in (str(x["player_id"]) for x in self.picks_for_slot(self.my_slot))
                if pid in self.by_id
            )
            if have_stash:
                return False
        # must-fill: remaining picks <= open starters -> starters only
        open_starters = sum(
            needs.get(k, 0) for k in ("QB", "RB", "WR", "TE", "FLEX", "K", "DEF")
        )
        if picks_left <= open_starters and not snake.needs_position(needs, pos):
            return False
        return True

    def _bye_warning(self, p: dict, needs) -> str:
        """Warn (never block) when a pick creates 3+ starters on one bye.

        Starters are assigned the same way snake.starter_needs fills slots
        (dedicated -> FLEX -> bench), not by draft order — an early bench
        stash must not count and a late-drafted real starter must.
        """
        remaining = {k: v for k, v in self.slots.items()}
        byes: list = []
        for x in self.picks_for_slot(self.my_slot):
            q = self.by_id.get(str(x.get("player_id")))
            if not q:
                continue
            pos = q["pos"]
            if remaining.get(pos, 0) > 0:
                remaining[pos] -= 1
            elif pos in snake.FLEX_ELIGIBLE and remaining.get("FLEX", 0) > 0:
                remaining["FLEX"] -= 1
            else:
                continue  # bench
            if q.get("bye") is not None:
                byes.append(q["bye"])
        if p.get("bye") is not None and byes.count(p["bye"]) >= 2:
            return f" ⚠ {byes.count(p['bye']) + 1} starters on bye {p['bye']}"
        return ""

    def recommendations(self, top_n: int = 5) -> list[tuple[float, str, dict]]:
        """Final spec §5: urgency-ranked positions, best VORP within, Δ tiebreak.

        Guardrails (§6) hard-filter candidates first; cliffs are UI-only (§3).
        """
        rnd, _ = snake.pick_to_round_slot(
            min(self.current_pick, self.teams * self.rounds), self.teams
        )
        if not self.my_slot:
            pool = self.remaining()[:top_n]
            return [(p["vorp"] or 0.0, "best value (spectator)", p) for p in pool]
        needs = self.my_needs()
        counts = self._my_pos_counts()
        picks_left = self.rounds - len(self.picks_for_slot(self.my_slot))
        report = self.urgency_report()
        # hoisted: the TE2 exception is a property of the board, not of each
        # candidate — computing it per-candidate re-sorted the TE pool ~30x
        top6_te_fell = any(
            q["pos_rank"] <= 6
            and q.get("adp") is not None
            and self.current_pick - q["adp"] >= self.te2_fall
            for q in self.remaining("TE")
        )

        cliff = self.cliff_report()
        cands = []
        from .planner import own_value as _ov
        fallback = self._fallback_points(needs) if self.adaptive_fallback else None
        repl = self._replacement_points() if fallback else None
        second: dict[str, float] = {}  # per-position 2nd-best, for the planner
        for pos in POS_ORDER:
            rem_p = sorted(
                (p for p in self.remaining(pos) if p.get("proj_source") != "no_market"),
                key=lambda q: -_ov(q, needs, fallback))
            # same currency as the planner's own/partner terms, or the cap
            # would compare a VORP level against a fallback-measured one
            second[pos] = _ov(rem_p[1], needs, fallback) if len(rem_p) > 1 else 0.0

        # One row per UNFILLED ROSTER SLOT, not per position (_open_markets).
        # A position with an open dedicated slot is its own market; every
        # flex-eligible player also competes in the FLEX market on vorp_flex.
        # A player can therefore win two markets -- deduped below, keeping the
        # more urgent slot he can fill.
        for mkt, member_pos, vkey in self._open_markets(needs):
            def mv(q, _k=vkey):
                return self._mval(q, _k)
            rem = sorted(
                (p for m in member_pos for p in self.remaining(m)
                 if p.get("proj_source") != "no_market"),
                key=lambda q: -mv(q))
            gpool = [
                p for p in rem
                if self._guardrail_ok(p, rnd, needs, counts, picks_left, top6_te_fell)
            ]
            # v2 item 1.5: benches win on 90th percentiles, not medians — from
            # upside_from_round, gated players (role-quality, see tiers.py)
            # score on an 85th-percentile proxy. Applied BEFORE the top-3
            # truncation so a gated player ranked 4th+ by median can surface
            # (code review 2026-08-30).
            if rnd >= self.upside_from_round:
                lam = float(getattr(self, "dispersion_lambda", 0.5))

                def _late(q, _mv=mv, _lam=lam):
                    sd = self._dispersion_for(q)
                    if sd is not None:
                        return _mv(q) + _lam * sd            # plan A3: mean + spread
                    # additive in |value|: a multiplier on a NEGATIVE market
                    # value (late rounds on a shallow board) pushed the flagged
                    # player DOWN, the opposite of the intent (review 2026-09-02)
                    boost = (self.upside_mult - 1.0) * abs(_mv(q)) if q.get("upside_flag") else 0.0
                    return _mv(q) + boost
                gpool = sorted(gpool, key=lambda q: -_late(q))
            pool = gpool[:3]
            if not pool:
                continue
            # best value within the market; near-ties (<= 2 pts of the market's
            # TOP candidate) broken by Δ — anchored so swaps can't chain
            anchor = pool[0]
            best = anchor

            def _delta(q):
                # 0.0 is a real delta, not a missing one (`or -999` read it as missing)
                d = q.get("adp_delta")
                return -999.0 if d is None else float(d)
            for q in pool[1:]:
                if abs(mv(anchor) - mv(q)) <= 2.0 and _delta(q) > _delta(best):
                    best = q
            pos = best["pos"]
            label = "your FLEX spot" if mkt == "FLEX" else mkt
            rem_pos = [p for p in self.remaining(pos)
                       if p.get("proj_source") != "no_market"]
            u = report.get(mkt) if report else None
            urgency = u["urgency"] if u else mv(best)
            # rationale: plain-English clauses, all from already-computed draft
            # state (no model calls on the clock, per spec §9)
            parts = []
            if u:
                if urgency >= 1.0:
                    parts.append(
                        f"waiting likely costs ~{urgency:.0f} pts at {label} "
                        f"(best option now {u['best_now']:.0f}, "
                        f"~{u['e_best_next']:.0f} by your next turn)"
                    )
                else:
                    parts.append(f"safe to wait on {label}")
                surv = u["survival"].get(best["sleeper_id"])
                if surv is not None:
                    parts.append(f"{surv:.0%} chance he's still there at your next pick")
            if needs.get(pos, 0) > 0:
                parts.append(f"fills your open {pos} slot")
            elif pos in snake.FLEX_ELIGIBLE and needs.get("FLEX", 0) > 0:
                parts.append("fills a FLEX slot")
            else:
                parts.append("bench depth (starters covered)")
            c = cliff.get(pos, {})
            same_tier = sum(1 for q in rem_pos if q["tier"] == best["tier"])
            next_tier = next((q["tier"] for q in rem_pos if q["tier"] > best["tier"]),
                             None)
            if c.get("urgent"):
                parts.append(
                    f"TAKE-NOW ZONE: only {c['before_cliff']} left before the {pos} "
                    f"value drops, and {c['intervening_demand']} team"
                    f"{'s' if c['intervening_demand'] != 1 else ''} picking before "
                    f"you still need one"
                )
            else:
                if next_tier is not None and same_tier == 1:
                    parts.append(f"last {pos} at this level — big drop after him")
                elif next_tier is not None and same_tier <= 3:
                    parts.append(f"only {same_tier} {pos}s left at this level")
                elif c.get("before_cliff") is not None and c["before_cliff"] <= 3:
                    parts.append(f"{c['before_cliff']} left before the {pos} value drops")
                demand = c.get("intervening_demand", 0)
                if demand:
                    parts.append(f"{demand} team{'s' if demand != 1 else ''} picking "
                                 f"before you still need a {pos}")
            if best.get("adp") is not None:
                d = self.current_pick - best["adp"]
                if d >= self.fall_alert:
                    parts.append(f"bargain: still here {d:.0f} picks after he's usually drafted")
                elif d >= 3:
                    parts.append(f"{d:.0f} picks past his usual draft spot")
            if rnd >= self.upside_from_round and self._dispersion_for(best) is not None:
                lo, hi = best.get("proj_lo"), best.get("proj_hi")
                span = f", {lo:.0f}-{hi:.0f}" if lo is not None and hi is not None else ""
                parts.append(f"sources disagree by ±{best['proj_sd']:.0f} pts ({best.get('n_sources')} sources{span})")
            elif rnd >= self.upside_from_round and best.get("upside_flag"):
                parts.append(f"UPSIDE play: {best.get('upside_why')}")
            why = " · ".join(parts) or "best value"
            why += self._bye_warning(best, needs)
            # UI-only handcuff tag (never scored): the late-round buy signal is
            # a backup whose starter is fragile or currently availability-flagged
            # standing contingency (post-v2 item 3): late rounds only, display
            # only — it never enters the score
            if rnd >= 12 and best.get("backs_up_pos") and best.get("starter_fragility_label"):
                why += (f" · standing handcuff: backs up {best['backs_up_pos']} "
                        f"({best['starter_fragility_label']} fragility)")
            if best.get("backs_up"):
                seg = float(best.get("starter_exp_games") or 16.0)
                sav = best.get("starter_avail")
                if seg <= 13.0 or sav:
                    tag = f" ⛑ backs up {best['backs_up']} ({seg:.0f}g"
                    tag += f", {sav})" if sav else ")"
                    why += tag
            # Tiebreak in the MARKET's own currency: within a pooled market
            # every candidate carries the same urgency, so this is what
            # actually picks the flex starter -- and it is the comparison that
            # stops an elite TE outranking an RB he does not out-produce.
            score = urgency + 0.001 * mv(best)  # stable ordering
            cands.append((score, why, best))
        cands.sort(key=lambda t: -t[0])
        # a player who wins two markets appears twice; keep the more urgent
        seen_ids: set[str] = set()
        cands = [c for c in cands
                 if not (c[2]["sleeper_id"] in seen_ids
                         or seen_ids.add(c[2]["sleeper_id"]))]
        # BENCH REALITIES (draftkit/bench.py). Once every non-K/DEF starter
        # is filled, a candidate's value is insurance -- weeks I will need
        # him x his edge over the waiver wire -- not VORP against the starter
        # baseline. Bench rows are ranked greedily on that number; the
        # two-pick planner is skipped for them because its partner term is a
        # VORP level, a different currency, and bench picks barely interact.
        bench_rows = False
        if self.bench_insurance:
            bench_rows = self._bench_candidates(
                cands, needs, counts, rnd, picks_left, top6_te_fell)
            if bench_rows:
                # the bench rows are appended to the market rows and the whole
                # list re-sorted; a player can now be in twice (review
                # 2026-09-02). Keep the higher-scored row.
                seen_ids = set()
                cands = [c for c in cands
                         if not (c[2]["sleeper_id"] in seen_ids
                                 or seen_ids.add(c[2]["sleeper_id"]))]
        # v2 item 1.2: joint two-pick re-rank on top of the greedy order.
        # Pure arithmetic over the cached urgency report — nothing new runs
        # on the clock; any failure or missing report keeps the greedy list
        # (amendment B's hard fallback).
        if not cands:
            # Shallow-baseline boards (10-team: RB24/WR24) go negative-VORP by
            # the late rounds, which turned the one-stash budget into a total
            # mute — zero recommendations from R11 on (caught by the local-pipe
            # replay, 2026-08-30). Hard rules keep holding (no_market, K/DEF
            # timing, QB/TE caps); only the stash budget yields, loudly.
            for pos in POS_ORDER:
                rem = [p for p in self.remaining(pos)
                       if p.get("proj_source") != "no_market"
                       and self._pos_allowed(pos, rnd, counts, picks_left, top6_te_fell)]
                if rem:
                    best = rem[0]
                    cands.append((best["vorp"] or 0.0,
                                  "bench depth — best remaining value (everyone left is "
                                  "below replacement, stash budget waived)", best))
            cands.sort(key=lambda t: -t[0])

        if bench_rows:
            for _sc, _w, p in cands:
                p.pop("_pair", None)   # bench mode skips the pair stage; drop stale math
            return cands[:top_n]
        try:
            from .planner import pair_rank

            def eligible_after(pos_taken: str) -> set[str]:
                # the partner set the NEXT pick will actually allow, from the
                # same predicate the guardrails use, with the candidate counted
                counts_after = dict(counts)
                counts_after[pos_taken] = counts_after.get(pos_taken, 0) + 1
                return {
                    pos2 for pos2 in POS_ORDER
                    if self._pos_allowed(pos2, min(rnd + 1, self.rounds),
                                         counts_after, picks_left - 1, top6_te_fell)
                }

            cands = pair_rank(cands, report, needs, second, eligible_after,
                              fallback=fallback, repl=repl)
        except Exception as e:  # noqa: BLE001 — planner must never block the clock
            # fall back to greedy, but never silently: a dead planner on draft
            # day must be visible (code review 2026-08-30)
            import logging
            logging.getLogger("draftkit").warning("two-pick planner fallback: %r", e)
            self._planner_note = f"planner fallback: {e.__class__.__name__}"
            for _sc, _w, p in cands:
                p.pop("_pair", None)   # a half-run pair stage must not leave numbers behind
        return cands[:top_n]

    # ---------- render ----------

    def render(self) -> Layout:
        s = self.state
        cur = self.current_pick
        rnd, slot_on_clock = snake.pick_to_round_slot(min(cur, self.teams * self.rounds), self.teams)
        on_clock_me = self.my_slot is not None and slot_on_clock == self.my_slot

        header = Text()
        header.append(f" {self.draft_id}  ", style="dim")
        header.append(f"status: {s.status}  ")
        if s.status == "complete":
            header.append("DRAFT COMPLETE", style="bold green")
        else:
            header.append(f"pick {cur} (R{rnd}.{(cur - 1) % self.teams + 1})  slot {slot_on_clock} on clock  ")
        if self.my_slot:
            nxt = snake.next_pick_for_slot(cur, self.my_slot, self.teams, self.rounds)
            if on_clock_me and s.status == "drafting":
                header.append("  >>> YOU ARE ON THE CLOCK <<<", style="bold white on red")
            elif nxt:
                header.append(f"my next pick: {nxt} ({nxt - cur} away)", style="cyan")
        if s.last_error:
            header.append(f"  [poll error: {s.last_error}]", style="red")

        # positional board: top 3 remaining per position
        board = Table(show_header=True, header_style="bold", expand=True)
        board.add_column("Pos", width=4)
        board.add_column("Top remaining (tier | VORP | ADPΔ)", overflow="fold")
        cliff = self.cliff_report()
        for pos in POS_ORDER:
            rem = self.remaining(pos)[:3]
            cells = []
            for p in rem:
                adp_d = ""
                if p.get("adp") is not None:
                    d = cur - p["adp"]
                    adp_d = f" {'+' if d >= 0 else ''}{d:.0f}v" if abs(d) >= 3 else ""
                mark = "⛰" if p["cliff_flag"] else ""
                cells.append(f"[bold]{p['player']}[/bold]{mark} (T{p['tier']}|{p['vorp']:.0f}{adp_d})")
            c = cliff.get(pos, {})
            tag = ""
            if c.get("urgent"):
                tag = f" [red bold]CLIFF NOW ({c['before_cliff']} left, {c['intervening_demand']} rivals)[/red bold]"
            elif c.get("before_cliff") is not None and c["before_cliff"] <= 3:
                tag = f" [yellow]cliff in {c['before_cliff']}[/yellow]"
            board.add_row(pos, "   ".join(cells) + tag)

        panels = [Panel(header, title="draft"), Panel(board, title="board")]

        if self.my_slot:
            needs = self.my_needs()
            my_pos = self.slot_positions(self.my_slot)
            roster_line = "  ".join(
                f"{k}:{self.slots[k] - needs.get(k, 0)}/{self.slots[k]}"
                for k in ("QB", "RB", "WR", "TE", "FLEX", "K", "DEF")
            )
            bench_used = max(0, len(my_pos) - sum(self.slots[k] - needs.get(k, 0) for k in ("QB", "RB", "WR", "TE", "FLEX", "K", "DEF")))
            roster_line += f"  BN:{bench_used}/{self.slots['BN']}"
            drafted_names = ", ".join(
                (self.by_id.get(str(p["player_id"]), {}).get("player")
                 or f"{(p.get('metadata') or {}).get('first_name','?')} {(p.get('metadata') or {}).get('last_name','')}")
                for p in self.picks_for_slot(self.my_slot)
            ) or "—"
            recs = self.recommendations()
            rec_lines = []
            for score, why, p in recs:
                rec_lines.append(
                    f"[bold]{p['player']}[/bold] {p['pos']}{p['pos_rank']} "
                    f"T{p['tier']} VORP {p['vorp']:.0f} — {why}"
                )
            panels.append(
                Panel(
                    Group(
                        Text.from_markup(f"[bold]{roster_line}[/bold]"),
                        Text(f"drafted: {drafted_names}", style="dim"),
                        Text.from_markup("\n".join(rec_lines) or "no candidates"),
                    ),
                    title="my roster & picks to make",
                    border_style="red" if on_clock_me else "cyan",
                )
            )

        fallers = self.fallers()
        if fallers:
            fl = "   ".join(
                f"{p['player']} ({p['pos']}, ADP {p['adp']:.0f}, -{cur - p['adp']:.0f})"
                for p in fallers
            )
            panels.append(Panel(Text.from_markup(fl), title="value fallers (≥1 round past ADP)", border_style="yellow"))

        layout = Layout()
        layout.update(Group(*panels))
        return layout

    # ---------- loop ----------

    def run(self) -> None:
        console = Console()
        console.print(
            f"[bold]draftkit tracker[/bold] — draft {self.draft_id}, "
            f"{self.teams} teams, {self.rounds} rounds, my slot: {self.my_slot or 'unknown (spectator mode)'}"
        )
        self.poll()
        backoff = self.poll_seconds
        with Live(self.render(), console=console, refresh_per_second=2, screen=False) as live:
            while True:
                time.sleep(backoff)
                changed = self.poll()
                if self.state.last_error:
                    backoff = min(backoff * 2, 60)
                else:
                    backoff = self.poll_seconds
                if changed or True:
                    live.update(self.render())
                if self.state.status == "complete":
                    live.update(self.render())
                    break
        console.print("[green]Draft complete.[/green] Final roster above — good luck in the playoffs.")
