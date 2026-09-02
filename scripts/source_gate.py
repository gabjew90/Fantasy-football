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

Test 2, OUTCOME -- both arms built into boards through the production code
(add_vorp, build_tiers, handcuff and upside flags), replayed through the
SAME engine at every draft slot against rivals drafting in that year's ADP
order, each roster graded on the ACTUAL season points of its best legal
lineup. K/DEF are absent from the history pools and removed from the slots
for both arms. external fails if its mean lineup points over all slots,
pairs and leagues are more than 1% below the model's.

Churn is not a gate; scripts/input_replay.py reports it by tier.

    venv\\Scripts\\python.exe scripts\\source_gate.py --leagues keefamania,omnibeta
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
import tempfile
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import engine_parity as EP  # noqa: E402
from draftkit import snake  # noqa: E402
from draftkit.config import Config  # noqa: E402
from draftkit.tiers import add_handcuff_info, add_upside_flags, build_tiers, write_tiers_csv  # noqa: E402
from draftkit.vorp import add_vorp  # noqa: E402

ARMS = ("usage", "curve", "blend", "lines")
MODEL_ARM, EXTERNAL_ARM = "blend", "lines"
LINE_GAMES = 17.0
FLEX_OK = ("RB", "WR", "TE")
# pre-registered thresholds (DECISIONS #23)
MAE_TOL, RHO_TOL, OUTCOME_TOL = 0.02, 0.02, 0.01
SLOTS_BY_LEAGUE = {
    "keefamania": {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1},
    "omnibeta": {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 2},
}
TEAMS_BY_LEAGUE = {"keefamania": 10, "omnibeta": 12}
SKILL_ROUNDS = 13          # 15 minus K and DEF


# ---------------------------------------------------------------- pure parts

