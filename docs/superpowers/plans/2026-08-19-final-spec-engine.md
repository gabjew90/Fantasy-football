# Final Spec Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the user's FINAL spec (uploads/33d60afe-draftkitfinalspec.md): durability haircut, smoothed QB/TE replacement, Monte Carlo urgency engine with rival modeling, and hard roster guardrails.

**Architecture:** Durability lands in `dataset.py` (per-player `exp_games` merged into usage.parquet) and is applied as a multiplier in `projections.py`. VORP smoothing is a small change in `vorp.py`. Rival tendencies (`rivals.py`) walk the league's `previous_league_id` chain and persist per-user seeds to JSON. The urgency engine (`urgency.py`) is a pure module: given the remaining pool, the picks between now and my next turn, and per-slot rival states, it Monte-Carlo-simulates rival picks and returns per-position urgency + survival. `Tracker.recommendations()` is rewritten to: hard guardrail filters → urgency ranking → best-VORP-within-position → Δ tiebreak, with a per-pick-state cache so the 2s web refresh simulates once per pick, not per request.

**Tech Stack:** numpy (already a dep) for the MC sampling; everything else stdlib/polars.

**Spec deviations (deliberate, all UI/plumbing-neutral):**
- tiers.csv keeps `player` (not `name`) and `pos_rank`/`value_rank` (not `pos_tier_rank`) — renaming would churn tracker/web/simulate/board for zero function. New columns `exp_games`, `rookie_flag` added per spec.
- Durability haircut applies before `overrides.csv` — a manual override is always the literal final number.
- §7 backtest: deferred, per the spec's own build priority.
- Spec says "No IR"; Sleeper's league settings report `reserve_slots: 1`. Engine unaffected (IR is not draftable); discrepancy reported to user.

**Config additions (`config.yaml`):**

```yaml
engine:
  sims: 1000          # Monte Carlo draft simulations per decision
  pool_size: 80       # rivals sample from the top-N undrafted by ADP
  sigma_early: 6.0    # ADP noise (picks) in round 1  (~0.5 rounds)
  sigma_late: 27.0    # ADP noise (picks) by round 15 (~2.25 rounds)

guardrails:
  qb2_earliest_round: 10   # 2nd QB never before this round
  te2_fall_picks: 12       # 2nd TE only if a top-6 TE fell >= this many picks past ADP
```

Also update the `projections:` comment block to document the convention rule: all projections and replacement levels use the same 16-game convention; `expected_games` (16.0) is the season-length convention, per-player durability is the separate `exp_games` haircut.

---

### Task 1: Durability — `exp_games` in the dataset, haircut in projections

**Files:**
- Modify: `draftkit/dataset.py` (add `build_durability`, merge into usage.parquet)
- Modify: `draftkit/projections.py` (haircut + rookie_flag)
- Modify: `draftkit/tiers.py` (TIERS_COLUMNS + rounding)
- Test: `tests/test_durability.py`

- [ ] **Step 1: Write failing tests** (`tests/test_durability.py`)

```python
import polars as pl

from draftkit.dataset import build_durability


def _weekly(rows):
    return pl.DataFrame(rows, schema={"player_id": pl.Utf8, "season": pl.Int64})


def test_ironman_gets_16():
    # played 17, 17, 17 -> 0 missed -> exp 16
    rows = [{"player_id": "a", "season": s} for s in (2023, 2024, 2025) for _ in range(17)]
    d = build_durability(_weekly(rows), seasons=(2023, 2024, 2025))
    assert d.filter(pl.col("gsis_id") == "a")["exp_games"][0] == 16.0


def test_average_missed_subtracted():
    # played 17, 11, 14 -> missed 0, 6, 3 -> avg 3 -> exp 13
    rows = (
        [{"player_id": "b", "season": 2023} for _ in range(17)]
        + [{"player_id": "b", "season": 2024} for _ in range(11)]
        + [{"player_id": "b", "season": 2025} for _ in range(14)]
    )
    d = build_durability(_weekly(rows), seasons=(2023, 2024, 2025))
    assert d.filter(pl.col("gsis_id") == "b")["exp_games"][0] == 13.0


def test_floor_at_12():
    # played 5, 5, 5 -> avg missed 12 -> 16-12=4 -> floored to 12
    rows = [{"player_id": "c", "season": s} for s in (2023, 2024, 2025) for _ in range(5)]
    d = build_durability(_weekly(rows), seasons=(2023, 2024, 2025))
    assert d.filter(pl.col("gsis_id") == "c")["exp_games"][0] == 12.0


def test_partial_history_averages_only_played_seasons():
    # entered league 2025, played 17 -> avg missed 0 -> 16
    rows = [{"player_id": "d", "season": 2025} for _ in range(17)]
    d = build_durability(_weekly(rows), seasons=(2023, 2024, 2025))
    assert d.filter(pl.col("gsis_id") == "d")["exp_games"][0] == 16.0
```

