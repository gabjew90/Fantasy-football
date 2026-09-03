"""Render a mock draft's complete trail (requested 2026-09-02).

Input: the JSON the driver page POSTs to the bridge's /trail at the end of a
mock (data/logs/mocks/mock_<room>.json): every pick with team ids and
player names, the managers, and our pick records -- the engine's reason,
the best-by-projection alternative at that moment, and the candidates it
passed on. Output: reports/mocks/mock_<room>.md with

  * our picks, one block each: what we took, why, what the top projection
    available was, what the engine ranked just below;
  * every manager's picks in order and final roster;
  * the round-by-round grid.

    venv\\Scripts\\python.exe scripts\\mock_trail.py --room 10502459
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from draftkit.snake import pick_to_round_slot  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from mock_common import header_line, load_trail, report_stem, to_pt  # noqa: E402


def render(t: dict, label: str | None = None, name: str | None = None) -> str:
    picks = sorted(t.get("picks") or [], key=lambda p: int(p["pick_no"]))
    # the room size is in the dump; failing that, count the seats that picked
    teams = int(t.get("teams") or len({str(p.get("team_id")) for p in picks}) or 10)
    managers = t.get("managers") or {}
    me = str(t.get("my_team"))
    recs = {int(r["pick_no"]): r for r in (t.get("our_records") or []) if r.get("pick_no") is not None}
    mine_picks = [p for p in picks if str(p.get("team_id")) == me]
    seat = pick_to_round_slot(int(mine_picks[0]["pick_no"]), teams)[1] if mine_picks else None
    L = [f"# {header_line(t, label, name, seat, teams)}",
         "", f"Captured {to_pt(t.get('captured_at'))}. Source: the draft client's store (every pick, team ids) "
         "plus the driver's pick records (engine reason, best-by-projection alternative, candidates passed on).", ""]
    # ours
    L += ["## Our picks and what the engine passed on", ""]
    for p in picks:
        if str(p.get("team_id")) != me:
            continue
        n = int(p["pick_no"])
        r = recs.get(n)
        rnd, _slot = pick_to_round_slot(n, teams)
        L.append(f"### R{rnd} pick {n}: {p['name']} ({p['pos']})")
        if r:
            L.append(f"- via `{r.get('via', '?')}`, verified `{r.get('verified', '?')}`"
                     + (f", {r.get('ms')} ms" if r.get('ms') is not None else ""))
            L.append(f"- engine: {r.get('why') or '—'}")
            alt = r.get("top_proj_available") or {}
            if alt:
                same = " (taken)" if r.get("took_top_projection") else ""
                L.append(f"- best available by projection: {alt.get('n')} ({alt.get('p')}, {alt.get('proj')} pts, VORP {alt.get('vorp')}){same}")
            passed = r.get("passed_on") or []
            if passed:
                L.append("- passed on: " + "; ".join(f"{x['n']} ({x['p']}, VORP {x['v']}) — {x.get('why', '')}" for x in passed))
        else:
            L.append("- no driver record (made before injection, or by Yahoo's autodraft)")
        L.append("")
    # by manager
    by_team = defaultdict(list)
    for p in picks:
        by_team[str(p.get("team_id"))].append(p)
    L += ["## Every manager's picks", ""]
    for tid in sorted(by_team, key=lambda x: int(x) if str(x).isdigit() else 99):
        m = managers.get(tid) or {}
        tag = " ← us" if tid == me else ""
        L.append(f"### Team {tid} — {m.get('nickname') or '?'}{tag}"
                 + (" (away)" if m.get("away") else ""))
        L.append(", ".join(f"{p['pick_no']} {p['name']} ({p['pos']})" for p in by_team[tid]))
        counts = defaultdict(int)
        for p in by_team[tid]:
            counts[p["pos"]] += 1
        L.append("roster: " + " ".join(f"{k}{counts[k]}" for k in ("QB", "RB", "WR", "TE", "K", "DEF") if counts[k]))
        L.append("")
    # grid: cells placed by pick_no, never by list position, so a pick the
    # store dump lacks leaves a visible hole instead of shifting the row
    by_no = {int(p["pick_no"]): p for p in picks}
    rounds = (max(by_no) + teams - 1) // teams if by_no else 0
    L += ["## Round by round", "", "| round | " + " | ".join(f"pick {i}" for i in range(1, teams + 1)) + " |",
          "|---|" + "---|" * teams]
    for rnd in range(1, rounds + 1):
        cells = []
        for i in range(1, teams + 1):
            p = by_no.get((rnd - 1) * teams + i)
            if not p:
                cells.append("—")
                continue
            mark = "**" if str(p.get("team_id")) == me else ""
            cells.append(f"{mark}{p['name'].split(' ')[-1]} {p['pos']}{mark}")
        L.append(f"| {rnd} | " + " | ".join(cells) + " |")
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--room", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--label", default=None, help="e.g. 'Mock 25' -- goes into the file name and the header")
    ap.add_argument("--name", default=None, help="the room's nickname when the trail only has the tab title")
    a = ap.parse_args()
    t = load_trail(ROOT, a.room)     # pre-reload records merged in, same start time as the scrutiny report
    picks = sorted(t.get("picks") or [], key=lambda p: int(p["pick_no"]))
    teams = int(t.get("teams") or 10)
    mine = [p for p in picks if str(p.get("team_id")) == str(t.get("my_team"))]
    seat = pick_to_round_slot(int(mine[0]["pick_no"]), teams)[1] if mine else None
    out = Path(a.out) if a.out else ROOT / "reports" / "mocks" / f"{report_stem(t, a.label, a.name, seat)}_trail.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(t, a.label, a.name), encoding="utf-8")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
