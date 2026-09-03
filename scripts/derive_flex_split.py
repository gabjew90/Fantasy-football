"""Derive the flex-demand split from the board (plan 2026-09-02 A4).

onboard.derive_baselines spreads each FLEX slot over RB/WR/TE by a fixed
45/45/10 heuristic. The split is a LEAGUE fact: it depends on how many
starters the league's dedicated slots already remove and on how many flex
slots remain, so it is derived per league and stored in that league's yaml
(`flex_split:`), never copied between leagues.

The walk: remove the top teams x slots[pos] players at RB, WR and TE by
projected points (the dedicated starters), then fill teams x FLEX slots
greedily from what is left. The position mix of those flex starters is the
split. Ties break on name so two runs agree.

    venv\\Scripts\\python.exe scripts\\derive_flex_split.py --league keefamania
    venv\\Scripts\\python.exe scripts\\derive_flex_split.py --league keefamania --export reports/flex_split.keefamania.json
    venv\\Scripts\\python.exe scripts\\derive_flex_split.py --league keefamania --write      # persists flex_split: into leagues/keefamania.yaml
    venv\\Scripts\\python.exe scripts\\derive_flex_split.py --league keefamania --board data/draftrig/ref_external.keefamania.csv   # sensitivity read
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import engine_parity as EP  # noqa: E402
from draftkit.config import Config  # noqa: E402
from draftkit.snake import FLEX_ELIGIBLE  # noqa: E402

FLEX_POS = tuple(p for p in ("RB", "WR", "TE") if p in FLEX_ELIGIBLE)


def flex_walk(board: list[dict], teams: int, slots: dict[str, int], key: str = "proj_pts") -> dict:
    """{shares, counts, n_flex, last: {pos: name of the last flex starter}}.
    A league with no FLEX slot returns zero shares (nothing to split)."""
    n_flex = int(teams * slots.get("FLEX", 0))
    by_pos = {pos: sorted((p for p in board if p.get("pos") == pos),
                          key=lambda p: (-float(p.get(key) or 0.0), p.get("name", "")))
              for pos in FLEX_POS}
    leftover = []
    for pos in FLEX_POS:
        leftover += by_pos[pos][int(teams * slots.get(pos, 0)):]
    leftover.sort(key=lambda p: (-float(p.get(key) or 0.0), p.get("name", "")))
    flex = leftover[:n_flex]
    counts = Counter(p["pos"] for p in flex)
    shares = {pos: (counts[pos] / n_flex if n_flex else 0.0) for pos in FLEX_POS}
    last = {}
    for pos in FLEX_POS:
        mine = [p for p in flex if p["pos"] == pos]
        if mine:
            last[pos] = mine[-1].get("name", "")
    return {"shares": shares, "counts": dict(counts), "n_flex": n_flex, "last": last}


def yaml_block(shares: dict[str, float], board_name: str, derived: str) -> str:
    L = ["flex_split:            # derived by scripts/derive_flex_split.py (plan A4); a league fact, re-derive, never copy"]
    L += [f"  {pos}: {shares[pos]:.3f}" for pos in FLEX_POS]
    L += [f"  derived: {derived}", f"  board: {board_name}"]
    return "\n".join(L) + "\n"


_BLOCK = re.compile(r"^flex_split:[^\n]*\n(?:[ \t]+[^\n]*\n?)*", re.M)


def write_split(yaml_path: Path, block: str) -> str:
    """Replace an existing top-level `flex_split:` block, or append one.
    Text-level on purpose: the league yamls carry comments a round trip
    through a yaml library would drop. Returns 'replaced' or 'appended'."""
    text = yaml_path.read_text(encoding="utf-8")
    if _BLOCK.search(text):
        new, how = _BLOCK.sub(lambda _m: block, text, count=1), "replaced"
    else:
        sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
        new, how = text + sep + block, "appended"
    yaml_path.write_text(new, encoding="utf-8")
    return how


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", required=True)
    ap.add_argument("--board", default=None, help="tiers csv (default: the league's scoped tiers.csv)")
    ap.add_argument("--export", default=None)
    ap.add_argument("--write", action="store_true", help="persist flex_split: into leagues/<league>.yaml")
    a = ap.parse_args()
    cfg = Config.load(league=a.league)
    teams, _rounds, slots = EP.league_shape(cfg)
    board_path = Path(a.board) if a.board else cfg.scoped(Path("tiers.csv"))
    if not board_path.exists():
        raise SystemExit(f"{board_path} missing: build the board first (python -m draftkit --league {a.league} tiers)")
    board = EP.load_board(str(board_path))
    res = flex_walk(board, teams, slots)
    sh = res["shares"]
    print(f"{a.league}: {teams} teams, dedicated RB {slots.get('RB', 0)} WR {slots.get('WR', 0)} TE {slots.get('TE', 0)}, "
          f"FLEX {slots.get('FLEX', 0)} -> {res['n_flex']} flex starters from {board_path.name}")
    print("  split: " + "  ".join(f"{pos} {sh[pos]:.3f} ({res['counts'].get(pos, 0)})" for pos in FLEX_POS))
    print("  last flex starter: " + "; ".join(f"{pos} {n}" for pos, n in res["last"].items()))
    out = {"league": a.league, "teams": teams, "slots": slots, "board": board_path.name,
           "derived": dt.date.today().isoformat(), **res}
    if a.export:
        Path(a.export).parent.mkdir(parents=True, exist_ok=True)
        Path(a.export).write_text(json.dumps(out, indent=1), encoding="utf-8")
        print(f"-> {a.export}")
    if a.write:
        ypath = ROOT / "leagues" / f"{a.league}.yaml"
        how = write_split(ypath, yaml_block(sh, board_path.name, out["derived"]))
        print(f"flex_split {how} in {ypath.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
