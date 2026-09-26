"""`nfl fantasy lineup`: start/sit for this week's matchup.

The user's framework (docs/plans/2026-09-24-consolidation-plan.md, section 6):
  1. opportunity, 2. role stability   -- the evidence table, step 4 (named as
                                          not yet covered in every report)
  3. scoring environment              -- spread, total, implied points per player
  4. matchup, opponent-adjusted, low  -- step 4 (named as not yet covered)
  5. game-day validity                -- status gating in fantasy.weekly
  Decision rule: likely to win -> the better floor; likely to lose -> the
  better ceiling. Implemented as maximising P(win) over the best-by-mean
  lineup and every legal one-player swap (fantasy.winprob), which is what the
  rule is an approximation of.

The verdict is personal only when the decision gate passes (fantasy.gate);
otherwise it is a CONDITIONAL comparison and says which check failed.

Writes a report (markdown) and a decision record (JSON) to the outputs folder.
With `record=True` it also appends a ledger row, graded against actuals like
every other. Chat never records (it is read-only). NOTHING PASSES IT YET: the
scheduled runs are rewired to call this command with --record in step 6
(the Actions rework), so until then no start/sit recommendation is graded.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from dataclasses import dataclass
from pathlib import Path

from core.manifest import Manifest
from draftkit.lineup import optimal_lineup

from . import environment as E
from . import evidence as EV
from . import gate as G
from . import league as LG
from . import weekly as W
from . import winprob as WP

OUT = Path(os.environ.get("NFL_OUT", "/mnt/user-data/outputs"))
MIN_GAIN = 0.005        # a swap must add half a point of P(win) to beat the best-by-mean lineup
BOOST = 1000.0          # forces a bench player into a candidate lineup


@dataclass
class LineupResult:
    markdown: str
    record: dict
    report_path: Path | None = None
    record_path: Path | None = None


def _rows(pids, info, projs):
    return [{"sleeper_id": p, "pos": (info.get(p) or {}).get("pos"),
             "weekly": projs[p].mean if p in projs else 0.0} for p in pids]


def candidates(my_pids, info, projs, slots, flex_slots, locked=frozenset(), current=None) -> list[tuple[str, list]]:
    """The best-by-mean lineup, then every legal lineup that starts one bench
    player in place of one starter (the optimizer re-seats the rest).

    A player whose game has kicked off is LOCKED where he is: a locked starter
    is forced into every candidate, a locked bench player is left out of the
    pool, and no swap moves either. Without a set lineup (`current` None) the
    lock cannot be placed and is ignored."""
    locked = set(locked) if current is not None else set()
    keep = locked & set(current or [])
    rows = [dict(r, weekly=r["weekly"] + BOOST if r["sleeper_id"] in keep else r["weekly"])
            for r in _rows(my_pids, info, projs) if r["sleeper_id"] not in locked - keep]
    best = [r["sleeper_id"] for r in optimal_lineup(rows, slots, flex_slots=flex_slots)]
    out, seen = [("best by mean", best)], {frozenset(best)}
    bench = [p for p in my_pids if p not in best and p not in locked and projs.get(p) and projs[p].mean > 0]
    for s in [x for x in best if x not in locked]:
        for b in bench:
            rr = [dict(r, weekly=(r["weekly"] + BOOST if r["sleeper_id"] == b else r["weekly"]))
                  for r in rows if r["sleeper_id"] != s]
            ids = [r["sleeper_id"] for r in optimal_lineup(rr, slots, flex_slots=flex_slots)]
            key = frozenset(ids)
            if b in ids and s not in ids and len(ids) == len(best) and key not in seen:
                seen.add(key)
                # label by the WHOLE change: forcing one player in can re-seat a
                # second (a WR into flex moves the bench QB into the QB slot)
                ins = sorted(p for p in ids if p not in best)
                outs = sorted(p for p in best if p not in ids)
                out.append((f"in:{','.join(ins)}|out:{','.join(outs)}", ids))
    return out


def change(label: str) -> tuple[list, list]:
    """(players in, players out) from a candidate label."""
    if not label.startswith("in:"):
        return [], []
    i, o = label[3:].split("|out:")
    return [x for x in i.split(",") if x], [x for x in o.split(",") if x]


def decide(cands, theirs, projs):
    """(chosen label, chosen ids, p_win by label). A swap beats the
    best-by-mean lineup only by MIN_GAIN of P(win): below that the difference
    is inside the simulation's noise."""
    pw = {label: WP.p_win(ids, theirs, projs) for label, ids in cands}
    base_label, base_ids = cands[0]
    best_label = max(pw, key=pw.get)
    if pw[best_label] - pw[base_label] < MIN_GAIN:
        return base_label, base_ids, pw
    return best_label, dict(cands)[best_label], pw


