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


# -------------------------------------------------------------- rank panel

def rank_panel(ctx, store=None) -> tuple[dict[str, dict], list[str]]:
    """sleeper_id -> {overall, positional, pos, panel, source}. Plus notes.

    The rank view the slot-based acceptance test reads (plan:
    docs/plans/2026-09-09-slot-based-trades-plan.md). OVERALL rank is the
    test's scale -- a WR4 against an RB13 is undecidable on positional rank
    and plain on the overall board -- and positional is carried for display,
    because "RB13 over RB27" is how a person reads a seat.

    Source order: the FantasyPros draft panel (~149 experts) while it is
    fresh, else the DynastyProcess mirror of the same consensus (a few days
    behind, no panel size published). ONE SCALE PER RUN: if FantasyPros
    carries anyone, the mirror is not consulted for the rest, because a
    WR4 on one panel against an RB13 on another is not a comparison. Every
    row says which source and carries the panel size, so a three-expert ROS
    rank can never be read as agreement.
    """
    from . import consensus as C, fantasypros as fp

    notes: list[str] = []
    cfg = ctx["cfg"]
    scoring = C._scoring(cfg)
    season = (ctx.get("state") or {}).get("season") or ctx.get("season")
    index = ctx.get("players")

    # WHICH OVERALL BOARD. "OP" is the superflex list, quarterbacks on top;
    # "ALL" is the one-QB list. A one-QB league reading OP would carry every
    # QB at a rank inflated by 50 or more into the acceptance test.
    slots = ctx.get("slots") or {}
    flex_sets = ctx.get("flex_slots") or ()
    superflex = int(slots.get("QB", 0) or 0) >= 2 or any("QB" in set(fs) for fs in flex_sets)
    board = fp.OVERALL_SUPERFLEX if superflex else fp.OVERALL_ONE_QB
    ov, n1 = fp.overall(scoring, season, index, kind=fp.DRAFT, store=store,
                        position=board)
    pos_rows, n2 = fp.fetch(scoring, season, index, kind=fp.DRAFT, store=store)
    for n in (n1, n2):
        if n:
            notes.append(n)

    out: dict[str, dict] = {}
    if ov:
        for pid, r in ov.items():
            pr = pos_rows.get(pid) or {}
            out[pid] = {"overall": r["overall"], "positional": pr.get("ecr"),
                        "pos": r["pos"], "panel": r.get("panel"),
                        "source": "fantasypros draft", "list": r.get("list")}
        return out, notes

    mirror, note = by_sleeper_id(ctx)
    if note:
        notes.append(note)
    for pid, r in (mirror or {}).items():
        if r.get("overall") is None:
            continue
        out[pid] = {"overall": r["overall"], "positional": r.get("ecr"),
                    "pos": r.get("pos"), "panel": None,
                    "source": f"dynastyprocess mirror {r.get('as_of') or ''}".strip(),
                    "list": "ro"}
    if out:
        notes.append("⚠ rank panel from the DynastyProcess mirror: the FantasyPros "
                     "draft feed was unavailable, and the mirror publishes no "
                     "panel size")
    else:
        notes.append("DATA MISSING: no rank panel reachable")
    return out, notes
