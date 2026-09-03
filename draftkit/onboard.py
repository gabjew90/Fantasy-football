"""Generate leagues/<name>.yaml from a live Sleeper league (v2 amendment A).

Baselines are DERIVED from the league's format — teams x starting slots x
flex demand — never copied from another league. Superflex slots count as
QB demand.

The flex-demand split (plan 2026-09-02 A4) resolves in this order:
  1. the league yaml's own `flex_split:` block, written by
     scripts/derive_flex_split.py from that league's board (a league fact);
  2. FLEX_SPLIT_BY_FORMAT[format_key(scoring)] when scoring is known but no
     board exists yet (straight after `onboard`);
  3. the legacy FLEX_SPLIT heuristic (45/45/10) for callers that pass neither.
"""

from __future__ import annotations

import re
from pathlib import Path

from .bench import ABSENT_WEEKS, BYE_WEEKS, FANTASY_WEEKS
from .sleeper import BASE, get_json

FLEX_SPLIT = {"RB": 0.45, "WR": 0.45, "TE": 0.10}     # legacy heuristic, kept for no-scoring callers
# Frozen from scripts/derive_flex_split.py on 2026-09-02 (the walk: remove the
# dedicated starters by projected points, fill the flex slots greedily):
#   half: Keefamania model board, 10 teams x 1 W/R/T -> RB 8 / WR 2 / TE 0 of
#         10 (last flex starters Jadarian Price, Emeka Egbuka); the external
#         board reads RB 6 / WR 4 -- a 0.2 sensitivity, stated not hidden.
#   full: Omnibeta model board, 12 teams x 2 FLEX -> RB 8 / WR 16 / TE 0 of 24
#         (Aaron Jones Sr., Chris Godwin Jr.); external board RB 6 / WR 18.
# TE never reaches a flex slot on either board once the TE1s are gone.
FLEX_SPLIT_BY_FORMAT = {
    "half": {"RB": 0.80, "WR": 0.20, "TE": 0.00},
    "full": {"RB": 0.333, "WR": 0.667, "TE": 0.00},
}
BENCH_ALLOWANCE_POSITIONS = ("RB", "WR")


def format_key(scoring: dict | None) -> str:
    """'full' when a reception is worth a point or more, else 'half' -- the
    consensus.adp_key rule (standard scoring folds into half here; no
    standard-scoring board has been derived)."""
    rec = float((scoring or {}).get("rec", 0) or 0)
    return "full" if rec >= 1 else "half"


def bench_allowance_factor(pos: str) -> float:
    """Expected starters absent per week at `pos` = insurance depth a roster
    actually holds: 1 + (absent weeks + bye) / fantasy weeks, from
    draftkit.bench's position base rates. 1.0 outside RB/WR."""
    if pos not in BENCH_ALLOWANCE_POSITIONS:
        return 1.0
    return 1.0 + (ABSENT_WEEKS[pos] + BYE_WEEKS) / FANTASY_WEEKS


def resolve_flex_split(scoring: dict | None = None, flex_split: dict | None = None) -> dict[str, float]:
    """The resolution order in the module docstring. A yaml block carries
    `derived`/`board` alongside the shares; only the shares are used."""
    if flex_split:
        shares = {pos: float(flex_split.get(pos, 0.0) or 0.0) for pos in ("RB", "WR", "TE")}
        if sum(shares.values()) > 0:
            return shares
    if scoring is not None:
        return dict(FLEX_SPLIT_BY_FORMAT[format_key(scoring)])
    return dict(FLEX_SPLIT)
# Sleeper writes "FLEX"; Yahoo writes "W/R/T". Both are the same slot, and a
# name this function does not recognise is silently dropped from demand --
# which quietly cost every Yahoo league its whole flex allocation (RB20 rather
# than RB24 on a 10-team roster). Found 2026-09-01.
FLEX_NAMES = ("FLEX", "W/R/T", "WRT", "W/R/T/QB", "R/W/T", "W/T")
REC_FLEX_NAMES = ("REC_FLEX", "WRRB_FLEX", "W/R", "R/W")
# roster slots that are never filled during a draft and carry no demand
NON_DEMAND = ("BN", "BENCH", "IR", "IR+", "NA", "TAXI")
# pool depth beyond the replacement baseline, per position
POOL_PAD = {"QB": 16, "RB": 25, "WR": 20, "TE": 16, "K": 4, "DEF": 4}