- [ ] **Step 2: Run to verify failure** — `pytest tests/test_durability.py` → ImportError.

- [ ] **Step 3: Implement `build_durability` in `dataset.py`**

```python
SEASON_GAMES = 17  # NFL regular-season length; 16 is the projection convention


def build_durability(active_weekly: pl.DataFrame, seasons: tuple[int, ...]) -> pl.DataFrame:
    """exp_games = clamp(16 - avg games missed over played seasons, 12, 16).

    Only seasons the player actually appeared in count toward the average
    (a 2025 debut is not 'missed' 2023). 2026 rookies have no rows at all and
    are handled downstream (exp_games null -> 16, rookie_flag).
    """
    per_season = (
        active_weekly.filter(pl.col("season").is_in(list(seasons)))
        .group_by("player_id", "season")
        .agg(pl.len().alias("games"))
        .with_columns(
            (SEASON_GAMES - pl.col("games")).clip(lower_bound=0).alias("missed")
        )
    )
    return (
        per_season.group_by("player_id")
        .agg(pl.col("missed").mean().alias("avg_missed"))
        .with_columns(
            (16.0 - pl.col("avg_missed")).clip(lower_bound=12.0, upper_bound=16.0)
            .alias("exp_games")
        )
        .rename({"player_id": "gsis_id"})
        .select("gsis_id", "avg_missed", "exp_games")
    )
```

In `build_usage`, load three seasons of weekly stats instead of one, keep the 2025 slice for the existing usage logic, and reuse the same activity filter for durability:

Replace:
```python
    season = int(cfg["stats_season"])
    weekly = nfl.load_player_stats([season]).filter(pl.col("season_type") == "REG")
```
with:
```python
    season = int(cfg["stats_season"])
    durability_seasons = (season - 2, season - 1, season)
    weekly_all = nfl.load_player_stats(list(durability_seasons)).filter(
        pl.col("season_type") == "REG"
    )
    weekly = weekly_all.filter(pl.col("season") == season)
```

After the existing `active = weekly.filter(...)` block, build the all-seasons active frame with the same activity condition on `weekly_all` (factor the condition into a helper `_activity_filter(df, carries_col)` used for both), then after the NGS join and before `return`:

```python
    durability = build_durability(active_all, durability_seasons)
    player = player.join(durability, on="gsis_id", how="left")
```

- [ ] **Step 4: Haircut + rookie_flag in `projections.py`**

In `default_projection`, add `"exp_games"` to the `u = usage.filter(...).select(...)` column list. Then, immediately after the blend/`proj_source` block and BEFORE the overrides block:

```python
    # Durability haircut (final spec §1): scale by expected games from the
    # 3-year availability record. No history (2026 rookies, K/DEF) -> no haircut.
    df = df.with_columns(
        pl.col("exp_games").fill_null(16.0).alias("exp_games"),
    ).with_columns(
        (pl.col("proj_pts") * pl.col("exp_games") / 16.0).alias("proj_pts"),
        (
            pl.col("proj_model_pts").is_null()
            & ~pl.col("pos").is_in(["K", "DEF"])
        ).alias("rookie_flag"),
    )
```

- [ ] **Step 5: Add columns to the board** — in `tiers.py` `TIERS_COLUMNS`, insert `"exp_games", "rookie_flag"` after `"proj_source"`; in `write_tiers_csv` add `pl.col("exp_games").round(1)` to the rounding block.

- [ ] **Step 6: Run** `pytest tests -q` (all green), then rebuild: `.\venv\Scripts\python.exe -m draftkit dataset` then `tiers`. Sanity-check: injury-prone veterans (e.g. CMC) drop; iron men hold.

