"""The survival refit (plan 2026-09-02 B7; pre-registered in DECISIONS #26;
autopick stage and LORO per DECISIONS #35 / plan 2026-09-03 s5).

The logged prose is report-only. The fit re-runs the simulation on every
archived state (picks made so far, seen from that room's real seat) with the
production board for the league, draft-day ADP, survival_shrink 1.0 and a
candidate knob set, and scores the RAW survival vector of every pooled
player against what the room actually did.

Objective: the mean over room types of the per-type log loss (equal weight
per type, so four autopick rooms cannot outvote the one human room). A
coordinate search on a coarse grid yields the best point ON THE GRID, not
identified parameters; nothing is reported finer than its grid step.

Autopick (DECISIONS #35): Yahoo rooms with a bridge sidecar carry a per-pick
AWAY SET (draft slots whose manager Yahoo flagged away at the nearest
preceding plan call); the tracker is rebuilt with `away_slots` = that set, so
the engine's autopick branch is exercised in the replay. The autopick stage
is three coordinate sub-stages (autopick_list_prob, autopick_sigma_scale,
autopick_need_damp) run only on rooms with a non-empty away set somewhere.

Calibration: per bucket, a cluster bootstrap over (room, seat, window) of
(observed - predicted), 500 resamples, 90% CI; effective n = clusters. The
CI bar flags a bucket only when its CI excludes 0 with >= 30 clusters. The
older 8-point bar is kept alongside for continuity.

    venv\\Scripts\\python.exe scripts\\fit_survival.py --fit [--stage autopick] [--sims 200 --every 2 --workers N]
    venv\\Scripts\\python.exe scripts\\fit_survival.py --loro --stage autopick
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
from fit_survival import BUCKETS, all_rooms, bucketize, norm  # noqa: E402

AUTOPICK_STAGES = (
    ("autopick_list_prob", [{"autopick_list_prob": p} for p in (0.0, 0.2, 0.3, 0.4, 0.6)]),
    ("autopick_sigma_scale", [{"autopick_sigma_scale": s} for s in (0.5, 0.75, 1.0, 1.5)]),
    # 0.45 is a recorded deviation from the pre-registered grid {0.02,0.15,0.30}:
    # the G1 fit (DECISIONS #35 result) put the away class's need damp at 0.45.
    ("autopick_need_damp", [{"autopick_need_damp": d} for d in (0.02, 0.15, 0.30, 0.45)]),
)
AUTOPICK_STAGE_NAMES = frozenset(name for name, _ in AUTOPICK_STAGES)
HUMAN_STAGES = (
    ("sigma", [{"sigma_early": e, "sigma_late": late}
               for e in (4.0, 6.0, 8.0, 10.0) for late in (15.0, 21.0, 27.0, 35.0)]),
    ("reach", [{"reach_prob": r} for r in (0.0, 0.10, 0.15, 0.25, 0.35)]),
    ("need", [{"need_damp": d} for d in (0.15, 0.30, 0.50)]),
)
STAGES = HUMAN_STAGES + AUTOPICK_STAGES
SMOKE_STAGES = (("sigma", [{"sigma_early": 6.0, "sigma_late": 27.0}, {"sigma_early": 8.0, "sigma_late": 27.0}]),)
CURRENT = {"sigma_early": 6.0, "sigma_late": 27.0, "reach_prob": 0.15, "need_damp": 0.15,
           "autopick_list_prob": 0.0, "autopick_sigma_scale": 0.5, "autopick_need_damp": 0.02}
CURRENT_AUTOPICK = {k: CURRENT[k] for k in ("autopick_list_prob", "autopick_sigma_scale", "autopick_need_damp")}
HUMAN_TYPE = "sleeper_human"          # the Omnibeta real draft
N_BOOT, CI_ALPHA, MIN_CLUSTERS = 500, 0.10, 30
_ROOMS: list[dict] = []          # per-worker room contexts (set by _init_worker)


def stages_for(name: str, smoke: bool = False):
    if smoke:
        return SMOKE_STAGES
    if name in (None, "", "all"):
        return STAGES
    if name == "autopick":
        return AUTOPICK_STAGES
    return tuple(s for s in STAGES if s[0] == name)


# ------------------------------------------------------------- room contexts

def league_for(room: dict) -> str:
    return "omnibeta" if int(room["teams"]) == 12 else "keefamania"


def room_date(room: dict, logs_dir: Path) -> str | None:
    if room["room_type"].startswith("yahoo"):      # Yahoo rooms: no Sleeper log, no FFC snapshot
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


def yahoo_rank_source(room: str, mocks_dir: Path) -> Path | None:
    """The players snapshot carrying Yahoo's default rank (o_rank): the
    room's own, else the newest on disk (o_rank moves slowly)."""
    own = [mocks_dir / f"players_{room}.json", mocks_dir / f"mock_players_{room}.json"]
    cands = [p for p in own if p.exists()]
    if not cands:
        cands = sorted(list(mocks_dir.glob("players_*.json")) + list(mocks_dir.glob("mock_players_*.json")),
                       key=lambda p: p.stat().st_mtime, reverse=True)
    return cands[0] if cands else None


