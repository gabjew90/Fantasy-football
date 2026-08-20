"""Rival tendency seeds from league draft history (final spec §5/§8.2).

Walks the previous_league_id chain, collects completed drafts, and summarizes
per-user tendencies: the round they first take each position and the share of
their picks spent on each position per round bucket. The urgency engine blends
these seeds with observed in-draft behavior.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

ROUND_BUCKETS = {"R1-3": (1, 3), "R4-6": (4, 6), "R7-9": (7, 9),
                 "R10-12": (10, 12), "R13+": (13, 99)}
POSITIONS = ["QB", "RB", "WR", "TE", "K", "DEF"]
MAX_SEASONS_BACK = 5


def _bucket(rnd: int) -> str:
    for name, (lo, hi) in ROUND_BUCKETS.items():
        if lo <= rnd <= hi:
            return name
    return "R13+"


def tendencies_from_picks(picks: list[dict], drafts: list[list[dict]] | None = None) -> dict:
    """Per-user tendency summary. `drafts` groups picks per historical draft so
    first-position rounds average across drafts; default treats `picks` as one."""
    draft_lists = drafts if drafts is not None else [picks]
    firsts: dict[str, dict[str, list[int]]] = {}
    counts: dict[str, dict[str, dict[str, int]]] = {}
    for dr in draft_lists:
        seen_first: dict[tuple[str, str], int] = {}
        for p in dr:
            user = str(p.get("picked_by") or "")
            raw_pos = (p.get("metadata") or {}).get("position")
            pos = {"DST": "DEF"}.get(raw_pos, raw_pos)
            rnd = int(p.get("round") or 0)
            if not user or user == "None" or pos not in POSITIONS or rnd < 1:
                continue
            key = (user, pos)
            if key not in seen_first:
                seen_first[key] = rnd
            b = _bucket(rnd)
            counts.setdefault(user, {}).setdefault(b, {}).setdefault(pos, 0)
            counts[user][b][pos] += 1
        for (user, pos), rnd in seen_first.items():
            firsts.setdefault(user, {}).setdefault(pos, []).append(rnd)

    out: dict[str, dict] = {}
    for user in counts:
        first_round = {
            pos: round(statistics.mean(rounds))
            for pos, rounds in firsts.get(user, {}).items()
        }
        bucket_share = {}
        for b in ROUND_BUCKETS:
            c = counts[user].get(b, {})
            total = sum(c.values())
            bucket_share[b] = (
                {pos: c.get(pos, 0) / total for pos in POSITIONS} if total else {}
            )
        out[user] = {"first_round": first_round, "bucket_share": bucket_share,
                     "drafts_seen": len(draft_lists)}
    return out


def build_seeds(cfg, client) -> dict:
    """Fetch league history and persist per-user seeds keyed by user_id."""
    all_drafts: list[list[dict]] = []
    seen_leagues = 0
    lg = client.league(cfg.league_id)
    while lg and seen_leagues < MAX_SEASONS_BACK:
        prev = lg.get("previous_league_id")
        if not prev or prev in ("0", 0):
            break
        lg = client.league(str(prev))
        seen_leagues += 1
        for d in client.league_drafts(str(lg["league_id"])):
            if d.get("status") == "complete" and d.get("type") == "snake":
                picks = client.draft_picks(str(d["draft_id"]))
                if picks:
                    all_drafts.append(picks)

    flat = [p for dr in all_drafts for p in dr]
    seeds = tendencies_from_picks(flat, drafts=all_drafts) if flat else {}
    payload = {"users": seeds, "history_drafts": len(all_drafts)}
    out = Path(cfg.path("processed")) / "rival_seeds.json"
    out.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return payload


def load_seeds(cfg) -> dict:
    p = Path(cfg.path("processed")) / "rival_seeds.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"users": {}, "history_drafts": 0}
