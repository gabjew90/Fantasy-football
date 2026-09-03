"""Re-draft OUR seat through a recorded Yahoo room, at every seat, with the
engine at a knob point (plan 2026-09-03 s5; DECISIONS #35 G3).

The trail data/logs/mocks/mock_<room>.json is adapted into slot_replay's
pick-log shape (pick_no, slot, player, round, type "pick"); the rivals' picks
stay fixed, our seat's picks are replaced by the engine's, for each draft
slot 1..teams in turn. Unlike slot_replay, every tracker is rebuilt HERE
with `away_slots` = the room's away set at that pick (from the bridge
sidecar, via fit_survival.away_at_from_sidecar), so an autopick knob point
is exercised the way the live driver would exercise it. Graded on
slot_replay.lineup_points (projected points of the best legal lineup;
baseline-free).

    venv\\Scripts\\python.exe scripts\\yahoo_trail_replay.py --room 10534350 --league keefamania \\
        --set autopick_list_prob=0.3 --set autopick_sigma_scale=0.75 --set autopick_need_damp=0.45 --compare

`--compare` runs the production point (the league yaml's engine block) as
the "current" arm and the same point plus the --set knobs as the "fitted"
arm, prints per-slot and mean deltas, and writes
reports/yahoo_trail_replay.<room>.md. Names are matched trail -> board with
mock_common.key on both sides, exact name as the fallback; unmatched names
are reported (they are simply "not on the board" for the engine).
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from draftkit import snake  # noqa: E402
from fit_survival import away_at_from_sidecar, load_sidecar, team_slots  # noqa: E402
from mock_common import key, load_trail  # noqa: E402

FITTED_DEFAULT = {"autopick_list_prob": 0.3, "autopick_sigma_scale": 0.75, "autopick_need_damp": 0.45}


# ------------------------------------------------------------------ adapters

def trail_to_log(trail: dict, teams: int | None = None) -> list[dict]:
    """A trail's picks as slot_replay pick-log dicts. `player` is the trail
    name; slot and round come from the snake, not from the trail."""
    teams = int(teams or trail.get("teams") or 10)
    out = []
    for p in sorted(trail.get("picks") or [], key=lambda x: int(x["pick_no"])):
        n = int(p["pick_no"])
        rnd, slot = snake.pick_to_round_slot(n, teams)
        out.append({"type": "pick", "pick_no": n, "slot": slot, "round": rnd,
                    "player": str(p.get("name") or ""), "pos": p.get("pos"), "team_id": str(p.get("team_id"))})
    return out


def away_sets(trail: dict, calls: list[dict], teams: int | None = None) -> dict[int, frozenset]:
    """{pick_no: frozenset(slots on autopick)} for the whole trail."""
    teams = int(teams or trail.get("teams") or 10)
    picks = trail.get("picks") or []
    n = max((int(p["pick_no"]) for p in picks), default=0)
    return away_at_from_sidecar(calls, team_slots(picks, teams), n) if calls else {}


def match_names(log: list[dict], board: list[dict]) -> tuple[dict[str, dict], list[str], list[str]]:
    """trail name -> board row. mock_common.key on both sides when the key is
    unique on the board; exact name as the fallback (and as the tiebreak for
    a colliding key). Returns (map, unmatched names, ambiguous names)."""
    by_name = {p["name"]: p for p in board}
    by_key: dict[str, list[dict]] = {}
    for p in board:
        by_key.setdefault(key(p["name"]), []).append(p)
    out, unmatched, ambiguous = {}, [], []
    for d in log:
        name = d["player"]
        if name in out:
            continue
        if name in by_name:
            out[name] = by_name[name]
            continue
        cands = by_key.get(key(name), [])
        if len(cands) == 1:
            out[name] = cands[0]
        elif len(cands) > 1:
            same_pos = [c for c in cands if d.get("pos") and c["pos"] == str(d["pos"]).upper()]
            if len(same_pos) == 1:
                out[name] = same_pos[0]
            else:
                ambiguous.append(name)
        else:
            unmatched.append(name)
    return out, unmatched, ambiguous


# --------------------------------------------------------------------- replay

def replay_seat(board: list[dict], log: list[dict], my_slot: int, teams: int, rounds: int, slots: dict,
                cfg=None, overrides: dict | None = None, away_at: dict | None = None,
                name_map: dict | None = None, errors: list | None = None) -> list[dict]:
    """slot_replay.replay's loop, with the tracker built per pick here so
    `away_slots` follows the room's away set at that pick."""
    import engine_parity as EP
    name_map = name_map if name_map is not None else match_names(log, board)[0]
    away_at = away_at or {}
    taken, chosen, picks_so_far = set(), [], []
    for d in log:
        if d.get("slot") != my_slot:
            p = name_map.get(d["player"])
            if p is not None:
                taken.add(p["name"])
            picks_so_far.append({"pick_no": d["pick_no"], "player_id": p["sleeper_id"] if p else "0",
                                 "draft_slot": d["slot"], "round": d["round"]})
            continue
        avail = [p for p in board if p["name"] not in taken]
        ov = {**(overrides or {}), "away_slots": frozenset(away_at.get(d["pick_no"], frozenset()))}
        t = EP.make_tracker(board, picks_so_far, my_slot, slots=slots, teams=teams, rounds=rounds,
                            cfg=cfg, overrides=ov)
        try:
            recs = t.recommendations(top_n=1)
            pick = next(p for p in board if p["name"] == recs[0][2]["name"]) if recs else avail[0]
        except Exception as e:  # noqa: BLE001
            if errors is not None:
                errors.append(f"slot {my_slot} pick {d['pick_no']}: {e!r}")
            pick = avail[0]
        chosen.append(pick)
        taken.add(pick["name"])
        picks_so_far.append({"pick_no": d["pick_no"], "player_id": pick["sleeper_id"],
                             "draft_slot": my_slot, "round": d["round"]})
    return chosen


