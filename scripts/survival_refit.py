"""The survival refit (plan 2026-09-02 B7; pre-registered in DECISIONS #26).

The logged prose is report-only. The fit re-runs the simulation on every
archived state (picks made so far, seen from that room's real seat) with the
production board for the league, draft-day ADP, survival_shrink 1.0 and a
candidate knob set, and scores the RAW survival vector of every pooled
player against what the room actually did.

Objective: the mean over room types of the per-type log loss (equal weight
per type, so four autopick rooms cannot outvote the one human room). A
coordinate search on a coarse grid yields the best point ON THE GRID, not
identified parameters; nothing is reported finer than its grid step.

    venv\\Scripts\\python.exe scripts\\fit_survival.py --fit [--sims 200 --every 2 --workers N]
"""

from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from draftkit import snake  # noqa: E402
from draftkit.draftlog import sim_window  # noqa: E402
from draftkit.urgency import POSITIONS  # noqa: E402
from fit_survival import all_rooms, bucketize, norm  # noqa: E402

STAGES = (
    ("sigma", [{"sigma_early": e, "sigma_late": late}
               for e in (4.0, 6.0, 8.0, 10.0) for late in (15.0, 21.0, 27.0, 35.0)]),
    ("reach", [{"reach_prob": r} for r in (0.0, 0.10, 0.15, 0.25, 0.35)]),
    ("need", [{"need_damp": d} for d in (0.15, 0.30, 0.50)]),
    # ("autopick", [{"autopick_sigma_scale": s} for s in (0.25, 0.5, 0.75, 1.0)])  -> once plan step B5 exists
)
SMOKE_STAGES = (("sigma", [{"sigma_early": 6.0, "sigma_late": 27.0}, {"sigma_early": 8.0, "sigma_late": 27.0}]),)
CURRENT = {"sigma_early": 6.0, "sigma_late": 27.0, "reach_prob": 0.15, "need_damp": 0.15}
_ROOMS: list[dict] = []          # per-worker room contexts (set by _init_worker)


# ------------------------------------------------------------- room contexts

def league_for(room: dict) -> str:
    return "omnibeta" if int(room["teams"]) == 12 else "keefamania"


def room_date(room: dict, logs_dir: Path) -> str | None:
    if room["room_type"] == "yahoo_autopick":
        return None
    p = logs_dir / f"draft_{room['room']}.jsonl"
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            ts = json.loads(line).get("ts")
        except ValueError:
            continue
        if ts:
            return dt.datetime.utcfromtimestamp(float(ts)).strftime("%Y-%m-%d")
    return None


def latest_snapshot_before(hist_dir: Path, date: str) -> Path | None:
    snaps = sorted(p for p in hist_dir.glob("adp_*.json") if p.stem.replace("adp_", "") < date)
    return snaps[-1] if snaps else None


def room_context(room: dict, logs_dir: Path) -> dict:
    """Board, shape and pick sequence for replaying one room's states."""
    import engine_parity as EP
    from draftkit.config import Config
    league = league_for(room)
    cfg = Config.load(league=league)
    teams, rounds, slots = EP.league_shape(cfg)
    board = EP.load_board(str(ROOT / ("tiers.csv" if league == "omnibeta" else "tiers.keefamania.csv")))
    adp_note = "board adp (Yahoo rank on this league's board)"
    date = room_date(room, logs_dir)
    if date and room["room_type"] != "yahoo_autopick":
        snap = latest_snapshot_before(ROOT / "data" / "raw" / "adp_history", date)
        if snap is not None:
            adp = {norm(r["name"]): float(r["adp"]) for r in json.loads(snap.read_text(encoding="utf-8"))}
            hit = 0
            for p in board:
                a = adp.get(norm(p["name"]))
                if a is not None:
                    p["adp"] = a
                    hit += 1
            adp_note = f"{snap.name} ({hit}/{len(board)} board rows overridden)"
    by_norm: dict[str, dict] = {}
    for p in board:
        by_norm.setdefault(norm(p["name"]), p)
    picks = []
    for p in sorted(room["picks"], key=lambda x: int(x["pick_no"])):
        n = int(p["pick_no"])
        rnd, slot = snake.pick_to_round_slot(n, teams)
        picks.append({"pick_no": n, "round": rnd, "draft_slot": slot,
                      "player_id": by_norm.get(norm(p["player"]), {}).get("sleeper_id", "0"),
                      "metadata": {"position": p.get("pos") or ""}})
    return {"room": room["room"], "room_type": room["room_type"], "league": league, "cfg": cfg,
            "teams": teams, "rounds": rounds, "slots": slots, "board": board, "picks": picks,
            "picked_at": {norm(p["player"]): int(p["pick_no"]) for p in room["picks"]},
            "my_slot": int(room["my_slot"]), "n_picks": len(picks),
            "matched": sum(1 for p in picks if p["player_id"] != "0"),
            "adp_note": adp_note, "id2name": {p["sleeper_id"]: p["name"] for p in board}}


