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
    reach_prob = 0.15
    reach_scale = 3.0
    run_window = 5
    run_min = 2
    run_boost = 1.5
    survival_shrink = 0.55
    upside_from_round = 8
    upside_mult = 1.15
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
            counts: dict[str, int] = {}
            for slotname in (str(x).upper() for x in (exp.get("roster") or [])):
                key = "FLEX" if slotname in ("W/R/T", "W/R", "FLEX", "WRT") else slotname
                if key != "IR":
                    counts[key] = counts.get(key, 0) + 1
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
        ecfg = cfg["engine"] if "engine" in cfg._data else {}
        self.sims = int(ecfg.get("sims", 1000))
        # rolling ADP window for the rival sampling pool (post-v2 item 1);
        # pool_size is retained as the FLOOR so old configs stay meaningful
        self.pool_min = int(ecfg.get("pool_min", ecfg.get("pool_size", 40)))
        self.pool_lookback = int(ecfg.get("pool_lookback", 20))
        self.pool_lookahead = int(ecfg.get("pool_lookahead", 60))
        self.sigma_early = float(ecfg.get("sigma_early", 6.0))
        self.sigma_late = float(ecfg.get("sigma_late", 27.0))
        # v2 item 1.1: fat-tail reaches, run escalation, empirical calibration
        self.reach_prob = float(ecfg.get("reach_prob", Tracker.reach_prob))
        self.reach_scale = float(ecfg.get("reach_scale", Tracker.reach_scale))
        self.run_window = int(ecfg.get("run_window", Tracker.run_window))
        self.run_min = int(ecfg.get("run_min", Tracker.run_min))
        self.run_boost = float(ecfg.get("run_boost", Tracker.run_boost))
        self.survival_shrink = float(ecfg.get("survival_shrink", Tracker.survival_shrink))
        # v2 item 1.5: round-dependent objective
        self.upside_from_round = int(ecfg.get("upside_from_round", Tracker.upside_from_round))
        self.upside_mult = float(ecfg.get("upside_mult", Tracker.upside_mult))
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

    def slot_positions(self, slot: int) -> list[str]:
        out = []
        for p in self.picks_for_slot(slot):
            pos = (p.get("metadata") or {}).get("position")
            if not pos:
                info = self.by_id.get(str(p["player_id"]))
                pos = info["pos"] if info else "?"
            out.append({"DST": "DEF"}.get(pos, pos))
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
        if not self.my_slot:
            return []
        nxt = snake.next_pick_for_slot(self.current_pick, self.my_slot, self.teams, self.rounds)
        if nxt is None:
            return []
        return [
            s
            for s in snake.slots_picking_between(self.current_pick, nxt, self.teams)
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
            })
        return out

    def _sigma(self, rnd: int) -> float:
        e, late = self.sigma_early, self.sigma_late
        return e + (late - e) * (rnd - 1) / max(1, self.rounds - 1)

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
        lo, hi = cur - self.pool_lookback, cur + self.pool_lookahead
        window = [p for p in avail
                  if p.get("adp") is not None and lo <= p["adp"] <= hi]
        if len(window) < self.pool_min:
            # floor: never starve — extend by ADP proximity to the window
            window = avail[: max(self.pool_min, len(window))]
        pool = window
        # crc32, not hash(): string hash is per-process randomized and would
        # let a mid-draft restart silently flip near-tie recommendations
        seed = zlib.crc32(f"{self.draft_id}:{key[0]}:{key[1]}".encode())
        rng = np.random.default_rng(seed)
        recent_pos = [str((p.get("metadata") or {}).get("position") or "")
                      for p in picks[-self.run_window:]]
        report = simulate_survival(
            pool, start, my_next, self._rival_states(start, my_next), self.rival_seeds,
            rng, sims=self.sims, sigma=self._sigma(rnd), teams=self.teams,
            reach_prob=self.reach_prob, reach_scale=self.reach_scale,
            run_window=self.run_window, run_min=self.run_min,
            run_boost=self.run_boost, survival_shrink=self.survival_shrink,
            recent_pos=recent_pos,
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
        second: dict[str, float] = {}  # per-position 2nd-best VORP, for the planner
        for pos in POS_ORDER:
            rem = [p for p in self.remaining(pos) if p.get("proj_source") != "no_market"]
            second[pos] = float(rem[1]["vorp"] or 0.0) if len(rem) > 1 else 0.0
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
                from .planner import slot_vorp as _sv
                gpool = sorted(
                    gpool,
                    key=lambda q: -(_sv(q, needs)
                                    * (self.upside_mult if q.get("upside_flag") else 1.0)))
            pool = gpool[:3]
            if not pool:
                continue
            # best VORP within position; near-ties (<= 2 VORP of the position's
            # TOP candidate) broken by Δ — anchored so swaps can't chain
            anchor = pool[0]
            best = anchor
            for q in pool[1:]:
                if abs((anchor["vorp"] or 0) - (q["vorp"] or 0)) <= 2.0 and (
                    (q.get("adp_delta") or -999) > (best.get("adp_delta") or -999)
                ):
                    best = q
            u = report.get(pos) if report else None
            urgency = u["urgency"] if u else (best["vorp"] or 0.0)
            # rationale: plain-English clauses, all from already-computed draft
            # state (no model calls on the clock, per spec §9)
            parts = []
            if u:
                if urgency >= 1.0:
                    parts.append(
                        f"waiting likely costs ~{urgency:.0f} pts "
                        f"(best {pos} now {u['best_now']:.0f}, ~{u['e_best_next']:.0f} "
                        f"by your next turn)"
                    )
                else:
                    parts.append(f"safe to wait at {pos}")
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
            same_tier = sum(1 for q in rem if q["tier"] == best["tier"])
            next_tier = next((q["tier"] for q in rem if q["tier"] > best["tier"]), None)
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
            if rnd >= self.upside_from_round and best.get("upside_flag"):
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
            # Slot-conditional: a candidate headed for the FLEX is worth
            # vorp_flex, not vorp. Without this a second elite TE carries his
            # full positional VORP into a slot he shares with RB/WR.
            from .planner import slot_vorp
            score = urgency + 0.001 * slot_vorp(best, needs)  # stable ordering
            cands.append((score, why, best))
        cands.sort(key=lambda t: -t[0])
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

            cands = pair_rank(cands, report, needs, second, eligible_after)
        except Exception as e:  # noqa: BLE001 — planner must never block the clock
            # fall back to greedy, but never silently: a dead planner on draft
            # day must be visible (code review 2026-08-30)
            import logging
            logging.getLogger("draftkit").warning("two-pick planner fallback: %r", e)
            self._planner_note = f"planner fallback: {e.__class__.__name__}"
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
