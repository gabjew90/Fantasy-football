"""Run the REAL engine for a Yahoo draft. The page only actuates.

Why this exists
---------------
The browser driver started as a JavaScript reimplementation of
draftkit/tracker.py, because Chrome's Private Network Access blocks the page
from calling a local Python server, so it looked like the decision loop had
to live in the page. Measured against the engine it was reimplementing, that
driver agreed on 25% of top picks and lost at 8 of 10 slots
(scripts/engine_bakeoff.py).

The premise was wrong. The page never needed to *think* -- only to *act*. Our
turn is preceded by roughly `teams` rival picks, which is minutes of wall
clock, so the ranked list can be computed ahead of time by the real engine
and handed to the page. The page walks the list and clicks.

So: this is the brain, `draft_driver.js` is the hands, and there is exactly
one ranking implementation in the repo again.

    python scripts/yahoo_bridge.py --league keefamania --state state.json
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import polars as pl  # noqa: E402

from draftkit import snake  # noqa: E402
from draftkit.config import Config  # noqa: E402
from draftkit.tracker import Tracker, TrackerState  # noqa: E402


def norm(n: str) -> str:
    s = unicodedata.normalize("NFKD", n or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return "".join(c for c in s.lower() if c.isalnum() or c == " ").strip()


def key(n: str) -> str:
    """first-initial + surname, matching how Yahoo renders a row."""
    parts = [p for p in norm(n).split() if p not in
             ("jr", "sr", "ii", "iii", "iv", "v")] or norm(n).split()
    if not parts:
        return ""
    return parts[0] if len(parts) == 1 else parts[0][0] + " " + parts[-1]


FLEX_NAMES = {"W/R/T", "WRT", "W/R", "FLEX", "W/T", "R/W/T"}


def slots_from_yahoo_roster(roster: list[str]) -> dict[str, int]:
    """Starter slots from a Yahoo roster list. BN and IR are not starters."""
    out = {"QB": 0, "RB": 0, "WR": 0, "TE": 0, "FLEX": 0, "K": 0, "DEF": 0, "BN": 0}
    for raw in roster:
        s = str(raw).strip().upper()
        if s in ("BN", "BENCH"):
            out["BN"] += 1
        elif s in ("IR", "IR+", "NA"):
            continue
        elif s in FLEX_NAMES:
            out["FLEX"] += 1
        elif s in out:
            out[s] += 1
    return out


def load_players(cfg: Config) -> list[dict]:
    df = pl.read_csv(cfg.scoped(cfg.root / "tiers.csv"), infer_schema_length=2000)
    out = []
    for i, r in enumerate(df.iter_rows(named=True)):
        pos = (r.get("pos") or "").upper()
        if pos not in ("QB", "RB", "WR", "TE", "K", "DEF"):
            continue
        out.append({
            "sleeper_id": str(i + 1), "name": r["player"], "pos": pos,
            "team": (r.get("team") or "").upper(),
            "vorp": float(r.get("vorp") or 0.0),
            "vorp_flex": float(r.get("vorp_flex") or r.get("vorp") or 0.0),
            "proj_pts": float(r.get("proj_pts") or 0.0),
            "adp": float(r["adp"]) if r.get("adp") not in (None, "") else None,
            "adp_delta": float(r.get("adp_delta") or 0.0),
            "tier": int(r.get("tier") or 9),
            "pos_rank": int(r.get("pos_rank") or 99),
            "value_rank": int(r.get("value_rank") or 999),
            "cliff_flag": bool(r.get("cliff_flag")),
            "upside_flag": bool(r.get("upside_flag")),
            "upside_why": r.get("upside_why") or "",
            "proj_source": r.get("proj_source") or "blend",
            "backs_up": r.get("backs_up") or "",
            "backs_up_pos": r.get("backs_up_pos") or "",
            "starter_fragility_label": r.get("starter_fragility_label") or "",
            "starter_exp_games": r.get("starter_exp_games"),
            "starter_avail": r.get("starter_avail"),
        })
    out.sort(key=lambda p: -p["vorp"])
    return out


def build_tracker(cfg: Config, players: list[dict], state: dict) -> Tracker:
    """A Tracker over Yahoo state. No Sleeper API is involved."""
    exp = cfg.get("expected") or {}
    teams = int(state.get("teams") or exp.get("teams") or 10)
    rounds = int(state.get("rounds") or exp.get("rounds") or 15)

    t = object.__new__(Tracker)
    t.teams, t.rounds = teams, rounds
    # Yahoo names its slots differently from Sleeper: the flex is "W/R/T" and
    # IR is a roster slot never filled during a draft.
    # roster_slots_from_draft_settings() reads Sleeper's slots_* keys, so
    # feeding it the Yahoo list silently produced an EMPTY slot map -- which
    # makes my_needs() all zeros and quietly disables every need-aware
    # guardrail. Build the map from the league yaml's own roster list.
    t.slots = slots_from_yahoo_roster(exp.get("roster") or [])
    t.my_slot = int(state["my_slot"])
    t.draft_id = "yahoo"
    t.poll_seconds, t.fall_alert = 5.0, 12

    # Engine knobs come from the SAME config the Sleeper tracker reads, so the
    # Yahoo draft is run by an identically-configured engine rather than by
    # defaults that merely look similar.
    e = cfg.get("engine") or {}
    t.sims = int(e.get("sims", 1000))
    t.pool_min = int(e.get("pool_min", e.get("pool_size", 40)))
    t.pool_lookback = int(e.get("pool_lookback", 20))
    t.pool_lookahead = int(e.get("pool_lookahead", 60))
    t.sigma_early = float(e.get("sigma_early", 6.0))
    t.sigma_late = float(e.get("sigma_late", 27.0))
    t.reach_prob = float(e.get("reach_prob", Tracker.reach_prob))
    t.reach_scale = float(e.get("reach_scale", Tracker.reach_scale))
    t.run_window = int(e.get("run_window", Tracker.run_window))
    t.run_min = int(e.get("run_min", Tracker.run_min))
    t.run_boost = float(e.get("run_boost", Tracker.run_boost))
    t.survival_shrink = float(e.get("survival_shrink", Tracker.survival_shrink))
    t.upside_from_round = int(e.get("upside_from_round", Tracker.upside_from_round))
    t.upside_mult = float(e.get("upside_mult", Tracker.upside_mult))
    t.local = True

    g = cfg.get("guardrails") or {}
    t.qb2_round = int(g.get("qb2_earliest_round", 10))
    t.te2_fall = int(g.get("te2_fall_picks", 12))
    t._urgency_cache = None
    t.rival_seeds, t.slot_to_user = {}, {}
    t.players = players
    t.by_id = {p["sleeper_id"]: p for p in players}

    by_key = {}
    for p in players:
        by_key.setdefault((key(p["name"]), p["pos"]), p)

    picks = []
    for d in state.get("drafted", []):
        p = by_key.get((key(d["name"]), d.get("pos", "")))
        if not p:
            continue
        pick_no = int(d["pick_no"])
        # Whose pick was it?
        #
        # Yahoo's pick feed names the player and the pick number but not the
        # slot. Reading d["slot"] defaulted every pick to 0, so NONE were
        # attributed to us, my_pos_counts() came back empty, and the engine
        # recommended a second QB in round 4 against a round-10 gate.
        #
        # The panel does label our own picks "You", and that flag beats snake
        # arithmetic: a mock reshuffled us from slot 3 to slot 10 seconds
        # before it started, which would have mis-attributed every pick. Trust
        # the flag when present, fall back to the snake position otherwise.
        rnd, snake_slot = snake.pick_to_round_slot(pick_no, teams)
        if d.get("mine"):
            slot = t.my_slot
        else:
            slot = int(d.get("slot") or snake_slot)
            if slot == t.my_slot:
                slot = 0        # not ours: never let the snake claim it for us
        picks.append({
            "pick_no": pick_no, "player_id": p["sleeper_id"],
            "draft_slot": slot, "round": rnd,
        })
    t.state = TrackerState(picks=picks,
                           drafted_ids={x["player_id"] for x in picks},
                           status="drafting")
    return t


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", default=None)
    ap.add_argument("--state", required=True, help="JSON from the page")
    ap.add_argument("--out", default="data/draftrig/plan.json")
    ap.add_argument("--depth", type=int, default=25)
    a = ap.parse_args()

    cfg = Config.load(league=a.league)
    state = json.loads(Path(a.state).read_text(encoding="utf-8"))
    players = load_players(cfg)
    t = build_tracker(cfg, players, state)

    recs = t.recommendations(top_n=a.depth)
    plan = [{
        "n": p["name"], "p": p["pos"], "t": p["team"],
        "v": round(float(p["vorp"] or 0.0), 1),
        "a": p["adp"], "why": why,
    } for _score, why, p in recs]

    # Depth beyond the engine's per-position candidates: if everything it
    # named is gone by the time we pick, the page still needs somewhere to go.
    named = {(x["n"], x["p"]) for x in plan}
    drafted = t.state.drafted_ids
    for p in players:
        if len(plan) >= a.depth:
            break
        if p["sleeper_id"] in drafted or (p["name"], p["pos"]) in named:
            continue
        if p.get("proj_source") == "no_market":
            continue
        plan.append({"n": p["name"], "p": p["pos"], "t": p["team"],
                     "v": round(float(p["vorp"] or 0.0), 1),
                     "a": p["adp"], "why": "depth fallback (engine list exhausted)"})

    out = {
        "current_pick": t.current_pick,
        "my_slot": t.my_slot,
        "round": snake.pick_to_round_slot(
            min(t.current_pick, t.teams * t.rounds), t.teams)[0],
        "needs": t.my_needs(),
        "plan": plan,
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print(f"pick {out['current_pick']} · round {out['round']} · "
          f"needs {out['needs']}")
    for i, x in enumerate(plan[:8], 1):
        print(f"  {i:2}. {x['n']:24} {x['p']:3} v{x['v']:6.1f}  {x['why'][:70]}")
    print(f"-> {a.out} ({len(plan)} deep)")


if __name__ == "__main__":
    main()