- [ ] **Step 7: Commit** — `feat: durability haircut (exp_games) + rookie_flag through to tiers.csv`

---

### Task 2: Smoothed QB/TE replacement in VORP

**Files:**
- Modify: `draftkit/vorp.py`
- Test: `tests/test_vorp.py`

- [ ] **Step 1: Failing tests** (`tests/test_vorp.py`)

```python
import polars as pl

from draftkit.vorp import add_vorp

BASELINES = {"QB": 12, "TE": 12, "RB": 3, "WR": 3}


def _pool(pos, pts):
    return [{"pos": pos, "proj_pts": float(p)} for p in pts]


def test_rb_uses_rank_directly():
    df = pl.DataFrame(_pool("RB", [100, 90, 80, 70]))
    out = add_vorp(df, {"RB": 3})
    top = out.sort("proj_pts", descending=True)
    assert top["replacement_pts"][0] == 80.0
    assert top["vorp"][0] == 20.0


def test_qb_uses_mean_of_ranks_10_14():
    pts = [300, 290, 280, 270, 260, 250, 240, 230, 220, 210, 200, 190, 180, 170, 160]
    df = pl.DataFrame(_pool("QB", pts))
    out = add_vorp(df, {"QB": 12})
    # ranks 10-14 -> 210, 200, 190, 180, 170 -> mean 190
    assert out["replacement_pts"][0] == 190.0


def test_qb_smoothing_with_short_pool():
    # only 11 QBs: ranks 10-14 window truncates to what exists (10, 11)
    pts = [300, 290, 280, 270, 260, 250, 240, 230, 220, 210, 200]
    df = pl.DataFrame(_pool("QB", pts))
    out = add_vorp(df, {"QB": 12})
    assert out["replacement_pts"][0] == 205.0  # mean(210, 200)
```

- [ ] **Step 2: Run to verify failure** — the 10–14 mean tests fail against rank-12 behavior.

- [ ] **Step 3: Implement** — in `add_vorp`, replace the single `repl = ...` computation:

```python
    # Final spec §2: QB/TE replacement = mean of positional ranks 10-14
    # (smooths streaming reality and single-projection outliers);
    # RB/WR/K/DEF use the baseline rank directly.
    SMOOTHED = {"QB": (10, 14), "TE": (10, 14)}
    repl_rows = []
    for pos, baseline in baselines.items():
        grp = df.filter(pl.col("pos") == pos)
        if grp.height == 0:
            continue
        if pos in SMOOTHED:
            lo, hi = SMOOTHED[pos]
            window = grp.filter(pl.col("pos_rank").is_between(lo, hi))
            if window.height == 0:
                window = grp.filter(pl.col("pos_rank") == grp["pos_rank"].max())
            repl_rows.append({"pos": pos, "replacement_pts": float(window["proj_pts"].mean())})
        else:
            at_rank = grp.filter(pl.col("pos_rank") == baseline)
            pts = (
                float(at_rank["proj_pts"][0])
                if at_rank.height
                else float(grp["proj_pts"].min())
            )
            repl_rows.append({"pos": pos, "replacement_pts": pts})
    repl = pl.DataFrame(repl_rows)
```

(Drop the old `missing`/fallback block — the loop covers short pools.)

- [ ] **Step 4: Run** `pytest tests -q`, rebuild `tiers`, sanity-check QB/TE VORPs shifted, RB/WR unchanged.

- [ ] **Step 5: Commit** — `feat: smoothed QB/TE replacement (mean of ranks 10-14)`

---

### Task 3: Rival tendency seeds from league history

**Files:**
- Create: `draftkit/rivals.py`
- Modify: `draftkit/sleeper.py` (add `league_drafts`), `draftkit/cli.py` (add `rivals` cmd)
- Test: `tests/test_rivals.py`

- [ ] **Step 1: Failing tests** (`tests/test_rivals.py`)

