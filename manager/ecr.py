"""Expert consensus ranks, and the range the panel actually spans.

Every projection source publishes ONE number per player. FantasyPros polls a
panel and publishes the most and least optimistic rank in it, which is a real
ceiling rather than the spread between two models arguing about a mean.

That distinction decides bench adds. A bench player only ever enters your
lineup when he breaks out, so his median is close to irrelevant and his
ceiling is the whole question. Ranking stash candidates on rest-of-season
mean -- which is what the waiver brief did until 2026-09-08 -- systematically
prefers the safe 128 over the volatile 105 whose best case is far higher.

Worked example from that day. Kayshon Boutte's mean beat Dontayvion Wicks',
so the brief preferred Boutte. But the panel's most bullish expert has Wicks
at WR46 and Boutte at WR50, so Wicks is the better dart and the mean said the
opposite. Both, incidentally, ceilinged out below the WORST case for the
players they would have replaced.

Source: the DynastyProcess mirror of FantasyPros ECR, free and unmetered,
refreshed a few times a week. `best` and `worst` are RANKS, so lower is
better and the arithmetic runs backwards from points all the way through.
"""

from __future__ import annotations

import csv
import io
import logging
import time as _time

import requests

log = logging.getLogger("manager")

URL = "https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_fpecr_latest.csv"
TTL = 12 * 3600
# 'rp' = redraft positional (WR37), 'ro' = redraft overall (WR37 -> 81st).
# Positional is what a start/sit or stash decision actually turns on.
POSITIONAL, OVERALL = "rp", "ro"


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def fetch(store=None) -> tuple[dict[str, dict], str | None]:
    """normalised name -> {ecr, best, worst, sd, pos, overall, as_of}."""
    if store is not None:
        cached = store.get("ecr")
        if cached and _time.time() - cached.get("ts", 0) < TTL:
            return cached["data"], None
    try:
        resp = requests.get(URL, timeout=30)
        resp.raise_for_status()
        rows = list(csv.DictReader(io.StringIO(resp.text)))
    except Exception as e:  # noqa: BLE001
        return {}, f"DATA MISSING: expert ranks ({e.__class__.__name__})"

    from draftkit.ids import normalize_name
    out: dict[str, dict] = {}
    for r in rows:
        kind = (r.get("ecr_type") or "").strip()
        if kind not in (POSITIONAL, OVERALL):
            continue
        nm = normalize_name(r.get("player") or "")
        if not nm:
            continue
        rec = out.setdefault(nm, {"pos": (r.get("pos") or "").upper(),
                                  "as_of": r.get("scrape_date")})
        if kind == POSITIONAL:
            rec.update({"ecr": _num(r.get("ecr")), "best": _num(r.get("best")),
                        "worst": _num(r.get("worst")), "sd": _num(r.get("sd"))})
        else:
            rec["overall"] = _num(r.get("ecr"))
    out = {k: v for k, v in out.items() if v.get("best") is not None}
    if store is not None:
        store.set("ecr", {"ts": _time.time(), "data": out})
    return out, None


def by_sleeper_id(ctx, store=None) -> tuple[dict[str, dict], str | None]:
    """sleeper_id -> the panel record, matched on name within position."""
    table, note = fetch(store)
    if not table:
        return {}, note
    from draftkit.ids import normalize_name
    out = {}
    for pid, d in (ctx.get("players") or {}).items():
        if not isinstance(d, dict):
            continue
        nm = d.get("full_name") or d.get("last_name")
        if not nm:
            continue
        rec = table.get(normalize_name(nm))
        # position must agree, or "Josh Allen" the linebacker inherits the QB
        if rec and rec.get("pos") == (d.get("position") or "").upper():
            out[str(pid)] = rec
    as_of = next((v.get("as_of") for v in out.values() if v.get("as_of")), None)
    return out, (f"expert ranks {as_of}" if as_of else note)


def annotate(rec: dict | None) -> str:
    """The inline suffix a brief shows. Ranks, so lower is better."""
    if not rec or rec.get("best") is None:
        return ""
    return (f" · experts {rec['pos']}{rec['ecr']:.0f}"
            f" (best {rec['pos']}{rec['best']:.0f}, worst {rec['pos']}{rec['worst']:.0f})")


def ceiling_beats(add: dict | None, drop: dict | None) -> bool:
    """Does the incoming player's BEST case beat the outgoing player's?

    The check the brief was missing. A stash is only worth a roster spot if
    its good outcome is better than the good outcome you already hold.
    """
    if not add or not drop or add.get("best") is None or drop.get("best") is None:
        return False
    if add.get("pos") != drop.get("pos"):
        return False
    return add["best"] < drop["best"]          # ranks: lower is better
