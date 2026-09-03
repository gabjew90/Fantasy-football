"""One scrutiny report per mock room, joined from the four logs (2026-09-02).

Inputs, all written live during the room:
  data/logs/mocks/mock_<room>.json          the driver's trail: every pick with team id, the
                                            managers, OUR pick records, the full action log
  data/logs/yahoo_<room>.plans.jsonl        the bridge's sidecar: one line per plan call with the
                                            state received, needs, recs, the full plan, every
                                            market's numbers, warnings
  data/logs/yahoo_<room>.jsonl              the room log: pick events and recs events with the
                                            survival window (the calibration record)
  data/draftrig/bridge_*.log (optional)     the bridge's stdout, one timestamped line per call

Output: reports/mocks/scrutiny_<room>.md --
  * the run in numbers (pick paths, latencies, heartbeats, away events, gate failures,
    local fallbacks, bridge warnings, injected faults);
  * for each of OUR picks: what landed and how, what the engine's plan said at that call
    (top rows with survival / expected-best / urgency, every market's numbers, needs, away
    seats), candidates skipped and why, plan rows the page dropped, and whether the engine's
    first choice was taken -- if not, the reason the record gives;
  * the survival scorecard: every shown survival vs what happened by my next pick;
  * the driver log, filtered to the lines that matter.

    venv\\Scripts\\python.exe scripts\\mock_scrutiny.py --room 10531886
    venv\\Scripts\\python.exe scripts\\mock_scrutiny.py --room 10531886 --bridge-log data/draftrig/bridge_2026-09-02_stress.log
"""

from __future__ import annotations

import argparse
import json
import re
import statistics as st
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from draftkit.snake import pick_to_round_slot  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from mock_common import HOW_THE_ENGINE_THINKS, header_line, load_trail, pt_lines, report_stem, to_pt  # noqa: E402

ISSUE = re.compile(r"ON CLOCK|GATE|LOCAL|AWAY|heartbeat|PLAN |WARNING|ERROR|preflight|trail:|driver st|roster full|draft over|retry|notours")


def load(room: str, bridge_log: str | None):
    trail = load_trail(ROOT, room)   # pre-reload records and log merged in
    plans_p = ROOT / "data" / "logs" / f"yahoo_{room}.plans.jsonl"
    plans = [json.loads(x) for x in plans_p.read_text(encoding="utf-8").splitlines()] if plans_p.exists() else []
    room_p = ROOT / "data" / "logs" / f"yahoo_{room}.jsonl"
    events = [json.loads(x) for x in room_p.read_text(encoding="utf-8").splitlines()] if room_p.exists() else []
    blog = []
    if bridge_log and Path(bridge_log).exists():
        blog = [x for x in Path(bridge_log).read_text(encoding="utf-8", errors="replace").splitlines() if "WARNING" in x or "Traceback" in x or "Error" in x]
    return trail, plans, events, blog


def key(name: str) -> str:
    """first initial + last token, lower -- the board key, for joining names across logs"""
    parts = re.sub(r"[^a-z0-9 ]", " ", (name or "").lower()).split()
    parts = [p for p in parts if p not in ("jr", "sr", "ii", "iii", "iv", "v")] or parts
    return (parts[0][0] + " " + parts[-1]) if parts else ""


def fmt_row(p: dict) -> str:
    def f(v, nd=1):
        return "-" if v is None else (f"{v:.{nd}f}" if isinstance(v, (int, float)) else str(v))
    return f"| {p.get('n')} | {p.get('p')} | {f(p.get('v'))} | {f(p.get('s'), 2)} | {f(p.get('sr'), 2)} | {f(p.get('e'))} | {f(p.get('b'))} | {(p.get('why') or '')[:90]} |"