```python
from draftkit.rivals import tendencies_from_picks, ROUND_BUCKETS


def _pick(user, rnd, pos, teams=12):
    return {"picked_by": user, "round": rnd, "metadata": {"position": pos}}


def test_first_position_rounds():
    picks = [
        _pick("u1", 1, "RB"), _pick("u1", 2, "WR"), _pick("u1", 5, "QB"),
        _pick("u1", 9, "TE"), _pick("u1", 14, "K"), _pick("u1", 15, "DEF"),
    ]
    t = tendencies_from_picks(picks)["u1"]
    assert t["first_round"]["QB"] == 5
    assert t["first_round"]["K"] == 14


def test_bucket_shares_sum_to_one():
    picks = [_pick("u1", r, p) for r, p in
             [(1, "RB"), (2, "RB"), (3, "WR"), (4, "WR"), (5, "QB"), (6, "TE")]]
    t = tendencies_from_picks(picks)["u1"]
    for bucket in t["bucket_share"]:
        total = sum(t["bucket_share"][bucket].values())
        assert abs(total - 1.0) < 1e-9 or total == 0


def test_multiple_drafts_average_first_rounds():
    picks = [_pick("u1", 4, "QB"), _pick("u1", 8, "QB")]
    # two drafts merged: first QB rounds 4 and 8 -> median-ish mean 6
    t = tendencies_from_picks(picks, drafts=[[picks[0]], [picks[1]]])["u1"]
    assert t["first_round"]["QB"] == 6
```

- [ ] **Step 2: Run to verify failure.**

- [ ] **Step 3: Implement `draftkit/rivals.py`**

```python
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
            pos = {"DST": "DEF"}.get((p.get("metadata") or {}).get("position"), 
                                     (p.get("metadata") or {}).get("position"))
            rnd = int(p.get("round") or 0)
            if not user or pos not in POSITIONS or rnd < 1:
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
    league_id = cfg.league_id
    all_drafts: list[list[dict]] = []
    seen_leagues = 0
    lg = client.league(league_id)
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
```

- [ ] **Step 4: Add `league_drafts` to `SleeperClient`** (after `draft_picks`):

```python
    def league_drafts(self, league_id: str) -> list[dict]:
        return get_json(f"{BASE}/league/{league_id}/drafts")
```

- [ ] **Step 5: CLI command** — in `cli.py`:

```python
def cmd_rivals(cfg: Config, args) -> None:
    from .rivals import build_seeds

    client = SleeperClient(cfg.path("raw"))
    payload = build_seeds(cfg, client)
    console.print(f"rival seeds: {len(payload['users'])} users from "
                  f"{payload['history_drafts']} historical drafts -> "
                  f"{cfg.path('processed') / 'rival_seeds.json'}")
```

Register `sub.add_parser("rivals")` and `"rivals": cmd_rivals` in the dispatch dict.

- [ ] **Step 6: Run** `pytest tests -q`, then `python -m draftkit rivals` live; inspect the JSON (first-QB rounds per rival should look sane). A first-year league yields 0 drafts — engine must work with empty seeds.

- [ ] **Step 7: Commit** — `feat: rival tendency seeds from league draft history`

---

### Task 4: Monte Carlo urgency engine + guardrails in Tracker

**Files:**
- Create: `draftkit/urgency.py`
- Modify: `draftkit/tracker.py` (recommendations rewrite + cache + seeds), `config.yaml`
- Test: `tests/test_urgency.py`

- [ ] **Step 1: Failing tests** (`tests/test_urgency.py`) — deterministic via seeded rng; small pool

