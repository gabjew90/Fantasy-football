"""Which replacement baseline drafts the better team?

Baselines do not change `proj_pts`. So build the board at each candidate,
draft with each against the archived draft's rivals at every slot, and score
the resulting starting lineup on PROJECTED POINTS, which is identical across
boards. Nothing here can grade itself: the boards disagree about value, and
the scoreboard belongs to neither of them.

Candidates (plan 2026-09-02 A4, DECISIONS #33), per league on its own log
and its own starter shape:

  yaml        the league yaml's replacement_baselines as they stand
  flex        derive_baselines with the league's derived flex_split
  flex+bench  the same plus the RB/WR bench allowance

Rule (pre-registered): a candidate replaces the yaml baselines in a league
only if its mean is >= the yaml's AND it wins at least as many slots as it
loses; ties keep the yaml. "No change" is a valid result.

    venv\\Scripts\\python.exe scripts\\baseline_bakeoff.py --league keefamania
    venv\\Scripts\\python.exe scripts\\baseline_bakeoff.py --league omnibeta
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import polars as pl  # noqa: E402

import engine_parity as EP  # noqa: E402
from slot_replay import lineup_points, replay, shape  # noqa: E402

from draftkit.config import Config  # noqa: E402
from draftkit.onboard import derive_baselines  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LOGS = {"keefamania": "1396184666897145856:10", "omnibeta": "1395566812157984768:12"}
POS = ("QB", "RB", "WR", "TE", "K", "DEF")


def build_board(cfg: Config, baselines: dict[str, int], out: Path) -> list[dict]:
    """cmd_tiers, minus the reporting, with the baselines swapped."""
    from draftkit.projections import PROJECTION_FNS
    from draftkit.tiers import finish_board, write_tiers_csv
    from draftkit.tilts import apply_tilts, prior_top5_by_pos

    processed = cfg.path("processed")
    market = pl.read_parquet(cfg.scoped(processed / "market.parquet"))
    usage = pl.read_parquet(cfg.scoped(processed / "usage.parquet"))
    df = PROJECTION_FNS["default"](cfg, usage, market)
    df, _ = apply_tilts(df, cfg.get("tilts"), prior_top5_by_pos(usage))
    write_tiers_csv(finish_board(df, cfg, baselines), out)
    return EP.load_board(str(out))


def candidates(cfg: Config) -> list[tuple[str, dict[str, int]]]:
    teams, _rounds, _slots = EP.league_shape(cfg)
    roster = list(cfg["expected"]["roster"])
    scoring = cfg.get("scoring") or (cfg.get("expected") or {}).get("scoring") or {}
    split = cfg.get("flex_split")
    yaml_b = {p: int(v) for p, v in cfg.baselines.items()}
    flex_b = derive_baselines(teams, roster, scoring=scoring, flex_split=split)
    bench_b = derive_baselines(teams, roster, scoring=scoring, flex_split=split, bench_allowance=True)
    return [("yaml", yaml_b), ("flex", flex_b), ("flex+bench", bench_b)]


def fmt(b: dict[str, int]) -> str:
    return "/".join(f"{p}{b.get(p, 0)}" for p in POS if b.get(p))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", default="keefamania")
    ap.add_argument("--logs", default=None, help="draft_id:teams (default: the league's archived 2026 draft)")
    ap.add_argument("--scratch", default="data/draftrig")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    cfg = Config.load(league=a.league)
    teams, _rounds_cfg, slots = EP.league_shape(cfg)
    scratch = Path(a.scratch)
    scratch.mkdir(parents=True, exist_ok=True)

    did, log_teams = (a.logs or LOGS[a.league]).split(":")
    if int(log_teams) != teams:
        raise SystemExit(f"log says {log_teams} teams, league yaml says {teams}")
    log = [json.loads(line) for line in open(f"data/logs/draft_{did}.jsonl", encoding="utf-8")
           if '"type": "pick"' in line]
    log.sort(key=lambda d: d["pick_no"])
    rounds = max(d["round"] for d in log)

    cands = candidates(cfg)
    print(f"Baseline bake-off -- {a.league}, draft {did}, {teams} slots, starters {slots}\n")
    print("scoring: PROJECTED POINTS of the starting lineup (identical across boards -- baselines cannot move it)\n")
    for label, b in cands:
        print(f"  {label:11} {fmt(b)}")
    print()

    results: dict[str, list[float]] = {}
    shapes: dict[str, list[str]] = {}
    for label, b in cands:
        board = build_board(cfg, b, scratch / f"tiers_bakeoff_{a.league}_{label.replace('+', '_')}.csv")
        pts, shp = [], []
        for s in range(1, teams + 1):
            chosen = replay(board, log, s, teams, rounds, True, slots=slots)
            pts.append(lineup_points(chosen, slots=slots))
            shp.append(shape(chosen))
        results[label], shapes[label] = pts, shp
        qb2 = sum(1 for x in shp if "QB2" in x or "QB3" in x)
        print(f"{label:11} mean {st.mean(pts):8.1f}   median {st.median(pts):8.1f}   min {min(pts):7.1f}   "
              f"2+QB rosters {qb2}/{len(shp)}")

    base = cands[0][0]
    L = [f"# Baseline bake-off -- {a.league}, draft {did}, {teams} slots", "",
         "Scoring: projected points of the best legal starting lineup on the league's own shape "
         f"({', '.join(f'{k} {v}' for k, v in slots.items())}). Rule (DECISIONS #33): a candidate replaces the "
         "yaml baselines only if mean >= yaml AND wins >= losses; ties keep the yaml.", "",
         "| candidate | baselines | mean | median | min | vs yaml mean | better | worse | tied |",
         "|---|---|---|---|---|---|---|---|---|"]
    print(f"\nvs {base}:")
    verdict = {}
    for label, b in cands:
        d = [n - o for n, o in zip(results[label], results[base])]
        better, worse, tied = sum(x > 0 for x in d), sum(x < 0 for x in d), sum(x == 0 for x in d)
        wins = label != base and st.mean(d) >= 0 and better >= worse and (better or st.mean(d) > 0)
        verdict[label] = bool(wins)
        L.append(f"| {label} | {fmt(b)} | {st.mean(results[label]):.1f} | {st.median(results[label]):.1f} | "
                 f"{min(results[label]):.1f} | {st.mean(d):+.1f} | {better} | {worse} | {tied} |")
        if label != base:
            print(f"  {label:11} mean {st.mean(d):+7.1f}  better {better:>2}  worse {worse:>2}  tied {tied:>2}"
                  f"  -> {'passes the rule' if wins else 'keeps the yaml'}")
    L += ["", "Per slot (projected lineup points):", "",
          "| slot | " + " | ".join(l for l, _b in cands) + " |", "|---|" + "---|" * len(cands)]
    for i in range(teams):
        L.append(f"| {i + 1} | " + " | ".join(f"{results[l][i]:.0f}" for l, _b in cands) + " |")
    L += ["", "Roster shapes (yaml arm): " + ", ".join(shapes[base]), ""]
    out = Path(a.out) if a.out else ROOT / "reports" / f"baseline_bakeoff.{a.league}.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