def attach_yahoo_rank(board: list[dict], snap_path: Path | None) -> str:
    """Fill board rows' `yahoo_rank` (None on the board today) from a players
    snapshot, joined on (mock_common.key(name), pos). The tracker reads
    `yahoo_rank` into the pool's `yrank`, which the list-walking autopick
    component follows; without it the engine falls back to adp and the
    autopick_list_prob knob would measure a different list than the one
    pre-registered. Returns a note for the report."""
    if snap_path is None or not snap_path.exists():
        return "yahoo_rank: no players snapshot (engine falls back to adp)"
    from mock_common import key
    d = json.loads(snap_path.read_text(encoding="utf-8"))
    ranks: dict[tuple[str, str], float] = {}
    for p in d.get("players") or []:
        r = p.get("o_rank")
        if r is None:
            continue
        ranks.setdefault((key(p.get("name", "")), str(p.get("pos") or "").upper()), float(r))
    hit = 0
    for p in board:
        if p.get("yahoo_rank") is not None:
            hit += 1
            continue
        r = ranks.get((key(p["name"]), p["pos"]))
        if r is not None:
            p["yahoo_rank"] = r
            hit += 1
    return f"yahoo_rank: {snap_path.name} ({hit}/{len(board)} board rows)"


def room_context(room: dict, logs_dir: Path) -> dict:
    """Board, shape, pick sequence and per-pick away sets for replaying one
    room's states."""
    import engine_parity as EP
    from draftkit.config import Config
    league = league_for(room)
    cfg = Config.load(league=league)
    teams, rounds, slots = EP.league_shape(cfg)
    board = EP.load_board(str(ROOT / ("tiers.csv" if league == "omnibeta" else "tiers.keefamania.csv")))
    adp_note = "board adp (Yahoo rank on this league's board)"
    date = room_date(room, logs_dir)
    yr_note = ""
    if date and not room["room_type"].startswith("yahoo"):
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
    if room["room_type"].startswith("yahoo"):
        yr_note = attach_yahoo_rank(board, yahoo_rank_source(room["room"], logs_dir / "mocks"))
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
    away_at = {int(k): frozenset(v) for k, v in (room.get("away_at") or {}).items()}
    n_away = sum(1 for v in away_at.values() if v)
    if room.get("has_sidecar"):
        away_note = (f"sidecar: away set non-empty at {n_away}/{len(picks)} picks, slots seen "
                     f"{sorted(set().union(*away_at.values())) if away_at else []}")
    else:
        away_note = "no sidecar: empty away set at every pick (autopick branch not exercised)"
    return {"room": room["room"], "room_type": room["room_type"], "league": league, "cfg": cfg,
            "teams": teams, "rounds": rounds, "slots": slots, "board": board, "picks": picks,
            "picked_at": {norm(p["player"]): int(p["pick_no"]) for p in room["picks"]},
            "my_slot": int(room["my_slot"]), "n_picks": len(picks),
            "matched": sum(1 for p in picks if p["player_id"] != "0"),
            "adp_note": adp_note, "yr_note": yr_note, "id2name": {p["sleeper_id"]: p["name"] for p in board},
            "away_at": away_at, "n_away_states": n_away, "has_sidecar": bool(room.get("has_sidecar")),
            "away_note": away_note}