# ------------------------------------------------------------- evaluation

def state_rows(ctx: dict, cp: int, seat: int, point: dict, sims: int) -> list[tuple[float, bool, str]]:
    """(raw survival, survived, pos) for every pooled player at state cp
    (picks 1..cp-1 made), seen from `seat`, under knob set `point`."""
    import engine_parity as EP
    teams, rounds = ctx["teams"], ctx["rounds"]
    start, nxt = sim_window(cp, seat, teams, rounds)
    if start is None or nxt is None or nxt <= start or nxt > ctx["n_picks"] + 1:
        return []                                   # no window, or a window past the archive's end
    t = EP.make_tracker(ctx["board"], ctx["picks"][:cp - 1], seat, slots=ctx["slots"], teams=teams,
                        rounds=rounds, cfg=ctx["cfg"],
                        overrides={**point, "sims": sims, "survival_shrink": 1.0})
    rep = t.urgency_report()
    if not rep:
        return []
    out = []
    for pos in POSITIONS:
        u = rep.get(pos)
        if not u:
            continue
        for pid, p in (u.get("survival_raw") or {}).items():
            at = ctx["picked_at"].get(norm(ctx["id2name"].get(pid, "")))
            if at is not None and at < start:
                continue
            if at is not None and at < nxt and snake.pick_to_round_slot(at, teams)[1] == seat:
                continue                            # my own take inside the window: unobservable
            out.append((float(p), at is None or at >= nxt, pos))
    return out


def _init_worker(rooms_ctx):
    global _ROOMS
    _ROOMS = rooms_ctx


def _task(args):
    ri, cp, seat, point, sims = args
    try:
        return ri, state_rows(_ROOMS[ri], cp, seat, point, sims)
    except Exception as e:  # noqa: BLE001
        return ri, [("err", str(e)[:80], "")]


def logloss(rows) -> float:
    if not rows:
        return float("nan")
    eps = 1e-3
    s = 0.0
    for p, y, _pos in rows:
        p = min(1 - eps, max(eps, p))
        s += -(math.log(p) if y else math.log(1 - p))
    return s / len(rows)


def evaluate(ctxs: list[dict], point: dict, sims: int, every: int, all_slots: bool, workers: int) -> dict:
    tasks = []
    for ri, c in enumerate(ctxs):
        seats = range(1, c["teams"] + 1) if all_slots else [c["my_slot"]]
        for cp in range(1, c["n_picks"] + 1, every):
            for seat in seats:
                tasks.append((ri, cp, seat, point, sims))
    rows_by_type: dict[str, list] = defaultdict(list)
    errors = 0

    def absorb(ri, rows):
        nonlocal errors
        for r in rows:
            if r[0] == "err":
                errors += 1
            else:
                rows_by_type[ctxs[ri]["room_type"]].append(r)

    if workers > 1:
        with cf.ProcessPoolExecutor(max_workers=workers, initializer=_init_worker, initargs=(ctxs,)) as ex:
            for ri, rows in ex.map(_task, tasks, chunksize=4):
                absorb(ri, rows)
    else:
        _init_worker(ctxs)
        for a in tasks:
            absorb(*_task(a))
    ll = {k: logloss(v) for k, v in rows_by_type.items()}
    return {"point": point, "rows": dict(rows_by_type), "logloss": ll,
            "objective": sum(ll.values()) / len(ll) if ll else float("nan"), "errors": errors,
            "n": sum(len(v) for v in rows_by_type.values())}


def calib_table(rows) -> list[dict]:
    return bucketize([{"pred": p, "survived": y} for p, y, _ in rows])


def bar_failures(rows) -> list[str]:
    """The pre-registered calibration bar: within 8 points in every bucket with n >= 15."""
    out = []
    for b in calib_table(rows):
        if b["n"] >= 15 and abs(b["pred"] - b["obs"]) > 0.08:
            out.append(f"{b['bucket']}% (pred {b['pred']:.0%} obs {b['obs']:.0%}, n {b['n']})")
    return out