def plain_english(r: dict) -> str:
    """One sentence a non-technical reader can check against the numbers."""
    why = r.get("why") or ""
    name, pos = r.get("drafted"), r.get("pos")
    alt = (r.get("top_proj_available") or {}).get("n")
    s = r.get("s")
    pct = f"{round(float(s) * 100)}%" if isinstance(s, (int, float)) and s else None
    parts = []
    m = re.search(r"waiting likely costs ~(\d+) pts at ([^(]+?)\s*\(", why)
    if m:
        parts.append(f"Took {name} ({pos}) because waiting would likely cost about {m.group(1)} points at {m.group(2).strip()}"
                     + (f", with a {pct} chance he would still be there next turn" if pct else "") + ".")
    elif why.startswith("safe to wait"):
        parts.append(f"Took {name} ({pos}): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot"
                     + (f" ({pct} to survive, but nobody better was worth waiting for)" if pct else "") + ".")
    elif why.startswith("bench insurance"):
        m2 = re.search(r"covers (\d+) (\w+) starters?[^~]*~([\d.]+) wks[^+]*\+([\d.]+)/wk[^(]*(?:\(([^)]+)\))?[^0-9]*(\d+) pts", why)
        if m2:
            parts.append(f"Lineup already full, so {name} ({pos}) is insurance: covers {m2.group(1)} {m2.group(2)} starter(s) for about {m2.group(3)} weeks a season at +{m2.group(4)} points a week over the waiver wire"
                         + (f" ({m2.group(5)})" if m2.group(5) else "") + f", worth about {m2.group(6)} points.")
        else:
            parts.append(f"Lineup already full, so {name} ({pos}) was priced as bench insurance, not by raw points.")
        if "HANDCUFF" in why:
            parts.append("He also backs up one of our own starters, which raises that value.")
    elif why.startswith("LOCAL ranker"):
        parts.append(f"The engine was unreachable, so the page's own simpler ranking took {name} ({pos}): {why}.")
    elif why.startswith("depth fallback") or why.startswith("fills your open"):
        parts.append(f"Took {name} ({pos}) to fill a mandatory slot; nothing the engine named was left.")
    else:
        parts.append(f"Took {name} ({pos}). Engine: {why[:120]}")
    if alt and alt != name:
        parts.append(f"The top raw projection available was {alt}; the engine passed on him on purpose.")
    if r.get("attempted"):
        parts.append("Before this landed the driver skipped: " + ", ".join(r["attempted"]) + ".")
    if r.get("source") == "local":
        parts.append("(Local ranker, not the engine.)")
    return " ".join(parts)


