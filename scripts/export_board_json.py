"""Export a league board to a compact JSON the in-page draft driver can hold.

The driver runs entirely inside the Yahoo page: no Python round-trip per pick.
That is what keeps us resident (autopick never arms) and keeps the queue
re-ranked against the CURRENT roster instead of the roster at queue time.
"""
from __future__ import annotations

import argparse
import csv
import json
import unicodedata
from pathlib import Path

SUFFIX = {"jr", "sr", "ii", "iii", "iv", "v"}


def norm(name: str) -> str:
    s = unicodedata.normalize("NFKD", name or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return "".join(c for c in s.lower() if c.isalnum() or c == " ").strip()


def key(name: str) -> str:
    """first-initial + last name, suffix-stripped: matches Yahoo's 'J. Gibbs'."""
    parts = [p for p in norm(name).split() if p]
    if not parts:
        return ""
    parts = [p for p in parts if p.rstrip(".") not in SUFFIX] or parts
    if len(parts) == 1:
        return parts[0]
    return parts[0][0] + " " + parts[-1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rows = list(csv.DictReader(open(a.board, encoding="utf-8")))
    out = []
    for r in rows:
        pos = (r.get("pos") or "").upper()
        if not pos:
            continue
        try:
            vorp = float(r.get("vorp") or 0.0)
        except ValueError:
            vorp = 0.0
        try:
            proj = float(r.get("proj_pts") or 0.0)
        except ValueError:
            proj = 0.0
        try:
            adp = float(r.get("adp") or 0.0) or None
        except ValueError:
            adp = None
        out.append({
            "n": r.get("player", ""),
            "k": key(r.get("player", "")),
            "p": pos,
            "t": (r.get("team") or "").upper(),
            "v": round(vorp, 1),
            "j": round(proj, 1),
            "a": adp,
            "s": (r.get("avail_status") or "")[:12],
            "u": (r.get("upside_flag") or "").lower() == "true",
            "tier": r.get("tier") or "",
        })
    out.sort(key=lambda x: -x["v"])
    Path(a.out).write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {len(out)} players -> {a.out}")
    for r in out[:5]:
        print(f"  {r['n']:22} {r['p']:3} {r['t']:4} vorp={r['v']:6.1f} key={r['k']}")

    # Collisions: players the Yahoo row text cannot tell apart by
    # initial+surname+position+team. Mock 2 queued Brian Robinson Jr. thinking
    # it was Bijan Robinson (both "b robinson", ATL, RB). ADP separates them,
    # so the driver needs it -- but a pair with near-identical ADP would be
    # genuinely ambiguous and must be surfaced, not silently mis-drafted.
    seen: dict = {}
    for r in out:
        seen.setdefault((r["k"], r["p"], r["t"]), []).append(r)
    clashes = {k: v for k, v in seen.items() if len(v) > 1}
    if clashes:
        print(f"\n{len(clashes)} NAME COLLISION(S) -- ADP must separate these:")
        for (k, p, t), group in clashes.items():
            adps = [f"{g['n']} (adp {g['a']}, vorp {g['v']})" for g in group]
            print(f"  {k} {p} {t}: " + " vs ".join(adps))
            gap = [g["a"] for g in group if g["a"] is not None]
            if len(gap) == len(group) and len(gap) > 1:
                if max(gap) - min(gap) < 25:
                    print("    !! ADP gap under 25 -- NOT separable, fix by hand")


if __name__ == "__main__":
    main()