```python
import numpy as np

from draftkit.urgency import simulate_survival


def player(pid, pos, vorp, adp):
    return {"sleeper_id": pid, "pos": pos, "vorp": vorp, "adp": adp, "player": pid}


POOL = [
    player("rb1", "RB", 50.0, 5.0),
    player("rb2", "RB", 30.0, 12.0),
    player("rb3", "RB", 10.0, 30.0),
    player("wr1", "WR", 45.0, 6.0),
    player("wr2", "WR", 25.0, 15.0),
    player("qb1", "QB", 20.0, 40.0),
]

RIVALS = [{"slot": s, "needs": {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 2, "K": 1, "DEF": 1},
           "user_id": None} for s in (3, 4, 5)]


def test_urgency_positive_when_rivals_want_position():
    rng = np.random.default_rng(7)
    rep = simulate_survival(POOL, current_pick=10, next_pick=13, rivals=RIVALS,
                            seeds={}, rng=rng, sims=300, sigma=6.0)
    # rb1/wr1 are prime targets for 3 rivals -> expected best at next pick < best now
    assert rep["RB"]["urgency"] > 0
    assert rep["RB"]["best_now"] == 50.0
    assert rep["RB"]["e_best_next"] < 50.0


def test_no_intervening_picks_zero_urgency():
    rng = np.random.default_rng(7)
    rep = simulate_survival(POOL, current_pick=10, next_pick=10, rivals=[],
                            seeds={}, rng=rng, sims=50, sigma=6.0)
    assert rep["RB"]["urgency"] == 0.0
    assert rep["RB"]["e_best_next"] == 50.0


def test_survival_probability_bounds_and_ordering():
    rng = np.random.default_rng(7)
    rep = simulate_survival(POOL, current_pick=10, next_pick=13, rivals=RIVALS,
                            seeds={}, rng=rng, sims=300, sigma=6.0)
    s1 = rep["RB"]["survival"]["rb1"]
    s3 = rep["RB"]["survival"]["rb3"]
    assert 0.0 <= s1 <= 1.0
    assert s3 >= s1  # later-ADP player survives more often


def test_filled_position_rarely_taken():
    rivals = [{"slot": 3, "needs": {"QB": 0, "RB": 2, "WR": 2, "TE": 1, "FLEX": 2, "K": 1, "DEF": 1},
               "user_id": None}]
    rng = np.random.default_rng(7)
    rep = simulate_survival(POOL, current_pick=39, next_pick=41, rivals=rivals,
                            seeds={}, rng=rng, sims=400, sigma=6.0)
    # qb1 at ADP 40 is the obvious ADP pick, but the rival's QB slot is filled
    assert rep["QB"]["survival"]["qb1"] > 0.8
```

- [ ] **Step 2: Run to verify failure.**

- [ ] **Step 3: Implement `draftkit/urgency.py`**

```python
"""Monte Carlo urgency engine (final spec §5).

urgency(pos) = VORP(best available now) - E[VORP(best available at my next turn)]

The expectation simulates every intervening rival pick: candidates weighted by
an ADP Gaussian (sigma grows with round), zeroed/damped by the rival's filled
starter slots, and tilted by their historical tendencies. Sampling is without
replacement within each simulation.

Known limitation (accepted in spec): one-step lookahead — optimizes the current
vs next turn only; turn N+2 sequencing is a next-season upgrade.
"""

from __future__ import annotations

import numpy as np

from . import snake

POSITIONS = ["QB", "RB", "WR", "TE", "K", "DEF"]
NEED_DAMP = 0.15          # multiplier for positions that fill no starter slot
QB_FILLED_DAMP = 0.05     # rival with QB filled, before late rounds
KDEF_EARLY_DAMP = 0.02    # K/DEF long before the rival's typical round


def _tendency_mult(seed: dict | None, rnd: int, pos: str) -> float:
    """How much this rival historically likes pos in this round bucket vs 1/6."""
    if not seed:
        return 1.0
    from .rivals import _bucket  # single source of bucket boundaries

    share = (seed.get("bucket_share", {}).get(_bucket(rnd), {}) or {}).get(pos)
    if share is None:
        return 1.0
    return float(np.clip(share / (1.0 / 6.0), 0.5, 2.0))


def simulate_survival(pool, current_pick, next_pick, rivals, seeds, rng,
                      sims=1000, sigma=6.0, teams=12):
    """Per-position urgency + per-player survival to my next pick.

    pool: undrafted players (dicts with sleeper_id/pos/vorp/adp), pre-truncated.
    rivals: intervening pickers in order — {"slot", "needs", "user_id"}.
    seeds: rival_seeds.json "users" mapping (may be empty).
    sigma: ADP noise in picks for the current round (caller scales by round).
    """
    n = len(pool)
    picks_between = max(0, next_pick - current_pick)
    pos_arr = np.array([p["pos"] for p in pool])
    vorp = np.array([float(p["vorp"] if p["vorp"] is not None else -99.0) for p in pool])
    adp = np.array([float(p["adp"]) if p.get("adp") is not None else 200.0 for p in pool])

    best_now = {
        pos: float(vorp[pos_arr == pos].max()) if (pos_arr == pos).any() else 0.0
        for pos in POSITIONS
    }
    if picks_between == 0 or not rivals or n == 0:
        return {
            pos: {"best_now": best_now[pos], "e_best_next": best_now[pos],
                  "urgency": 0.0, "survival": {p["sleeper_id"]: 1.0 for p in pool
                                               if p["pos"] == pos}}
            for pos in POSITIONS
        }

    # static per-rival positional multiplier (needs + tendencies), per pick index
    rival_mult = np.ones((len(rivals), n))
    for i, rv in enumerate(rivals):
        pick_no = current_pick + i
        rnd = (pick_no - 1) // teams + 1
        seed = (seeds or {}).get(str(rv.get("user_id"))) if rv.get("user_id") else None
        for pos in POSITIONS:
            mask = pos_arr == pos
            if not mask.any():
                continue
            fills = snake.needs_position(rv["needs"], pos)
            m = 1.0 if fills else NEED_DAMP
            if pos == "QB" and rv["needs"].get("QB", 0) == 0 and rnd < 10:
                m = QB_FILLED_DAMP
            if pos in ("K", "DEF"):
                typical = (seed or {}).get("first_round", {}).get(pos, 13)
                if rnd < typical - 1:
                    m = KDEF_EARLY_DAMP
            m *= _tendency_mult(seed, rnd, pos)
            rival_mult[i, mask] = m

    # ADP likelihood per intervening pick (same sigma across the window is fine
    # at this window size; sigma itself scales with round at the call site)
    pick_nos = np.arange(current_pick, next_pick)
    adp_like = np.exp(-0.5 * ((pick_nos[:, None] - adp[None, :]) / sigma) ** 2) + 1e-9

    survived = np.zeros(n, dtype=np.int64)
    e_best = {pos: 0.0 for pos in POSITIONS}
    for _ in range(sims):
        alive = np.ones(n, dtype=bool)
        for i in range(len(rivals)):
            w = adp_like[i] * rival_mult[i] * alive
            total = w.sum()
            if total <= 0:
                break
            choice = rng.choice(n, p=w / total)
            alive[choice] = False
        survived += alive
        for pos in POSITIONS:
            mask = (pos_arr == pos) & alive
            e_best[pos] += float(vorp[mask].max()) if mask.any() else 0.0

    report = {}
    for pos in POSITIONS:
        e = e_best[pos] / sims
        report[pos] = {
            "best_now": best_now[pos],
            "e_best_next": e,
            "urgency": best_now[pos] - e,
            "survival": {
                pool[j]["sleeper_id"]: survived[j] / sims
                for j in range(n) if pos_arr[j] == pos
            },
        }
    return report
```