def render(room: str, trail: dict, plans: list[dict], events: list[dict], blog: list[str],
           label: str | None = None, name: str | None = None) -> str:
    teams = int(trail.get("teams") or 10)
    my_team = str(trail.get("my_team"))
    picks = sorted(trail.get("picks") or [], key=lambda x: x["pick_no"])
    pick_at = {p["pick_no"]: p for p in picks}
    gone_at = {}   # board key|pos -> pick_no drafted
    for p in picks:
        gone_at.setdefault(key(p["name"]) + "|" + p["pos"], p["pick_no"])
    recs = trail.get("our_records") or []
    rec_by_pick = {r.get("pick_no"): r for r in recs if r.get("pick_no")}
    log = trail.get("log") or []
    mine = [p for p in picks if str(p["team_id"]) == my_team]
    my_slot = pick_to_round_slot(mine[0]["pick_no"], teams)[1] if mine else None

    # ---- the run in numbers
    via = Counter(r.get("via") or "?" for r in recs)
    lat = [r["ms"] for r in recs if isinstance(r.get("ms"), (int, float))]
    yahoo_made = [p for p in mine if p["pick_no"] not in rec_by_pick]
    n_hb = sum(1 for l in log if "heartbeat: setAwayStatus" in l)
    n_away = sum(1 for l in log if "AWAY detected" in l)
    n_gate = sum(1 for l in log if "GATE FAILED" in l)
    n_local = sum(1 for l in log if "LOCAL ranking" in l)
    n_planfail = sum(1 for l in log if re.search(r"PLAN (bridge|engine)", l))
    warnings = sorted({w for d in plans for w in (d.get("warnings") or [])})
    away_sets = []
    for d in plans:
        s = tuple(d.get("away_slots") or [])
        if not away_sets or away_sets[-1] != s:
            away_sets.append(s)
    L = [f"# Scrutiny: {header_line(trail, label, name, my_slot, teams)}", "",
         f"Captured {to_pt(trail.get('captured_at'))}. Times below are Pacific. {teams} teams, our team id {my_team}, draft slot {my_slot}. "
         f"{len(picks)} picks in the trail, {len(plans)} bridge plan calls, {sum(1 for e in events if e.get('type') == 'recs')} recs events in the room log.", ""]
    if trail.get("reloaded"):
        L += [f"The page was reloaded mid-draft at {to_pt(trail['reloaded'])}; records from before it are merged in.", ""]
    if trail.get("stress"):
        L += [f"Injected: {trail['stress']}", ""]
    L += [HOW_THE_ENGINE_THINKS]
    L += ["## The run in numbers", "",
          f"- Our picks: {len(mine)}; by the driver {len(recs)} (action {via.get('action', 0)}, click {via.get('click', 0)}), "
          f"by Yahoo from the queue / autopick {len(yahoo_made)}" + (": " + ", ".join(f"{p['pick_no']} {p['name']}" for p in yahoo_made) if yahoo_made else "") + ".",
          f"- Action latency to store confirmation: " + (f"median {st.median(lat):.0f} ms, min {min(lat):.0f}, max {max(lat):.0f}" if lat else "n/a") + ".",
          f"- Heartbeats {n_hb}; away flags detected and cleared {n_away}; gate failures {n_gate}; local-ranker fallbacks {n_local}; plan refresh failures {n_planfail}.",
          f"- Bridge warnings ({len(warnings)}): " + ("; ".join(warnings) if warnings else "none") + ".",
          f"- Away seats over the room (each change): " + " -> ".join("{" + ",".join(map(str, s)) + "}" for s in away_sets) + ".",
          f"- Managers away at the end: " + ", ".join(f"{k} {v.get('nickname', '')}".strip() for k, v in (trail.get('managers') or {}).items() if v.get('away')) + ".", ""]

    # ---- per pick
    L += ["## Our picks, one block each", ""]
    for p in mine:
        no = p["pick_no"]
        rnd, _ = pick_to_round_slot(no, teams)
        r = rec_by_pick.get(no)
        L += [f"### Pick {no} (round {rnd}): {p['name']} ({p['pos']})", ""]
        if r:
            L += [f"- In plain English: {plain_english(r)}",
                  f"- Driver: via **{r.get('via')}**, verified {r.get('verified')}, {r.get('ms', '-')} ms, ranker {r.get('source', '?')}, plan call {r.get('plan_call')}, plan age {r.get('plan_age_ms')} ms, at {to_pt(r.get('ts'), '%H:%M:%S PT') or '?'}.",
                  f"- Engine's reason: {r.get('why', '')}",
                  f"- Top projection available: {(r.get('top_proj_available') or {}).get('n')} -> took it: {r.get('took_top_projection')}."]
            if r.get("attempted"):
                L.append(f"- Skipped before this landed: {', '.join(r['attempted'])}.")
            if r.get("dropped"):
                L.append("- Plan rows the page dropped: " + ", ".join(x["n"] + " (" + str(x["why"]) + ")" for x in r["dropped"]) + ".")
            if r.get("passed_on"):
                L.append("- Passed on: " + "; ".join(f"{x['n']} ({x['p']}, s={x.get('s')}, e={x.get('e')})" for x in r["passed_on"]) + ".")
        else:
            L.append("- **No driver record**: Yahoo made this pick (queue head or autopick).")
            # the turn's own log lines: from the previous own pick to this one
            prev_no = max([q["pick_no"] for q in mine if q["pick_no"] < no], default=0)
            prev_rec = rec_by_pick.get(prev_no)
            t_from = (prev_rec or {}).get("ts") or ""
            turn_lines = []
            for l in log:
                ts = l[:24]
                if t_from and ts <= t_from:
                    continue
                if re.search(r"ON CLOCK|GATE|LOCAL|PLAN |AWAY|notours|retry", l):
                    turn_lines.append(l)
                if f'"pick_no":{no + 1}' in l or f'"pick_no":{no + 2}' in l:
                    break
            if turn_lines:
                L.append("- The turn in the driver log:")
                L += [f"    {l[:260]}" for l in pt_lines(turn_lines[:12])]
        # the plan at that call, else the last plan computed at this pick
        # number, else the LAST plan before it (a bridge outage leaves none)
        d = None
        if r and r.get("plan_call") is not None:
            d = next((x for x in plans if x.get("call") == r["plan_call"]), None)
        if d is None:
            cands = [x for x in plans if x.get("current_pick") == no]
            d = cands[-1] if cands else None
        if d is None:
            before = [x for x in plans if (x.get("current_pick") or 0) < no]
            if before:
                d = before[-1]
                L.append(f"- No plan call at this pick; the last plan before it was call {d.get('call')} @pick {d.get('current_pick')}:")
        if d:
            first = (d.get("plan") or [{}])[0]
            landed_first = bool(first) and key(first.get("n", "")) == key(p["name"]) and first.get("p") == p["pos"]
            L += [f"- Plan call {d.get('call')} @pick {d.get('current_pick')}: needs {d.get('needs')}, away seats {d.get('away_slots')}, "
                  f"state {d.get('state_in', {}).get('source')} with {d.get('state_in', {}).get('drafted')} drafted / {d.get('state_in', {}).get('mine')} mine"
                  + (f", warnings {d['warnings']}" if d.get("warnings") else "") + ".",
                  f"- Engine's first choice was **{first.get('n')}** -> {'taken' if landed_first else 'NOT taken'}.", "",
                  "| plan row | pos | vorp | s | sr | e_best_next | best_now | why |", "|---|---|---|---|---|---|---|---|"]
            L += [fmt_row(x) for x in (d.get("plan") or [])[:6]]
            L += ["", "| market | best_now | e_best_next | urgency | pool |", "|---|---|---|---|---|"]
            for mk, m in (d.get("markets") or {}).items():
                L.append(f"| {mk} | {m.get('best_now')} | {'-' if m.get('e_best_next') is None else round(m['e_best_next'], 1)} | "
                         f"{'-' if m.get('urgency') is None else round(m['urgency'], 1)} | {m.get('pool')} |")
        else:
            L.append("- No plan call recorded at this pick (bridge down?).")
        # log lines around the pick
        around = [l for l in log if f"ON CLOCK" in l and f'"pick_no":{no}' in l] or []
        L.append("")

    # ---- survival scorecard from the room log
    rows = []
    for e in events:
        if e.get("type") != "recs" or not e.get("my_next_pick"):
            continue
        nxt = int(e["my_next_pick"])
        for rr in e.get("recommendations") or []:
            s = rr.get("survival_shown")
            if s is None:
                continue
            k = key(rr.get("player", "")) + "|" + rr.get("pos", "")
            g = gone_at.get(k)
            if g is not None and g < int(e["current_pick"]):
                continue                      # already gone when shown: not a prediction
            survived = g is None or g >= nxt
            rows.append((float(s), survived, e["current_pick"], nxt, rr.get("player")))
    L += ["## Survival scorecard (shown survival vs what happened by my next pick)", ""]
    if rows:
        L += ["| bucket | n | mean shown | observed survived |", "|---|---|---|---|"]
        for lo, hi in ((0, 30), (30, 50), (50, 70), (70, 90), (90, 101)):
            b = [r for r in rows if lo <= r[0] * 100 < hi]
            if b:
                L.append(f"| {lo}-{min(hi, 100)}% | {len(b)} | {100 * st.mean(x[0] for x in b):.0f}% | {100 * st.mean(1.0 if x[1] else 0.0 for x in b):.0f}% |")
        L.append("")
        L.append(f"{len(rows)} predictions over {len({(r[2], r[3]) for r in rows})} windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.")
    else:
        L.append("No recs events with a survival window in the room log.")
    L.append("")

    # ---- bridge warnings / errors
    if blog:
        L += ["## Bridge log: warnings and errors", ""] + [f"    {x[:200]}" for x in blog[:40]] + [""]

    # ---- the narration, exactly as the panel showed it
    narr = trail.get("narration") or []
    if narr:
        L += ["## Narration (what the panel showed live, Pacific time)", ""]
        L += [f"    {to_pt(e.get('ts'), '%H:%M:%S')}  {e.get('text', '')[:230]}" for e in narr]
        L.append("")
    # ---- driver log
    L += ["## Driver log (the lines that matter, Pacific time)", ""]
    L += [f"    {l[:240]}" for l in pt_lines([l for l in log if ISSUE.search(l)])]
    L.append("")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--room", required=True)
    ap.add_argument("--bridge-log", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--label", default=None, help="e.g. 'Mock 25' -- goes into the file name and the header")
    ap.add_argument("--name", default=None, help="the room's nickname when the trail only has the tab title")
    a = ap.parse_args()
    trail, plans, events, blog = load(a.room, a.bridge_log)
    md = render(a.room, trail, plans, events, blog, a.label, a.name)
    teams = int(trail.get("teams") or 10)
    mine = [p for p in sorted(trail.get("picks") or [], key=lambda x: x["pick_no"]) if str(p["team_id"]) == str(trail.get("my_team"))]
    seat = pick_to_round_slot(mine[0]["pick_no"], teams)[1] if mine else None
    out = Path(a.out) if a.out else ROOT / "reports" / "mocks" / f"{report_stem(trail, a.label, a.name, seat)}_scrutiny.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"-> {out} ({len(md.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
