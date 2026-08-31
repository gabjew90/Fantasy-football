"""Daily ADP diff: the market's own news detector.

A player whose ADP moved 15+ picks in ~48 hours is the market reacting to
news; the diff is a pre-built "find out why" list for the night-before
research pass. Dumb by design: one API call, dated snapshots, a diff.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

DEFAULT_THRESHOLD = 15.0
MAX_LOOKBACK_DAYS = 4


def diff_snapshots(old: list[dict], new: list[dict], threshold: float = DEFAULT_THRESHOLD) -> list[dict]:
    """Movers >= threshold picks, plus entrants/dropouts of the ADP pool."""
    old_by = {r["name"]: r for r in old}
    new_by = {r["name"]: r for r in new}
    movers = []
    for name, r in new_by.items():
        if name in old_by:
            delta = round(r["adp"] - old_by[name]["adp"], 1)
            if abs(delta) >= threshold:
                movers.append({
                    "name": name, "pos": r["pos"], "adp": r["adp"], "delta": delta,
                    "kind": "riser" if delta < 0 else "faller",
                })
        else:
            movers.append({"name": name, "pos": r["pos"], "adp": r["adp"],
                           "delta": None, "kind": "entered"})
    for name, r in old_by.items():
        if name not in new_by:
            movers.append({"name": name, "pos": r["pos"], "adp": r["adp"],
                           "delta": None, "kind": "left"})
    movers.sort(key=lambda m: -(abs(m["delta"]) if m["delta"] is not None else 0))
    return movers


def run(cfg, threshold: float = DEFAULT_THRESHOLD) -> dict:
    """Fetch fresh ADP, snapshot it, diff vs the newest prior snapshot."""
    from .market import FFC_URL, _cached_fetch

    hist_dir = Path(cfg.path("raw")) / "adp_history"
    hist_dir.mkdir(parents=True, exist_ok=True)

    mcfg = cfg.get("market") or {}
    url = FFC_URL.format(fmt=str(mcfg.get("ffc_format", "ppr")),
                         teams=int(mcfg.get("teams", 12)), year=int(cfg["season"]))
    fresh = json.loads(_cached_fetch(url, hist_dir / "_latest_pull.json", ttl=0))
    rows = [{"name": r["name"], "pos": r["position"], "adp": float(r["adp"])}
            for r in fresh.get("players", [])]

    today = time.strftime("%Y-%m-%d")
    (hist_dir / f"adp_{today}.json").write_text(json.dumps(rows), encoding="utf-8")

    prior = sorted(p for p in hist_dir.glob("adp_*.json") if p.stem != f"adp_{today}")
    result = {"date": today, "players": len(rows), "movers": [], "baseline": None}
    if prior:
        base = prior[-1]
        age_days = (time.time() - base.stat().st_mtime) / 86400
        if age_days <= MAX_LOOKBACK_DAYS:
            old_rows = json.loads(base.read_text(encoding="utf-8"))
            result["movers"] = diff_snapshots(old_rows, rows, threshold)
            result["baseline"] = base.stem.replace("adp_", "")

    lines = [f"# ADP movers — {today}",
             f"\nBaseline: {result['baseline'] or 'none (first snapshot)'} | "
             f"threshold: {threshold} picks | pool: {len(rows)} players\n"]
    for m in result["movers"]:
        if m["kind"] in ("riser", "faller"):
            arrow = "↑" if m["kind"] == "riser" else "↓"
            lines.append(f"- {arrow} **{m['name']}** ({m['pos']}) ADP {m['adp']:.1f} "
                         f"({'+' if m['delta'] > 0 else ''}{m['delta']}) — find out why")
        else:
            verb = "ENTERED the ADP pool" if m["kind"] == "entered" else "LEFT the ADP pool"
            lines.append(f"- **{m['name']}** ({m['pos']}) {verb} (ADP {m['adp']:.1f})")
    if not result["movers"]:
        lines.append("- no movers past threshold" if result["baseline"]
                     else "- first snapshot recorded; diffs start tomorrow")
    (Path(cfg.root) / "reports" / "adp_movers.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    return result