def spearman(a: list[float], b: list[float]) -> float:
    def ranks(x):
        order = sorted(range(len(x)), key=lambda i: x[i])
        r = [0.0] * len(x)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and x[order[j + 1]] == x[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    n = len(a)
    if n < 3:
        return float("nan")
    ra, rb = ranks(a), ranks(b)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = sum((x - ma) ** 2 for x in ra) ** 0.5
    vb = sum((y - mb) ** 2 for y in rb) ** 0.5
    return cov / (va * vb) if va and vb else float("nan")


def pooled_accuracy(rows: pl.DataFrame, model: str = MODEL_ARM, ext: str = EXTERNAL_ARM) -> dict:
    """Test 1 for one league. Rows every arm projected; pooled MAE and the
    n-weighted mean of per-(pair, pos) Spearman, for both arms."""
    common = rows.filter(pl.all_horizontal([pl.col(a).is_not_null() for a in ARMS]))
    out = {"n": common.height, "by_cell": []}
    for arm in (model, ext):
        err = (common[arm] - common["actual"]).abs()
        out[f"{arm}_mae"] = float(err.mean()) if common.height else float("nan")
    wsum = {model: 0.0, ext: 0.0}
    for (pair, pos), cell in sorted(common.group_by(["pair", "pos"]), key=lambda kv: kv[0]):
        n = cell.height
        rec = {"pair": pair, "pos": pos, "n": n}
        for arm in (model, ext):
            rho = spearman(cell[arm].to_list(), cell["actual"].to_list())
            rec[f"{arm}_rho"] = rho
            rec[f"{arm}_mae"] = float((cell[arm] - cell["actual"]).abs().mean())
            if rho == rho:      # not nan
                wsum[arm] += rho * n
        out["by_cell"].append(rec)
    for arm in (model, ext):
        out[f"{arm}_rho"] = wsum[arm] / common.height if common.height else float("nan")
    out["mae_ratio"] = out[f"{ext}_mae"] / out[f"{model}_mae"] if out.get(f"{model}_mae") else float("nan")
    out["rho_delta"] = out[f"{ext}_rho"] - out[f"{model}_rho"]
    out["pass"] = bool(out["mae_ratio"] <= 1 + MAE_TOL and out["rho_delta"] >= -RHO_TOL)
    return out


def lineup_actual(chosen: list[dict], actual_by_name: dict[str, float], slots: dict) -> float:
    """Actual season points of the best legal lineup (no K/DEF in history)."""
    rem, flex, total = dict(slots), int(slots.get("FLEX", 0)), 0.0
    graded = sorted(chosen, key=lambda p: -float(actual_by_name.get(p["name"], 0.0)))
    for p in graded:
        pts = float(actual_by_name.get(p["name"], 0.0))
        if rem.get(p["pos"], 0) > 0:
            rem[p["pos"]] -= 1
            total += pts
        elif p["pos"] in FLEX_OK and flex > 0:
            flex -= 1
            total += pts
    return total


def adp_replay(board: list[dict], my_slot: int, teams: int, rounds: int, slots: dict) -> tuple[list[dict], int]:
    """Rivals take the best remaining ADP; our picks are the engine's top
    recommendation at every turn. Returns (our roster, engine errors)."""
    by_name = {p["name"]: p for p in board}
    adp_order = sorted((p for p in board if p.get("adp")), key=lambda p: float(p["adp"]))
    taken: set[str] = set()
    chosen, picks, errors = [], [], 0
    for pick_no in range(1, teams * rounds + 1):
        rnd, slot = snake.pick_to_round_slot(pick_no, teams)
        if slot != my_slot:
            p = next((q for q in adp_order if q["name"] not in taken), None)
            if p is None:
                break
            taken.add(p["name"])
            picks.append({"pick_no": pick_no, "player_id": p["sleeper_id"], "draft_slot": slot, "round": rnd})
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


def verdict(acc: dict[str, dict], outcome: dict) -> dict:
    acc_pass = all(v["pass"] for v in acc.values())
    out_pass = bool(outcome["pass"])
    if acc_pass and out_pass:
        decision = "flip"
    elif not acc_pass and not out_pass:
        decision = "stay"
    else:
        decision = "split"
    return {"accuracy_pass": acc_pass, "outcome_pass": out_pass, "decision": decision}


# ------------------------------------------------------------- data plumbing

def history_board(cfg: Config, rows: pl.DataFrame, arm: str) -> list[dict]:
    """One history year's pool, projected by `arm`, through the production
    board code, loaded the way every replay loads a board."""
    games = float(cfg["projections"].get("games", cfg["projections"].get("expected_games", 16.0)))
    df = (rows.filter(pl.col(arm).is_not_null())
          .select(pl.col("sleeper_id").cast(pl.Utf8), "name", "pos", "adp",
                  (pl.col(arm) * games / LINE_GAMES).alias("proj_pts"),
                  pl.col("usage").is_null().alias("rookie_flag"))
          .with_columns(pl.lit(None, dtype=pl.Utf8).alias("team"),
                        pl.lit(None, dtype=pl.Float64).alias("ecr"),
                        pl.lit(None, dtype=pl.Int64).alias("bye"),
                        pl.lit(arm).alias("proj_source"),
                        pl.lit(16.0).alias("exp_games"),
                        pl.lit(None, dtype=pl.Utf8).alias("avail_status"),
                        pl.lit(False).alias("no_market_flag"),
                        *[pl.lit(None, dtype=pl.Float64).alias(c) for c in ("wopr", "tprr", "yprr")]))
    df = add_vorp(df, cfg.baselines)
    tiers = add_upside_flags(add_handcuff_info(build_tiers(df, cfg)))
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


def run_outcome(league: str, rows: pl.DataFrame) -> list[dict]:
    cfg = Config.load(league=league)
    teams, slots = TEAMS_BY_LEAGUE[league], SLOTS_BY_LEAGUE[league]
    out = []
    for pair in sorted(rows["pair"].unique().to_list()):
        sub = rows.filter(pl.col("pair") == pair)
        actual = {r["name"]: float(r["actual"]) for r in sub.select("name", "actual").iter_rows(named=True)}
        boards = {arm: history_board(cfg, sub, arm) for arm in (MODEL_ARM, EXTERNAL_ARM)}
        rounds = min(SKILL_ROUNDS, min(len(b) for b in boards.values()) // teams - 1)
        rec = {"league": league, "pair": pair, "teams": teams, "rounds": rounds,
               "board_sizes": {a: len(b) for a, b in boards.items()}, "slots": []}
        for slot in range(1, teams + 1):
            row = {"slot": slot}
            for arm in (MODEL_ARM, EXTERNAL_ARM):
                chosen, errs = adp_replay(boards[arm], slot, teams, rounds, slots)
                row[arm] = lineup_actual(chosen, actual, slots)
                row[f"{arm}_errors"] = errs
                row[f"{arm}_roster"] = [f"{p['name']} ({p['pos']})" for p in chosen]
            rec["slots"].append(row)
            print(f"  {league} {pair} slot {slot:>2}: model {row[MODEL_ARM]:.0f}  external {row[EXTERNAL_ARM]:.0f}"
                  f"  Δ {row[EXTERNAL_ARM] - row[MODEL_ARM]:+.0f}", flush=True)
        out.append(rec)
    return out


def summarize_outcome(pairs: list[dict]) -> dict:
    m = [s[MODEL_ARM] for p in pairs for s in p["slots"]]
    e = [s[EXTERNAL_ARM] for p in pairs for s in p["slots"]]
    d = [b - a for a, b in zip(m, e)]
    summary = {"n": len(d), "model_mean": st.mean(m), "ext_mean": st.mean(e), "delta_mean": st.mean(d),
               "better": sum(x > 0 for x in d), "worse": sum(x < 0 for x in d), "tied": sum(x == 0 for x in d),
               "by_pair": [{"league": p["league"], "pair": p["pair"],
                            "model_mean": st.mean(s[MODEL_ARM] for s in p["slots"]),
                            "ext_mean": st.mean(s[EXTERNAL_ARM] for s in p["slots"])} for p in pairs]}
    summary["pass"] = bool(summary["ext_mean"] >= summary["model_mean"] * (1 - OUTCOME_TOL))
    return summary


def render(acc: dict[str, dict], pairs: list[dict], outcome: dict, v: dict) -> str:
    L = ["# Projection-source gate (DECISIONS #23)", "",
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
        L.append(f"| {lg} | {a['n']} | {a[MODEL_ARM + '_mae']:.1f} | {a[EXTERNAL_ARM + '_mae']:.1f} | {a['mae_ratio']:.3f} | "
                 f"{a[MODEL_ARM + '_rho']:.3f} | {a[EXTERNAL_ARM + '_rho']:.3f} | {a['rho_delta']:+.3f} | {'yes' if a['pass'] else 'NO'} |")
    L += ["", "Per cell (pair × position):", "",
          "| league | pair | pos | n | model MAE | external MAE | model ρ | external ρ |", "|---|---|---|---|---|---|---|---|"]
    for lg, a in acc.items():
        for c in a["by_cell"]:
            L.append(f"| {lg} | {c['pair']} | {c['pos']} | {c['n']} | {c[MODEL_ARM + '_mae']:.1f} | {c[EXTERNAL_ARM + '_mae']:.1f} | "
                     f"{c[MODEL_ARM + '_rho']:.3f} | {c[EXTERNAL_ARM + '_rho']:.3f} |")
    L += ["", "## Test 2 — outcome (ADP-order rivals, engine at every slot, lineups graded on actual points)", "",
          f"Over {outcome['n']} slot-drafts: model {outcome['model_mean']:.1f}, external {outcome['ext_mean']:.1f} "
          f"(Δ {outcome['delta_mean']:+.1f}, {100 * outcome['delta_mean'] / outcome['model_mean']:+.2f}%); external better in "
          f"{outcome['better']}, worse in {outcome['worse']}, tied {outcome['tied']}. Pass: {'yes' if outcome['pass'] else 'NO'}.", "",
          "| league | pair | model mean | external mean | Δ |", "|---|---|---|---|---|"]
    for b in outcome["by_pair"]:
        L.append(f"| {b['league']} | {b['pair']} | {b['model_mean']:.1f} | {b['ext_mean']:.1f} | {b['ext_mean'] - b['model_mean']:+.1f} |")
    for p in pairs:
        L += ["", f"### {p['league']} {p['pair']} — {p['teams']} teams, {p['rounds']} rounds, boards "
              f"{p['board_sizes'][MODEL_ARM]} / {p['board_sizes'][EXTERNAL_ARM]}", "",
              "| slot | model | external | Δ | engine errors |", "|---|---|---|---|---|"]
        for s in p["slots"]:
            L.append(f"| {s['slot']} | {s[MODEL_ARM]:.0f} | {s[EXTERNAL_ARM]:.0f} | {s[EXTERNAL_ARM] - s[MODEL_ARM]:+.0f} | "
                     f"{s[MODEL_ARM + '_errors']}/{s[EXTERNAL_ARM + '_errors']} |")
    L += ["", "Rivals never deviate from ADP here, so runs and reaches are absent; the comparison is between "
          "the two inputs under identical rivals, which is the question. K/DEF are absent from both arms.", ""]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--leagues", default="keefamania,omnibeta")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    leagues = [x.strip() for x in a.leagues.split(",") if x.strip()]
    acc, pairs = {}, []
    for lg in leagues:
        src = ROOT / "reports" / f"projection_backtest.{lg}.rows.csv"
        if not src.exists():
            raise SystemExit(f"{src} missing: run scripts/projection_backtest.py --league {lg} first")
        rows = dedupe_names(pl.read_csv(src, infer_schema_length=10000))
        acc[lg] = pooled_accuracy(rows)
        print(f"{lg} accuracy: model MAE {acc[lg][MODEL_ARM + '_mae']:.1f} ρ {acc[lg][MODEL_ARM + '_rho']:.3f} | "
              f"external MAE {acc[lg][EXTERNAL_ARM + '_mae']:.1f} ρ {acc[lg][EXTERNAL_ARM + '_rho']:.3f} -> "
              f"{'pass' if acc[lg]['pass'] else 'FAIL'}", flush=True)
        pairs += run_outcome(lg, rows)
    outcome = summarize_outcome(pairs)
    v = verdict(acc, outcome)
    md = render(acc, pairs, outcome, v)
    out = Path(a.out) if a.out else ROOT / "reports" / "source_gate.md"
    out.write_text(md, encoding="utf-8")
    out.with_suffix(".json").write_text(json.dumps(
        {"accuracy": acc, "outcome": outcome, "verdict": v, "pairs": pairs}, indent=1), encoding="utf-8")
    print(f"\nverdict: {v}\n-> {out}")


if __name__ == "__main__":
    main()
