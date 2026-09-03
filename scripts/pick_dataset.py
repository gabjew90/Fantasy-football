"""Pick-level rival dataset for the autopick refit (plan 2026-09-03 s2, DECISIONS #35).

One row per RIVAL pick in every logged Yahoo room: who was available at that
moment, what that seat still needed, where the taken player ranked by our
board's ADP and by Yahoo's own default rank (`o_rank`), and how the seat is
labelled. The labels are the pre-registered ones:

  timing_label  from the driver's first-sight stamp (new rooms only):
                'instant' = clock_left >= clock_max - 3 AND poll gap <= 2 s;
                'human' = clock_left <= clock_max - 10; else 'unknown'/'unseen'
  away_label    'away' if the seat's team id was in away_teams at the nearest
                preceding bridge call (sidecar, built from TEAM IDS, never from
                the slot map); 'present' otherwise; 'no_sidecar' for rooms
                without one
  end_away      the trail's final managers[].away flag
  seat_class    ours | instant | away | human | unknown  (fit classes)

Ranks are 1-based among the players still available; `rank_fit_*` restricts
the pool to positions that fit an open starter slot (starters-first rule),
which is the pre-declared need-rule check: if instant/away picks are not
much more often #1 under that filter, the list being walked is not o_rank.

    venv\\Scripts\\python.exe scripts\\pick_dataset.py --league keefamania --report
    -> data/processed/rival_picks.csv, reports/rival_picks.md
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from draftkit import snake  # noqa: E402
from draftkit.config import Config  # noqa: E402
from engine_parity import league_shape  # noqa: E402
from mock_common import key, load_trail  # noqa: E402

MOCKS = ROOT / "data" / "logs" / "mocks"
LOGS = ROOT / "data" / "logs"
BUCKETS = ((0, 60, "early (pick<=60)"), (61, 200, "late (pick>60)"))


# ---------------------------------------------------------------- loading

def rooms_available() -> list[str]:
    out = []
    for p in sorted(MOCKS.glob("mock_*.json")):
        stem = p.stem[len("mock_"):]
        if stem.startswith("players_") or stem.endswith("_prereload") or stem.startswith("email"):
            continue
        out.append(stem)
    return out


def load_sidecar(room: str) -> list[dict]:
    p = LOGS / f"yahoo_{room}.plans.jsonl"
    if not p.exists():
        return []
    rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    return sorted(rows, key=lambda d: (d.get("call") or 0))


def load_snapshot(room: str) -> tuple[dict, str]:
    """{(key, pos): {o_rank, avg_pick, psr_rank}} and where it came from: the
    room's own snapshot, else the newest snapshot on disk (o_rank is Yahoo's
    default list and moves slowly), else empty."""
    own = [MOCKS / f"players_{room}.json", MOCKS / f"mock_players_{room}.json"]
    cands = [p for p in own if p.exists()]
    src = "own"
    if not cands:
        cands = sorted(list(MOCKS.glob("players_*.json")) + list(MOCKS.glob("mock_players_*.json")),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        src = "newest-on-disk" if cands else "none"
    if not cands:
        return {}, src
    d = json.loads(cands[0].read_text(encoding="utf-8"))
    out = {}
    for p in d.get("players") or []:
        out[(key(p.get("name", "")), p.get("pos", ""))] = {"o_rank": p.get("o_rank"), "avg_pick": p.get("avg_pick"),
                                                             "psr_rank": p.get("psr_rank")}
    return out, f"{src}:{cands[0].name}"


def load_board_adp(league: str) -> dict:
    cfg = Config.load(league=league)
    path = cfg.scoped(Path("tiers.csv"))
    out = {}
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r.get("adp"):
                out[(key(r["player"]), r["pos"])] = float(r["adp"])
    return out


# ---------------------------------------------------------------- pure parts

def away_teams_at(sidecar: list[dict], pick_no: int) -> list[str] | None:
    """away_teams from the latest call whose current_pick <= pick_no (that call
    happened while pick_no was on the clock or earlier). None = no sidecar."""
    if not sidecar:
        return None
    best = None
    for d in sidecar:
        cp = d.get("current_pick")
        if cp is not None and cp <= pick_no:
            best = d
    if best is None:
        return []
    return [str(x) for x in ((best.get("state_in") or {}).get("away_teams") or [])]


def seat_class(is_ours: bool, timing: str | None, away: str) -> str:
    if is_ours:
        return "ours"
    if timing == "instant":
        return "instant"
    if away == "away":
        return "away"
    if timing == "human" or away == "present":
        return "human"
    return "unknown"


def rank_among(value, others: list) -> int | None:
    """1 + the count of available values strictly better (lower); None when the
    taken player has no value."""
    if value is None:
        return None
    return 1 + sum(1 for v in others if v is not None and v < value)


def build_rows(room: str, trail: dict, sidecar: list[dict], snap: dict, board_adp: dict,
               slots: dict, teams: int, pools: list | None = None) -> list[dict]:
    picks = sorted(trail.get("picks") or [], key=lambda x: x["pick_no"])
    managers = trail.get("managers") or {}
    me = str(trail.get("my_team"))
    starters = {k: v for k, v in slots.items() if k not in ("BN", "BENCH", "IR")}
    # the universe: every snapshot player (all carry o_rank) plus board players
    universe = set(snap) | set(board_adp)
    taken: set = set()
    by_seat_pos: dict[int, list[str]] = defaultdict(list)
    rows = []
    for p in picks:
        no = int(p["pick_no"])
        rnd, seat = snake.pick_to_round_slot(no, teams)
        k = (key(p.get("name", "")), p.get("pos", ""))
        needs = snake.starter_needs(by_seat_pos[seat], dict(starters))
        starters_open = any(v > 0 for v in needs.values())
        avail = [q for q in universe if q not in taken]
        fits = {q for q in avail if (not starters_open) or snake.needs_position(needs, q[1])}
        yr = (snap.get(k) or {}).get("o_rank")
        ap = board_adp.get(k)
        yr_all = [(snap.get(q) or {}).get("o_rank") for q in avail]
        yr_fit = [(snap.get(q) or {}).get("o_rank") for q in avail if q in fits]
        ad_all = [board_adp.get(q) for q in avail]
        ad_fit = [board_adp.get(q) for q in avail if q in fits]
        tid = str(p.get("team_id"))
        away_list = away_teams_at(sidecar, no)
        away = "no_sidecar" if away_list is None else ("away" if tid in away_list else "present")
        timing = p.get("label") if p.get("label") in ("instant", "human", "unknown", "unseen") else None
        is_ours = tid == me
        cls = seat_class(is_ours, timing, away)
        yahoo_adp_now = (snap.get(k) or {}).get("avg_pick")
        drift = (abs(yahoo_adp_now - ap) if (yahoo_adp_now is not None and ap is not None) else None)
        rows.append({
            "room": room, "pick_no": no, "round": rnd, "seat": seat, "team_id": tid,
            "player": p.get("name"), "pos": p.get("pos"),
            "seat_class": cls, "timing_label": timing or "", "away_label": away,
            "end_away": bool((managers.get(tid) or {}).get("away")),
            "clock_left": p.get("clock_left"), "poll_gap_ms": p.get("poll_gap_ms"),
            "yahoo_rank": yr, "board_adp": ap, "yahoo_adp_now": yahoo_adp_now,
            "adp_drift": None if drift is None else round(drift, 1), "unscoreable": bool(drift is not None and drift > 10),
            "rank_by_yrank": rank_among(yr, yr_all), "rank_fit_by_yrank": rank_among(yr, yr_fit) if k in fits else None,
            "rank_by_adp": rank_among(ap, ad_all), "rank_fit_by_adp": rank_among(ap, ad_fit) if k in fits else None,
            "fits_open_starter": k in fits, "starters_open": starters_open,
            "needs_before": " ".join(f"{a}{b}" for a, b in needs.items() if b),
            "n_available": len(avail),
        })
        if k in taken:
            # a key collision (two players with the same initial + surname +
            # position, e.g. the two Browns): the second one cannot be placed
            # in the pool honestly; the row is kept and flagged, the pool skipped
            rows[-1]["key_collision"] = True
        else:
            rows[-1]["key_collision"] = False
        if pools is not None and k in universe and k not in taken:
            # the multinomial's candidate set at this pick, for rival_fit.py
            cand = sorted(avail, key=lambda q: ((snap.get(q) or {}).get("o_rank") or 9999, board_adp.get(q) or 999))
            pools.append({
                "room": room, "pick_no": no, "round": rnd, "seat": seat, "seat_class": cls,
                "taken": cand.index(k), "starters_open": starters_open,
                "yrank": [(snap.get(q) or {}).get("o_rank") for q in cand],
                "adp": [board_adp.get(q) for q in cand],
                "fits": [q in fits for q in cand],
                "pos": [q[1] for q in cand],
                "needs": {a: b for a, b in needs.items() if b},
            })
        taken.add(k)
        by_seat_pos[seat].append(p.get("pos", ""))
    return rows


# ---------------------------------------------------------------- report

def _share(vals, k):
    v = [x for x in vals if x is not None]
    return (sum(1 for x in v if x <= k) / len(v)) if v else None


def _fmt(x, nd=2):
    return "-" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def summarize(rows: list[dict]) -> list[str]:
    L = []
    classes = ["instant", "away", "human", "unknown"]
    L += ["## Rank of the taken player among the players still available", "",
          "Lower is tighter. `top1` = share taken exactly the best available; `>10` = share taken someone ranked below tenth. "
          "`fit` = pool restricted to positions that fit an open starter slot (starters-first). "
          "Rooms: " + ", ".join(sorted({r['room'] for r in rows})) + ".", "",
          "| seat class | n | by Yahoo rank: median | top1 | top3 | >10 | fit: top1 | top3 | by board ADP: median | top1 | top3 | >10 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in classes:
        rs = [r for r in rows if r["seat_class"] == c]
        if not rs:
            continue
        yr = [r["rank_by_yrank"] for r in rs if r["rank_by_yrank"] is not None]
        yf = [r["rank_fit_by_yrank"] for r in rs if r["rank_fit_by_yrank"] is not None]
        ad = [r["rank_by_adp"] for r in rs if r["rank_by_adp"] is not None]
        L.append(f"| {c} | {len(rs)} | {_fmt(st.median(yr) if yr else None, 0)} | {_fmt(_share(yr, 1))} | {_fmt(_share(yr, 3))} | "
                 f"{_fmt(1 - _share(yr, 10) if yr else None)} | {_fmt(_share(yf, 1))} | {_fmt(_share(yf, 3))} | "
                 f"{_fmt(st.median(ad) if ad else None, 0)} | {_fmt(_share(ad, 1))} | {_fmt(_share(ad, 3))} | {_fmt(1 - _share(ad, 10) if ad else None)} |")
    L += ["", "### Histograms (rank by Yahoo rank, 1..9 then 10+)", "", "| seat class | " + " | ".join(str(i) for i in range(1, 10)) + " | 10+ |",
          "|---|" + "---|" * 10]
    for c in classes:
        rs = [r["rank_by_yrank"] for r in rows if r["seat_class"] == c and r["rank_by_yrank"] is not None]
        if not rs:
            continue
        h = Counter(min(x, 10) for x in rs)
        L.append(f"| {c} | " + " | ".join(str(h[i]) for i in range(1, 11)) + " |")
    L += ["", "### By draft stage (rank by Yahoo rank)", "", "| seat class | stage | n | median | top1 | top3 |", "|---|---|---|---|---|---|"]
    for c in classes:
        for lo, hi, name in BUCKETS:
            rs = [r["rank_by_yrank"] for r in rows if r["seat_class"] == c and lo <= r["pick_no"] <= hi and r["rank_by_yrank"] is not None]
            if rs:
                L.append(f"| {c} | {name} | {len(rs)} | {st.median(rs):.0f} | {_fmt(_share(rs, 1))} | {_fmt(_share(rs, 3))} |")
    # the need-rule check, said in words
    aw = [r for r in rows if r["seat_class"] in ("instant", "away")]
    t_all = _share([r["rank_by_yrank"] for r in aw], 1)
    t_fit = _share([r["rank_fit_by_yrank"] for r in aw], 1)
    L += ["", "### Need-rule check (pre-declared, DECISIONS #35)", "",
          f"instant/away picks, share exactly #1 by Yahoo rank: all positions {_fmt(t_all)} -> starters-first filter {_fmt(t_fit)}. "
          + ("The filter RAISES the exact-hit share: the list walked is consistent with o_rank plus a starters-first rule; the one-hot list component stands."
             if (t_all is not None and t_fit is not None and t_fit > t_all + 0.05)
             else "The filter does NOT raise the exact-hit share materially: the list walked is not o_rank (personal pre-ranks, or a different rule); the pre-declared branch applies -- the list component becomes a tight Gaussian in o_rank."), ""]
    drift = [r for r in rows if r["unscoreable"]]
    L += ["### ADP drift", "", f"{len(drift)} of {len(rows)} rival picks are unscoreable for the ADP-Gaussian likelihood "
          "(board ADP vs Yahoo's ADP at the snapshot moved > 10 picks); they stay in the Yahoo-rank likelihood.", ""]
    return L


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", default="keefamania")
    ap.add_argument("--rooms", default=None, help="comma list; default every mock_<room>.json with a trail")
    ap.add_argument("--out", default=str(ROOT / "data" / "processed" / "rival_picks.csv"))
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--pools", default=str(ROOT / "data" / "processed" / "rival_pools.jsonl"),
                    help="per-pick candidate pools for rival_fit.py (JSON lines)")
    a = ap.parse_args()
    cfg = Config.load(league=a.league)
    teams, _rounds, slots = league_shape(cfg)
    board_adp = load_board_adp(a.league)
    rooms = [x.strip() for x in a.rooms.split(",")] if a.rooms else rooms_available()
    all_rows, notes, pools = [], [], []
    for room in rooms:
        try:
            trail = load_trail(ROOT, room)
        except Exception as e:  # noqa: BLE001
            notes.append(f"{room}: no usable trail ({type(e).__name__})")
            continue
        if int(trail.get("teams") or teams) != teams:
            notes.append(f"{room}: {trail.get('teams')} teams, skipped (league shape is {teams})")
            continue
        snap, src = load_snapshot(room)
        side = load_sidecar(room)
        rows = build_rows(room, trail, side, snap, board_adp, slots, teams, pools)
        n_side = "sidecar" if side else "NO sidecar"
        notes.append(f"{room}: {len(rows)} picks, {n_side}, snapshot {src}, timing labels "
                     f"{sum(1 for r in rows if r['timing_label'] in ('instant', 'human'))}")
        all_rows += rows
    rival = [r for r in all_rows if r["seat_class"] != "ours"]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if all_rows:
        with out.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(all_rows[0].keys()))
            w.writeheader()
            w.writerows(all_rows)
    print(f"{len(all_rows)} rows ({len(rival)} rival picks) -> {out}")
    if a.pools:
        pp = Path(a.pools)
        pp.parent.mkdir(parents=True, exist_ok=True)
        with pp.open("w", encoding="utf-8") as fh:
            for rec in pools:
                if rec["seat_class"] != "ours":
                    fh.write(json.dumps(rec) + "\n")
        print(f"{sum(1 for r in pools if r['seat_class'] != 'ours')} candidate pools -> {pp}")
    for n in notes:
        print("  " + n)
    if a.report:
        L = ["# Rival picks -- the pick-level dataset behind the autopick refit (DECISIONS #35)", "",
             f"{len(rival)} rival picks over {len({r['room'] for r in rival})} rooms; our own picks excluded. Rows: {out}", ""]
        L += ["Rooms:"] + [f"- {n}" for n in notes] + [""]
        L += summarize(rival)
        rep = ROOT / "reports" / "rival_picks.md"
        rep.write_text("\n".join(L) + "\n", encoding="utf-8")
        print(f"-> {rep}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