Note: `rivals` must be the actual intervening pickers **in pick order** (length == picks_between); the caller builds it from `snake.slots_picking_between`.

- [ ] **Step 4: Run** `pytest tests/test_urgency.py -v` → 4 passed. Add a timing check by hand:
`python -c "...1000 sims, 22 rivals, 80 players..."` — must be < 1s.

- [ ] **Step 5: Rewrite `Tracker.recommendations()`** with guardrails + urgency (cache per pick-state). Replace the whole method; add helpers. New behavior:

```python
    # ---------- engine ----------

    def _rival_states(self, my_next: int) -> list[dict]:
        """Intervening pickers in order, with their open starter slots."""
        out = []
        for pick_no in range(self.current_pick, my_next):
            _, slot = snake.pick_to_round_slot(pick_no, self.teams)
            if slot == self.my_slot:
                continue
            needs = snake.starter_needs(self.slot_positions(slot), self.slots)
            out.append({
                "slot": slot, "needs": needs,
                "user_id": self.slot_to_user.get(slot),
            })
        return out

    def _sigma(self, rnd: int) -> float:
        e, l = self.sigma_early, self.sigma_late
        return e + (l - e) * (rnd - 1) / max(1, self.rounds - 1)

    def urgency_report(self) -> dict | None:
        """Cached per pick-state; None when no slot or draft not in progress."""
        if not self.my_slot:
            return None
        key = len(self.state.picks)
        if self._urgency_cache and self._urgency_cache[0] == key:
            return self._urgency_cache[1]
        import numpy as np
        from .urgency import simulate_survival

        cur = self.current_pick
        my_next = snake.next_pick_for_slot(cur, self.my_slot, self.teams, self.rounds)
        if my_next is None:
            return None
        rnd, _ = snake.pick_to_round_slot(min(cur, self.teams * self.rounds), self.teams)
        pool = sorted(
            self.remaining(),
            key=lambda p: p["adp"] if p.get("adp") is not None else 999.0,
        )[: self.pool_size]
        rng = np.random.default_rng(hash((self.draft_id, key)) & 0xFFFFFFFF)
        report = simulate_survival(
            pool, cur, my_next, self._rival_states(my_next), self.rival_seeds,
            rng, sims=self.sims, sigma=self._sigma(rnd), teams=self.teams,
        )
        self._urgency_cache = (key, report)
        return report
```

