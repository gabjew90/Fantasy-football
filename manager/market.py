"""FantasyCalc market values, matched to the league's own format.

The second opinion on every trade. Projections say what a player is expected
to SCORE; this says what the market currently CHARGES for him, and the two
disagree in ways that change answers. On 2026-09-08 the projection consensus
priced Derrick Henry 4.5 points above Saquon Barkley while the market had
Saquon 554 clear of him, and rated Tucker Kraft above Harold Fannin where the
consensus had it the other way round -- which flipped a trade verdict from
"do not send" to "send".

Neither number is the truth. A disagreement between them is the signal: it
says the market is paying for something the projection does not model (age,
role change, name), or that the projection knows something the market has not
priced yet. Both cases are actionable and neither is visible from one source.

PARAMETER SURFACE, measured against the live API on 2026-09-08. The endpoint
SILENTLY IGNORES parameters it does not know -- a bogus key returns byte
identical values -- so every knob here was verified to actually move numbers
before being wired up:

    numQbs       HUGE.   1 -> 2 moves values +59% on average (superflex
                         revalues the whole board around quarterbacks).
    isDynasty    Changes the universe: 199 redraft rows, 423 dynasty.
    ppr          Small on average (1 -> 0.5 is -1.3%) but up to 50% on an
                 individual pass-catcher, which is exactly who trades turn on.
    numTeams     Small (12 -> 10 is -0.9%) and real.

    teMultiplier   IGNORED -- identical values to a bogus parameter.
    numStarters    IGNORED -- likewise.

So there is no TE-premium support to expose, however much a TE-premium league
would want it. Do not add the knob; it would be a lie in the config.

Coverage is the top ~199 redraft players, so a deep-wire free agent has no
market value and `price` reports how many pieces it could not see rather than
scoring them as zero.
"""

from __future__ import annotations

import logging
import time as _time
from typing import NamedTuple

import requests

log = logging.getLogger("manager")

BASE = "https://api.fantasycalc.com/values/current"
TTL = 24 * 3600

# roster tokens that mean "a quarterback can start here" (draftkit.onboard
# uses the same list when it derives baselines)
SUPERFLEX_SLOTS = ("SUPER_FLEX", "SUPERFLEX", "Q/W/R/T", "OP")


class Format(NamedTuple):
    teams: int
    ppr: float
    qbs: int
    dynasty: bool

    def params(self) -> dict:
        return {"isDynasty": "true" if self.dynasty else "false",
                "numQbs": self.qbs, "numTeams": self.teams, "ppr": self.ppr}

    def label(self) -> str:
        return (f"{self.teams}-team, {self.ppr:g} PPR, "
                f"{'superflex' if self.qbs > 1 else '1QB'}"
                f"{', dynasty' if self.dynasty else ''}")


def _cfg_get(cfg, *keys, default=None):
    """cfg is a dict-like that may also be an object; expected: nests."""
    exp = (cfg.get("expected") if hasattr(cfg, "get") else None) or {}
    for k in keys:
        for src in (cfg, exp):
            try:
                v = src.get(k)
            except AttributeError:
                v = None
            if v is not None:
                return v
    return default


def league_format(ctx) -> Format:
    """The FantasyCalc query shape, derived from the league rather than assumed.

    Hardcoding this to 12-team full PPR is a defect that already shipped once
    (fixed 2026-09-07): Keefamania is 10-team half-PPR and was being priced on
    Omnibeta's market with no error raised anywhere.
    """
    cfg = ctx.get("cfg") or {}
    teams = len(ctx.get("rosters") or []) or int(_cfg_get(cfg, "teams", default=12) or 12)

    scoring = _cfg_get(cfg, "scoring", default={}) or {}
    ppr = float(scoring.get("rec", 1.0))

    # Prefer the live slot map; fall back to the roster token list, which is
    # what a league built from yaml alone (no Sleeper context) carries.
    slots = ctx.get("slots") or {}
    qbs = 2 if any(int(slots.get(s, 0)) for s in SUPERFLEX_SLOTS) else 1
    if qbs == 1:
        roster = _cfg_get(cfg, "roster", "roster_positions", default=[]) or []
        tokens = {str(s).upper().replace(" ", "") for s in roster}
        if tokens & {s.replace(" ", "") for s in SUPERFLEX_SLOTS}:
            qbs = 2

    dynasty = bool(_cfg_get(cfg, "dynasty", default=False))
    return Format(int(teams), ppr, int(qbs), dynasty)


