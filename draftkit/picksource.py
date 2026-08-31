"""Local pick source for drafts without a pollable API (Yahoo leagues).

One JSON file is the single source of truth for the pick sequence. Writers:
the dashboard's manual-entry mode (clicks/POSTs) and/or the browser poller
script (idempotent full replace). Reader: the Tracker. Snake order turns a
bare ordered list of "who just got drafted" into full pick records — no
other input is ever needed.

Unresolved names still occupy their pick slot (the draft advances even when
a name misses our board); they resolve as unknown:<norm> with the raw name
carried in metadata so the UI shows what was typed.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import snake

SUFFIXES = re.compile(r"\s+(jr\.?|sr\.?|i{2,4}|iv|v)$", re.IGNORECASE)


def norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", SUFFIXES.sub("", (name or "").strip().lower()))


class LocalDraft:
    def __init__(self, path: Path, board: list[dict], teams: int, rounds: int):
        self.path = Path(path)
        self.teams, self.rounds = int(teams), int(rounds)
        self._by_norm: dict[str, list[dict]] = {}
        for p in board:
            self._by_norm.setdefault(norm(p["player"]), []).append(p)
        self._mtime: float | None = None
        self._picks_cache: list[dict] = []

    # -- file ------------------------------------------------------------
    def _read(self) -> dict:
        if not self.path.exists():
            return {"picks": []}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except ValueError:
            return {"picks": []}
        data.setdefault("picks", [])
        return data

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=1), encoding="utf-8")

    # -- writers ---------------------------------------------------------
    def add_pick(self, name: str, pos: str | None = None) -> dict:
        data = self._read()
        if len(data["picks"]) >= self.teams * self.rounds:
            return {"ok": False, "error": "draft is complete"}
        entry: dict = {"name": (name or "").strip()}
        if not entry["name"]:
            return {"ok": False, "error": "empty name"}
        if pos:
            entry["pos"] = pos
        rid = self.resolve(entry)
        taken = {self.resolve(e)["sleeper_id"] for e in data["picks"]}
        if rid["sleeper_id"] in taken:
            return {"ok": False, "error": f"{rid['player']} is already drafted"}
        data["picks"].append(entry)
        self._write(data)
        return {"ok": True, "pick_no": len(data["picks"]), "resolved": rid["player"],
                "matched": not rid["sleeper_id"].startswith("unknown:")}

    def undo(self) -> dict:
        data = self._read()
        if not data["picks"]:
            return {"ok": False, "error": "nothing to undo"}
        dropped = data["picks"].pop()
        self._write(data)
        return {"ok": True, "removed": dropped.get("name")}

    def set_picks(self, names: list[str]) -> None:
        """Poller path: idempotent full replace of the pick sequence."""
        data = self._read()
        data["picks"] = [{"name": n} for n in names][: self.teams * self.rounds]
        self._write(data)

    # -- reader ----------------------------------------------------------
    def resolve(self, entry: dict) -> dict:
        name = entry.get("name", "")
        # strip trailing ALL-CAPS status tags Yahoo appends (Q, CEL, PUP, IR-R)
        parts = name.strip().split()
        while len(parts) > 1 and parts[-1].isupper() and len(parts[-1]) <= 4:
            parts.pop()
        name = " ".join(parts)
        cand = self._by_norm.get(norm(name)) or []
        pos = entry.get("pos")
        if not cand and len(parts) > 1 and len(parts[0].rstrip(".")) == 1:
            # abbreviated Yahoo feed form ("J. Gibbs"): first initial + surname
            initial = parts[0][0].lower()
            last = norm(" ".join(parts[1:]))
            cand = [c for group in self._by_norm.values() for c in group
                    if c["player"].lower().lstrip()[0] == initial
                    and norm(" ".join(c["player"].split()[1:])).startswith(last)]
        if pos and len(cand) > 1:
            cand = [c for c in cand if c["pos"] == pos] or cand
        if cand:
            c = cand[0]
            return {"sleeper_id": str(c["sleeper_id"]), "player": c["player"],
                    "pos": c["pos"]}
        return {"sleeper_id": f"unknown:{norm(entry.get('name', '?')) or '?'}",
                "player": entry.get("name", "?"), "pos": pos or "?"}

    def picks(self) -> list[dict]:
        """Sleeper-shaped pick dicts (mtime-cached, cheap to poll)."""
        try:
            mt = self.path.stat().st_mtime
        except OSError:
            mt = None
        if mt is not None and mt == self._mtime:
            return self._picks_cache
        out = []
        for i, e in enumerate(self._read()["picks"][: self.teams * self.rounds]):
            r = self.resolve(e)
            rnd, slot = snake.pick_to_round_slot(i + 1, self.teams)
            first, _, last = r["player"].partition(" ")
            out.append({"player_id": r["sleeper_id"], "pick_no": i + 1,
                        "round": rnd, "draft_slot": slot,
                        "metadata": {"position": r["pos"], "first_name": first,
                                     "last_name": last}})
        self._mtime, self._picks_cache = mt, out
        return out

    def status(self) -> str:
        return "complete" if len(self.picks()) >= self.teams * self.rounds \
            else "drafting"