def stage_rooms(ctxs: list[dict], stage: str) -> list[dict]:
    """The autopick sub-stages fit only on rooms whose away set is non-empty
    somewhere; every other stage fits on every room."""
    if stage in AUTOPICK_STAGE_NAMES:
        return [c for c in ctxs if c.get("n_away_states", 0) > 0]
    return list(ctxs)


# ------------------------------------------------------------- evaluation

def state_rows(ctx: dict, cp: int, seat: int, point: dict, sims: int) -> list[tuple]:
    """(raw survival, survived, pos, cluster) for every pooled player at
    state cp (picks 1..cp-1 made), seen from `seat`, under knob set `point`.
    cluster = (room, seat, my_next) -- one prediction window; the
    calibration bootstrap resamples these."""
    import engine_parity as EP
    teams, rounds = ctx["teams"], ctx["rounds"]
    start, nxt = sim_window(cp, seat, teams, rounds)
    if start is None or nxt is None or nxt <= start or nxt > ctx["n_picks"] + 1:
        return []                                   # no window, or a window past the archive's end
    away = (ctx.get("away_at") or {}).get(cp, frozenset())
    t = EP.make_tracker(ctx["board"], ctx["picks"][:cp - 1], seat, slots=ctx["slots"], teams=teams,
                        rounds=rounds, cfg=ctx["cfg"],
                        overrides={**point, "sims": sims, "survival_shrink": 1.0, "away_slots": frozenset(away)})
    rep = t.urgency_report()
    if not rep:
        return []
    cluster = f"{ctx['room']}:{seat}:{nxt}"
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
            out.append((float(p), at is None or at >= nxt, pos, cluster))
    return out


def _init_worker(rooms_ctx):
    global _ROOMS
    _ROOMS = rooms_ctx


def _task(args):
    ri, cp, seat, point, sims = args
    try:
        return ri, state_rows(_ROOMS[ri], cp, seat, point, sims)
    except Exception as e:  # noqa: BLE001
        return ri, [("err", str(e)[:80], "", "")]


def logloss(rows) -> float:
    if not rows:
        return float("nan")
    eps = 1e-3
    s = 0.0
    for r in rows:
        p = min(1 - eps, max(eps, r[0]))
        s += -(math.log(p) if r[1] else math.log(1 - p))
    return s / len(rows)


def evaluate(ctxs: list[dict], point: dict, sims: int, every: int, all_slots: bool, workers: int) -> dict:
    tasks = []
    for ri, c in enumerate(ctxs):
        seats = range(1, c["teams"] + 1) if all_slots else [c["my_slot"]]
        for cp in range(1, c["n_picks"] + 1, every):
            for seat in seats:
                tasks.append((ri, cp, seat, point, sims))
    rows_by_type: dict[str, list] = defaultdict(list)
    rows_by_room: dict[str, list] = defaultdict(list)
    errors = 0

    def absorb(ri, rows):
        nonlocal errors
        for r in rows:
            if r[0] == "err":
                errors += 1
            else:
                rows_by_type[ctxs[ri]["room_type"]].append(r)
                rows_by_room[ctxs[ri]["room"]].append(r)

    if workers > 1 and len(tasks) > 1:
        with cf.ProcessPoolExecutor(max_workers=workers, initializer=_init_worker, initargs=(ctxs,)) as ex:
            for ri, rows in ex.map(_task, tasks, chunksize=4):
                absorb(ri, rows)
    else:
        _init_worker(ctxs)
        for a in tasks:
            absorb(*_task(a))
    ll = {k: logloss(v) for k, v in rows_by_type.items()}
    return {"point": point, "rows": dict(rows_by_type), "rows_by_room": dict(rows_by_room), "logloss": ll,
            "logloss_by_room": {k: logloss(v) for k, v in rows_by_room.items()},
            "objective": sum(ll.values()) / len(ll) if ll else float("nan"), "errors": errors,
            "n": sum(len(v) for v in rows_by_type.values())}


