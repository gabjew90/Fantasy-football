"""The projection-source gate (DECISIONS 2026-09-02 #23), pre-registered.

Decides `projections.source` between `model` (the retired usage + log-rank
blend; the backtest's `blend` arm) and `external` (outside stat lines; in
history only Sleeper's week-1 lines exist, the backtest's `lines` arm, so
they stand in for the 2026 sheet + Sleeper combination).

Test 1, ACCURACY -- read from the backtest's row export
(reports/projection_backtest.<league>.rows.csv): on the rows every arm
projected, pooled MAE over all positions and both pairs, and the n-weighted
mean of the per-(pair, position) Spearman. external fails if pooled MAE is
more than 2% above the model's or weighted Spearman more than 0.02 below,
in either league.

Test 2, OUTCOME -- both arms built into boards through the production board
code (draftkit.tiers.finish_board) and replayed through the SAME engine at
every draft slot against the SAME rivals: rivals draft the history year's
pool in ADP order, from one shared list, whether or not a player is on our
arm's board (an arm that never projected a player cannot draft him; the
rivals still can). Each roster is graded on the ACTUAL season points of its
best legal lineup. K/DEF are absent from the history pools and removed from
the slots for both arms. external fails if its mean lineup points over all
slots, pairs and leagues are more than 1% below the model's.

Churn is not a gate; scripts/input_replay.py reports it by tier.

Two things the outcome half now says about itself, neither of which moves a
pre-registered threshold:

  * `--seeds N` redraws the rival room N-1 times with ADP noise (the same draw
    for every arm, so a per-slot delta stays a paired comparison). With rivals
    pinned to exact consensus, a pair's slot-drafts are ONE draft universe
    sampled at each seat, not independent draws, so a 1% delta reported over
    "44 slot-drafts" claims more evidence than it has. The report prints the
    per-seed spread and says outright when the delta is inside it.
  * Engine exceptions and an inert candidate INVALIDATE the run rather than
    appearing as a footnote. An exception falls back to the best available
    player, which is a different and dumber drafting policy; if one arm throws
    more often than another, the two were not graded on the same engine.

    venv\\Scripts\\python.exe scripts\\source_gate.py --leagues keefamania,omnibeta
    venv\\Scripts\\python.exe scripts\\source_gate.py --seeds 5   # with an error bar
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
import tempfile
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import engine_parity as EP  # noqa: E402
from projection_backtest import ARMS, SEASON_GAMES, spearman  # noqa: E402
from slot_replay import lineup_points  # noqa: E402
from draftkit import snake  # noqa: E402
from draftkit.config import Config  # noqa: E402
from draftkit.tiers import finish_board, write_tiers_csv  # noqa: E402

MODEL_ARM, EXTERNAL_ARM = "blend", "lines"
# Every arm in the rows csv is already normalised to a season basis by
# projection_backtest (the model arms at :251-253, `lines` via week1_lines'
# games= default), so history_board's conversion back to the league's own
# games convention is one shared constant, imported rather than retyped. A
# local copy here would drift silently the day the backtest's basis changes
# and would rescale one arm against another.
LINE_GAMES = SEASON_GAMES
# pre-registered thresholds (DECISIONS #23)
MAE_TOL, RHO_TOL, OUTCOME_TOL = 0.02, 0.02, 0.01
# Rival-noise defaults. sigma is in PICKS of ADP: rivals reach and fall around
# the consensus instead of drafting it exactly. See rival_order.
JITTER_PICKS, DEFAULT_SEEDS = 6.0, 5
# the history pools carry no K/DEF: those two rounds and slots are removed
# from every league's shape, for both arms alike
NO_KDEF = ("K", "DEF")


# ---------------------------------------------------------------- pure parts

def pooled_accuracy(rows: pl.DataFrame, candidate: str = EXTERNAL_ARM,
                    rivals: tuple = (MODEL_ARM,)) -> dict:
    """Test 1 for one league. Rows every compared arm projected; pooled MAE
    and the n-weighted mean of per-(pair, pos) Spearman for the candidate
    and every rival. Pass = the candidate is not worse than EVERY rival
    (plan A1 generalisation; the #23 call is candidate lines vs rival blend).
    Every value is keyed by its ARM NAME only; the summary keys mae_ratio /
    rho_delta describe the candidate against the FIRST rival. (An earlier
    version also wrote #23-style alias keys, which overwrote a rival's own
    value whenever an arm under test was itself named `blend` or `lines` --
    the games-table gate's lines_gt-vs-lines run compared the candidate with
    itself. Aliases are gone; render() reads the names.)"""
    arms = [candidate, *rivals]
    # the apples-to-apples population: rows every backtest arm PRESENT in the
    # file projected (the #23 population on the backtest exports), plus the
    # arms under test; the forward file carries only its own arms
    present = [c for c in dict.fromkeys([*ARMS, *arms]) if c in rows.columns]
    common = rows.filter(pl.all_horizontal([pl.col(a).is_not_null() for a in present]))
    out = {"n": common.height, "by_cell": [], "candidate": candidate, "rivals": list(rivals)}
    for arm in arms:
        err = (common[arm] - common["actual"]).abs()
        out[f"{arm}_mae"] = float(err.mean()) if common.height else float("nan")
    wsum = {arm: 0.0 for arm in arms}
    for (pair, pos), cell in sorted(common.group_by(["pair", "pos"]), key=lambda kv: kv[0]):
        n = cell.height
        rec = {"pair": pair, "pos": pos, "n": n}
        for arm in arms:
            rho = spearman(cell[arm].to_list(), cell["actual"].to_list())
            rec[f"{arm}_rho"] = rho
            rec[f"{arm}_mae"] = float((cell[arm] - cell["actual"]).abs().mean())
            if rho == rho:      # not nan
                wsum[arm] += rho * n
        out["by_cell"].append(rec)
    for arm in arms:
        out[f"{arm}_rho"] = wsum[arm] / common.height if common.height else float("nan")
    # per rival: the candidate's ratio / delta against it; pass = every rival
    out["vs"] = {}
    for r in rivals:
        ratio = out[f"{candidate}_mae"] / out[f"{r}_mae"] if out.get(f"{r}_mae") else float("nan")
        delta = out[f"{candidate}_rho"] - out[f"{r}_rho"]
        out["vs"][r] = {"mae_ratio": ratio, "rho_delta": delta,
                        "pass": bool(ratio <= 1 + MAE_TOL and delta >= -RHO_TOL)}
    first = rivals[0]
    out["mae_ratio"], out["rho_delta"] = out["vs"][first]["mae_ratio"], out["vs"][first]["rho_delta"]
    out["pass"] = all(v["pass"] for v in out["vs"].values())
    return out


def rival_order(rows: pl.DataFrame, seed: int | None = None,
                jitter: float = JITTER_PICKS) -> list[str]:
    """The shared rival draft list: pool players with an ADP, in ADP order.

    Both arms face EXACTLY this list, which is what makes a per-slot delta a
    paired comparison. `seed` perturbs the order; `seed=None` is the exact
    consensus and reproduces every result recorded before seeds existed.

    Why the noise matters for what the numbers mean. With no jitter the rivals
    make identical picks in every replay, so a pair's `teams` slot-drafts are
    not independent draws: they are ONE draft universe sampled at each seat,
    and neighbouring seats see nearly the same board. Reporting 44 such
    numbers as 44 observations overstates the evidence behind a 1% delta. A
    seed redraws the universe, so the spread of per-seed means is the first
    honest read on whether a delta is resolvable at all.

    The model is Gaussian noise on the ADP position, in picks: a rival reaches
    or falls around consensus by about `jitter`. It is deliberately crude --
    it does not model position runs or tier cliffs -- so it bounds the
    variance from rival disagreement rather than reproducing a real room.
    """
    have = rows.filter(pl.col("adp").is_not_null())
    if seed is None or not jitter:
        return have.sort("adp")["name"].to_list()
    rng = np.random.default_rng(seed)
    noisy = have.with_columns(
        (pl.col("adp") + pl.Series(rng.normal(0.0, jitter, have.height))).alias("_adp"))
    return noisy.sort("_adp")["name"].to_list()


def adp_replay(board: list[dict], rivals: list[str], my_slot: int, teams: int, rounds: int,
               slots: dict) -> tuple[list[dict], int]:
    """Rivals take the best remaining name from the shared ADP list; our picks
    are the engine's top recommendation at every turn, from our arm's board.
    Returns (our roster, engine errors)."""
    by_name = {p["name"]: p for p in board}
    taken: set[str] = set()
    chosen, picks, errors = [], [], 0
    for pick_no in range(1, teams * rounds + 1):
        rnd, slot = snake.pick_to_round_slot(pick_no, teams)
        if slot != my_slot:
            name = next((q for q in rivals if q not in taken), None)
            if name is None:
                break
            taken.add(name)
            picks.append({"pick_no": pick_no, "player_id": by_name.get(name, {}).get("sleeper_id", "0"),
                          "draft_slot": slot, "round": rnd})
            continue
        avail = [p for p in board if p["name"] not in taken]
        if not avail:
            break
        t = EP.make_tracker(board, picks, my_slot, slots=slots, teams=teams, rounds=rounds)
        t.slot_markets = True
        try:
            recs = t.recommendations(top_n=1)
            pick = by_name[recs[0][2]["name"]] if recs else avail[0]
        except Exception:  # noqa: BLE001
            errors += 1
            pick = avail[0]
        chosen.append(pick)
        taken.add(pick["name"])
        picks.append({"pick_no": pick_no, "player_id": pick["sleeper_id"], "draft_slot": my_slot, "round": rnd})
    return chosen, errors


def grade_actual(chosen: list[dict], actual_by_name: dict[str, float], slots: dict) -> float:
    """Actual season points of the best legal lineup."""
    return lineup_points([dict(p, actual=actual_by_name.get(p["name"], 0.0)) for p in chosen],
                         slots=slots, key="actual")


def verdict(acc: dict[str, dict], outcome: dict) -> dict:
    acc_pass = all(v["pass"] for v in acc.values())
    out_pass = bool(outcome["pass"])
    if acc_pass and out_pass:
        decision = "flip"
    elif not acc_pass and not out_pass:
        decision = "stay"
    else:
        decision = "split"
    v = {"accuracy_pass": acc_pass, "outcome_pass": out_pass, "decision": decision}

    # Contamination is not a footnote. Either of these means the outcome half
    # did not measure what it claims, so no decision may be read off it.
    invalid = []
    if not outcome.get("errors_clean", True):
        invalid.append(f"engine errors {outcome['errors']}: an exception falls back to the "
                       "best available player, a different drafting policy, so the arms were "
                       "not graded on the same engine")
    if outcome.get("inert"):
        invalid.append("the candidate drafted an identical roster to its first rival in every "
                       "slot: the outcome half tested nothing")
    v["invalid"] = invalid
    if invalid:
        v["decision"] = "invalid"
    # Resolvability does NOT change the pre-registered verdict -- moving a
    # threshold after seeing numbers is the failure this repo names by name.
    # It is carried so the entry records how much of the delta is signal.
    v["resolvable"] = outcome.get("resolvable")
    v["delta_spread_pct"] = outcome.get("delta_spread")
    return v


def skill_shape(cfg: Config) -> tuple[int, int, dict[str, int]]:
    """League shape from the yaml, minus K/DEF (absent from history pools)."""
    teams, rounds, slots = EP.league_shape(cfg)
    slots = {k: v for k, v in slots.items() if k not in NO_KDEF}
    return teams, rounds - len(NO_KDEF), slots


# ------------------------------------------------------------- data plumbing

def history_board(cfg: Config, rows: pl.DataFrame, arm: str) -> list[dict]:
    """One history year's pool, projected by `arm`, through the production
    board code, loaded the way every replay loads a board.

    The history rows carry no team, depth chart or route data, so the
    columns the board code expects are present but empty (labelled absence,
    not invented values -- except exp_games, which the tracker requires
    numeric and which is set to the season convention for every player
    alike). Consequence, stated in the report: the handcuff (backs_up) and
    RB-receiving upside paths are inert on these boards for BOTH arms; only
    the rookie upside path can fire."""
    games = float(cfg["projections"].get("games", cfg["projections"].get("expected_games", 16.0)))
    df = (rows.filter(pl.col(arm).is_not_null())
          .select(pl.col("sleeper_id").cast(pl.Utf8), "name", "pos", "adp",
                  (pl.col(arm) * games / LINE_GAMES).alias("proj_pts"),
                  pl.col("usage").is_null().alias("rookie_flag"))
          .with_columns(pl.lit(None, dtype=pl.Utf8).alias("team"),
                        pl.lit(None, dtype=pl.Float64).alias("ecr"),
                        pl.lit(None, dtype=pl.Int64).alias("bye"),
                        pl.lit(arm).alias("proj_source"),
                        pl.lit(games).alias("exp_games"),
                        pl.lit(None, dtype=pl.Utf8).alias("avail_status"),
                        pl.lit(False).alias("no_market_flag"),
                        *[pl.lit(None, dtype=pl.Float64).alias(c) for c in ("wopr", "tprr", "yprr")]))
    tiers = finish_board(df, cfg)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "board.csv"
        write_tiers_csv(tiers, path)
        return EP.load_board(str(path))


def dedupe_names(rows: pl.DataFrame) -> pl.DataFrame:
    """Boards are keyed by name downstream; two pool players sharing one
    name get the id appended so neither grades as the other."""
    dup = rows.group_by(["pair", "name"]).len().filter(pl.col("len") > 1).select("pair", "name")
    if dup.height == 0:
        return rows
    return rows.join(dup.with_columns(pl.lit(True).alias("_dup")), on=["pair", "name"], how="left").with_columns(
        pl.when(pl.col("_dup")).then(pl.col("name") + " (" + pl.col("sleeper_id").cast(pl.Utf8) + ")")
        .otherwise(pl.col("name")).alias("name")).drop("_dup")


def run_outcome(league: str, rows: pl.DataFrame, candidate: str = EXTERNAL_ARM,
                rivals: tuple = (MODEL_ARM,), seeds: tuple = (None,),
                jitter: float = JITTER_PICKS) -> list[dict]:
    """Test 2 for one league: every arm replayed against the SAME rival list;
    per-slot results keyed by arm name only (see pooled_accuracy on why no
    alias keys); each pair record names its candidate, rivals and seed.

    One record per (pair, seed). Within a record every arm faces one rival
    list at one seat, so the delta stays paired; across seeds the rival room
    is redrawn, which is what supplies an error bar (see rival_order)."""
    arms = [candidate, *rivals]
    cfg = Config.load(league=league)
    teams, skill_rounds, slots = skill_shape(cfg)
    out = []
    for pair in sorted(rows["pair"].unique().to_list()):
        sub = rows.filter(pl.col("pair") == pair)
        actual = {r["name"]: float(r["actual"]) for r in sub.select("name", "actual").iter_rows(named=True)}
        boards = {arm: history_board(cfg, sub, arm) for arm in arms}
        for seed in seeds:
            rivals_list = rival_order(sub, seed, jitter)
            # depth is set by the SHARED pool, never by one arm's coverage
            rounds = min(skill_rounds, len(rivals_list) // teams - 1)
            rec = {"league": league, "pair": pair, "seed": seed, "teams": teams,
                   "rounds": rounds, "skill_rounds": skill_rounds,
                   "rounds_capped_by_pool": bool(rounds < skill_rounds),
                   "rival_pool": len(rivals_list),
                   "candidate": candidate, "rivals": list(rivals),
                   "board_sizes": {a: len(b) for a, b in boards.items()}, "slots": []}
            first = rivals[0]
            for slot in range(1, teams + 1):
                row = {"slot": slot}
                for arm in arms:
                    chosen, errs = adp_replay(boards[arm], rivals_list, slot, teams, rounds, slots)
                    row[arm] = grade_actual(chosen, actual, slots)
                    row[f"{arm}_errors"] = errs
                    row[f"{arm}_roster"] = [f"{p['name']} ({p['pos']})" for p in chosen]
                # how many of our own picks the candidate actually changed. An
                # arm that draft-for-draft matches its rival cannot have earned
                # its outcome number; see summarize_outcome's inertness check.
                row["picks_differing"] = sum(
                    1 for x, y in zip(row[f"{first}_roster"], row[f"{candidate}_roster"]) if x != y)
                row["picks_total"] = len(row[f"{first}_roster"])
                rec["slots"].append(row)
                print(f"  {league} {pair} seed {seed} slot {slot:>2}: {first} {row[first]:.0f}  "
                      f"{candidate} {row[candidate]:.0f}  delta {row[candidate] - row[first]:+.0f}", flush=True)
            out.append(rec)
    return out


def summarize_outcome(pairs: list[dict], candidate: str = EXTERNAL_ARM, rivals: tuple = (MODEL_ARM,)) -> dict:
    """Pass = the candidate's mean lineup points are within OUTCOME_TOL of
    EVERY rival's (never below); the summary keys model_mean / delta_mean /
    better / worse / tied describe the candidate against the FIRST rival.

    The pre-registered threshold is unchanged. What is added here is whether
    the measurement can resolve it: `by_seed` gives the per-seed mean delta
    and `delta_spread` its range, so a delta smaller than the spread is
    reported as unresolved instead of as a result.
    """
    first = rivals[0]
    e = [s[candidate] for p in pairs for s in p["slots"]]
    summary = {"n": len(e), "ext_mean": st.mean(e), "candidate": candidate, "rivals": list(rivals), "vs": {}}
    for r in rivals:
        m = [s[r] for p in pairs for s in p["slots"]]
        d = [b - a for a, b in zip(m, e)]
        summary["vs"][r] = {"model_mean": st.mean(m), "delta_mean": st.mean(d),
                            "better": sum(x > 0 for x in d), "worse": sum(x < 0 for x in d), "tied": sum(x == 0 for x in d),
                            "pass": bool(summary["ext_mean"] >= st.mean(m) * (1 - OUTCOME_TOL))}
    head = summary["vs"][first]
    summary.update({k: head[k] for k in ("model_mean", "delta_mean", "better", "worse", "tied")})
    summary["by_pair"] = [{"league": p["league"], "pair": p["pair"], "seed": p.get("seed"),
                           "model_mean": st.mean(s[first] for s in p["slots"]),
                           "ext_mean": st.mean(s[candidate] for s in p["slots"])} for p in pairs]
    summary["pass"] = all(v["pass"] for v in summary["vs"].values())

    # --- can the harness resolve the threshold it is asked to judge? --------
    seeds = list(dict.fromkeys(p.get("seed") for p in pairs))
    by_seed = []
    for sd in seeds:
        sl = [s for p in pairs if p.get("seed") == sd for s in p["slots"]]
        dm = st.mean(s[candidate] - s[first] for s in sl)
        by_seed.append({"seed": sd, "n": len(sl), "delta_mean": dm,
                        "pct": 100 * dm / st.mean(s[first] for s in sl)})
    summary["by_seed"] = by_seed
    pcts = [b["pct"] for b in by_seed]
    summary["delta_spread"] = (max(pcts) - min(pcts)) if len(pcts) > 1 else None
    summary["delta_pct"] = 100 * head["delta_mean"] / head["model_mean"]
    summary["resolvable"] = (None if summary["delta_spread"] is None
                             else bool(abs(summary["delta_pct"]) > summary["delta_spread"]))
    summary["seeds"] = seeds

    # --- contamination guards: these fail the run, they are not footnotes ---
    errs = {a: sum(s.get(f"{a}_errors", 0) for p in pairs for s in p["slots"])
            for a in [candidate, *rivals]}
    summary["errors"] = errs
    # An engine exception falls back to avail[0], a different and dumber
    # drafting policy. If one arm throws more often than another it is being
    # graded on a partly different policy, so the comparison is contaminated.
    summary["errors_clean"] = bool(max(errs.values()) == 0)
    diff = sum(s.get("picks_differing", 0) for p in pairs for s in p["slots"])
    tot = sum(s.get("picks_total", 0) for p in pairs for s in p["slots"])
    summary["picks_differing"], summary["picks_total"] = diff, tot
    # A candidate that drafts what its rival drafts has not been tested by the
    # outcome half at all, and its "pass" would be a null result wearing a
    # passing grade.
    summary["inert"] = bool(tot and diff == 0)
    summary["capped_pairs"] = [f"{p['league']} {p['pair']} seed {p.get('seed')}: "
                               f"{p['rounds']} of {p['skill_rounds']} rounds "
                               f"(pool {p['rival_pool']})"
                               for p in pairs if p.get("rounds_capped_by_pool")]
    return summary


def render(acc: dict[str, dict], pairs: list[dict], outcome: dict, v: dict) -> str:
    c = outcome.get("candidate", EXTERNAL_ARM)
    rivals = list(outcome.get("rivals") or [MODEL_ARM])
    m = rivals[0]
    L = ["# Projection-source gate (DECISIONS #23)", ""]
    if c != EXTERNAL_ARM or rivals != [MODEL_ARM]:
        L += [f"Arms: in every table below `model` is the first rival (`{m}`) and `external` is the "
              f"candidate (`{c}`); rivals judged: {', '.join(f'`{r}`' for r in rivals)}.", ""]
    L += [
         f"Decision: **{v['decision']}** — accuracy {'pass' if v['accuracy_pass'] else 'FAIL'}, "
         f"outcome {'pass' if v['outcome_pass'] else 'FAIL'}. Thresholds pre-registered: MAE within "
         f"{MAE_TOL:.0%}, Spearman within {RHO_TOL}, outcome within {OUTCOME_TOL:.0%}.", "",
         "`model` = usage + log-rank blend. `external` = outside stat lines; in history only Sleeper's "
         "week-1 lines exist and stand in for the 2026 sheet + Sleeper combination. The 2026 sheet itself "
         "cannot be judged until 2026 is played.", "",
         "## Test 1 — accuracy (rows every arm projected, both pairs pooled)", "",
         "| league | n | model MAE | external MAE | ratio | model ρ (weighted) | external ρ | Δρ | pass |",
         "|---|---|---|---|---|---|---|---|---|"]
    for lg, a in acc.items():
        L.append(f"| {lg} | {a['n']} | {a[m + '_mae']:.1f} | {a[c + '_mae']:.1f} | {a['mae_ratio']:.3f} | "
                 f"{a[m + '_rho']:.3f} | {a[c + '_rho']:.3f} | {a['rho_delta']:+.3f} | {'yes' if a['pass'] else 'NO'} |")
    L += ["", "Per cell (pair × position):", "",
          "| league | pair | pos | n | model MAE | external MAE | model ρ | external ρ |", "|---|---|---|---|---|---|---|---|"]
    for lg, a in acc.items():
        for cell in a["by_cell"]:
            L.append(f"| {lg} | {cell['pair']} | {cell['pos']} | {cell['n']} | {cell[m + '_mae']:.1f} | {cell[c + '_mae']:.1f} | "
                     f"{cell[m + '_rho']:.3f} | {cell[c + '_rho']:.3f} |")
    L += ["", "## Test 2 — outcome (shared rival list, engine at every slot, lineups graded on actual points)", "",
          f"Over {outcome['n']} slot-drafts: model {outcome['model_mean']:.1f}, external {outcome['ext_mean']:.1f} "
          f"(Δ {outcome['delta_mean']:+.1f}, {outcome['delta_pct']:+.2f}%); external better in "
          f"{outcome['better']}, worse in {outcome['worse']}, tied {outcome['tied']}. Pass: {'yes' if outcome['pass'] else 'NO'}.", ""]
    if v.get("invalid"):
        L += ["**This run is INVALID and no decision may be read off it.**", ""] + \
             [f"- {x}" for x in v["invalid"]] + [""]
    L += [f"Engine errors (exception → best-available fallback): "
          f"{', '.join(f'`{a}` {n}' for a, n in outcome['errors'].items())}. "
          f"Our own picks the candidate changed: {outcome['picks_differing']} of "
          f"{outcome['picks_total']}"
          f"{' — **the candidate is inert here**' if outcome.get('inert') else ''}.", ""]
    if outcome.get("capped_pairs"):
        L += ["Replay depth was capped by a thin rival pool, so these graded fewer rounds of "
              "bench construction than the league plays:", ""] + \
             [f"- {x}" for x in outcome["capped_pairs"]] + [""]

    # --- resolvability ------------------------------------------------------
    seeds = outcome.get("seeds") or [None]
    if len(seeds) > 1:
        L += ["### Is the delta bigger than the noise?", "",
              "With rivals pinned to exact consensus ADP, every replay of a pair makes the same "
              "rival picks, so its slot-drafts are one draft universe sampled at each seat rather "
              "than independent draws — and neighbouring seats see nearly the same board. Each "
              f"seed below redraws the rival room (Gaussian noise of {JITTER_PICKS:.0f} picks on "
              "ADP, the same draw for every arm, so the per-slot comparison stays paired).", "",
              "| seed | n | Δ mean | Δ % |", "|---|---|---|---|"]
        for b in outcome["by_seed"]:
            L.append(f"| {b['seed'] if b['seed'] is not None else 'exact ADP'} | {b['n']} | "
                     f"{b['delta_mean']:+.1f} | {b['pct']:+.2f}% |")
        spread = outcome.get("delta_spread")
        res = outcome.get("resolvable")
        L += ["", f"Observed Δ {outcome['delta_pct']:+.2f}%, spread across seeds {spread:.2f} points of "
              f"percentage. **{'The delta exceeds the seed spread' if res else 'The delta is inside the seed spread, so this harness cannot resolve it'}"
              f"** at {len(seeds)} seeds. The pre-registered {OUTCOME_TOL:.0%} threshold is unchanged; "
              "this line records how much of the measured delta is signal, and never moves the bar.", ""]
    else:
        L += ["Rivals were pinned to exact consensus ADP (one seed), so the slot-drafts of a pair "
              "are one draft universe sampled at each seat, not independent draws. Re-run with "
              "`--seeds N` for an error bar.", ""]

    L += ["| league | pair | seed | model mean | external mean | Δ |", "|---|---|---|---|---|---|"]
    for b in outcome["by_pair"]:
        L.append(f"| {b['league']} | {b['pair']} | {b['seed'] if b['seed'] is not None else 'exact'} | "
                 f"{b['model_mean']:.1f} | {b['ext_mean']:.1f} | {b['ext_mean'] - b['model_mean']:+.1f} |")
    for p in pairs:
        L += ["", f"### {p['league']} {p['pair']} seed {p.get('seed') if p.get('seed') is not None else 'exact'} — "
              f"{p['teams']} teams, {p['rounds']} of {p['skill_rounds']} rounds, rival pool {p['rival_pool']}, "
              f"boards {p['board_sizes'][m]} / {p['board_sizes'][c]}", "",
              "| slot | model | external | Δ | engine errors | picks changed |", "|---|---|---|---|---|---|"]
        for s in p["slots"]:
            L.append(f"| {s['slot']} | {s[m]:.0f} | {s[c]:.0f} | {s[c] - s[m]:+.0f} | "
                     f"{s[m + '_errors']}/{s[c + '_errors']} | "
                     f"{s.get('picks_differing', '?')}/{s.get('picks_total', '?')} |")
    L += ["", "### What this harness does not test", "",
          "- Both arms face one rival list per (pair, seed), so a player one arm never projected is "
          "still taken by the rivals at his ADP; only our own picks differ.",
          "- Rivals reach and fall independently around ADP. Position runs and tier cliffs, where "
          "rivals correlate with each other, are not modelled, so the seed spread bounds rival "
          "variance from below.",
          "- K/DEF are absent from both arms.",
          "- The history rows carry no team, depth-chart or route data, so the handcuff and "
          "RB-receiving upside flags are inert on these boards for both arms; only the rookie "
          "upside path is live.",
          "- `ecr` is null on these boards, so any board-side market-rank path is dead here. An arm "
          "that differs from its rival only through ECR would show up as inert above rather than as "
          "a pass; the picks-changed column is what distinguishes the two cases.", ""]
    return "\n".join(L) + "\n"


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")   # Windows console/pipe default is cp1252
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--leagues", default="keefamania,omnibeta")
    ap.add_argument("--candidate", default=EXTERNAL_ARM, help="arm under test (a column of the rows csv)")
    ap.add_argument("--rivals", default=MODEL_ARM, help="comma list of arms it must not be worse than")
    ap.add_argument("--rows", default=None,
                    help="comma list of rows csvs, one per league in --leagues order (default: the backtest exports)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--seeds", type=int, default=1,
                    help=f"rival-room redraws for an error bar (default 1 = exact consensus ADP "
                         f"only, reproducing every pre-seed result; {DEFAULT_SEEDS} is a usable bar)")
    ap.add_argument("--jitter", type=float, default=JITTER_PICKS,
                    help="sd of the ADP noise, in picks, for seeds after the first")
    a = ap.parse_args()
    # seed None is always first: it is the exact-consensus run every earlier
    # entry in DECISIONS was measured on, so a re-run stays comparable.
    seeds = tuple([None] + list(range(1, a.seeds))) if a.seeds > 0 else (None,)
    leagues = [x.strip() for x in a.leagues.split(",") if x.strip()]
    rivals = tuple(x.strip() for x in a.rivals.split(",") if x.strip())
    row_files = ([Path(x) for x in a.rows.split(",")] if a.rows
                 else [ROOT / "reports" / f"projection_backtest.{lg}.rows.csv" for lg in leagues])
    acc, pairs = {}, []
    for lg, src in zip(leagues, row_files):
        if not src.exists():
            raise SystemExit(f"{src} missing: run scripts/projection_backtest.py --league {lg} first")
        rows = dedupe_names(pl.read_csv(src, infer_schema_length=10000))
        acc[lg] = pooled_accuracy(rows, a.candidate, rivals)
        m, c = rivals[0], a.candidate
        print(f"{lg} accuracy: {m} MAE {acc[lg][m + '_mae']:.1f} rho {acc[lg][m + '_rho']:.3f} | "
              f"{c} MAE {acc[lg][c + '_mae']:.1f} rho {acc[lg][c + '_rho']:.3f} -> "
              f"{'pass' if acc[lg]['pass'] else 'FAIL'}", flush=True)
        pairs += run_outcome(lg, rows, a.candidate, rivals, seeds, a.jitter)
    outcome = summarize_outcome(pairs, a.candidate, rivals)
    v = verdict(acc, outcome)
    md = render(acc, pairs, outcome, v)
    out = Path(a.out) if a.out else ROOT / "reports" / "source_gate.md"
    out.write_text(md, encoding="utf-8")
    out.with_suffix(".json").write_text(json.dumps(
        {"accuracy": acc, "outcome": outcome, "verdict": v, "pairs": pairs}, indent=1), encoding="utf-8")
    print(f"\nverdict: {v}\n-> {out}")
    if v["invalid"]:
        raise SystemExit("gate INVALID: " + "; ".join(v["invalid"]))


if __name__ == "__main__":
    main()
