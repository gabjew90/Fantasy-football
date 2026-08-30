"""CLV retro: score a completed draft against closing ADP (v2 plan item 0.1).

CLV (closing line value) = closing ADP - pick slot. Positive = the market
would have let you wait; negative = a reach past the market price. The first
out-of-sample measurement of the engine, and the survival-prediction scoring
is the calibration input for v2 item 1.1.

Generalized to any draft_id with a play-by-play log at
data/logs/draft_<id>.jsonl. Usage:
    python scripts/clv_retro.py [--draft-id ID] [--adp PATH] [--out PATH]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from draftkit.config import Config  # noqa: E402

SUFFIXES = re.compile(r"\s+(jr\.?|sr\.?|i{2,4}|iv|v)$", re.IGNORECASE)
SURV = re.compile(r"(\d+)% chance he'?s still there")


def norm(name: str) -> str:
    n = SUFFIXES.sub("", name.strip().lower())
    return re.sub(r"[^a-z0-9]", "", n)


def latest_snapshot_before(hist_dir: Path, date: str) -> Path | None:
    snaps = sorted(p for p in hist_dir.glob("adp_*.json")
                   if p.stem.replace("adp_", "") < date)
    return snaps[-1] if snaps else None


def load_log(path: Path) -> tuple[list[dict], list[dict]]:
    events = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]
    picks = [e for e in events if e["type"] == "pick"]
    recs = [e for e in events if e["type"] == "recs"
            and isinstance(e.get("current_pick"), int)]
    return picks, recs


def survival_calibration(picks: list[dict], recs: list[dict]) -> list[dict]:
    """(player, my_next_pick) -> last predicted survival %, vs outcome."""
    picked_at = {norm(p["player"]): p["pick_no"] for p in picks}
    preds: dict[tuple[str, int], int] = {}
    for e in recs:
        nxt = e.get("my_next_pick")
        if not isinstance(nxt, int):
            continue
        for r in e.get("recommendations", []):
            m = SURV.search(r.get("why", ""))
            if m:
                preds[(norm(r["player"]), nxt)] = int(m.group(1))
    rows = []
    for (player, nxt), pct in preds.items():
        at = picked_at.get(player)
        survived = at is None or at >= nxt
        rows.append({"player": player, "next": nxt, "pred": pct, "survived": survived})
    return rows


def main() -> int:
    cfg = Config.load()
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft-id", default=str(cfg["draft_id"]))
    ap.add_argument("--adp", default=None, help="ADP snapshot json (name/pos/adp rows)")
    ap.add_argument("--draft-date", default="2026-08-23",
                    help="used to pick the last snapshot strictly BEFORE this date")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    log_path = Path(cfg.path("logs")) / f"draft_{args.draft_id}.jsonl"
    picks, recs = load_log(log_path)

    if args.adp:
        snap = Path(args.adp)
    else:
        snap = latest_snapshot_before(Path(cfg.path("raw")) / "adp_history",
                                      args.draft_date)
    if snap is None:
        print("no ADP snapshot found before the draft date")
        return 1
    adp_rows = json.loads(snap.read_text(encoding="utf-8"))
    adp = {norm(r["name"]): float(r["adp"]) for r in adp_rows}

    slots_users = {}  # draft slot -> display label (slot N if unknown)
    scored, unmatched = [], []
    for p in picks:
        a = adp.get(norm(p["player"]))
        if a is None:
            unmatched.append(p["player"])
            continue
        scored.append({**p, "adp": a, "clv": round(a - p["pick_no"], 1)})
        slots_users.setdefault(p["slot"], f"slot {p['slot']}")

    my_slot = int(cfg["me"].get("draft_slot") or 2)
    mine = [p for p in scored if p["slot"] == my_slot]
    my_avg = sum(p["clv"] for p in mine) / len(mine) if mine else 0.0

    by_slot = defaultdict(list)
    for p in scored:
        by_slot[p["slot"]].append(p)

    calib = survival_calibration(picks, recs)
    buckets = {"50-69": [], "70-89": [], "90-100": []}
    for r in calib:
        key = "50-69" if r["pred"] < 70 else ("70-89" if r["pred"] < 90 else "90-100")
        buckets[key].append(r)

    out = Path(args.out or f"reports/clv_omnibeta_{cfg['season']}.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    L = [f"# CLV retro — draft {args.draft_id}",
         "",
         f"Closing ADP: `{snap.name}` (last FFC pull before {args.draft_date}; "
         f"~1 day stale vs draft start — noted per plan amendment C).",
         f"Matched {len(scored)}/{len(picks)} picks against the ADP pool "
         f"({len(unmatched)} unmatched: late K/DEF and deep fliers outside FFC's top "
         f"{len(adp_rows)}).",
         "",
         f"## My draft (slot {my_slot})",
         f"**Average CLV: {my_avg:+.1f} picks** (positive = market would have let me wait)",
         ""]
    for p in mine:
        L.append(f"- r{p.get('round'):>2} #{p['pick_no']:>3} {p['player']:<24} "
                 f"ADP {p['adp']:>5.1f} → CLV {p['clv']:+.1f}")
    L += ["", "## Per-rival reach profiles (avg CLV, most negative = reachiest)", ""]
    for slot, ps in sorted(by_slot.items(), key=lambda kv: sum(x["clv"] for x in kv[1]) / len(kv[1])):
        avg = sum(p["clv"] for p in ps) / len(ps)
        worst = min(ps, key=lambda p: p["clv"])
        L.append(f"- slot {slot:>2}: avg {avg:+.1f} over {len(ps)} picks · biggest reach "
                 f"{worst['player']} ({worst['clv']:+.1f})")
    L += ["", "## 10 biggest reaches league-wide", ""]
    for p in sorted(scored, key=lambda p: p["clv"])[:10]:
        L.append(f"- #{p['pick_no']:>3} slot {p['slot']:>2}: {p['player']:<24} "
                 f"ADP {p['adp']:.1f} ({p['clv']:+.1f})")
    L += ["", "## 10 biggest values league-wide", ""]
    for p in sorted(scored, key=lambda p: -p["clv"])[:10]:
        L.append(f"- #{p['pick_no']:>3} slot {p['slot']:>2}: {p['player']:<24} "
                 f"ADP {p['adp']:.1f} ({p['clv']:+.1f})")
    L += ["", "## Survival-prediction calibration (engine said -> reality)", "",
          "| predicted bucket | n | predicted avg | actual survival |",
          "|---|---|---|---|"]
    for k, rows in buckets.items():
        if rows:
            pavg = sum(r["pred"] for r in rows) / len(rows)
            actual = sum(r["survived"] for r in rows) / len(rows)
            L.append(f"| {k}% | {len(rows)} | {pavg:.0f}% | {actual:.0%} |")
    L += ["", "These rows are the empirical calibration map for v2 item 1.1.", ""]
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {out}")
    print(f"my avg CLV {my_avg:+.1f} | rivals scored: {len(by_slot)} slots | "
          f"calibration pairs: {len(calib)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
