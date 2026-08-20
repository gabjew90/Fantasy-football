"""Play-by-play draft log: every pick, plus the engine's recommendations at
each pick-state, appended as JSON lines for post-draft review.

Restart-safe by construction: on init the existing file is scanned for the
highest pick_no already logged, so a crash + relaunch never duplicates events.
Logging is best-effort — a log failure must never break the draft loop.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from . import snake


class DraftLog:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._last_pick = 0
        self._last_status: str | None = None
        self._snapped: set[int] = set()  # current_pick values with a recs snapshot
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

    def _sync(self, t) -> None:
        status = t.state.status
        if status != self._last_status:
            self._append({"type": "status", "status": status})
            self._last_status = status

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
            if my_pick and status == "drafting" and pick_no not in self._snapped:
                recs = self._retro_recs(t, upto=i)
                if recs is not None:
                    self._append(self._recs_event(t, pick_no, recs, reconstructed=True))
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

        cp = len(picks) + 1
        if status == "drafting" and cp not in self._snapped:
            self._append(self._recs_event(t, cp, t.recommendations(), reconstructed=False))
            self._snapped.add(cp)

    def _recs_event(self, t, current_pick: int, recs, reconstructed: bool) -> dict:
        my_next = (
            snake.next_pick_for_slot(current_pick, t.my_slot, t.teams, t.rounds)
            if t.my_slot else None
        )
        e = {
            "type": "recs",
            "current_pick": current_pick,
            "on_clock_slot": snake.pick_to_round_slot(
                min(current_pick, t.teams * t.rounds), t.teams
            )[1],
            "my_next_pick": my_next,
            "recommendations": [
                {
                    "player": p["player"], "pos": p["pos"], "tier": p["tier"],
                    "vorp": p["vorp"], "score": round(score, 1), "why": why,
                }
                for score, why, p in recs
            ],
        }
        if reconstructed:
            e["reconstructed"] = True
        return e

    def _retro_recs(self, t, upto: int):
        """Engine view with only the first `upto` picks made; restores state."""
        saved_picks = t.state.picks
        saved_ids = t.state.drafted_ids
        saved_cache = t._urgency_cache
        try:
            t.state.picks = saved_picks[:upto]
            t.state.drafted_ids = {str(p["player_id"]) for p in t.state.picks}
            t._urgency_cache = None
            return t.recommendations()
        except Exception:  # noqa: BLE001 — a failed retro must not break logging
            return None
        finally:
            t.state.picks = saved_picks
            t.state.drafted_ids = saved_ids
            t._urgency_cache = saved_cache