Guardrail filter + recommendation assembly (replaces the scoring loop; keeps the
`list[(score, why, player)]` return shape both UIs consume):

```python
    def _my_pos_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for pos in self.slot_positions(self.my_slot):
            counts[pos] = counts.get(pos, 0) + 1
        return counts

    def _guardrail_ok(self, p: dict, rnd: int, needs, counts, picks_left) -> bool:
        """Final spec §6 — hard rules, override the engine."""
        pos = p["pos"]
        if pos in ("K", "DEF"):
            kdef_needed = needs.get("K", 0) + needs.get("DEF", 0)
            if picks_left > 2 and picks_left > kdef_needed:
                return False
            if counts.get(pos, 0) >= 1:
                return False
        if pos == "QB" and counts.get("QB", 0) >= 1 and rnd < self.qb2_round:
            return False
        if pos == "TE" and counts.get("TE", 0) >= 1:
            top6_fell = any(
                q["pos"] == "TE" and q["pos_rank"] <= 6
                and q.get("adp") is not None
                and self.current_pick - q["adp"] >= self.te2_fall
                for q in self.remaining("TE")
            )
            if not top6_fell:
                return False
        # max one zero-role stash: proxy = negative-VORP player already on bench
        if (p["vorp"] or 0) <= 0 and not snake.needs_position(needs, pos):
            have_stash = any(
                (self.by_id.get(pid, {}).get("vorp") or 1) <= 0
                for pid in (str(x["player_id"]) for x in self.picks_for_slot(self.my_slot))
                if pid in self.by_id
            )
            if have_stash:
                return False
        # must-fill: remaining picks <= open starters -> starters only
        open_starters = sum(needs.get(k, 0) for k in ("QB", "RB", "WR", "TE", "FLEX", "K", "DEF"))
        if picks_left <= open_starters and not snake.needs_position(needs, pos):
            return False
        return True

    def _bye_warning(self, p: dict, needs) -> str:
        """Warn (never block) when a pick creates 3+ starters on one bye."""
        my_starter_byes: list = []
        filled = {k: self.slots[k] - needs.get(k, 0) for k in self.slots}
        starters_needed = sum(v for k, v in self.slots.items() if k != "BN")
        picked = [self.by_id.get(str(x["player_id"])) for x in self.picks_for_slot(self.my_slot)]
        for q in picked[:starters_needed]:
            if q and q.get("bye") is not None:
                my_starter_byes.append(q["bye"])
        if p.get("bye") is not None and my_starter_byes.count(p["bye"]) >= 2:
            return f" ⚠ {my_starter_byes.count(p['bye']) + 1} starters on bye {p['bye']}"
        return ""

    def recommendations(self, top_n: int = 5) -> list[tuple[float, str, dict]]:
        """Final spec §5: urgency-ranked positions, best VORP within, Δ tiebreak."""
        rnd, _ = snake.pick_to_round_slot(
            min(self.current_pick, self.teams * self.rounds), self.teams
        )
        if not self.my_slot:
            pool = self.remaining()[:top_n]
            return [(p["vorp"] or 0.0, "best value (spectator)", p) for p in pool]
        needs = self.my_needs()
        counts = self._my_pos_counts()
        picks_left = self.rounds - len(self.picks_for_slot(self.my_slot))
        report = self.urgency_report()

        cands = []
        for pos in ("RB", "WR", "TE", "QB", "K", "DEF"):
            pool = [
                p for p in self.remaining(pos)
                if self._guardrail_ok(p, rnd, needs, counts, picks_left)
            ][:3]
            if not pool:
                continue
            # best VORP within position; near-ties (<= 2 VORP) broken by Δ
            best = pool[0]
            for q in pool[1:]:
                if abs((best["vorp"] or 0) - (q["vorp"] or 0)) <= 2.0 and (
                    (q.get("adp_delta") or -999) > (best.get("adp_delta") or -999)
                ):
                    best = q
            u = report[pos] if report and pos in report else None
            urgency = u["urgency"] if u else (best["vorp"] or 0.0)
            surv = u["survival"].get(best["sleeper_id"]) if u else None
            why = ""
            if u:
                why = (
                    f"urgency +{urgency:.1f}: best {pos} {u['best_now']:.0f} now → "
                    f"{u['e_best_next']:.0f} expected at your next pick"
                )
                if surv is not None:
                    why += f" (he survives {surv:.0%})"
            else:
                why = "best value"
            why += self._bye_warning(best, needs)
            score = urgency + 0.001 * (best["vorp"] or 0.0)  # stable ordering
            cands.append((score, why, best))
        cands.sort(key=lambda t: -t[0])
        return cands[:top_n]
```