def need_damp_estimate(ctxs: list[dict], sigma_of) -> dict:
    """One-parameter empirical damp: for every rival pick, the plain-Gaussian
    ADP mass over the alive pool split into positions that fill one of that
    rival's open starter slots vs not; solve sum_i m_closed_i*d /
    (m_open_i + m_closed_i*d) = (# picks that filled no slot) for d."""
    import numpy as np
    out = {}
    for rt in sorted({c["room_type"] for c in ctxs}):
        obs, terms = 0, []
        for c in (c for c in ctxs if c["room_type"] == rt):
            slots = c["slots"]
            taken: set[str] = set()
            by_slot: dict[int, list[str]] = defaultdict(list)
            for p in c["picks"]:
                n, slot, pos, rnd = p["pick_no"], p["draft_slot"], p["metadata"]["position"], p["round"]
                needs = snake.starter_needs(by_slot[slot], slots)
                alive = [b for b in c["board"] if b["sleeper_id"] not in taken and b.get("adp") is not None]
                if alive and pos in POSITIONS:
                    adp = np.array([float(b["adp"]) for b in alive])
                    w = np.exp(-0.5 * ((n - adp) / sigma_of(rnd, c["rounds"])) ** 2) + 1e-9
                    fills = np.array([snake.needs_position(needs, b["pos"]) for b in alive])
                    m_open, m_closed = float(w[fills].sum()), float(w[~fills].sum())
                    if m_open + m_closed > 0:
                        terms.append((m_open, m_closed))
                        if not snake.needs_position(needs, pos):
                            obs += 1
                by_slot[slot].append(pos)
                if p["player_id"] != "0":
                    taken.add(p["player_id"])
        if not terms:
            continue

        def expected(d, terms=terms):
            return sum(mc * d / (mo + mc * d) for mo, mc in terms)
        lo, hi = 1e-4, 10.0
        for _ in range(60):
            mid = (lo * hi) ** 0.5
            if expected(mid) < obs:
                lo = mid
            else:
                hi = mid
        out[rt] = {"damp": (lo * hi) ** 0.5, "closed_picks": obs, "picks": len(terms)}
    return out


# ------------------------------------------------------------------ the run

def confirm_point(a, point: dict) -> dict:
    """One knob set at confirmation sims, against the pre-registered bar;
    written to reports/survival_fit_point.<tag>.json."""
    logs_dir = Path(a.logs)
    ctxs = [room_context(r, logs_dir) for r in all_rooms(logs_dir)]
    res = evaluate(ctxs, point, a.confirm_sims, a.every, a.all_slots, a.workers)
    pooled = [r for rows in res["rows"].values() for r in rows]
    human = res["rows"].get("sleeper_human", [])
    out = {"point": point, "objective": res["objective"], "logloss": res["logloss"], "n": res["n"],
           "pooled": calib_table(pooled), "human": calib_table(human),
           "bar": {"pooled_fail": bar_failures(pooled), "human_fail": bar_failures(human)}}
    tag = "_".join(f"{k}{v}" for k, v in sorted(point.items()))
    path = Path(a.fit_out).parent / f"survival_fit_point.{tag}.json"
    path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"point {point}: objective {res['objective']:.4f} " + " ".join(f"{k} {v:.4f}" for k, v in sorted(res["logloss"].items())))
    for name, rows in (("pooled", pooled), ("human", human)):
        print(f"  {name}: " + "; ".join(f"{b['bucket']}% n{b['n']} pred {b['pred']:.0%} obs {b['obs']:.0%}" for b in calib_table(rows) if b["n"]))
        f = bar_failures(rows)
        print(f"  {name} bar: " + ("PASS" if not f else "FAIL " + "; ".join(f)))
    print(f"-> {path}")
    return out