def views(rows_by_type: dict) -> list[tuple[str, list]]:
    """The three reporting views: pooled / human (the Omnibeta real draft) /
    autopick (every Yahoo room type)."""
    pooled = [r for rows in rows_by_type.values() for r in rows]
    human = list(rows_by_type.get(HUMAN_TYPE, []))
    auto = [r for rt, rows in rows_by_type.items() if rt.startswith("yahoo") for r in rows]
    return [("pooled", pooled), ("human", human), ("autopick", auto)]


# ------------------------------------------------------------- calibration

def calib_table(rows) -> list[dict]:
    return bucketize([{"pred": r[0], "survived": r[1]} for r in rows])


def bar_failures(rows) -> list[str]:
    """The older calibration bar (DECISIONS #26): within 8 points in every
    bucket with n >= 15. Kept for continuity; the CI bar below is the one
    DECISIONS #35 G2 reads."""
    out = []
    for b in calib_table(rows):
        if b["n"] >= 15 and abs(b["pred"] - b["obs"]) > 0.08:
            out.append(f"{b['bucket']}% (pred {b['pred']:.0%} obs {b['obs']:.0%}, n {b['n']})")
    return out


def bootstrap_ci(rows, n_boot: int = N_BOOT, alpha: float = CI_ALPHA, seed: int = 0, buckets=BUCKETS) -> list[dict]:
    """Per bucket: (observed - predicted) with a cluster-bootstrap CI.
    Clusters = the rows' 4th field (room:seat:window); each resample draws
    clusters with replacement and recomputes the bucket's mean difference
    from the pooled rows of the drawn clusters. Effective n = clusters.
    Rows are (pred, survived, pos, cluster); rows without a cluster field
    fall into one cluster each (no clustering)."""
    import numpy as np
    rng = np.random.default_rng(seed)
    out = []
    for lo, hi, label in buckets:
        agg: dict = {}
        for i, r in enumerate(rows):
            if not (lo <= round(r[0] * 100) < hi):
                continue
            cl = r[3] if len(r) > 3 else i
            a = agg.setdefault(cl, [0.0, 0.0, 0])
            a[0] += 1.0 if r[1] else 0.0
            a[1] += float(r[0])
            a[2] += 1
        if not agg:
            out.append({"bucket": label, "n": 0, "clusters": 0, "pred": None, "obs": None,
                        "diff": None, "lo": None, "hi": None})
            continue
        m = np.array(list(agg.values()), dtype=float)           # (k, 3): sum_y, sum_p, count
        k = len(m)
        n = int(m[:, 2].sum())
        obs, pred = m[:, 0].sum() / n, m[:, 1].sum() / n
        idx = rng.integers(0, k, size=(n_boot, k))
        s = m[idx].sum(axis=1)                                   # (n_boot, 3)
        d = (s[:, 0] - s[:, 1]) / s[:, 2]
        lo_ci, hi_ci = (float(x) for x in np.quantile(d, [alpha / 2, 1 - alpha / 2]))
        out.append({"bucket": label, "n": n, "clusters": k, "pred": float(pred), "obs": float(obs),
                    "diff": float(obs - pred), "lo": lo_ci, "hi": hi_ci})
    return out


