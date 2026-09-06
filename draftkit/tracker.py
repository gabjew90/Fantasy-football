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
from .boardrow import published_range
from .shape import starting_slots
from .sleeper import SleeperClient, get_json, BASE

POS_ORDER = ["RB", "WR", "TE", "QB", "K", "DEF"]
# Bench rows are priced in a DIFFERENT currency from market rows, and the
# dedup has to tell them apart. One constant, written once and matched once.
BENCH_WHY_PREFIX = "bench insurance:"
BENCH_ZERO = 0.5  # season insurance under this is nothing: the zero-insurance fallthrough (ceiling over the wire)


def calibrate_survival(s: float, knots: list[tuple[float, float]]) -> float:
    """Piecewise-linear map from the sim's survival to what the SHOWN rows
    actually did (engine.survival_calibration, [[predicted, observed], ...]).
    Endpoints (0, 0) and (1, 1) are implied. The rows the engine shows are the
    rows other drafters want too: over eleven rooms the fitted rival model
    still showed 40% where 21% survived and 60% where 43% did (reports/
    survival_fit_study_2026-09-05.md), a gap no draw form in the grid closes.
    Applied to `survival` only; `survival_raw` stays the sim's number."""
    if not knots:
        return s
    pts = sorted([(0.0, 0.0)] + [(float(a), float(b)) for a, b in knots] + [(1.0, 1.0)])
    s = min(1.0, max(0.0, float(s)))
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if s <= x1:
            if x1 == x0:
                return y1
            return y0 + (y1 - y0) * (s - x0) / (x1 - x0)
    return pts[-1][1]
BENCH_TIE = 2.0   # bench rows this close on the RAW insurance value are a coin flip: the higher
                  # CEILING breaks it (proj_hi, else proj_pts + band/2; never the width, DECISIONS #55)

FALLBACK_FLOORS = ("board_min", "replacement")


