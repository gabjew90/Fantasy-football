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
from projection_backtest import ARMS, spearman  # noqa: E402
from slot_replay import lineup_points  # noqa: E402
from draftkit import snake  # noqa: E402
from draftkit.config import Config  # noqa: E402
from draftkit.tiers import finish_board, write_tiers_csv  # noqa: E402

MODEL_ARM, EXTERNAL_ARM = "blend", "lines"
LINE_GAMES = 17.0
# pre-registered thresholds (DECISIONS #23)
MAE_TOL, RHO_TOL, OUTCOME_TOL = 0.02, 0.02, 0.01
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
    The #23 report keys are kept: MODEL_ARM-keyed values describe the FIRST
    rival, EXTERNAL_ARM-keyed values the candidate."""
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
    # the #23 report keys, for render()
    out[MODEL_ARM + "_mae"], out[MODEL_ARM + "_rho"] = out[f"{first}_mae"], out[f"{first}_rho"]
    out[EXTERNAL_ARM + "_mae"], out[EXTERNAL_ARM + "_rho"] = out[f"{candidate}_mae"], out[f"{candidate}_rho"]
    for c in out["by_cell"]:
        c[MODEL_ARM + "_mae"], c[MODEL_ARM + "_rho"] = c[f"{first}_mae"], c[f"{first}_rho"]
        c[EXTERNAL_ARM + "_mae"], c[EXTERNAL_ARM + "_rho"] = c[f"{candidate}_mae"], c[f"{candidate}_rho"]
    return out


def rival_order(rows: pl.DataFrame) -> list[str]:
    """The shared rival draft list: every pool player with an ADP, in ADP
    order, by name. Both arms face exactly this list."""
    return rows.filter(pl.col("adp").is_not_null()).sort("adp")["name"].to_list()


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
    return {"accuracy_pass": acc_pass, "outcome_pass": out_pass, "decision": decision}


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
                rivals: tuple = (MODEL_ARM,)) -> list[dict]:
    """Test 2 for one league: every arm replayed against the SAME rival list;
    per-slot results keyed by arm name, plus the #23 keys (MODEL_ARM = first
    rival, EXTERNAL_ARM = candidate) so render() and the summary read as before."""
    arms = [candidate, *rivals]
    cfg = Config.load(league=league)
    teams, skill_rounds, slots = skill_shape(cfg)
    out = []
    for pair in sorted(rows["pair"].unique().to_list()):
        sub = rows.filter(pl.col("pair") == pair)
        actual = {r["name"]: float(r["actual"]) for r in sub.select("name", "actual").iter_rows(named=True)}
        rivals_list = rival_order(sub)
        boards = {arm: history_board(cfg, sub, arm) for arm in arms}
        # depth is set by the SHARED pool, never by one arm's coverage
        rounds = min(skill_rounds, len(rivals_list) // teams - 1)
        rec = {"league": league, "pair": pair, "teams": teams, "rounds": rounds, "rival_pool": len(rivals_list),
               "candidate": candidate, "rivals": list(rivals),
               "board_sizes": {a: len(b) for a, b in boards.items()}, "slots": []}
        for slot in range(1, teams + 1):
            row = {"slot": slot}
            for arm in arms:
                chosen, errs = adp_replay(boards[arm], rivals_list, slot, teams, rounds, slots)
                row[arm] = grade_actual(chosen, actual, slots)
                row[f"{arm}_errors"] = errs
                row[f"{arm}_roster"] = [f"{p['name']} ({p['pos']})" for p in chosen]
            first = rivals[0]
            row[MODEL_ARM], row[EXTERNAL_ARM] = row[first], row[candidate]
            row[MODEL_ARM + "_errors"], row[EXTERNAL_ARM + "_errors"] = row[f"{first}_errors"], row[f"{candidate}_errors"]
            rec["slots"].append(row)
            print(f"  {league} {pair} slot {slot:>2}: model {row[MODEL_ARM]:.0f}  external {row[EXTERNAL_ARM]:.0f}"
                  f"  delta {row[EXTERNAL_ARM] - row[MODEL_ARM]:+.0f}", flush=True)
        out.append(rec)
    return out


def summarize_outcome(pairs: list[dict], candidate: str = EXTERNAL_ARM, rivals: tuple = (MODEL_ARM,)) -> dict:
    """Pass = the candidate's mean lineup points are within OUTCOME_TOL of
    EVERY rival's (never below); the #23 keys describe the first rival."""
    def col(arm, fallback):
        return arm if all(arm in s for p in pairs for s in p["slots"]) else fallback
    e = [s[col(candidate, EXTERNAL_ARM)] for p in pairs for s in p["slots"]]
    summary = {"n": len(e), "ext_mean": st.mean(e), "candidate": candidate, "vs": {}}
    for r in rivals:
        m = [s[col(r, MODEL_ARM)] for p in pairs for s in p["slots"]]
        d = [b - a for a, b in zip(m, e)]
        summary["vs"][r] = {"model_mean": st.mean(m), "delta_mean": st.mean(d),
                            "better": sum(x > 0 for x in d), "worse": sum(x < 0 for x in d), "tied": sum(x == 0 for x in d),
                            "pass": bool(summary["ext_mean"] >= st.mean(m) * (1 - OUTCOME_TOL))}
    first = summary["vs"][rivals[0]]
    summary.update({k: first[k] for k in ("model_mean", "delta_mean", "better", "worse", "tied")})
    summary["by_pair"] = [{"league": p["league"], "pair": p["pair"],
                           "model_mean": st.mean(s[MODEL_ARM] for s in p["slots"]),
                           "ext_mean": st.mean(s[EXTERNAL_ARM] for s in p["slots"])} for p in pairs]
    summary["pass"] = all(v["pass"] for v in summary["vs"].values())
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
    L += ["", "## Test 2 — outcome (shared ADP-order rivals, engine at every slot, lineups graded on actual points)", "",
          f"Over {outcome['n']} slot-drafts: model {outcome['model_mean']:.1f}, external {outcome['ext_mean']:.1f} "
          f"(Δ {outcome['delta_mean']:+.1f}, {100 * outcome['delta_mean'] / outcome['model_mean']:+.2f}%); external better in "
          f"{outcome['better']}, worse in {outcome['worse']}, tied {outcome['tied']}. Pass: {'yes' if outcome['pass'] else 'NO'}.", "",
          "| league | pair | model mean | external mean | Δ |", "|---|---|---|---|---|"]
    for b in outcome["by_pair"]:
        L.append(f"| {b['league']} | {b['pair']} | {b['model_mean']:.1f} | {b['ext_mean']:.1f} | {b['ext_mean'] - b['model_mean']:+.1f} |")
    for p in pairs:
        L += ["", f"### {p['league']} {p['pair']} — {p['teams']} teams, {p['rounds']} rounds, rival pool {p['rival_pool']}, "
              f"boards {p['board_sizes'][MODEL_ARM]} / {p['board_sizes'][EXTERNAL_ARM]}", "",
              "| slot | model | external | Δ | engine errors |", "|---|---|---|---|---|"]
        for s in p["slots"]:
            L.append(f"| {s['slot']} | {s[MODEL_ARM]:.0f} | {s[EXTERNAL_ARM]:.0f} | {s[EXTERNAL_ARM] - s[MODEL_ARM]:+.0f} | "
                     f"{s[MODEL_ARM + '_errors']}/{s[EXTERNAL_ARM + '_errors']} |")
    L += ["", "Both arms face one rival list (the year's pool in ADP order), so a player one arm never "
          "projected is still taken by the rivals at his ADP; only our own picks differ. Rivals never "
          "deviate from ADP, so runs and reaches are absent. K/DEF are absent from both arms. The history "
          "rows carry no team or route data, so the handcuff and RB-receiving upside flags are inert on "
          "these boards for both arms; only the rookie upside path is live.", ""]
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
    a = ap.parse_args()
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
        print(f"{lg} accuracy: model MAE {acc[lg][MODEL_ARM + '_mae']:.1f} rho {acc[lg][MODEL_ARM + '_rho']:.3f} | "
              f"external MAE {acc[lg][EXTERNAL_ARM + '_mae']:.1f} rho {acc[lg][EXTERNAL_ARM + '_rho']:.3f} -> "
              f"{'pass' if acc[lg]['pass'] else 'FAIL'}", flush=True)
        pairs += run_outcome(lg, rows, a.candidate, rivals)
    outcome = summarize_outcome(pairs, a.candidate, rivals)
    v = verdict(acc, outcome)
    md = render(acc, pairs, outcome, v)
    out = Path(a.out) if a.out else ROOT / "reports" / "source_gate.md"
    out.write_text(md, encoding="utf-8")
    out.with_suffix(".json").write_text(json.dumps(
        {"accuracy": acc, "outcome": outcome, "verdict": v, "pairs": pairs}, indent=1), encoding="utf-8")
    print(f"\nverdict: {v}\n-> {out}")


if __name__ == "__main__":
    main()