def bar_failures_ci(rows, min_clusters: int = MIN_CLUSTERS, n_boot: int = N_BOOT, alpha: float = CI_ALPHA,
                    seed: int = 0) -> list[str]:
    """DECISIONS #35 G2 bar: a bucket fails only when its cluster-bootstrap
    90% CI of (observed - predicted) excludes 0 AND it has >= min_clusters
    clusters. Buckets with fewer clusters cannot fail (they cannot decide)."""
    out = []
    for b in bootstrap_ci(rows, n_boot=n_boot, alpha=alpha, seed=seed):
        if b["clusters"] >= min_clusters and b["lo"] is not None and (b["lo"] > 0 or b["hi"] < 0):
            out.append(f"{b['bucket']}% (obs-pred {b['diff']:+.0%}, CI [{b['lo']:+.0%}, {b['hi']:+.0%}], "
                       f"n {b['n']}, clusters {b['clusters']})")
    return out


def _calib_lines(name: str, rows) -> list[str]:
    L = ["", f"{name} (n={len(rows)})", "",
         "| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |",
         "|---|---|---|---|---|---|---|---|"]
    ll = {b["bucket"]: b["logloss"] for b in calib_table(rows)}
    for b in bootstrap_ci(rows):
        if not b["n"]:
            L.append(f"| {b['bucket']}% | 0 | 0 | - | - | - | - | - |")
        else:
            L.append(f"| {b['bucket']}% | {b['n']} | {b['clusters']} | {b['pred']:.0%} | {b['obs']:.0%} | "
                     f"{b['diff']:+.0%} | [{b['lo']:+.0%}, {b['hi']:+.0%}] | {ll[b['bucket']]:.3f} |")
    return L


def _bar_lines(rows_by_type: dict) -> tuple[list[str], dict]:
    L = ["", f"## Calibration bars (three views; CI bar = DECISIONS #35 G2: a bucket fails only when its "
         f"cluster-bootstrap {int((1 - CI_ALPHA) * 100)}% CI of obs-pred excludes 0 with >= {MIN_CLUSTERS} clusters; "
         "8-point bar = DECISIONS #26, n >= 15, for continuity)", "",
         "| view | n | CI bar | 8-point bar |", "|---|---|---|---|"]
    bar = {}
    for name, rows in views(rows_by_type):
        ci = bar_failures_ci(rows)
        old = bar_failures(rows)
        bar[name] = {"ci_fail": ci, "eight_point_fail": old, "n": len(rows)}
        L.append(f"| {name} | {len(rows)} | {'PASS' if not ci else 'FAIL ' + '; '.join(ci)} | "
                 f"{'PASS' if not old else 'FAIL ' + '; '.join(old)} |")
    return L, bar


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

def coordinate_fit(ctxs: list[dict], stages, start: dict, a, log=None, t0: float | None = None):
    """Coordinate search: for each stage, every grid point on that stage's
    rooms, keep the best. Returns (point, history, report lines)."""
    t0 = t0 or time.time()
    point = dict(start)
    history, L = [], []
    for stage, grid in stages:
        rooms = stage_rooms(ctxs, stage)
        if not rooms:
            L += ["", f"## Stage: {stage}", "", "SKIPPED: no room with a non-empty away set."]
            history.append((stage, dict(point), float("nan")))
            continue
        types = sorted({c["room_type"] for c in rooms})
        L += ["", f"## Stage: {stage} ({len(rooms)} room(s): {', '.join(c['room'] for c in rooms)})", "",
              "| point | objective | " + " | ".join(types) + " |", "|---|---|" + "---|" * len(types)]
        best = None
        for g in grid:
            cand = {**point, **g}
            res = evaluate(rooms, cand, a.sims, a.every, a.all_slots, a.workers)
            L.append(f"| {g} | {res['objective']:.4f} | " + " | ".join(f"{res['logloss'].get(k, float('nan')):.4f}" for k in types) + " |")
            if log:
                log(f"  {stage} {g}: {res['objective']:.4f} ({time.time() - t0:.0f}s)")
            if best is None or res["objective"] < best[1]:
                best = (cand, res["objective"])
        point = best[0]
        history.append((stage, dict(point), best[1]))
        L.append(f"\nbest after {stage}: {point} (objective {best[1]:.4f})")
    return point, history, L