def fallback_value(survivor_vals: list[float], pool_vals: list[float],
                   repl: float | None, mode: str = "board_min") -> float | None:
    """One position's fallback: the best player still gettable by the deadline.

    Pure, and module-level, so the CONTINUITY PROPERTY can be tested against
    the real decision instead of a copy of it.

    `board_min` is the original. When nobody survives the deadline it flips the
    operator from max to min over the whole pool, and since ADP order and
    projection order differ, the pool minimum sits well below the last
    survivor. The fallback enters own_value with a MINUS sign, so that step is
    an instant board-wide UPWARD spike in apparent value -- at the scarce
    position, sized by whichever junk player is lowest-projected.

    `replacement` treats streaming as a FLOOR UNDER EVERY ANSWER, not just as
    the answer when the position empties. Substituting it only in the empty
    case still jumps -- the first attempt at this fix did exactly that and the
    property test caught an 80-point step. The floor is also the more correct
    statement: you can always stream, so what you would end up with at a
    position is never worse than replacement, whether or not a draftable
    survivor exists.

    That makes the curve max(falling survivor line, flat floor) -- monotonically
    non-increasing, and it flattens at replacement instead of falling off
    anything. Replacement level is what replacement_baselines means
    (draftkit/baselines.py derives it from a streaming backtest).

    UNITS: every argument is SEASON POINTS on the projections.games
    convention. bench.waiver_ppw is the same idea but speaks points-per-week
    over FANTASY_WEEKS=17, which is why it is not used here.
    """
    best = max(survivor_vals) if survivor_vals else None
    if mode == "replacement" and repl is not None:
        return float(repl) if best is None else max(best, float(repl))
    if best is not None:
        return best
    return min(pool_vals) if pool_vals else None


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
    rival_draw = "lottery"      # survival study 2026-09-04: lottery (today) | floored | order (urgency.simulate_survival)
    # BENCH ROWS (2026-09-04, user-approved design). bench_survival_discount:
    # rank a bench row on its cost of waiting -- insurance value now minus
    # the expected best insurance value at my next turn (urgency.expected_best
    # over the position's candidates and their simulated survivals) -- the
    # same operator the market path uses, instead of raw insurance points,
    # which took Tracy at 79 while he was 95% to be there at 89.
    # bench_contingency: price the role shift when a backup's starter on
    # ANOTHER roster goes down (bench.insurance_value, contingency term).
    bench_survival_discount = False
    bench_contingency = False
    # bench_two_pick (2026-09-04, #47 follow-up): a bench position scores as
    # its value now plus the expected best insurance still gettable at the
    # OTHER bench positions next turn (the market path's two-pick shape); at
    # the last bench pick value alone counts. Supersedes the drop-off when on.
    bench_two_pick = False
    # TURN SEATS (2026-09-04): at the turn my next pick is one pick away with
    # nobody in between, so every survival is exactly 1.0 and every urgency 0,
    # and the two picks are ranked on value alone with no view of the 18-pick
    # gap that follows. With the knob on, an empty window looks through to
    # the FOLLOWING turn for survival and urgency, and the pair planner prices
    # the partner at best_now (he is certain) instead of e_best_next.
    turn_look_through = False
    # DECISIONS #53: how a near-tie between two skill players is broken.
    # scarcity = the less-likely-to-survive player first inside
    # planner.NEAR_TIE, then the higher floor (#55). touchdowns = the player
    # with more projected touchdowns first inside tie_window; QB/K/DEF pairs
    # keep scarcity. Tried for one room on 2026-09-05 and reverted the same
    # morning (the 2024-25 backtest has the higher-TD player of a near-tie
    # scoring LESS 57% of the time at RB/WR); kept, off, like the bench knobs.
    tie_break = "scarcity"
    tie_window = 1.0
    # DECISIONS #58: a handcuff's uplifted rate applies only in HIS starter's
    # absence weeks; the rest of the cover is at his own rate. Off = the #8
    # pricing (uplift across every cover week).
    handcuff_split = False
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
    # --- the 2026-09-04 correctness set. EVERY DEFAULT IS TODAY'S BEHAVIOUR. ---
    # E: the upside boost measured from the market floor (a difference, so a
    #    baseline shift cancels) instead of abs() of the level (non-linear, so
    #    it does not).
    upside_boost_relative = False
    # A/C: when a position is picked clean before the deadline, price the
    #    fallback at replacement level -- what you can actually stream -- rather
    #    than at the worst player left on the board, which flips the operator
    #    from max to min and drops a cliff.
    fallback_floor = "board_min"        # "board_min" | "replacement"
    # B: at the market/bench seam, prefer the insurance row over the market row
    #    (except for a genuine upgrade). See the dedup in recommendations().
    bench_row_wins_dedupe = False
    # D: a per-position deadline instead of one shared across positions that
    #    empty at different rates. IMPLEMENTED, MEASURED, AND DELIBERATELY LEFT
    #    OFF: churn is not a verdict and DECISIONS #41 shows lineup points
    #    cannot resolve it. Turning it on needs more season pairs first.
    per_position_deadline = False
    # F: draft-time k hedges PREDICTION ERROR (which undrafted player is really
    #    best) and has nothing to do with waiver format; baselines.waiver_k
    #    hedges CLAIM FRICTION and belongs to the in-season path. Split so each
    #    is defended separately. 3 = today; the derivation from backtest error
    #    is what should move it.
    draft_k = 3
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
        # The draft path uses draft_k ONLY. waiver_k is keyed on FAAB-vs-rolling
        # because it models CLAIM FRICTION, which is an in-season fact; the
        # bench wire at draft time is hedging PREDICTION ERROR instead, and
        # deciding it by waiver format was defending a number with a reason
        # that is false here (2026-09-04). apply_engine_cfg has already set
        # draft_k from the engine block by this point.
        gcfg = cfg["guardrails"] if "guardrails" in cfg._data else {}
        self.qb2_round = int(gcfg.get("qb2_earliest_round", 10))
        self.te2_fall = int(gcfg.get("te2_fall_picks", 12))
        self.position_max = {str(k): int(v) for k, v in (gcfg.get("position_max") or {}).items()}
        self.position_earliest_round = {str(k): int(v) for k, v in (gcfg.get("earliest_round") or {}).items()}
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
        if self.local:
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
        ("need_damp", float), ("qb_filled_damp", float), ("qb_damp_until_round", int),
        ("kdef_early_damp", float), ("kdef_typical_round", int),
        ("autopick_sigma_scale", float), ("autopick_need_damp", float), ("autopick_list_prob", float),
        ("rival_draw", str),
        ("rival_needs_update", bool),
        ("upside_from_round", int), ("upside_mult", float),
        ("late_round_dispersion", bool), ("dispersion_lambda", float),
        ("slot_markets", bool), ("adaptive_fallback", bool), ("bench_insurance", bool),
        ("upside_boost_relative", bool), ("fallback_floor", str),
        ("bench_row_wins_dedupe", bool), ("per_position_deadline", bool),
        ("draft_k", int),
        ("bench_survival_discount", bool), ("bench_contingency", bool), ("bench_two_pick", bool),
        ("turn_look_through", bool),
        ("tie_break", str), ("tie_window", float),
        ("handcuff_split", bool),
    )

    def _dispersion_for(self, q: dict) -> float | None:
        """The candidate's projection spread when the late-round dispersion
        objective applies to him. None otherwise (the boolean upside
        multiplier then applies).

        TWO different quantities can supply it, in this order:

          proj_sd    disagreement BETWEEN sources, valid only at n >= 2. One
                     source has an sd of zero by construction, which is an
                     absence of evidence and not a narrow forecast, so the
                     n >= 2 guard stays exactly as it was.
          proj_band  ONE source's own published range (its high and low lines
                     either side of its base). A real uncertainty statement
                     from the forecaster rather than an artifact of how many
                     feeds happened to be pulled.

        They are not the same thing and are deliberately not summed. Combining
        them (in quadrature, say) is a modelling claim nobody here has
        measured, and preferring cross-source disagreement when it exists
        keeps the arm identical to the one plan A3 was written for.
        """
        if not self.late_round_dispersion:
            return None
        sd, n = q.get("proj_sd"), q.get("n_sources") or 0
        if sd is not None and sd == sd and n >= 2:
            return float(sd)
        band = q.get("proj_band")
        if band is not None and band == band and float(band) > 0.0:
            return float(band)
        return None

    def apply_engine_cfg(self, ecfg: dict | None) -> None:
        """Read the `engine:` block onto this tracker; absent keys keep the
        class defaults. pool_size is the legacy alias of pool_min."""
        ecfg = ecfg or {}
        for name, cast in self.ENGINE_KNOBS:
            setattr(self, name, cast(ecfg.get(name, getattr(Tracker, name))))
        from .planner import TIE_BREAKS
        if self.tie_break not in TIE_BREAKS:
            # a free string that silently ran scarcity (review 2026-09-05):
            # an A/B typed 'touchdown' would compare two identical arms
            raise ValueError(f"engine.tie_break must be one of {TIE_BREAKS}, got {self.tie_break!r}")
        # rolling ADP window for the rival sampling pool (post-v2 item 1);
        # pool_size is retained as the FLOOR so old configs stay meaningful
        self.pool_min = int(ecfg.get("pool_min", ecfg.get("pool_size", Tracker.pool_min)))
        # engine.prefer: the user's named calls, [[preferred, over], ...] in
        # board names. When a market's best is the second name and the first
        # is in that market's shortlist, the first is the row (user,
        # 2026-09-05: Chase over Nacua at pick 3, a 1.6-point sheet gap).
        prefer = ecfg.get("prefer") or []
        pairs: list[tuple[str, str]] = []
        for item in prefer:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                raise ValueError(f"engine.prefer entries are [preferred, over] pairs, got {item!r}")
            pairs.append((str(item[0]), str(item[1])))
        self.prefer = pairs
        # engine.survival_calibration: [[predicted, observed], ...] knots for
        # calibrate_survival; empty means the sim's number is shown as is
        knots = ecfg.get("survival_calibration") or []
        cal: list[tuple[float, float]] = []
        for item in knots:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                raise ValueError(f"engine.survival_calibration entries are [predicted, observed] pairs, got {item!r}")
            a, b = float(item[0]), float(item[1])
            if not (0.0 <= a <= 1.0 and 0.0 <= b <= 1.0):
                raise ValueError(f"engine.survival_calibration knots are probabilities, got {item!r}")
            cal.append((a, b))
        self.survival_calibration = cal

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
                "autopick": slot in (self.away_slots or ()),
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
        if not self.slot_markets:
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
        def _deadline(open_slots: int) -> int:
            """My last starter-filling pick, given that many slots to fill.
            With no starters left, the question is what the BENCH could still
            get me, so the answer is my final pick."""
            return remaining[min(max(open_slots, 1), len(remaining)) - 1]

        # D (2026-09-04): ONE deadline for every position, or one per position?
        #
        # Shared (today) counts every open starter slot, FLEX included, so a
        # held-open flex pushes the deadline later for QB too. Per-position
        # counts only the slots the position is ELIGIBLE for, so QB's horizon
        # ignores the flex entirely.
        #
        # Neither is obviously right, and the comment says so rather than
        # picking a winner. Shared is correct if picks are a SHARED BUDGET:
        # spending one on a flex really does push the quarterback later,
        # whether or not a quarterback could have filled that slot.
        # Per-position is correct if each position has its own QUEUE: the
        # positions empty at very different rates, and "who survives to my
        # pick 90" is a fair question for TE and a meaningless one for RB.
        #
        # This is a modelling disagreement, not a defect, and nothing
        # available can settle it -- churn is not a verdict, and lineup points
        # cannot resolve below ~3% (DECISIONS #41). So it ships OFF and stays
        # off. See DECISIONS for what would unblock it.
        per_pos = bool(self.per_position_deadline)
        shared_deadline = _deadline(sum(needs.get(k, 0) for k in
                                        ("QB", "RB", "WR", "TE", "FLEX", "K", "DEF")))

        def _deadline_for(pos: str) -> int:
            if not per_pos:
                return shared_deadline
            slots = needs.get(pos, 0)
            if pos in snake.FLEX_ELIGIBLE:
                slots += needs.get("FLEX", 0)
            return _deadline(slots)

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

        # WHEN A POSITION IS PICKED CLEAN before the deadline, what is the
        # honest alternative? `board_min` (today) takes the worst player left,
        # which makes the operator flip from max to min and drops a cliff:
        # ADP order and projection order differ, so the pool minimum sits well
        # below the last survivor, and because the fallback enters own_value
        # with a MINUS sign that is an instant board-wide UPWARD spike in
        # apparent value -- at the scarce position, driven by whichever junk
        # player happens to be lowest-projected.
        #
        # `replacement` answers it with what you can actually stream, which is
        # exactly what replacement_baselines means (draftkit/baselines.py
        # derives them from a streaming backtest). Continuous, and it reuses a
        # number the engine already trusts for this question.
        #
        # UNITS: both branches are SEASON TOTALS on the projections.games
        # convention -- _fb() reads proj_pts, and _replacement_points()
        # recovers proj_pts - vorp. They agree today, and this assert is here
        # because a later change to projections.games would otherwise break it
        # silently. (bench.waiver_ppw was rejected for this fix precisely
        # because it speaks points-per-week over FANTASY_WEEKS=17 while
        # projections.games is 16.)
        floor_mode = str(self.fallback_floor)
        # `wire` (2026-09-04): the floor is what the WIRE will hold, not the
        # season replacement level. Measured on the headline board,
        # `replacement` still churned 28% of picks with the currency
        # mismatch gone, because replacement_baselines (QB10/RB24/WR24/TE11)
        # are DRAFTED players by the mid rounds -- the 24th RB is gone by pick
        # 60 -- so as a floor it overstated what is freely available and bound
        # in rounds 5-7 where nothing is empty. The k-th best player the market
        # leaves undrafted (bench.waiver_ppw, the same operator the bench
        # insurance uses) is below every survivor while survivors exist and
        # is the honest answer when the position is picked clean.
        if floor_mode == "replacement":
            repl_pts = self._replacement_points()
        elif floor_mode == "wire":
            repl_pts = self._wire_points()
        else:
            repl_pts = {}
        floor_arg = "replacement" if floor_mode in ("replacement", "wire") else floor_mode

        out: dict[str, float] = {}
        for pos in POS_ORDER:
            pool = [p for p in self.remaining(pos)
                    if p.get("proj_source") != "no_market"]
            deadline = _deadline_for(pos)
            survivors = [p for p in pool
                         if p.get("adp") is not None and p["adp"] >= deadline]
            # C: an EMPTY pool used to `continue`, dropping the position from
            # the dict -- planner.own_value then silently returned slot_vorp, a
            # VORP LEVEL compared against points-above-fallback numbers in the
            # same sort. In `replacement` mode the key always exists, so the
            # currency cannot switch mid-sort.
            v = fallback_value([_fb(p) for p in survivors], [_fb(p) for p in pool],
                               repl_pts.get(pos), floor_arg)
            if v is not None:
                out[pos] = v
        return out

    def _wire_points(self) -> dict[str, float]:
        """Season points of the wire at each position: the draft_k-th best
        player the market leaves undrafted (ADP past the last pick), the
        bench module's operator, times its 17 weeks. Empty when nothing is
        predicted undrafted at a position (fallback_value then falls back)."""
        from .bench import FANTASY_WEEKS, predicted_undrafted, waiver_ppw
        k = int(self.draft_k or 3)
        last_pick = self.teams * self.rounds
        rem_all = [p for p in self.remaining() if p.get("proj_source") != "no_market"]
        wire_names = predicted_undrafted(rem_all, self.current_pick, last_pick)
        out: dict[str, float] = {}
        for pos in POS_ORDER:
            rem = [p for p in rem_all if p.get("pos") == pos]
            if not rem:
                continue
            ppw, _who = waiver_ppw(rem, last_pick, k, wire_names=wire_names)
            if ppw is not None:
                out[pos] = float(ppw) * FANTASY_WEEKS
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
                          rnd: int, picks_left: int, top6_te_fell: bool
                          ) -> tuple[bool, set]:
        """Append one insurance-priced row per bench position.

        Returns (added, upgrade_ids). `added` True when bench rows were
        produced (the caller then skips the planner). `upgrade_ids` are the
        bench candidates whose OWN PROJECTION BEATS THE WEAKEST STARTER THEY
        WOULD DISPLACE -- for those, insurance is the wrong ruler. Insurance
        prices a man who only plays when someone is out; a late upgrade plays
        every week, and pricing him as a backup understates him badly. The
        dedup uses this to keep the market row for exactly those players.

        Only active once every non-K/DEF starter is filled, and never inside
        the must-fill window where remaining picks are owed to open starters.
        """
        from .bench import (BENCH_POSITIONS, insurance_value, starter_exposure,
                            waiver_ppw)
        open_skill = sum(needs.get(k, 0) for k in ("QB", "RB", "WR", "TE", "FLEX"))
        open_all = open_skill + needs.get("K", 0) + needs.get("DEF", 0)
        if open_skill > 0 or picks_left <= open_all:
            return False, set()
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
        # the weakest starter I hold at each position: the man a bench
        # candidate would actually displace if he is an upgrade rather than
        # insurance. Season points on both sides (starter_ppw above is the
        # per-week form the handcuff uplift needs; this is not that).
        weakest_starter: dict[str, float] = {}
        for q in self.players:
            nm = str(q.get("player") or q.get("name") or "")
            if nm not in my_starters:
                continue
            qp = q.get("pos")
            pts = float(q.get("proj_pts") or 0.0)
            if qp and (qp not in weakest_starter or pts < weakest_starter[qp]):
                weakest_starter[qp] = pts

        # draft-time k: hedges which undrafted player is really best, not
        # whether a claim would be won (draftkit/baselines.py draft_k)
        k = int(self.draft_k or 3)
        last_pick = self.teams * self.rounds
        from .bench import predicted_undrafted
        rem_all = [p for p in self.remaining() if p.get("proj_source") != "no_market"]
        wire_names = predicted_undrafted(rem_all, self.current_pick, last_pick)
        from .bench import ABSENT_WEEKS, FANTASY_WEEKS
        from .staged import SURV_GAP, VARIANCE_BAND
        # BENCH STAGES (user design 2026-09-05 afternoon):
        #   1. insurance value picks the player, across every bench position at
        #      once: the defensive term (weeks needed x edge over the wire) plus
        #      the offensive term when it lands (his starter on another roster
        #      goes down, he inherits, displaces my weakest starter);
        #   2. timing as a multiplier: score = insurance x (1 - survival), so a
        #      handcuff who will still be there next turn waits;
        #   3. scarcity, banded, same thresholds as the starters;
        #   4. ceiling, always: bench spots are lottery tickets;
        #   5. no pair, bench mode stays greedy.
        # When every candidate's insurance is zero: ceiling alone (over the
        # position's wire so positions compare), then role-shift flags, never
        # raw board order.
        # Survival to my next turn per player, the same simulation the market
        # path uses; a player outside the simulated window has no entry and
        # counts as certain to survive.
        rep = self.urgency_report() or {}
        surv_by_pos = {pos: (rep.get(pos) or {}).get("survival") or {} for pos in BENCH_POSITIONS}
        # the starter a role shift would displace, per position: at a
        # flex-eligible position the weakest flex-eligible starter (the new
        # starter pushes him out through the FLEX)
        displace_ppw: dict[str, float] = {}
        for pos in BENCH_POSITIONS:
            group = set(snake.FLEX_ELIGIBLE) if pos in snake.FLEX_ELIGIBLE else {pos}
            vals = [weakest_starter[g] for g in group if g in weakest_starter]
            if vals:
                displace_ppw[pos] = min(vals) / 17.0
        by_name = {str(q.get("player") or q.get("name") or ""): q for q in self.players}

        def _ceiling(q: dict) -> float | None:
            """The best published case (boardrow.published_range): the high
            line, else the point plus half the band; None without either."""
            return published_range(q)[1]

        def _role_flag(q: dict) -> bool:
            return bool((q.get("backs_up_pos") and q.get("starter_fragility_label")) or q.get("upside_flag"))

        # bench picks I still hold AFTER this one (K and DEF are owed their
        # own picks): with none left there is nothing to wait for, so the
        # timing multiplier is dropped and insurance alone ranks
        last_bench = (picks_left - 1 - needs.get("K", 0) - needs.get("DEF", 0)) < 1
        scored: list[dict] = []
        upgrade_ids: set = set()
        for pos in BENCH_POSITIONS:
            rem = [p for p in self.remaining(pos)
                   if p.get("proj_source") != "no_market"
                   and self._pos_allowed(pos, rnd, counts, picks_left, top6_te_fell)]
            if not rem:
                continue
            waiver, wname = waiver_ppw(rem, last_pick, k, wire_names=wire_names)
            # a bench candidate must be VIABLE, the same test the wire applies
            # (bench.waiver_ppw): projects above 0 and is not out. Room
            # 10799518 pick 116: Josh Jacobs at 0.0 projected points and a
            # stale ADP of 49 was "scarcest" among 26 zero-insurance rows and
            # the engine named him.
            rem = [p for p in rem
                   if float(p.get("proj_pts") or 0.0) > 0.0
                   and str(p.get("avail_status") or "") != "out"]
            if not rem:
                continue
            s_map = surv_by_pos.get(pos, {})
            floor = weakest_starter.get(pos)
            for p in rem:
                hc = starter_ppw.get(str(p.get("backs_up") or ""))
                kw: dict = {}
                if hc is None and p.get("backs_up") and pos in displace_ppw:
                    st = by_name.get(str(p.get("backs_up")))
                    kw = {"contingency_weeks": ABSENT_WEEKS[pos],
                          "contingency_starter_ppw": (float(st.get("proj_pts") or 0.0) / 17.0) if st else None,
                          "my_weakest_ppw": displace_ppw[pos]}
                iv = insurance_value(p, waiver, exposure.get(pos, 0), hc,
                                     depth_ahead=depth_ahead.get(pos, 0),
                                     split_handcuff=bool(self.handcuff_split), **kw)
                s = float(s_map.get(str(p.get("sleeper_id")), 1.0))
                ins = float(iv["value_raw"])
                ceil = _ceiling(p)
                scored.append({"p": p, "iv": iv, "pos": pos, "wname": wname, "s": s, "ins": ins,
                               "score": ins if last_bench else ins * (1.0 - s),
                               "ceil": ceil,
                               "ceil_wire": None if ceil is None else ceil - waiver * FANTASY_WEEKS})
                # an upgrade rather than insurance: his own projection beats the
                # weakest starter he would displace at his position
                if floor is not None and float(p.get("proj_pts") or 0.0) > floor:
                    upgrade_ids.add(str(p.get("sleeper_id")))
        if not scored:
            return False, set()

        # "every candidate scores zero on insurance" is a materiality test, not
        # an exact one: with two reserves already held a third back covers
        # 0.0 weeks, so every back is exactly 0 while a receiver at 0.01 kept
        # 25 worthless rows inside the scarcity band (room 10799518 pick 116)
        zero = all(r["ins"] < BENCH_ZERO for r in scored)
        if zero:
            def _cw(r):
                return r["ceil_wire"] if r["ceil_wire"] is not None else -1e9
            ordered = sorted(scored, key=lambda r: -_cw(r))
            # role-shift flags break ceilings inside VARIANCE_BAND, one pass
            for i in range(len(ordered) - 1):
                a, b = ordered[i], ordered[i + 1]
                if (a["ceil_wire"] is not None and b["ceil_wire"] is not None
                        and a["ceil_wire"] - b["ceil_wire"] <= VARIANCE_BAND
                        and _role_flag(b["p"]) and not _role_flag(a["p"])):
                    ordered[i], ordered[i + 1] = b, a
            top = ordered[0]
            mode = (f"zero insurance everywhere: ceiling over the wire "
                    f"({top['ceil_wire']:.0f}" if top["ceil_wire"] is not None else "zero insurance everywhere: ceiling over the wire (none published")
            mode += ", role flag)" if _role_flag(top["p"]) else ")"
        else:
            ordered = sorted(scored, key=lambda r: (-r["score"], -r["ins"]))
            top_score = ordered[0]["score"]
            tied = [r for r in ordered if top_score - r["score"] <= BENCH_TIE]
            rest = ordered[len(tied):]
            # a man below the wire never wins a tie against one above it
            # (DECISIONS #55/#56: the widest band used to take the row)
            if any(r["ins"] >= 0.0 for r in tied):
                below = [r for r in tied if r["ins"] < 0.0]
                tied = [r for r in tied if r["ins"] >= 0.0]
                rest = below + rest
            if len(tied) == 1:
                mode = ("insurance alone (last bench pick)" if last_bench
                        else f"insurance x timing ({tied[0]['ins']:.0f} x {1.0 - tied[0]['s']:.0%})")
            else:
                by_s = sorted(tied, key=lambda r: r["s"])
                if by_s[1]["s"] - by_s[0]["s"] >= SURV_GAP - 1e-9:
                    tied = by_s
                    mode = (f"{len(by_s)} within {BENCH_TIE:g}: scarcer first "
                            f"({by_s[0]['s']:.0%} vs {by_s[1]['s']:.0%} for {by_s[1]['p'].get('player') or by_s[1]['p'].get('name')})")
                else:
                    def _ck(r):
                        # ceiling OVER THE POSITION'S WIRE, the currency the
                        # zero-insurance path uses: raw season points let a QB2
                        # (290) win every late tie against backs and receivers
                        # (120-160) by default (room 10804278 pick 114, DECISIONS
                        # #64). A published ceiling still beats none.
                        return r["ceil_wire"] if r["ceil_wire"] is not None else -1e9
                    tied = sorted(tied, key=lambda r: -_ck(r))
                    c0 = tied[0]["ceil_wire"]
                    mode = (f"{len(tied)} within {BENCH_TIE:g}, survival within {SURV_GAP:g}: "
                            + (f"higher ceiling over the wire ({c0:.0f})" if c0 is not None else "no ceiling published, insurance order"))
            ordered = tied + rest

        rows: list[tuple] = []
        for i, r in enumerate(ordered[:8]):
            p, iv, pos = r["p"], r["iv"], r["pos"]
            n = exposure.get(pos, 0)
            d = depth_ahead.get(pos, 0)
            why = (f"bench insurance: covers {n} {pos} starter{'s' if n != 1 else ''}"
                   + (f" behind {d} reserve{'s' if d != 1 else ''} already held" if d else "")
                   + f" ~{iv['weeks']:.1f} wks/season · +{iv['edge']:.1f}/wk over "
                   f"the wire ({r['wname'] or 'nobody'}) ≈ {iv['value']:.0f} pts")
            if iv["handcuff"]:
                why += f" · HANDCUFF: backs up your {p.get('backs_up')}"
            if iv.get("contingency"):
                why += (f" · +{iv['contingency']:.0f} of that is the role shift if "
                        f"{p.get('backs_up')} goes down (he would start over your weakest {pos})")
            if not last_bench:
                why += f" · timing: {r['s']:.0%} he is still there next turn -> score {r['score']:.1f}"
            if r["ceil"] is not None:
                why += f" · ceiling {r['ceil']:.0f}"
            if i == 0:
                why += f" · BENCH STAGED: {mode}"
            p["_bench_value"] = r["ins"]
            p["_staged"] = {"mode": "bench", "insurance": round(r["ins"], 1), "surv": round(r["s"], 3),
                            "score": round(r["score"], 1), "ceiling": r["ceil"]}
            rows.append((r["score"], why, p))
        # bench rows lead; the revived market rows follow as information and
        # lose the dedup to the bench row of the same player
        cands[:0] = rows
        return True, upgrade_ids

    def _apply_prefer(self, cands: list) -> list:
        """engine.prefer as a final reorder: for each [preferred, over] pair
        with both men in the list and the preferred one below, move him to
        just above the other and say so in his reason (user, 2026-09-05:
        Chase over Nacua at pick 3). Inert otherwise."""
        pairs = getattr(self, "prefer", None) or []
        if not pairs or len(cands) < 2:
            return cands
        out = list(cands)

        def _nm(row):
            return str(row[2].get("name") or row[2].get("player") or "")
        for want, over in pairs:
            iw = next((i for i, r in enumerate(out) if _nm(r) == want), None)
            io = next((i for i, r in enumerate(out) if _nm(r) == over), None)
            if iw is None or io is None or iw < io:
                continue
            row = out.pop(iw)
            row = (row[0], row[1] + f" · USER PREFERENCE: {want} over {over} (league yaml engine.prefer)", row[2])
            out.insert(io, row)
        return out

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
        self._look_through = False
        if self.turn_look_through and my_next == start:
            # the turn: no rival between this pick and my next. Price the
            # window to the turn after, the one the second pick has to survive.
            later = snake.next_pick_for_slot(start + 1, self.my_slot, self.teams, self.rounds)
            if later is not None and later > start + 1:
                # the window opens after my consecutive pick (which is mine,
                # not a rival's) and runs to the turn after
                start, my_next, self._look_through = start + 1, later, True
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
            run_boost=self.run_boost,
            recent_pos=recent_pos, markets=markets,
            need_damp=self.need_damp, qb_filled_damp=self.qb_filled_damp,
            kdef_early_damp=self.kdef_early_damp,
            qb_damp_until_round=self.qb_damp_until_round,
            kdef_typical_round=self.kdef_typical_round, run_ratio=self.run_ratio,
            autopick_sigma_scale=self.autopick_sigma_scale,
            autopick_need_damp=self.autopick_need_damp,
            autopick_list_prob=self.autopick_list_prob,
            rival_draw=self.rival_draw,
            rival_needs_update=self.rival_needs_update,
        )
        # the shown survival is the calibrated one (calibrate_survival); the
        # sim's own number stays in survival_raw for the harness
        knots = getattr(self, "survival_calibration", None) or []
        if knots and report:
            from .urgency import expected_best
            for mkt, u in report.items():
                if not (isinstance(u, dict) and isinstance(u.get("survival"), dict)):
                    continue
                u["survival"] = {k: calibrate_survival(v, knots) for k, v in u["survival"].items()}
                # The expectation and the urgency must come from the SAME
                # probabilities the stages read. Room 10802514 pick 34: the
                # calibrated survival said Javonte 23%, the raw expectation
                # still promised a 180-point back at 47, and the RB market
                # read as safe; Judkins was the back at 47. Recompute the
                # expected best with the independent walk the page uses
                # (urgency.expected_best) over the calibrated survivals; the
                # sim's own numbers stay as *_raw.
                vkey = "vorp_flex" if mkt == "FLEX" else "vorp"
                sids = [sid for sid in u["survival"] if sid in self.by_id]
                if sids:
                    vals = [self._mval(self.by_id[sid], vkey) for sid in sids]
                    e_cal = expected_best(vals, [u["survival"][sid] for sid in sids])
                    u["e_best_next_raw"] = u.get("e_best_next")
                    u["urgency_raw"] = u.get("urgency")
                    u["e_best_next"] = e_cal
                    u["urgency"] = float(u.get("best_now", 0.0) or 0.0) - e_cal
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
        # The host's roster cap per position (guardrails.position_max). Rooms
        # 10797402 and 10798461 (2026-09-05): the engine named a SEVENTH back
        # (Gainwell at 126, White at 130), Yahoo refused the thunk and the
        # click, the driver logged action-timeout then noland and fell to the
        # next name with the clock running. The cap is a room fact the engine
        # must never test.
        mx = (getattr(self, "position_max", None) or {}).get(pos)
        if mx is not None and counts.get(pos, 0) >= int(mx):
            return False
        # guardrails.earliest_round: the user's round floor per position
        # (Keefamania 2026-09-05: QB from round 4, TE from round 3, DECISIONS
        # #67). Before it the position has no market row at all.
        er = (getattr(self, "position_earliest_round", None) or {}).get(pos)
        if er is not None and rnd < int(er):
            return False
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
        # each open market's shortlist beyond its representative, for the
        # plan's runner-up rows (review 2026-09-04): the engine always had
        # these numbers and used to throw them away, leaving the page to pad
        # the list with board order
        self._market_alternates: dict[str, dict] = {}
        from .planner import own_value as _ov
        fallback = self._fallback_points(needs) if self.adaptive_fallback else None
        repl = self._replacement_points() if fallback else None
        second: dict[str, float] = {}  # per-position 2nd-best, for the planner
        urgency_of: dict[str, float] = {}   # market -> urgency, for stage 1
        for q in self.players:
            q.pop("_mkts", None)            # per-call: which markets he won this call
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
                lam = float(self.dispersion_lambda)
                relative = bool(self.upside_boost_relative)
                # The market's own floor, taken ONCE before the sort so the key
                # is stable. A boost measured FROM it is a difference, so a
                # baseline shift cancels -- the same reason urgency is immune.
                floor_v = min((mv(q) for q in gpool), default=0.0) if relative else 0.0

                def _late(q, _mv=mv, _lam=lam, _rel=relative, _floor=floor_v):
                    sd = self._dispersion_for(q)
                    if sd is not None:
                        return _mv(q) + _lam * sd            # plan A3: mean + spread
                    if not q.get("upside_flag"):
                        return _mv(q)
                    # A multiplier on a NEGATIVE market value pushed the flagged
                    # player DOWN, the opposite of the intent (review
                    # 2026-09-02). abs() fixed the sign but is NON-LINEAR, so a
                    # shift in the market's baseline (vorp vs vorp_flex, whose
                    # gap is per position: TE 38.0, WR 18.1, RB 0.0 on the
                    # 2026-09-04 Keefamania board) reorders the shortlist. Measuring the span from the market floor is a
                    # difference and cancels instead. Knob so the A/B runs.
                    span = (_mv(q) - _floor) if _rel else abs(_mv(q))
                    return _mv(q) + (self.upside_mult - 1.0) * span
                gpool = sorted(gpool, key=lambda q: -_late(q))
            pool = gpool[:3]
            if not pool:
                continue
            # The market's head: best value, near-ties (<= 2 pts of the TOP
            # candidate) broken by Δ, anchored so swaps can't chain. EVERY
            # member of the shortlist becomes a row (user, 2026-09-05): the
            # stages (value band, banded scarcity, floor/ceiling, pair) run
            # over same-position candidates too, where one representative per
            # market used to settle Chase vs Nacua on 1.6 VORP before any
            # stage ran.
            anchor = pool[0]
            head = anchor

            def _delta(q):
                # 0.0 is a real delta, not a missing one (`or -999` read it as missing)
                d = q.get("adp_delta")
                return -999.0 if d is None else float(d)
            for q in pool[1:]:
                if abs(mv(anchor) - mv(q)) <= 2.0 and _delta(q) > _delta(head):
                    head = q
            ordered = [head] + [q for q in pool if q is not head]
            self._market_alternates[mkt] = {"best": mv(head), "alts": [(q, mv(q)) for q in pool if q is not head]}
            for best in ordered:
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
              if rnd >= self.upside_from_round and (_d := self._dispersion_for(best)) is not None:
                  n = best.get("n_sources") or 0
                  sd = best.get("proj_sd")
                  if sd is not None and sd == sd and n >= 2:
                      lo, hi = best.get("proj_lo"), best.get("proj_hi")
                      span = f", {lo:.0f}-{hi:.0f}" if lo is not None and hi is not None else ""
                      parts.append(f"sources disagree by ±{sd:.0f} pts ({n} sources{span})")
                  else:
                      # naming the quantity matters: this is the forecaster's own
                      # stated range, not two feeds disagreeing
                      parts.append(f"wide forecast: the source's own range is ±{_d:.0f} pts")
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
              # the market this row was built in and its urgency, for stage 1
              # of the staged ranker (draftkit/staged.py)
              # a player can win two markets (WR and FLEX); the dedup below keeps
              # the more urgent row, so stage 1 must read THAT market, not the
              # last one written (room 10799518 pick 7: JSN read as FLEX 21.9
              # when his WR row at 43.5 was the one kept)
              best.setdefault("_mkts", {})[mkt] = float(urgency)
              urgency_of[mkt] = float(urgency)
              if u and fallback is not None and repl is not None:
                  # The sim scores a market with NO survivor at replacement
                  # (VORP 0), so a market that can empty inside the window
                  # carries a LEVEL in its urgency, not a difference, and a
                  # baseline shift leaks in by shift x P(empties). The honest
                  # alternative when the market empties is the fallback player:
                  # add P(empties) x his VORP back. A member outside the
                  # simulated window has no survival entry and is certain to
                  # survive, so then P(empties) is 0 and nothing changes.
                  surv_m = u.get("survival") or {}
                  ids = {str(q.get("sleeper_id")) for q in rem}
                  ss = [float(s) for sid_, s in surv_m.items() if sid_ in ids]
                  if ss and len(ss) == len(ids):
                      p_none = 1.0
                      for s in ss:
                          p_none *= (1.0 - s)
                      if mkt == "FLEX":
                          fbs = [fallback[q] for q in snake.FLEX_ELIGIBLE if q in fallback]
                          fb_pts = max(fbs) if fbs else None
                      else:
                          fb_pts = fallback.get(pos)
                      if fb_pts is not None and p_none > 0.0:
                          fb_vorp = fb_pts - repl.get(mkt, repl.get(pos, 0.0))
                          urgency_of[mkt] = float(urgency) - p_none * fb_vorp
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
            bench_rows, upgrade_ids = self._bench_candidates(
                cands, needs, counts, rnd, picks_left, top6_te_fell)
            if bench_rows:
                # A player can now be in the list twice (review 2026-09-02):
                # once from a market row and once insurance-priced. The two
                # scores are in INCOMMENSURABLE CURRENCIES -- market rows carry
                # urgency + 0.001*mv, bench rows carry raw season insurance
                # points -- so "keep the higher number" is not a comparison,
                # it is a coin flip between rulers. It matters because
                # _open_markets never returns empty (it revives all six
                # positional markets once every slot is full), which is exactly
                # when bench mode is also active.
                #
                # Prefer the BENCH row, because insurance is the right ruler
                # for a bench player -- EXCEPT for an upgrade, whose own
                # projection beats the starter he would displace. Insurance
                # prices a man who plays only when someone is out; an upgrade
                # plays every week, so pricing him as a backup would swap one
                # bug for a systematic undervaluation of late upgrades.
                # The choice is SYMMETRIC. Picking the bench row for a backup
                # but leaving an upgrade on whichever row happened to sort
                # first is not a rule, it is the same coin flip with an
                # exception bolted on -- and the sort puts the bench row first
                # whenever insurance out-scores urgency, which for a big-VORP
                # backup QB is most of the time (caught by the regression test
                # below, which is why it exists).
                # Since the staged bench (2026-09-05) the bench row is ALWAYS
                # the ruler for a backup and the market row for an upgrade;
                # bench_row_wins_dedupe stays registered for config
                # compatibility and no longer switches anything.
                by_id: dict[str, list] = {}
                for c in cands:
                    by_id.setdefault(c[2]["sleeper_id"], []).append(c)

                def _is_bench(row) -> bool:
                    return str(row[1]).startswith(BENCH_WHY_PREFIX)

                seen_ids: set[str] = set()
                kept: list = []
                for c in cands:
                    sid = c[2]["sleeper_id"]
                    if sid in seen_ids:
                        continue
                    seen_ids.add(sid)
                    rows = by_id[sid]
                    want_bench = sid not in upgrade_ids
                    pick = next((d for d in rows if _is_bench(d) == want_bench), None)
                    kept.append(pick if pick is not None else c)
                # ORDER, never a re-sort across the two currencies: upgrades on
                # their market row first (a man who out-projects the starter
                # he would displace is a starter question), then the bench
                # rows in staged order, then the revived market rows as
                # information.
                ups = sorted((c for c in kept if not _is_bench(c) and c[2]["sleeper_id"] in upgrade_ids),
                             key=lambda t: -t[0])
                bench = [c for c in kept if _is_bench(c)]
                others = [c for c in kept if not _is_bench(c) and c[2]["sleeper_id"] not in upgrade_ids]
                cands = ups + bench + others
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
                                  "bench depth — best remaining value. Every "
                                  "candidate was refused by the one-stash rule "
                                  "(all below replacement, no slot to fill), so "
                                  "that rule alone was waived to avoid "
                                  "recommending nothing at all", best))
            cands.sort(key=lambda t: -t[0])

        if bench_rows:
            for _sc, _w, p in cands:
                p.pop("_pair", None)   # bench mode skips the pair stage; drop stale math
                p.pop("_bench_value", None)
            return cands[:top_n]
        try:
            from .staged import staged_rank

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

            # STAGED RANKING (user design 2026-09-05): urgency picks the
            # position, value the player, then banded scarcity, variance by
            # round, and the pair last. At the turn the pair leads.
            market_of = {}
            for _s, _w, p in cands:
                won = p.get("_mkts") or {}
                market_of[str(p.get("sleeper_id"))] = (max(won, key=won.get) if won else str(p.get("pos")))
            cands = staged_rank(cands, report, needs, rnd, urgency_of, market_of, second, eligible_after,
                                fallback=fallback, repl=repl,
                                partner_certain=bool(getattr(self, "_look_through", False)),
                                tie_break=str(self.tie_break), tie_window=float(self.tie_window))
            cands = self._apply_prefer(cands)
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
