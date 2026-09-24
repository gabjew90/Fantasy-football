"""Source: market-implied expected fantasy points from Sleeper Picks prop lines.

Migrated from the nfl-fantasy-research skill's scripts/market_points.py on
2026-09-24. The conversions are unchanged; what changed is where it reads
(core.fetch), how it scores (core.scoring and the league yaml, not a private
three-preset table), and one scoring fix:

  A QUARTERBACK'S ANYTIME TD IS A RUSHING TD. The skill priced it as a passing
  TD (4 points). The anytime market pays when the player himself scores, which
  for a QB is a rush (or a rare catch) worth 6, so every QB total was 2 points
  per expected score too low.

WHY A POSTED LINE IS A LEGITIMATE PROJECTION. It is a consensus with money
behind it, and early in a season it carries role information no public model
has. Used naively it misleads in three ways, each handled here:
  1. A LINE IS A MEDIAN, NOT A MEAN. Fantasy pays the mean and per-game
     yardage is right-skewed. The two-sided price locates the market's median
     relative to the line; the shape table (fantasy/resources/
     market_shape_params.json, fitted 2024-25, holdout-checked) converts it.
  2. RECEPTIONS ARE DISCRETE. P(catches <= 3.5) is P(catches <= 3); a negative
     binomial is solved on the integer CDF.
  3. AN ANYTIME-TD PRICE IS P(AT LEAST ONE). Fantasy pays per TD:
     lambda = -ln(1 - p) under a Poisson assumption.

It is a mean-only source with partial coverage: a player is only as complete
as his posted markets (`detail["markets"]`). A missing market is a zero, so a
player with fewer props is understated and is flagged `partial`. No passing-TD
market is posted, so a QB total is always partial.

This is context for a fantasy decision, never a betting output: a projection
built from the book's own line has no edge against that book.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from core import fetch as F
from core.scoring import score

from ..contract import WEEK, Projection, SourceResult, fantasy_position, validate

NAME = "market_points"
PARAMS_PATH = Path(__file__).resolve().parent.parent / "resources" / "market_shape_params.json"

# Sleeper wager_type -> our stat key
WAGER = {"receiving_yards": "rec_yds", "receptions": "catches",
         "rushing_yards": "rush_yds", "passing_yards": "pass_yds",
         "anytime_touchdowns": "anytime_td"}
PG = {"WR": "WR", "TE": "TE", "RB": "RB", "QB": "QB", "FB": "RB"}
# Bins are on the MEDIAN, not the mean (see the params file's method note).
BINS = {"rec_yds": [2, 10, 25, 45, 70, 1e9], "catches": [0.5, 1.5, 3, 5, 1e9],
        "rush_yds": [2, 10, 30, 60, 1e9], "pass_yds": [50, 180, 230, 270, 1e9]}
THIN_PLAYERS = 12
RATIO_SPREAD = 0.15
# every market a skill player can have; anything short of this is `partial`
FULL_BOARD = {"QB": {"pass_yds", "rush_yds", "anytime_td"},
              "RB": {"rush_yds", "rec_yds", "catches", "anytime_td"},
              "WR": {"rec_yds", "catches", "anytime_td"},
              "TE": {"rec_yds", "catches", "anytime_td"}}


def amer(mult) -> int:
    m = float(mult)
    return int(round((m - 1) * 100)) if m >= 2 else int(round(-100 / (m - 1)))


def implied(price) -> float:
    p = float(price)
    return 100 / (p + 100) if p > 0 else -p / (-p + 100)


def devig(p_over: float, p_under: float) -> tuple[float, float]:
    """Two-sided proportional de-vig. Sleeper runs ~12% overround per leg."""
    s = p_over + p_under
    return (p_over / s, p_under / s) if s > 0 else (p_over, p_under)


# ---------------------------------------------------------- distributions

def gamma_cdf(x: float, shape: float) -> float:
    """Regularized lower incomplete gamma P(shape, x), series / continued fraction."""
    if x <= 0:
        return 0.0
    if x < shape + 1:
        term = 1.0 / shape
        s = term
        for n in range(1, 500):
            term *= x / (shape + n)
            s += term
            if abs(term) < abs(s) * 1e-12:
                break
        return s * math.exp(-x + shape * math.log(x) - math.lgamma(shape))
    b, c, d, h = x + 1 - shape, 1e300, 1.0 / (x + 1 - shape), 1.0 / (x + 1 - shape)
    for i in range(1, 500):
        an = -i * (i - shape)
        b += 2
        d = an * d + b
        if abs(d) < 1e-300:
            d = 1e-300
        c = b + an / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1) < 1e-12:
            break
    return 1 - math.exp(-x + shape * math.log(x) - math.lgamma(shape)) * h


def gamma_ppf(q: float, shape: float) -> float:
    lo, hi = 1e-9, max(50.0, shape * 40)
    for _ in range(200):
        mid = (lo + hi) / 2
        if gamma_cdf(mid, shape) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def nbinom_cdf(k: float, mu: float, r: float) -> float:
    """P(X <= k), negative binomial with mean mu and dispersion r (var = mu + mu^2/r)."""
    if k < 0:
        return 0.0
    p = r / (r + mu)
    term = p ** r
    s = term
    for i in range(1, int(k) + 1):
        term *= (r + i - 1) / i * (1 - p)
        s += term
    return min(s, 1.0)


def level_bin(stat: str, med: float) -> int:
    b = BINS[stat]
    if med < b[0]:
        return 0
    for i in range(len(b) - 1):
        if b[i] <= med < b[i + 1]:
            return i
    return len(b) - 2


def shape_row(params: dict, stat: str, pos: str, med: float):
    pg = PG.get(pos)
    if pg is None:
        return None, None
    i = level_bin(stat, med)
    for j in (i, i - 1, i + 1):                   # exact bin, then the nearest populated one
        key = f"{stat}|{pg}|{j}"
        if key in params:
            return params[key], key
    return None, None


def bin_flag(row: dict, key: str) -> list[str]:
    """Say when a ratio rests on thin or season-unstable evidence instead of hiding it."""
    f = []
    if row.get("n_players", 99) < THIN_PLAYERS:
        f.append(f"{key} thin ({row['n_players']} player-seasons)")
    r24, r25 = row.get("ratio_2024"), row.get("ratio_2025")
    if r24 and r25 and abs(r24 - r25) > RATIO_SPREAD:
        f.append(f"{key} ratio unstable ({r24:.2f} vs {r25:.2f} across seasons)")
    elif row.get("seasons", 2) < 2:
        f.append(f"{key} one season only")
    return f


def market_mean_continuous(params, stat, pos, line, q_under):
    """The market's mean for a continuous stat: fit a gamma of the local shape to
    the book's no-vig under probability at `line` (its median), then scale by the
    empirical mean/median ratio. The bin depends on the answer, so iterate."""
    median = line
    row = key = None
    for _ in range(3):
        row, key = shape_row(params, stat, pos, median)
        if row is None:
            return None, None, ["no shape row for this position"]
        shape = row["gamma_shape"]
        z = gamma_ppf(min(max(q_under, 1e-4), 1 - 1e-4), shape)
        if z <= 0:
            return None, key, ["degenerate quantile"]
        scale = line / z
        median = gamma_ppf(0.5, shape) * scale
    return median * row["mean_over_median"], key, bin_flag(row, key)


def market_mean_count(params, stat, pos, line, q_under):
    """The market's mean for a count stat, solved on the integer CDF."""
    k = math.floor(line)                           # P(X <= 3.5) == P(X <= 3)
    row, key = shape_row(params, stat, pos, line)
    if row is None:
        return None, None, ["no shape row for this position"]
    var_z = row["var_z"]
    lo, hi = 0.05, 20.0
    for _ in range(60):
        mid = (lo + hi) / 2
        var = (mid ** 2) * var_z
        r = mid ** 2 / max(var - mid, 1e-6) if var > mid else 1e6
        if nbinom_cdf(k, mid, r) > q_under:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2, key, bin_flag(row, key)