def run_fit(a) -> None:
    t0 = time.time()
    logs_dir = Path(a.logs)
    ctxs = [room_context(r, logs_dir) for r in all_rooms(logs_dir)]
    stages = SMOKE_STAGES if a.smoke else STAGES
    L = ["# Survival refit (plan B7, DECISIONS #26)", "",
         f"Rooms: {len(ctxs)}. sims {a.sims} (confirmation {a.confirm_sims}), every {a.every} state(s), "
         f"{'all seats' if a.all_slots else 'real seat'}, workers {a.workers}. Objective = mean over room "
         "types of the per-type log loss (equal weight per type; the one human room cannot be outvoted). "
         "Coordinate search on a coarse grid: the best point ON THE GRID, not identified parameters.", "",
         "| room | type | league | picks | matched to board | adp |", "|---|---|---|---|---|---|"]
    for c in ctxs:
        L.append(f"| {c['room']} | {c['room_type']} | {c['league']} | {c['n_picks']} | {c['matched']} | {c['adp_note']} |")
    point = dict(CURRENT)
    base = evaluate(ctxs, point, a.sims, a.every, a.all_slots, a.workers)
    types = sorted(base["logloss"])
    L += ["", f"## Current knobs {point}: objective {base['objective']:.4f} "
          + " ".join(f"{k} {v:.4f}" for k, v in sorted(base["logloss"].items()))
          + f" (n {base['n']}, errors {base['errors']})"]
    print(f"current {point}: {base['objective']:.4f} (n {base['n']}, {time.time() - t0:.0f}s)", flush=True)
    history = [("current", dict(point), base["objective"])]
    for stage, grid in stages:
        L += ["", f"## Stage: {stage}", "", "| point | objective | " + " | ".join(types) + " |", "|---|---|" + "---|" * len(types)]
        best = None
        for g in grid:
            cand = {**point, **g}
            res = evaluate(ctxs, cand, a.sims, a.every, a.all_slots, a.workers)
            L.append(f"| {g} | {res['objective']:.4f} | " + " | ".join(f"{res['logloss'].get(k, float('nan')):.4f}" for k in types) + " |")
            print(f"  {stage} {g}: {res['objective']:.4f} ({time.time() - t0:.0f}s)", flush=True)
            if best is None or res["objective"] < best[1]:
                best = (cand, res["objective"])
        point = best[0]
        history.append((stage, dict(point), best[1]))
        L.append(f"\nbest after {stage}: {point} (objective {best[1]:.4f})")
    # confirmation at full sims: current vs fitted, three views each
    L += ["", f"## Confirmation at sims {a.confirm_sims}"]
    final = {}
    for label, pt in (("current", CURRENT), ("fitted", point)):
        res = evaluate(ctxs, pt, a.confirm_sims, a.every, a.all_slots, a.workers)
        final[label] = res
        L += ["", f"### {label}: {pt} -> objective {res['objective']:.4f}"]
        views = [("pooled", [r for rows in res["rows"].values() for r in rows])] + sorted(res["rows"].items())
        for name, rows in views:
            L += ["", f"{name} (n={len(rows)})", "", "| predicted | n | predicted avg | observed | log loss |", "|---|---|---|---|---|"]
            for b in calib_table(rows):
                L.append(f"| {b['bucket']}% | {b['n']} | " + ("- | - | - |" if not b["n"] else f"{b['pred']:.0%} | {b['obs']:.0%} | {b['logloss']:.3f} |"))
    fitted_rows = final["fitted"]["rows"]
    pooled_fail = bar_failures([r for rows in fitted_rows.values() for r in rows])
    human_fail = bar_failures(fitted_rows.get("sleeper_human", []))
    L += ["", "## Pre-registered calibration bar (within 8 points in every bucket with n >= 15)", "",
          f"pooled: {'PASS' if not pooled_fail else 'FAIL ' + '; '.join(pooled_fail)}",
          f"human room: {'PASS' if not human_fail else 'FAIL ' + '; '.join(human_fail)}"]

    def sigma_of(rnd, rounds, e=point["sigma_early"], late=point["sigma_late"]):
        return e + (late - e) * (rnd - 1) / max(1, rounds - 1)
    est = need_damp_estimate(ctxs, sigma_of)
    L += ["", "## Empirical need damp (closed-slot take rate vs the ADP mass, one parameter, by room type)", "",
          "| room type | picks | filled no open starter slot | implied damp | in use |", "|---|---|---|---|---|"]
    for rt, v in est.items():
        L.append(f"| {rt} | {v['picks']} | {v['closed_picks']} | {v['damp']:.2f} | {point['need_damp']} |")
    L += ["", f"Wall time {time.time() - t0:.0f} s."]
    out = Path(a.fit_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    out.with_suffix(".json").write_text(json.dumps(
        {"current": CURRENT, "fitted": point, "history": history,
         "confirmation": {k: {"objective": v["objective"], "logloss": v["logloss"], "n": v["n"],
                              "calibration": {rt: calib_table(rows) for rt, rows in v["rows"].items()},
                              "pooled_calibration": calib_table([r for rows in v["rows"].values() for r in rows])}
                          for k, v in final.items()},
         "bar": {"pooled_fail": pooled_fail, "human_fail": human_fail}, "need_damp_estimate": est,
         "seconds": time.time() - t0}, indent=1), encoding="utf-8")
    print(f"\nfitted: {point}\npooled bar: {'PASS' if not pooled_fail else 'FAIL'}  human bar: {'PASS' if not human_fail else 'FAIL'}\n-> {out}")