SKILL = ("QB", "RB", "WR", "TE")
# THIS WEEK'S designations only. A teammate on IR, PUP or out for the season
# has been missing for weeks: his absence is already in the usage data and the
# projections, and listing him only buries the news.
GAME_WEEK = ("Questionable", "Doubtful", "Out")
TEAMMATE_OUT = ("Out", "Doubtful", "IR", "PUP")
# ...except a FRESH placement: an IR/PUP teammate whose Sleeper news is this
# recent was most likely placed this week, and his absence is not in the data yet.
FRESH_IR_DAYS = 7


STATUS_LEAD_MIN = 90          # a designation is settled with the inactive list, ~90 minutes before kickoff


def _kick(env_row):
    k = (env_row or {}).get("kickoff_utc")
    return dt.datetime.fromisoformat(k.replace("Z", "+00:00")) if k else None


def _pt(t: dt.datetime) -> str:
    try:
        from zoneinfo import ZoneInfo
        t = t.astimezone(ZoneInfo("America/Los_Angeles"))
    except Exception:  # noqa: BLE001 -- no tz database: UTC, and say so
        return t.strftime("%a %H:%M UTC")
    return t.strftime("%a %I:%M %p PT").replace(" 0", " ")


def lock_order(watch: list[dict], my_pids, info, env: dict, now: dt.datetime) -> None:
    """For each injury-watch row, when the designation is settled (the
    inactive list, STATUS_LEAD_MIN before that team's kickoff) and which of
    my players AT HIS POSITION -- the ones I would swap him with -- lock
    before then: the rule-8 question "do I have to choose before the news?".
    Filled in place; nothing when kickoffs are unknown."""
    for w in watch:
        k = _kick(env.get(w["team"]))
        if k is None:
            continue
        known = k - dt.timedelta(minutes=STATUS_LEAD_MIN)
        w["status_known_pt"] = _pt(known)
        earlier = []
        my_pos = (info.get(w["pid"]) or {}).get("pos")
        for p in my_pids:
            if p == w["pid"] or (info.get(p) or {}).get("pos") != my_pos:
                continue
            kp = _kick(env.get((info.get(p) or {}).get("team")))
            if kp is not None and now < kp < known:
                earlier.append((kp, (info.get(p) or {}).get("name") or p))
        w["locks_before"] = [f"{n} ({_pt(t)})" for t, n in sorted(earlier)]