def shape(chosen) -> str:
    c = Counter(p["pos"] for p in chosen)
    return " ".join(f"{k}{c[k]}" for k in ("QB", "RB", "WR", "TE", "K", "DEF") if c[k])


def parse_sets(items: list[str]) -> dict:
    out = {}
    for kv in items:
        k, v = kv.split("=", 1)
        try:
            out[k] = int(v) if v.strip().lstrip("-").isdigit() else float(v)
        except ValueError:
            out[k] = {"true": True, "false": False}.get(v.lower(), v)
    return out


def run(room: str, league: str, board_path: str | None, sets: dict, compare: bool, seat_list: list[int] | None,
        out_path: Path | None, root: Path = ROOT) -> dict:
    import engine_parity as EP
    from slot_replay import lineup_points
    from survival_refit import attach_yahoo_rank, yahoo_rank_source
    from draftkit.config import Config
    t0 = time.time()
    cfg = Config.load(league=league)
    teams, rounds, slots = EP.league_shape(cfg)
    trail = load_trail(root, room)
    if int(trail.get("teams") or teams) != teams:
        print(f"!! trail says {trail.get('teams')} teams, league {league} says {teams}; using the league shape")
    board_path = board_path or str(cfg.scoped(Path("tiers.csv")))
    board = EP.load_board(board_path)
    yr_note = attach_yahoo_rank(board, yahoo_rank_source(room, root / "data" / "logs" / "mocks"))
    calls = load_sidecar(room, root / "data" / "logs")
    log = trail_to_log(trail, teams)
    away_at = away_sets(trail, calls, teams)
    n_away = sum(1 for v in away_at.values() if v)
    name_map, unmatched, ambiguous = match_names(log, board)
    rounds_seen = max((d["round"] for d in log), default=rounds)
    seats = seat_list or list(range(1, teams + 1))
    arms = [("fitted", dict(sets))]
    if compare:
        arms = [("current", {}), ("fitted", dict(sets))]
    print(f"Yahoo trail replay -- room {room}, league {league}, {teams} teams, {rounds_seen} rounds, "
          f"{len(log)} picks; away set non-empty at {n_away}/{len(log)} picks"
          + (" (no sidecar)" if not calls else "") + f"; {yr_note}")
    print(f"board {board_path}: {len(name_map)} trail names matched, {len(unmatched)} unmatched"
          + (f" ({', '.join(unmatched)})" if unmatched else "") + f", {len(ambiguous)} ambiguous"
          + (f" ({', '.join(ambiguous)})" if ambiguous else ""))
    print(f"arms: " + ", ".join(f"{n} {ov or 'production engine block'}" for n, ov in arms))
    results = {n: {} for n, _ in arms}
    errors: list[str] = []
    hdr = f"{'slot':>4}" + "".join(f"{n:>12}" for n, _ in arms) + (f"{'delta':>9}" if compare else "") + "   shape " + " / ".join(n for n, _ in arms)
    print(hdr)
    rows = []
    for s in seats:
        line = f"{s:>4}"
        pts = {}
        for n, ov in arms:
            chosen = replay_seat(board, log, s, teams, rounds_seen, slots, cfg=cfg, overrides=ov,
                                 away_at=away_at, name_map=name_map, errors=errors)
            pts[n] = lineup_points(chosen, slots=slots)
            results[n][s] = {"points": pts[n], "shape": shape(chosen), "roster": [p["name"] for p in chosen]}
            line += f"{pts[n]:>12.1f}"
        if compare:
            line += f"{pts['fitted'] - pts['current']:>+9.1f}"
        line += "   " + " / ".join(results[n][s]["shape"] for n, _ in arms)
        print(line, flush=True)
        rows.append((s, pts))
    summary = {"room": room, "league": league, "teams": teams, "rounds": rounds_seen, "board": board_path,
               "sets": sets, "away_states": n_away, "sidecar": bool(calls), "unmatched": unmatched,
               "ambiguous": ambiguous, "per_slot": results, "errors": errors, "seconds": time.time() - t0}
    L = [f"# Yahoo trail replay -- room {room} ({league}, {teams} teams, {rounds_seen} rounds)", "",
         f"Our seat re-drafted by the engine at each of {len(seats)} slot(s); rivals fixed to the trail. "
         f"Away set non-empty at {n_away}/{len(log)} picks" + (" (no sidecar: never)" if not calls else "")
         + f". {yr_note}. Graded on projected points of the best legal lineup (slot_replay.lineup_points).", "",
         f"Arms: " + "; ".join(f"**{n}** = {ov or 'production engine block (league yaml)'}" for n, ov in arms), ""]
    if compare:
        d = [r[1]["fitted"] - r[1]["current"] for r in rows]
        mean_cur = st.mean(r[1]["current"] for r in rows)
        mean_fit = st.mean(r[1]["fitted"] for r in rows)
        summary.update({"mean_current": mean_cur, "mean_fitted": mean_fit, "mean_delta": st.mean(d),
                        "better": sum(1 for x in d if x > 0), "worse": sum(1 for x in d if x < 0),
                        "tied": sum(1 for x in d if x == 0)})
        print(f"\nn={len(rows)} slots  fitted - current: mean {st.mean(d):+.1f}  median {st.median(d):+.1f}  "
              f"better {summary['better']}  worse {summary['worse']}  tied {summary['tied']}  "
              f"worst {min(d):+.1f}  best {max(d):+.1f}")
        print(f"  current mean {mean_cur:.1f}  fitted mean {mean_fit:.1f}  ({100 * st.mean(d) / mean_cur:+.2f}%)")
        L += ["| slot | current | fitted | delta | shape current | shape fitted |", "|---|---|---|---|---|---|"]
        for s, pts in rows:
            L.append(f"| {s} | {pts['current']:.1f} | {pts['fitted']:.1f} | {pts['fitted'] - pts['current']:+.1f} | "
                     f"{results['current'][s]['shape']} | {results['fitted'][s]['shape']} |")
        L += ["", f"Mean: current {mean_cur:.1f}, fitted {mean_fit:.1f}, delta {st.mean(d):+.1f} "
              f"({100 * st.mean(d) / mean_cur:+.2f}%); median {st.median(d):+.1f}; better {summary['better']}, "
              f"worse {summary['worse']}, tied {summary['tied']}; worst {min(d):+.1f}, best {max(d):+.1f}."]
    else:
        L += ["| slot | fitted | shape |", "|---|---|---|"]
        for s, pts in rows:
            L.append(f"| {s} | {pts['fitted']:.1f} | {results['fitted'][s]['shape']} |")
        L += ["", f"Mean {st.mean(r[1]['fitted'] for r in rows):.1f}."]
    L += ["", "## Names", "",
          f"{len(name_map)} trail names matched to the board (mock_common.key, exact-name fallback); "
          f"{len(unmatched)} unmatched: {', '.join(unmatched) or 'none'}; "
          f"{len(ambiguous)} ambiguous (key collision, position did not resolve): {', '.join(ambiguous) or 'none'}."]
    if errors:
        L += ["", "## Engine errors (fell back to best available)", ""] + [f"- {e}" for e in errors]
    L += ["", f"Wall time {time.time() - t0:.0f} s."]
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(L) + "\n", encoding="utf-8")
        out_path.with_suffix(".json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
        print(f"-> {out_path}")
    return summary


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--room", required=True)
    ap.add_argument("--league", default="keefamania")
    ap.add_argument("--board", default=None, help="default: the league's scoped tiers csv")
    ap.add_argument("--set", action="append", default=[], metavar="KNOB=VALUE",
                    help="engine knob for the fitted arm (repeatable)")
    ap.add_argument("--compare", action="store_true", help="also run the production point and print deltas")
    ap.add_argument("--slots", default="", help="comma list of seats to replay (default all)")
    ap.add_argument("--out", default=None, help="default reports/yahoo_trail_replay.<room>.md")
    a = ap.parse_args()
    sets = parse_sets(a.set)
    seats = [int(x) for x in a.slots.split(",") if x.strip()] or None
    out = Path(a.out) if a.out else ROOT / "reports" / f"yahoo_trail_replay.{a.room}.md"
    run(a.room, a.league, a.board, sets, a.compare, seats, out)


if __name__ == "__main__":
    main()