def selected_rooms(a, logs_dir: Path) -> list[dict]:
    """all_rooms, restricted to `--rooms a,b,c` when given (G4: score one
    forward room at a time at both knob sets)."""
    rooms = all_rooms(logs_dir)
    want = getattr(a, "rooms", None)
    if want:
        keep = {s.strip() for s in str(want).split(",") if s.strip()}
        rooms = [r for r in rooms if str(r["room"]) in keep]
        missing = keep - {str(r["room"]) for r in rooms}
        if missing:
            raise SystemExit(f"--rooms: no archived room named {sorted(missing)}")
    return rooms


def confirm_point(a, point: dict) -> dict:
    """One knob set at confirmation sims, against both bars, three views;
    written to reports/survival_fit_point.<tag>.json."""
    logs_dir = Path(a.logs)
    ctxs = [room_context(r, logs_dir) for r in selected_rooms(a, logs_dir)]
    res = evaluate(ctxs, point, a.confirm_sims, a.every, a.all_slots, a.workers)
    _, bar = _bar_lines(res["rows"])
    out = {"point": point, "objective": res["objective"], "logloss": res["logloss"], "n": res["n"],
           "calibration": {name: bootstrap_ci(rows) for name, rows in views(res["rows"])}, "bar": bar}
    tag = "_".join(f"{k}{v}" for k, v in sorted(point.items()))
    path = Path(a.fit_out).parent / f"survival_fit_point.{tag}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"point {point}: objective {res['objective']:.4f} " + " ".join(f"{k} {v:.4f}" for k, v in sorted(res["logloss"].items())))
    for name, rows in views(res["rows"]):
        print(f"  {name}: " + "; ".join(f"{b['bucket']}% n{b['n']} k{b['clusters']} pred {b['pred']:.0%} obs {b['obs']:.0%} "
                                        f"CI [{b['lo']:+.0%},{b['hi']:+.0%}]" for b in bootstrap_ci(rows) if b["n"]))
        f = bar[name]["ci_fail"]
        print(f"  {name} CI bar: " + ("PASS" if not f else "FAIL " + "; ".join(f)))
    print(f"-> {path}")
    return out


def _room_table(ctxs: list[dict]) -> list[str]:
    L = ["| room | type | league | picks | matched to board | adp | yahoo_rank | away set |",
         "|---|---|---|---|---|---|---|---|"]
    for c in ctxs:
        L.append(f"| {c['room']} | {c['room_type']} | {c['league']} | {c['n_picks']} | {c['matched']} | "
                 f"{c['adp_note']} | {c['yr_note'] or '-'} | {c['away_note']} |")
    return L