`__init__` additions (after existing tcfg block):

```python
        ecfg = cfg["engine"] if "engine" in cfg._data else {}
        self.sims = int(ecfg.get("sims", 1000))
        self.pool_size = int(ecfg.get("pool_size", 80))
        self.sigma_early = float(ecfg.get("sigma_early", 6.0))
        self.sigma_late = float(ecfg.get("sigma_late", 27.0))
        gcfg = cfg["guardrails"] if "guardrails" in cfg._data else {}
        self.qb2_round = int(gcfg.get("qb2_earliest_round", 10))
        self.te2_fall = int(gcfg.get("te2_fall_picks", 12))
        self._urgency_cache: tuple[int, dict] | None = None
        from .rivals import load_seeds
        seeds = load_seeds(cfg)
        self.rival_seeds = seeds.get("users", {})
        order = self.draft.get("draft_order") or {}
        self.slot_to_user = {int(v): str(k) for k, v in order.items()}
```

Delete the old scoring body (`must_fill_only`, cliff bonus, faller bonus) — cliff/fallers remain UI panels only, per spec §3/§9. `kdef_allowed` becomes unused by the engine; keep it only if the render path still calls it (it does not — remove it).

Also update `config.yaml` with the `engine:` and `guardrails:` blocks from the header and the convention-rule comment under `projections:`.

- [ ] **Step 6: Update affected tests.** `tests/test_web_state.py` `make_tracker` needs the new attrs: add
`t.sims = 50; t.pool_size = 80; t.sigma_early = 6.0; t.sigma_late = 27.0; t.qb2_round = 10; t.te2_fall = 12; t._urgency_cache = None; t.rival_seeds = {}; t.slot_to_user = {}` — recommendations flow through the new engine with tiny sims. The web `why` assertions still hold (why is never empty).

- [ ] **Step 7: Run** `pytest tests -q` (all green), then `python -m draftkit simulate --slot 2 --quiet` — a full 15-round sim through the new engine must complete in sensible wall time (< ~60s) and produce a legal roster (1-2 QB, K+DEF last two picks, no stash pileup).

- [ ] **Step 8: Commit** — `feat: Monte Carlo urgency engine, rival modeling, and hard guardrails`

---

### Task 5: Rebuild data, live smoke, push

- [ ] **Step 1:** `python -m draftkit dataset && python -m draftkit tiers && python -m draftkit rivals` — full rebuild with durability + smoothing on real data.
- [ ] **Step 2:** Start `python -m draftkit web`, GET `/state`: recommendations show urgency-style why strings; JSON valid; response under ~1.5s cold, instant warm (cache). Read the board for sanity (CMC haircut visible; QB/TE VORPs shifted).
- [ ] **Step 3:** `pytest tests -q` one final time; commit any data artifacts (tiers.csv/board.md) and push the branch.

## Self-review notes
- Spec §1 durability → Task 1; §2 smoothing → Task 2; §3 cliff-informational → Task 4 Step 5 (bonus removed); §4 schema → Task 1 Step 5 (+ documented deviations); §5 engine (MC, seeds, sigma-by-round, Δ tiebreak, one-step limitation comment) → Tasks 3–4; §6 guardrails → Task 4 `_guardrail_ok` + `_bye_warning`; §7 backtest → deferred per spec; §8 priorities honored; §9 posture (no LLM in loop, 5s poll, resumable) → unchanged architecture + per-pick cache.
- Type check: `simulate_survival(pool, current_pick, next_pick, rivals, seeds, rng, sims, sigma, teams)` matches test and tracker call sites; report keys `best_now/e_best_next/urgency/survival` used consistently.