def fetch(store, ctx) -> tuple[dict[str, dict], str | None]:
    """sleeper_id -> the market row. Cached per format for TTL."""
    fmt = league_format(ctx)
    ckey = f"fantasycalc:{fmt.teams}:{fmt.ppr}:{fmt.qbs}:{int(fmt.dynasty)}"
    cached = store.get(ckey) if store is not None else None
    if cached and _time.time() - cached.get("ts", 0) < TTL:
        return cached["data"], None
    try:
        resp = requests.get(BASE, params=fmt.params(), timeout=20)
        resp.raise_for_status()
        data = {}
        for row in resp.json():
            sid = (row.get("player") or {}).get("sleeperId")
            if not sid:
                continue
            data[str(sid)] = {
                "value": int(row.get("value") or 0),
                "overall": row.get("overallRank"),
                "pos_rank": row.get("positionRank"),
                "trend30": row.get("trend30Day"),
                "rostered": row.get("maybeRosterPercent"),
                "trade_freq": row.get("maybeTradeFrequency"),
                "age": (row.get("player") or {}).get("maybeAge"),
                "pos": (row.get("player") or {}).get("position"),
            }
        if store is not None:
            store.set(ckey, {"ts": _time.time(), "data": data})
        # `note` is the WARNING channel, not provenance: trade_radar.build
        # renders any note it gets with a warning marker, so a chatty success
        # message would print as a problem. Callers that want the format on
        # the record ask league_format(ctx).label() -- it is stateless and
        # needs no fetch.
        return data, None
    except Exception as e:  # noqa: BLE001
        if cached:
            return (cached["data"],
                    "DATA MISSING: FantasyCalc refresh failed — using cached values")
        return {}, f"DATA MISSING: FantasyCalc values ({e.__class__.__name__})"


def values(store, ctx) -> tuple[dict[str, int], str | None]:
    """sleeper_id -> value only, the shape the trade radar body consumes."""
    rows, note = fetch(store, ctx)
    return {k: int(v.get("value") or 0) for k, v in rows.items()}, note


def _vid(p) -> str:
    return str(p["sleeper_id"] if isinstance(p, dict) else p)


def price(vals: dict[str, int], give, get) -> dict:
    """Market cost of a package. Reports coverage instead of hiding gaps.

    A player outside the top ~199 has no row. Scoring him as 0 would make
    every deal involving the deep wire look like a steal, so the unpriced
    pieces are counted and named and the caller decides.
    """
    def side(players):
        total, missing = 0, []
        for p in players:
            v = vals.get(_vid(p))
            if v is None:
                missing.append(p.get("name", _vid(p)) if isinstance(p, dict) else _vid(p))
            else:
                total += int(v)
        return total, missing

    out, miss_out = side(give)
    inn, miss_in = side(get)
    delta = inn - out
    return {"out": out, "in": inn, "delta": delta,
            "pct": round(100.0 * delta / out, 1) if out else None,
            "unpriced": miss_out + miss_in}


def annotate(pkg: dict) -> str:
    """One line for a brief."""
    if not pkg or (pkg["out"] == 0 and pkg["in"] == 0):
        return ""
    s = f"market {pkg['out']} out / {pkg['in']} in ({pkg['delta']:+d}"
    s += f", {pkg['pct']:+.0f}%)" if pkg["pct"] is not None else ")"
    if pkg["unpriced"]:
        s += f" · unpriced: {', '.join(pkg['unpriced'][:3])}"
    return s