# ------------------------------------------------------------- the source

def stat_line(comp: dict, pos: str, scoring: dict) -> dict:
    """Market components -> a Sleeper-keyed stat line for core.scoring.

    Expected TDs go to the stat the player would score them in: a receiver's
    catch, a back's or a quarterback's run (a QB's anytime TD is his own score,
    not a pass). A back's receiving TDs are scored as rushing; the two carry
    the same points in every league here."""
    line = {"rec_yd": comp.get("rec_yds", 0.0), "rec": comp.get("catches", 0.0),
            "rush_yd": comp.get("rush_yds", 0.0), "pass_yd": comp.get("pass_yds", 0.0)}
    td_key = "rec_td" if pos in ("WR", "TE") else "rush_td"
    line[td_key] = comp.get("etd", 0.0)
    if pos == "TE" and "bonus_rec_te" in scoring:     # tight-end premium, per catch
        line["bonus_rec_te"] = comp.get("catches", 0.0)
    return line


def collect_markets(lines: list, players: dict) -> dict:
    """Two-sided pre-game Sleeper markets per Sleeper id."""
    book = {}
    for m in lines or []:
        if m.get("sport") != "nfl" or m.get("wager_type") not in WAGER \
                or m.get("line_type", "normal") != "normal":
            continue
        opts = m.get("options") or []
        if not opts or opts[0].get("game_status") != "pre_game":
            continue
        pid = str(m.get("subject_id") or "")
        info = players.get(pid) or {}
        if not pid or not info:
            continue
        over = next((o for o in opts if o.get("outcome") == "over" and o.get("status") == "active"), None)
        under = next((o for o in opts if o.get("outcome") == "under" and o.get("status") == "active"), None)
        if over is None or under is None:          # one-sided: cannot de-vig
            continue
        rec = book.setdefault(pid, {"pos": fantasy_position(info),
                                    "team": opts[0].get("subject_team") or info.get("team"),
                                    "game": m.get("game_id"), "updated_ms": 0, "markets": {}})
        rec["updated_ms"] = max(rec["updated_ms"], int(m.get("updated_at") or 0))
        po, pu = devig(implied(amer(over["payout_multiplier"])), implied(amer(under["payout_multiplier"])))
        rec["markets"][WAGER[m["wager_type"]]] = {
            "line": None if m["wager_type"] == "anytime_touchdowns" else float(over["outcome_value"]),
            "p_over": po, "p_under": pu}
    return book