def injury_watch(my_pids, info, players, league: str) -> list[dict]:
    """For each of my skill players: his own designation, and every designated
    skill-position teammate who matters -- the starting QB, a depth-chart 1-2
    RB/WR/TE, or a top-200 Sleeper search rank -- carrying a THIS-WEEK
    designation (Questionable, Doubtful, Out): the absences that move his
    volume. Long-term absences (IR, PUP) are already in the data. From Sleeper's player
    data at run time. A teammate Out or Doubtful comes with the scenario
    command that prices his absence."""
    import time as _time
    fresh_after_ms = (_time.time() - FRESH_IR_DAYS * 86400) * 1000
    by_team: dict[str, list] = {}
    for sid, p in (players or {}).items():
        status = p.get("injury_status")
        fresh_ir = status in ("IR", "PUP") and (p.get("news_updated") or 0) >= fresh_after_ms
        if p.get("team") and p.get("position") in SKILL and (status in GAME_WEEK or fresh_ir):
            depth = p.get("depth_chart_order") or 99
            relevant = depth <= (1 if p.get("position") == "QB" else 2) or (p.get("search_rank") or 9999) <= 200
            if relevant:
                by_team.setdefault(p["team"], []).append((str(sid), p))
    rows = []
    for pid in my_pids:
        me = info.get(pid) or {}
        if me.get("pos") not in SKILL:
            continue
        raw = (players or {}).get(pid) or {}
        mates = sorted(((sid, p) for sid, p in by_team.get(me.get("team"), []) if sid != pid),
                       key=lambda sp: (sp[1].get("position") or "", sp[1].get("depth_chart_order") or 99))
        own = raw.get("injury_status") or ""
        if not own and not mates:
            continue
        rows.append({"pid": pid, "name": me.get("name"), "team": me.get("team"), "own": own,
                     "own_part": raw.get("injury_body_part") or "", "practice": raw.get("practice_participation") or "",
                     "teammates": [{"sid": sid, "name": p.get("full_name"), "pos": p.get("position"),
                                    "status": p.get("injury_status"), "part": p.get("injury_body_part") or "",
                                    "scenario": (f'nfl.py fantasy scenario --league {league} --player "{me.get("name")}" '
                                                 f'--out "{p.get("full_name")}"'
                                                 if p.get("injury_status") in TEAMMATE_OUT else "")}
                                   for sid, p in mates]})
    return rows


def fp_practice(watch: list[dict], season: int, week: int, manifest) -> tuple[dict[str, dict], str]:
    """FantasyPros' injury report -- practice participation and the
    probability of playing -- for exactly the players the injury watch names
    (a designated player of mine, his designated teammates). Joined through the
    DynastyProcess id map (sleeper -> fantasypros), not the keyless ranking
    feed, which the chat container reaches only some sessions. Needs
    FANTASYPROS_API_KEY (the chat skill's credential file, GitHub secrets, a
    local .env); without it, ({}, why). Never raises: a missing practice report
    is a gap in the watch, not a failed lineup."""
    sids = {w["pid"] for w in watch if w.get("own")} | {t["sid"] for w in watch for t in w["teammates"]}
    if not sids:
        return {}, "no designated players to look up"
    try:
        from core import fetch as F
        from core import ids as IDS
        from manager import fantasypros as FP
        if not FP._api_key():
            return {}, "FantasyPros practice reports need FANTASYPROS_API_KEY, which this environment does not have"
        idm = IDS.load_id_map(F.DEFAULT_CACHE, manifest=manifest)
        fp = {s: f for s, f in zip(idm["sleeper_id"].to_list(), idm["fantasypros_id"].to_list())
              if s in sids and f}
        data, note = FP.injuries({s: {"fp_id": f} for s, f in fp.items()}, season, week)
    except Exception as e:  # noqa: BLE001
        data, note = {}, f"FantasyPros practice reports failed ({type(e).__name__})"
    bad = (note or "").startswith(("DATA MISSING", "⚠")) or "failed" in (note or "")
    manifest.record("fantasypros injuries (practice, probability of playing)",
                    source="api.fantasypros.com/public/v2/json/nfl/injuries",
                    status="failed" if bad else "fresh", detail=(note or "")[:200],
                    fetched_at=None if bad else dt.datetime.now(dt.timezone.utc))
    return data, note or ""


def _fp_text(r: dict | None) -> str:
    """'practice DNP / Limited / Full; plays 65% (FantasyPros)', or ''."""
    if not r:
        return ""
    bits = []
    if r.get("practice"):
        bits.append("practice " + " / ".join(str(p) for p in r["practice"]))
    if r.get("play_prob") is not None:
        bits.append(f"plays {r['play_prob']:.0%}")
    return ("; ".join(bits) + " (FantasyPros)") if bits else ""


def _fmt(v, d=1):
    return "—" if v is None else f"{v:.{d}f}"


def _name(pid, info):
    i = info.get(pid) or {}
    return f"{i.get('name') or pid} ({i.get('team') or 'FA'})"


