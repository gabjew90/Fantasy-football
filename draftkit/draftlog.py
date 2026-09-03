"""Play-by-play draft log: every pick, plus the engine's recommendations at
each pick-state, appended as JSON lines for post-draft review.

Restart-safe by construction: on init the existing file is scanned for the
highest pick_no already logged, so a crash + relaunch never duplicates events.
Logging is best-effort — a log failure must never break the draft loop.

The recs event is also the survival-calibration record (plan 2026-09-02 B1):
every recommendation carries the engine's RAW survival, the shown survival,
and its market's best_now / e_best_next / urgency as structured fields, and
the event carries the simulation window, the knob set in force, and the
rivals' needs. Before this the calibration had to regex the English why
string, and the logged `my_next_pick` was the on-clock pick itself when I was
on the clock, so every on-clock prediction graded as "survived" — the n=67
the 0.55 shrink was fitted on was mis-scored that way.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from . import snake

# the simulation knobs recorded on every recs event (class defaults resolve
# through getattr for trackers built without __init__)
KNOBS = ("sims", "sigma_early", "sigma_late", "reach_prob", "reach_scale",
         "run_window", "run_min", "run_boost", "run_ratio",
         "need_damp", "qb_filled_damp", "kdef_early_damp", "autopick_sigma_scale",
         "survival_shrink", "pool_min", "pool_lookback", "pool_lookahead")


def sim_window(current_pick: int, my_slot: int | None, teams: int, rounds: int) -> tuple[int | None, int | None]:
    """(window_start, my_next_pick) — the rival picks the survival sim spans
    at this state. When I am ON the clock the window runs from the next pick
    to my FOLLOWING turn (mirrors Tracker.urgency_report)."""
    if not my_slot:
        return None, None
    total = teams * rounds
    _rnd, slot_on_clock = snake.pick_to_round_slot(min(current_pick, total), teams)
    start = current_pick + 1 if slot_on_clock == my_slot else current_pick
    return start, snake.next_pick_for_slot(start, my_slot, teams, rounds)


class DraftLog:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._last_pick = 0
        self._last_status: str | None = None
        self._snapped: set[int] = set()  # current_pick values with a recs snapshot
        self._snap_keys: set = set()     # snapshot() keys already written
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                # sequential, not max(): a reset event legitimately lowers the
                # high-water mark and later re-made picks must be re-logged
                if e.get("type") == "pick":
                    self._last_pick = int(e.get("pick_no", 0))
                elif e.get("type") == "recs":
                    self._snapped.add(int(e.get("current_pick", 0)))
                    if e.get("snapshot_key") is not None:
                        self._snap_keys.add(tuple(e["snapshot_key"]))
                elif e.get("type") == "reset":
                    self._last_pick = int(e.get("picks", 0))
                    self._snapped = {c for c in self._snapped if c <= self._last_pick}
                elif e.get("type") == "status":
                    self._last_status = e.get("status")

    def _append(self, event: dict) -> None:
        event["ts"] = round(time.time(), 1)
        event["at"] = time.strftime("%H:%M:%S")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def sync(self, t) -> None:
        """Append status changes, new picks, and a recs snapshot when the
        pick-state advanced. Idempotent for an unchanged tracker state."""
        try:
            self._sync(t)
        except Exception:  # noqa: BLE001 — never let logging break the draft
            pass

    def snapshot(self, t, recs, report, key) -> bool:
        """The bridge's per-state hook: log any new picks, then ONE recs event
        for this key (e.g. (current_pick, picks made)). Returns whether an
        event was written. Best-effort like sync()."""
        try:
            self._log_picks(t, with_retro=False)
            k = tuple(key) if isinstance(key, (list, tuple)) else (key,)
            if k in self._snap_keys:
                return False
            e = self._recs_event(t, len(t.state.picks) + 1, recs, reconstructed=False, report=report)
            e["snapshot_key"] = list(k)
            self._append(e)
            self._snap_keys.add(k)
            self._snapped.add(len(t.state.picks) + 1)
            return True
        except Exception:  # noqa: BLE001
            return False

    def _sync(self, t) -> None:
        status = t.state.status
        if status != self._last_status:
            self._append({"type": "status", "status": status})
            self._last_status = status
        self._log_picks(t, with_retro=(status == "drafting"))
        picks = t.state.picks
        cp = len(picks) + 1
        if status == "drafting" and cp not in self._snapped:
            recs = t.recommendations()
            self._append(self._recs_event(t, cp, recs, reconstructed=False, report=self._report(t)))
            self._snapped.add(cp)

    @staticmethod
    def _report(t):
        try:
            return t.urgency_report()
        except Exception:  # noqa: BLE001
            return None

    def _log_picks(self, t, with_retro: bool) -> None:
        picks = t.state.picks
        if len(picks) < self._last_pick:
            # commissioner pause/reset/undo: the pick list shrank. Mark it and
            # lower the high-water mark so re-made picks get logged fresh
            # (entries above the new mark are superseded history).
            self._append({"type": "reset", "picks": len(picks),
                          "note": f"pick list shrank {self._last_pick} -> {len(picks)}; "
                                  "entries above this point are superseded"})
            self._last_pick = len(picks)
            self._snapped = {c for c in self._snapped if c <= len(picks)}

        for i in range(self._last_pick, len(picks)):
            p = picks[i]
            pick_no = i + 1
            rnd, slot = snake.pick_to_round_slot(pick_no, t.teams)
            slot_val = int(p.get("draft_slot") or slot)
            my_pick = t.my_slot is not None and slot_val == t.my_slot
            # bot-burst repair: several picks can arrive in one poll, skipping
            # the live snapshot that would have preceded MY pick. State is
            # rebuildable, so reconstruct the engine's view at that moment.
            if with_retro and my_pick and pick_no not in self._snapped:
                got = self._retro_recs(t, upto=i)
                if got is not None:
                    recs, report = got
                    self._append(self._recs_event(t, pick_no, recs, reconstructed=True, report=report))
                    self._snapped.add(pick_no)
            info = t.by_id.get(str(p.get("player_id"))) or {}
            meta = p.get("metadata") or {}
            name = info.get("player") or (
                f"{meta.get('first_name', '?')} {meta.get('last_name', '')}".strip()
            )
            adp = info.get("adp")
            self._append({
                "type": "pick",
                "pick_no": pick_no,
                "round": rnd,
                "slot": slot_val,
                "my_pick": my_pick,
                "player": name,
                "pos": info.get("pos") or meta.get("position"),
                "team": info.get("team"),
                "tier": info.get("tier"),
                "vorp": info.get("vorp"),
                "adp": adp,
                "vs_adp": round(pick_no - adp, 1) if adp is not None else None,
            })
        self._last_pick = max(self._last_pick, len(picks))

    def _recs_event(self, t, current_pick: int, recs, reconstructed: bool, report=None) -> dict:
        from .planner import market_for

        teams, rounds = t.teams, t.rounds
        on_clock_slot = snake.pick_to_round_slot(min(current_pick, teams * rounds), teams)[1]
        window_start, my_next = sim_window(current_pick, t.my_slot, teams, rounds)
        needs = t.my_needs() if t.my_slot else {}
        rows = []
        for score, why, p in recs:
            row = {
                # Sleeper boards key the name as "player", the Yahoo bridge's as "name"
                "player": p.get("player") or p.get("name"), "pos": p["pos"], "tier": p.get("tier"),
                "vorp": p.get("vorp"), "score": round(score, 1), "why": why,
                "sleeper_id": str(p.get("sleeper_id")) if p.get("sleeper_id") is not None else None,
                "adp": p.get("adp"),
            }
            if report:
                mkt = market_for(p["pos"], needs)
                u = report.get(mkt) or report.get(p["pos"])
                if u:
                    sid = row["sleeper_id"]
                    row.update({
                        "market": mkt if mkt in report else p["pos"],
                        "survival": (u.get("survival_raw") or {}).get(sid),      # RAW
                        "survival_shown": (u.get("survival") or {}).get(sid),    # calibrated, displayed
                        "best_now": u.get("best_now"), "e_best_next": u.get("e_best_next"),
                        "urgency": u.get("urgency"),
                    })
            rows.append(row)
        knobs = {k: getattr(t, k, None) for k in KNOBS}
        try:
            rnd = snake.pick_to_round_slot(min(current_pick, teams * rounds), teams)[0]
            knobs["sigma_at_round"] = float(t._sigma(rnd))
        except Exception:  # noqa: BLE001
            knobs["sigma_at_round"] = None
        rivals = []
        if window_start is not None and my_next is not None:
            try:
                rivals = [{"slot": r["slot"], "needs": r["needs"], "autopick": bool(r.get("autopick", False))}
                          for r in t._rival_states(window_start, my_next)]
            except Exception:  # noqa: BLE001
                rivals = []
        e = {
            "type": "recs",
            "survival_shrink": float(getattr(t, "survival_shrink", 1.0)),
            "current_pick": current_pick,
            "on_clock_slot": on_clock_slot,
            "window_start": window_start,
            "my_next_pick": my_next,
            "knobs": knobs,
            "rivals": rivals,
            "away_slots": sorted(int(s) for s in (getattr(t, "away_slots", None) or ())),
            "recommendations": rows,
        }
        if reconstructed:
            e["reconstructed"] = True
        return e

    def _retro_recs(self, t, upto: int):
        """Engine view (recs, urgency report) with only the first `upto` picks
        made; restores state. The report is captured WHILE rewound."""
        saved_picks = t.state.picks
        saved_ids = t.state.drafted_ids
        saved_cache = t._urgency_cache
        try:
            t.state.picks = saved_picks[:upto]
            t.state.drafted_ids = {str(p["player_id"]) for p in t.state.picks}
            t._urgency_cache = None
            recs = t.recommendations()
            return recs, self._report(t)
        except Exception:  # noqa: BLE001 — a failed retro must not break logging
            return None
        finally:
            t.state.picks = saved_picks
            t.state.drafted_ids = saved_ids
            t._urgency_cache = saved_cache