def slot_counts(roster_positions: list[str], split: dict[str, float] | None = None,
                bench_allowance: bool = False) -> tuple[dict[str, float], int]:
    """Positional starter demand (flex spread by `split`, FLEX_SPLIT when
    None) + bench size. `bench_allowance` multiplies RB/WR demand by
    bench_allowance_factor: the starters a roster expects to have absent in
    a given week, which it covers from the bench."""
    split = split or FLEX_SPLIT
    demand: dict[str, float] = {p: 0.0 for p in ("QB", "RB", "WR", "TE", "K", "DEF")}
    bench = 0
    unknown: list[str] = []
    for slot in roster_positions:
        s = str(slot).upper().strip()
        if s in demand:
            demand[s] += 1
        elif s in FLEX_NAMES:
            for pos, share in split.items():
                demand[pos] += share
        elif s in ("SUPER_FLEX", "SUPERFLEX", "Q/W/R/T", "OP"):
            demand["QB"] += 0.8          # superflex is a QB slot in practice
            demand["RB"] += 0.1
            demand["WR"] += 0.1
        elif s in REC_FLEX_NAMES:
            for pos in ("WR", "RB"):
                demand[pos] += 0.5
        elif s in ("BN", "BENCH"):
            bench += 1
        elif s in NON_DEMAND:
            pass
        else:
            unknown.append(s)
    if unknown:
        # loud, not silent: an unrecognised STARTING slot understates demand
        # and therefore the baseline, and the failure is invisible downstream
        raise ValueError(
            f"unrecognised roster slots {sorted(set(unknown))} — add them to "
            "onboard.py (FLEX_NAMES / NON_DEMAND) rather than letting them "
            "drop out of positional demand")
    if bench_allowance:
        for pos in BENCH_ALLOWANCE_POSITIONS:
            demand[pos] *= bench_allowance_factor(pos)
    return demand, bench


def derive_baselines(teams: int, roster_positions: list[str], scoring: dict | None = None,
                     flex_split: dict | None = None, bench_allowance: bool = False) -> dict[str, int]:
    """Replacement level = league-wide startable demand, rounded, floored at
    one per team for K/DEF and at teams for onesie positions. With neither
    `scoring` nor `flex_split` the legacy 45/45/10 split applies, so the
    older callers are byte-identical."""
    split = resolve_flex_split(scoring, flex_split)
    demand, _bench = slot_counts(roster_positions, split, bench_allowance)
    out = {}
    for pos, d in demand.items():
        n = round(teams * d)
        out[pos] = max(n, teams if d > 0 else 0)
    return out


def derive_pool_sizes(baselines: dict[str, int]) -> dict[str, int]:
    return {pos: b + POOL_PAD.get(pos, 10) for pos, b in baselines.items() if b}


def onboard(league_id: str, username: str, name: str | None = None,
            root: Path = Path(".")) -> Path:
    lg = get_json(f"{BASE}/league/{league_id}")
    if not lg:
        raise SystemExit(f"league {league_id} not found on Sleeper")
    teams = int(lg["settings"].get("num_teams") or len(lg.get("roster_positions", [])) or 12)
    positions = lg.get("roster_positions") or []
    scoring = lg.get("scoring_settings") or {}
    split = resolve_flex_split(scoring)          # by-format fallback: no board exists yet
    baselines = derive_baselines(teams, positions, scoring=scoring)
    pools = derive_pool_sizes(baselines)
    rounds = sum(1 for s in positions if s.upper() != "IR")
    slug = name or re.sub(r"[^a-z0-9]+", "-", str(lg.get("name", league_id)).lower()).strip("-")
    ppr = float(scoring.get("rec", 0))

    y = [
        f"# {lg.get('name', '?')} — generated by `draftkit onboard` from live settings.",
        f"# {teams} teams · rec={ppr} · roster: {' '.join(positions)}",
        "# Baselines DERIVED from format (v2 amendment A) — verify then adjust.",
        "",
        f'league_id: "{league_id}"',
        f'draft_id: "{lg.get("draft_id") or ""}"',
        f"season: {lg.get('season', 2026)}",
        "stats_season: 2025",
        "",
        "me:",
        f"  username: {username}",
        "  user_id: null",
        "  draft_slot: null",
        "",
        "replacement_baselines:",
        *[f"  {pos}: {n}" for pos, n in baselines.items() if n],
        "",
        "pool_sizes:",
        *[f"  {pos}: {n}" for pos, n in pools.items()],
        "",
        f"# Flex-demand split: the {format_key(scoring)}-PPR FORMAT fallback (no board yet).",
        "# Once a board exists, run scripts/derive_flex_split.py --league <name> --write",
        "# to replace this with the split derived from THIS league's board.",
        "flex_split:",
        *[f"  {pos}: {share:.3f}" for pos, share in split.items()],
        f"  derived: format-fallback-{format_key(scoring)}",
        "",
        "guardrails:",
        "  qb2_earliest_round: 10",
        "  te2_fall_picks: 12",
        "",
        "tiers:",
        "  break_z: 0.5",
        "  cliff_z: 1.0",
        f"  adp_include_within: {teams * max(rounds, 13)}",
        "",
        "tilts:",
        "  enabled: true",
        "  mid_te_fade: 0.08",
        "  nonrush_qb_fade: 0.08",
        "  rush_qb_late_boost: 0.08",
        "  elite_te_boost: 0.05",
        "  top5_regression: 0.10",
        "  cap: 0.10",
        "",
    ]
    out = root / "leagues" / f"{slug}.yaml"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(y), encoding="utf-8")
    return out