def _ordinal(n: int) -> str:
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def record_line(st: dict) -> str:
    """The standing, stated so it cannot be misread: '1-1, 8th of 10 teams'.
    Every lineup report heads with it, so chat never has to ask for it."""
    if st.get("unavailable") or st.get("rank") is None:
        return "**Record:** not available yet (no games played, or the platform's standings did not load)."
    return f"**Record:** {st['record']}, {_ordinal(int(st['rank']))} of {st['teams']} teams."


def run(league: str, week: int | None = None, *, record: bool = False, out_dir: Path | None = None,
        write: bool = True) -> LineupResult:
    m = Manifest(f"fantasy lineup {league}")
    view = LG.load(league, week, m)
    cfg = view.ctx["cfg"]
    pids = list(dict.fromkeys(view.my_players + view.opp_players))
    projs, env, notes = W.project_players(pids, view.info, view.season, view.week, view.scoring,
                                          league, m, (cfg.get("fantasy") or {}).get("market_weight"))
    gate = G.evaluate(m, view.scoring_yaml, view.scoring_platform, view.my_players, projs)
    ev = EV.for_sleeper(view.my_players, view.info, view.season, manifest=m)

    now = dt.datetime.now(dt.timezone.utc)
    locked_ids = {p for p in view.my_players if E.started(env.get((view.info.get(p) or {}).get("team")), now)}
    current_set = view.my_starters or None
    cands = candidates(view.my_players, view.info, projs, view.slots, view.flex_slots,
                       locked=locked_ids, current=current_set)
    n_start = len(cands[0][1])
    if view.opp_rid is None:
        theirs, their_how = [], "no opponent this week"
    elif len(view.opp_starters) >= n_start:
        theirs, their_how = view.opp_starters, "the lineup they have set"
    else:
        theirs = [r["sleeper_id"] for r in optimal_lineup(_rows(view.opp_players, view.info, projs),
                                                          view.slots, flex_slots=view.flex_slots)]
        their_how = "their best-by-mean lineup (they have not set a full one)"
    label, chosen, pw = decide(cands, theirs, projs) if theirs else (cands[0][0], cands[0][1], {})
    current = view.my_starters if len(view.my_starters) >= n_start else None
    pw_current = WP.p_win(current, theirs, projs) if (current and theirs) else None
    locked = sorted({(view.info.get(p) or {}).get("team") for p in locked_ids} - {None})

    def total(ids):
        return sum(projs[p].mean for p in ids if p in projs)

    # ------------------------------------------------------------ report
    L = [f"# Start/sit -- {league}, {view.season} week {view.week}", "", f"**{gate.line()}**", ""]
    L += [record_line(view.standing), ""]
    if theirs:
        fav = pw.get(label, 0.5) >= 0.5
        L += [f"**{view.my_name} vs {view.opp_name}.** Recommended lineup projects {total(chosen):.1f} "
              f"vs {total(theirs):.1f} ({their_how}); P(win) **{pw.get(label, 0):.0%}**"
              + (f" (the lineup you have set: {pw_current:.0%})" if pw_current is not None else "") + ".",
              "", f"*{'Likely to win: among close calls the better FLOOR wins.' if fav else 'Likely to lose: among close calls the better CEILING wins.'} "
              "Found by maximising P(win) over the best-by-mean lineup and every one-player swap.*", ""]
    else:
        L += ["No opponent this week: the lineup below maximises projected points.", ""]
    if locked:
        L += [f"Locked (game under way or over): {', '.join(_name(p, view.info) for p in sorted(locked_ids))}. "
              "They stay where they are in every lineup below; a finished game counts its actual score"
              + ("" if current_set else " -- except that no lineup is set, so the lock could not be placed") + ".", ""]
    empty = [p for p in chosen if p in projs and projs[p].mean <= 0]
    if empty:
        L += ["⚠ **A starting slot scores nothing:** " + "; ".join(
            f"{_name(p, view.info)} ({(view.info.get(p) or {}).get('pos')}, "
            f"{projs[p].detail.get('zero_reason') or 'projected 0'})" for p in empty)
              + ". No eligible bench player can fill it -- this is a waiver question, not a lineup one.", ""]

    L += ["## Recommended lineup", "",
          "| Pos | Player | Opp | Implied pts | Spread | Status | Mean | Floor (p10) | Ceiling (p90) | Sleeper | Market (weight) |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for pid in sorted(chosen, key=lambda p: ["QB", "RB", "WR", "TE", "K", "DEF"].index(
            (view.info.get(p) or {}).get("pos") or "DEF") if (view.info.get(p) or {}).get("pos") in
            ("QB", "RB", "WR", "TE", "K", "DEF") else 9):
        L.append(_row(pid, view.info, projs))
    if current:
        ins = [p for p in chosen if p not in current]
        outs = [p for p in current if p not in chosen]
        L += ["", "## Changes from the lineup you have set", ""]
        L += ([f"- Start **{_name(i, view.info)}**" for i in ins] + [f"- Bench {_name(o, view.info)}" for o in outs]
              if ins or outs else ["- none: your lineup is already the recommendation"])

    calls = [(lab, ids) for lab, ids in cands[1:] if lab in pw]
    close = sorted(calls, key=lambda c: -pw[c[0]])[:5]
    if close and theirs:
        L += ["", "## The close calls", "",
              "*Each row is one legal alternative to the best-by-mean lineup; P(win) is compared with "
              f"{pw[cands[0][0]]:.1%} for that lineup.*", "",
              "| Start | Bench | Mean change | P(win) | Floor in / out | Ceiling in / out |", "|---|---|---|---|---|---|"]

        def fl(ids, attr):
            return " + ".join(_fmt(getattr(projs.get(x), attr, None)) for x in ids) or "—"
        for lab, ids in close:
            ins, outs = change(lab)
            L.append(f"| {', '.join(_name(x, view.info) for x in ins)} | {', '.join(_name(x, view.info) for x in outs)} | "
                     f"{total(ids) - total(cands[0][1]):+.1f} | {pw[lab]:.1%} | {fl(ins, 'floor')} / {fl(outs, 'floor')} | "
                     f"{fl(ins, 'ceiling')} / {fl(outs, 'ceiling')} |")

    watch = injury_watch(view.my_players, view.info, view.ctx.get("players"), league)
    L += ["", "## Injury watch (game-day status, framework question 5)", "",
          "*Sleeper designations at run time: yours, and this week's designations (Questionable, Doubtful, Out) on the "
          "teammates who move your players' volume (the starting QB, depth chart 1-2 at RB/WR/TE, or top-200); "
          "long-term IR/PUP absences are already in the data. Practice participation and the probability of "
          "playing come from FantasyPros' injury report where this environment has the key; news is not in this "
          "report, and a close call involving any row here is checked against it before it is answered.*", ""]
    fp, fp_note = fp_practice(watch, view.season, view.week, m) if watch else ({}, "")
    if watch and not fp:
        L += [f"*No FantasyPros practice reports this run: {fp_note}.*", ""]
    if watch:
        lock_order(watch, view.my_players, view.info, env, now)
        L += ["| Your player | His status | Designated teammates | Settled by | Your players at his position locking before then "
              "| Price the absence |", "|---|---|---|---|---|---|"]
        for w in watch:
            fp_own = _fp_text(fp.get(w["pid"]))
            own = (f"**{w['own']}**" + (f" ({w['own_part']})" if w["own_part"] else "")
                   + (f"; {fp_own}" if fp_own else (f", practice: {w['practice']}" if w["practice"] else ""))
                   ) if w["own"] else "none"
            mates = "; ".join(f"{t['name']} ({t['pos']}) {t['status']}" + (f" ({t['part']})" if t["part"] else "")
                              + (f" -- {_fp_text(fp.get(t['sid']))}" if _fp_text(fp.get(t["sid"])) else "")
                              for t in w["teammates"]) or "none"
            runs = "<br>".join(f"`{t['scenario']}`" for t in w["teammates"] if t["scenario"]) or "--"
            settled = w.get("status_known_pt") or "kickoff unknown"
            before = ", ".join(w.get("locks_before") or []) or "none"
            L.append(f"| {w['name']} ({w['team']}) | {own} | {mates} | {settled} | {before} | {runs} |")
    else:
        L += ["No designations on your players or their key teammates."]

    L += ["", "## Opportunity and role (framework questions 1 and 2)", "",
          "*This season, by week. A role CHANGED when the last two weeks differ from the earlier ones by more "
          "than two noise standard deviations of that metric (noise_bands_v0); fewer than four weeks is "
          "INSUFFICIENT_SAMPLE. Usage, not box score. A week marked partial (under 60% of the player's usual "
          "snaps) is an exit or a benching, not a role: its snap share is not role evidence.*", "",
          "| Player | Weeks | Snap % (season / last) | Target share | Carry share | WOPR | Inside-10 tgt+car | Role |",
          "|---|---|---|---|---|---|---|---|"]
    for pid in [p for p in chosen + [b for b in view.my_players if b not in chosen]
                if (view.info.get(p) or {}).get("pos") in ("QB", "RB", "WR", "TE")]:
        L.append(_ev_row(pid, view.info, ev.get(pid) or {}))

    bench = [p for p in view.my_players if p not in chosen]
    if bench:
        L += ["", "## Bench", "", "| Pos | Player | Opp | Implied pts | Spread | Status | Mean | Floor (p10) | "
              "Ceiling (p90) | Sleeper | Market (weight) |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        L += [_row(p, view.info, projs) for p in sorted(bench, key=lambda p: -(projs[p].mean if p in projs else 0))]

    by_pos = {}
    for p in chosen:
        for c in (projs[p].detail.get("range_caveats") or []) if p in projs else []:
            by_pos.setdefault(c.split(" ", 1)[0].rstrip(":"), set()).add(c)
    cav = [f"{pos} ({sum(1 for c in cs if ' p' in c.split(':')[0])} of 5 percentiles off by 3+ points"
           + ("; no better than a scaled normal" if any("no better" in c for c in cs) else "") + ")"
           for pos, cs in sorted(by_pos.items())]
    no_range = sorted({(view.info.get(p) or {}).get("pos") for p in chosen
                       if p in projs and projs[p].mean > 0 and not projs[p].quantiles} - {None})
    L += ["", "## How to read this", "",
          "- **Mean** blends Sleeper's weekly projection with the market-implied points where the player has a "
          "full prop board (weight shown; it decays through the season). A partial market board never enters the blend.",
          "- **Floor / ceiling** are the 10th / 90th percentile weeks from dispersion_v0 (fitted 2024, tested on 2025: "
          "the p10-p90 range held ~80% of outcomes).",
          "- **P(win)** assumes players are independent -- a same-team or same-game stack's variance is understated.",
          "- **Not covered yet:** an opponent-adjusted matchup read (framework question 4, weighted low by design)."]
    if cav:
        L += [f"- **Range caveats** (reports/dispersion_v0.{league}.md): {'; '.join(cav)}."]
    if no_range:
        L += [f"- **No measured range for {', '.join(no_range)}:** their weeks are held at the mean in P(win), "
              "which understates the uncertainty a little."]
    L += ["", f"*{m.summary_line()}*"] + ([f"*Notes: {'; '.join(notes + view.notes)}*"] if notes or view.notes else [])
    md = "\n".join(L) + "\n"

    rec_evidence = {p: {k: v for k, v in (e or {}).items() if k != "series"} for p, e in ev.items()}
    rec = {"command": "fantasy lineup", "league": league, "season": view.season, "week": view.week,
           "evidence": rec_evidence, "injury_watch": watch, "fantasypros_injuries": fp,
           "generated_at_utc": now.isoformat(), "gate": gate.to_dict(), "manifest": m.to_dict(),
           "standing": view.standing,
           "me": view.my_name, "opponent": view.opp_name, "opponent_lineup": theirs, "opponent_lineup_from": their_how,
           "recommended": {"label": label, "starters": chosen, "p_win": pw.get(label)},
           "current": {"starters": current, "p_win": pw_current},
           "candidates": [{"label": lab, "starters": ids, "p_win": pw.get(lab)} for lab, ids in cands],
           "projections": {p: {"mean": pr.mean, "quantiles": {str(k): v for k, v in pr.quantiles.items()},
                               "detail": {k: v for k, v in pr.detail.items() if k != "env"},
                               "env": pr.detail.get("env"), "range_from": pr.range_from}
                           for p, pr in projs.items()},
           "notes": notes + view.notes}
    res = LineupResult(md, rec)
    if write:
        d = Path(out_dir or OUT)
        d.mkdir(parents=True, exist_ok=True)
        slug = f"{league}_{view.season}_wk{view.week:02d}"
        res.report_path = d / f"lineup_{slug}.md"
        res.record_path = d / f"lineup_{slug}.json"
        res.report_path.write_text(md, encoding="utf-8")
        res.record_path.write_text(json.dumps(rec, indent=1, default=str), encoding="utf-8")
    if record:
        _record(view, chosen, projs, pw.get(label), gate)
    return res


def _pct(v):
    return "—" if v is None else f"{100 * v:.0f}%"


def _ev_row(pid, info, e) -> str:
    if not e or not e.get("weeks"):
        return f"| {_name(pid, info)} | 0 | {e.get('note') or 'no usage this season'} | | | | | |"
    mean, ser = e.get("mean") or {}, e.get("series") or {}
    last_snap = (ser.get("snap_pct") or [None])[-1]
    changed = [f"{m.replace('_', ' ')} {f['earlier']:.0%}->{f['recent']:.0%}"
               for m, f in (e.get("role_change") or {}).items() if f.get("changed")]
    role = e.get("trajectory", "") + (f" ({'; '.join(changed)})" if changed else "")
    t = e.get("totals") or {}
    wopr = "—" if mean.get("wopr") is None else f"{mean['wopr']:.2f}"
    partial = e.get("partial_weeks") or []
    mark = f" (partial: wk {', '.join(str(w) for w in partial)})" if partial else ""
    return (f"| {_name(pid, info)} | {e['weeks']} | {_pct(mean.get('snap_pct'))} / {_pct(last_snap)}{mark} | "
            f"{_pct(mean.get('tgt_share'))} | {_pct(mean.get('carry_share'))} | {wopr} | "
            f"{t.get('i10_tgt', 0)}+{t.get('i10_car', 0)} | {role} |")


def _row(pid, info, projs) -> str:
    i, p = info.get(pid) or {}, projs.get(pid)
    if p is None:
        return f"| {i.get('pos')} | {_name(pid, info)} | | | | {i.get('status') or ''} | — | | | | |"
    e = p.detail.get("env") or {}
    why = p.detail.get("zero_reason")
    status = (i.get("status") or "") + (f" -- {why}" if why else "")
    mk = p.detail.get("market")
    mk_txt = "—" if mk is None else (f"{mk:.1f}" + (" partial" if p.detail.get("market_partial") else "")
                                     + f" ({p.detail.get('market_weight', 0):.0%})")
    sp = e.get("spread")
    return (f"| {i.get('pos')} | {_name(pid, info)} | {e.get('opp') or '—'} | {_fmt(e.get('implied'))} | "
            f"{'—' if sp is None else f'{sp:+.1f}'} | {status} | {p.mean:.1f} | {_fmt(p.floor)} | {_fmt(p.ceiling)} | "
            f"{_fmt(p.detail.get('sleeper'))} | {mk_txt} |")


def _record(view, chosen, projs, p_win, gate) -> int:
    from manager import ledger
    from manager.context import state_dir
    from manager.store import Store
    row = {"subject": f"lineup:{view.week}:nfl", "starters": chosen, "pool": view.my_players,
           "pos": {p: (view.info.get(p) or {}).get("pos") for p in view.my_players},
           "projected": {p: projs[p].mean for p in chosen if p in projs},
           "floor": {p: projs[p].floor for p in chosen if p in projs},
           "ceiling": {p: projs[p].ceiling for p in chosen if p in projs},
           "p_win": p_win, "gate_passed": gate.passed, "source": "nfl fantasy lineup"}
    return ledger.emit(Store(state_dir()), view.ctx, "lineup", [row])