def run_fit(a) -> None:
    t0 = time.time()
    logs_dir = Path(a.logs)
    ctxs = [room_context(r, logs_dir) for r in selected_rooms(a, logs_dir)]
    stages = stages_for(getattr(a, "stage", "all"), a.smoke)
    L = ["# Survival refit (plan B7, DECISIONS #26; autopick stage DECISIONS #35)", "",
         f"Rooms: {len(ctxs)}. sims {a.sims} (confirmation {a.confirm_sims}), every {a.every} state(s), "
         f"{'all seats' if a.all_slots else 'real seat'}, workers {a.workers}, stage {getattr(a, 'stage', 'all')}. "
         "Objective = mean over room types of the per-type log loss (equal weight per type; the one human room "
         "cannot be outvoted). Coordinate search on a coarse grid: the best point ON THE GRID, not identified "
         "parameters. The autopick sub-stages run only on rooms whose sidecar gives a non-empty away set; the "
         "tracker at each state carries that pick's away set as `away_slots`.", ""] + _room_table(ctxs)
    point = dict(CURRENT)
    base = evaluate(ctxs, point, a.sims, a.every, a.all_slots, a.workers)
    L += ["", f"## Current knobs {point}: objective {base['objective']:.4f} "
          + " ".join(f"{k} {v:.4f}" for k, v in sorted(base["logloss"].items()))
          + f" (n {base['n']}, errors {base['errors']})"]
    print(f"current {point}: {base['objective']:.4f} (n {base['n']}, {time.time() - t0:.0f}s)", flush=True)
    history = [("current", dict(point), base["objective"])]
    point, hist, lines = coordinate_fit(ctxs, stages, point, a, log=lambda s: print(s, flush=True), t0=t0)
    history += hist
    L += lines
    # confirmation at full sims: current vs fitted, three views each, both bars
    L += ["", f"## Confirmation at sims {a.confirm_sims}"]
    final, bars = {}, {}
    for label, pt in (("current", CURRENT), ("fitted", point)):
        res = evaluate(ctxs, pt, a.confirm_sims, a.every, a.all_slots, a.workers)
        final[label] = res
        L += ["", f"### {label}: {pt} -> objective {res['objective']:.4f} "
              + " ".join(f"{k} {v:.4f}" for k, v in sorted(res["logloss"].items()))]
        for name, rows in views(res["rows"]) + sorted(res["rows"].items()):
            L += _calib_lines(name, rows)
        bl, bars[label] = _bar_lines(res["rows"])
        L += bl
    fitted_bar = bars["fitted"]

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
        {"current": CURRENT, "fitted": point, "stage": getattr(a, "stage", "all"), "history": history,
         "rooms": [{"room": c["room"], "type": c["room_type"], "has_sidecar": c["has_sidecar"],
                    "away_states": c["n_away_states"]} for c in ctxs],
         "confirmation": {k: {"objective": v["objective"], "logloss": v["logloss"], "n": v["n"],
                              "calibration": {name: bootstrap_ci(rows) for name, rows in views(v["rows"])},
                              "by_type": {rt: calib_table(rows) for rt, rows in v["rows"].items()}}
                          for k, v in final.items()},
         "bar": bars, "need_damp_estimate": est, "seconds": time.time() - t0}, indent=1), encoding="utf-8")
    print(f"\nfitted: {point}\n" + "  ".join(f"{n} CI bar: {'PASS' if not fitted_bar[n]['ci_fail'] else 'FAIL'}"
                                            for n in ("pooled", "human", "autopick")) + f"\n-> {out}")


def loro_split(ctxs: list[dict], stage: str) -> list[tuple[dict, list[dict]]]:
    """(held-out room, fit rooms) for every room the stage fits on. The fit
    rooms for the autopick stage are the other rooms WITH away sets; for the
    human stages every other room."""
    rooms = stage_rooms(ctxs, next(iter(AUTOPICK_STAGE_NAMES)) if stage == "autopick" else stage)
    out = []
    for held in rooms:
        out.append((held, [c for c in rooms if c["room"] != held["room"]]))
    return out


