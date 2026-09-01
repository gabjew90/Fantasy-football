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


if __name__ == "__main__":
    main()