def from_markets(book: dict, scoring: dict, params: dict) -> SourceResult:
    out = SourceResult(source=NAME, horizon=WEEK)
    for pid, r in book.items():
        pos, comp, flags = r["pos"], {}, []
        for stat, mk in r["markets"].items():
            if stat == "anytime_td":
                comp["etd"] = -math.log(max(1 - mk["p_over"], 1e-6))   # expected TDs, not P(>=1)
                comp["td_p"] = mk["p_over"]
                continue
            fn = market_mean_count if stat == "catches" else market_mean_continuous
            mu, key, f = fn(params, stat, pos, mk["line"], mk["p_under"])
            if mu is None:
                flags.append(f"{stat}: {'; '.join(f)}")
                continue
            flags += [f"{stat}: {x}" for x in f]
            comp[stat] = mu
            comp[stat + "_line"] = mk["line"]
        have = sorted(s for s in ("rec_yds", "catches", "rush_yds", "pass_yds") if s in comp) \
            + (["anytime_td"] if "etd" in comp else [])
        missing = sorted(FULL_BOARD.get(pos, set()) - set(have))
        partial = bool(missing) or pos == "QB"
        out.projections[pid] = validate(Projection(
            player_id=pid, source=NAME, horizon=WEEK,
            mean=round(score(stat_line(comp, pos, scoring), scoring), 2),
            detail={"pos": pos, "team": r["team"], "game": r["game"], "markets": have,
                    "missing_markets": missing + (["pass_td (never posted)"] if pos == "QB" else []),
                    "partial": partial, "flags": flags, "updated_ms": r["updated_ms"],
                    "components": {k: round(v, 3) for k, v in comp.items() if isinstance(v, float)}}))
    if not out.projections:
        out.available = False
        out.notes.append("no two-sided Sleeper Picks lines are posted for these players")
    return out


def load_params(path: Path = PARAMS_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))["params"]


def project(scoring: dict, *, cache_dir=None, manifest=None) -> SourceResult:
    lines = json.loads(F.sleeper_lines(cache_dir=cache_dir, manifest=manifest).read_text(encoding="utf-8"))
    players = json.loads(F.sleeper_players(cache_dir=cache_dir, manifest=manifest).read_text(encoding="utf-8"))
    return from_markets(collect_markets(lines, players), scoring, load_params())