def run_loro(a, evaluator=None, fitter=None) -> dict:
    """Leave-one-room-out: for each room the stage fits on, fit on the others
    and score the held-out room at the fitted point AND at CURRENT. Prints
    per-room held-out log-loss for both and the pooled mean; writes
    reports/survival_loro.md (+ .json). `evaluator`/`fitter` are injection
    points for tests."""
    t0 = time.time()
    stage = getattr(a, "stage", "all")
    logs_dir = Path(a.logs)
    ctxs = [room_context(r, logs_dir) for r in selected_rooms(a, logs_dir)]
    stages = stages_for(stage, a.smoke)
    evaluator = evaluator or (lambda rooms, pt: evaluate(rooms, pt, a.sims, a.every, a.all_slots, a.workers))
    fitter = fitter or (lambda rooms: coordinate_fit(rooms, stages, CURRENT, a, log=lambda s: print(s, flush=True), t0=t0))
    splits = loro_split(ctxs, stage)
    L = ["# Survival refit: leave-one-room-out (DECISIONS #35 G2)", "",
         f"Stage {stage}; sims {a.sims}, every {a.every}, {'all seats' if a.all_slots else 'real seat'}. "
         "For each room the stage fits on: coordinate fit on the OTHER rooms from CURRENT, then the held-out "
         "room's Bernoulli log-loss at that fitted point and at CURRENT. Held-out numbers are the only ones "
         "that count; the fitted point per fold is reported at grid precision.", ""] + _room_table(ctxs) + [
        "", "| held-out room | type | n rows | fitted point (fold) | held-out at fitted | at CURRENT | delta |",
        "|---|---|---|---|---|---|---|"]
    rows_fit, rows_cur, folds = [], [], []
    print(f"LORO stage {stage}: {len(splits)} fold(s)", flush=True)
    for held, fit_rooms in splits:
        print(f"fold: hold out {held['room']} ({held['room_type']}), fit on {len(fit_rooms)} room(s)", flush=True)
        point, hist, _lines = fitter(fit_rooms)
        r_fit = evaluator([held], point)
        r_cur = evaluator([held], CURRENT)
        lf, lc = r_fit["objective"], r_cur["objective"]
        fold = {"room": held["room"], "type": held["room_type"], "n": r_fit["n"], "point": point,
                "heldout_fitted": lf, "heldout_current": lc, "delta": lf - lc,
                "fit_rooms": [c["room"] for c in fit_rooms], "history": hist}
        folds.append(fold)
        rows_fit += [r for rows in r_fit["rows"].values() for r in rows]
        rows_cur += [r for rows in r_cur["rows"].values() for r in rows]
        changed = {k: v for k, v in point.items() if v != CURRENT.get(k)}
        L.append(f"| {held['room']} | {held['room_type']} | {r_fit['n']} | {changed or 'CURRENT'} | {lf:.4f} | {lc:.4f} | {lf - lc:+.4f} |")
        print(f"  held-out {held['room']}: fitted {lf:.4f}  current {lc:.4f}  delta {lf - lc:+.4f}  point {changed or 'CURRENT'}", flush=True)
    valid = [f for f in folds if f["heldout_fitted"] == f["heldout_fitted"]]
    mean_fit = sum(f["heldout_fitted"] for f in valid) / len(valid) if valid else float("nan")
    mean_cur = sum(f["heldout_current"] for f in valid) / len(valid) if valid else float("nan")
    pooled_fit, pooled_cur = logloss(rows_fit), logloss(rows_cur)
    L += ["", f"Pooled mean over rooms (equal weight per room): fitted {mean_fit:.4f}  current {mean_cur:.4f}  "
          f"delta {mean_fit - mean_cur:+.4f}",
          f"Row-pooled held-out log-loss: fitted {pooled_fit:.4f}  current {pooled_cur:.4f}  delta {pooled_fit - pooled_cur:+.4f}",
          "", "## Held-out calibration (rows pooled across folds, each scored at its fold's fitted point)"]
    by_type_fit: dict[str, list] = defaultdict(list)
    by_type_cur: dict[str, list] = defaultdict(list)
    room_type = {c["room"]: c["room_type"] for c in ctxs}
    for r in rows_fit:
        by_type_fit[room_type[r[3].split(":")[0]]].append(r)
    for r in rows_cur:
        by_type_cur[room_type[r[3].split(":")[0]]].append(r)
    bars = {}
    for label, bt in (("fitted (held-out)", by_type_fit), ("current", by_type_cur)):
        L += ["", f"### {label}"]
        for name, rows in views(bt):
            if rows:
                L += _calib_lines(name, rows)
        bl, bars[label] = _bar_lines(bt)
        L += bl
    L += ["", f"Wall time {time.time() - t0:.0f} s."]
    out = Path(getattr(a, "loro_out", ROOT / "reports" / "survival_loro.md"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    summary = {"stage": stage, "current": CURRENT, "folds": folds, "mean_heldout_fitted": mean_fit,
               "mean_heldout_current": mean_cur, "pooled_heldout_fitted": pooled_fit,
               "pooled_heldout_current": pooled_cur, "bars": bars, "seconds": time.time() - t0}
    out.with_suffix(".json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")
    print(f"\nLORO pooled mean: fitted {mean_fit:.4f}  current {mean_cur:.4f}  delta {mean_fit - mean_cur:+.4f}"
          f"\nrow-pooled:       fitted {pooled_fit:.4f}  current {pooled_cur:.4f}\n-> {out}")
    return summary
