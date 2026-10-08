"""The renders behind publish.py (DECISIONS #217, #218): the QA/QC version in the structure of the
user's report guide (docs/plans/2026-10-08-report-format-design.md), and the agent version.

Every table here is built from the run file; every sentence the analyst wrote has passed
publish.check before it reaches a render. The generated pieces are computed here, never written
by the analyst, so they cannot drift from the run:
- the verdict words;
- the closing paragraph's computed half;
- the receptions-vs-yards comparison;
- the production paths;
- the scenario table's status.
"""
from __future__ import annotations

import json
import re

import publish as PB

ENGINE = PB.ENGINE
SCENARIO_ROWS = (("Favorite wins comfortably ({n}+ points)", "More potential late rushing; fewer necessary late passes"),
                 ("Final margin stays within one score", "More sustained passing and less pressure to abandon rushing"),
                 ("Underdog wins comfortably ({n}+ points)", "Reverses the expected workload pressure"))


# ---------------------------------------------------------------- formatting
def pct(v):
    return "-" if v is None else f"{100 * float(v):.0f}%"


def odds(v):
    if v is None:
        return "-"
    v = float(v)
    return f"+{v:.0f}" if v > 0 else f"{v:.0f}"


def f1(v):
    return "-" if v is None else f"{float(v):.1f}"


def _esc(s):
    return str(s).replace("|", "/").replace("\n", " ")


SECRET_PATTERNS = [re.compile(r"(?i)\b(api[_-]?key|apikey|access[_-]?token|token|secret|password|key)=[^&\s|)]+"),
                   re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{32}(?![0-9a-fA-F])")]


def scrub(text: str) -> str:
    """Key-shaped strings out of anything written: a query-string credential (apiKey=...) and a
    bare 32-hex key (the Odds API's shape). The 64-hex release hash is left alone."""
    text = SECRET_PATTERNS[0].sub(lambda m: m.group(1) + "=<redacted>", text)
    return SECRET_PATTERNS[1].sub("<redacted>", text)


def cutoff(run) -> str:
    return re.sub(r"^-?\s*\*\*Data cutoff:\*\*\s*", "", run.get("data_cutoff") or "") or "-"


def checks_table(checks) -> list[str]:
    L = ["| Check | The read says | The run says | Result |", "|---|---|---|---|"]
    for c in checks:
        res = "pass" if c["ok"] else f"**FAIL**: {c['detail']}"
        L.append(f"| {c['check']} | {_esc(c['stated'])} | {_esc(c['run'])} | {res} |")
    return L


def _resource(name):
    p = ENGINE / "resources" / name
    return p.read_text(encoding="utf-8") if p.exists() else None


def margin_model() -> dict:
    """The shipped margin model's record (scripts/fit_margin_model.py), or {} when absent."""
    txt = _resource("margin_buckets_v0.json")
    return json.loads(txt) if txt else {}


# ---------------------------------------------------------------- the team brief
def teams(run):
    return run["home"], run["away"]


def header_lines(run) -> list[str]:
    """The run's matchup header without its bold title line (the page's own title names the game)."""
    h = list(run.get("header") or [])
    while h and (not h[0].strip() or h[0].strip().startswith("**")):
        h.pop(0)
    return h


def market_table(run, compact=False) -> list[str]:
    home, away = teams(run)
    me = run.get("market_env") or {}
    hs = me.get("home_spread")
    tm = run.get("teams") or {}
    L = [f"| Market measure | {home} | {away} |", "|---|---:|---:|"]
    if hs is not None:
        L.append(f"| Spread | {hs:+g} | {-hs:+g} |")
    L.append(f"| Implied points | {f1((tm.get(home) or {}).get('implied_points'))} | {f1((tm.get(away) or {}).get('implied_points'))} |")
    wp = me.get("home_win_prob")
    L.append(f"| Win probability* | {pct(wp)} | {pct(None if wp is None else 1 - wp)} |")
    if me.get("total_line") is not None:
        L.append(f"| Total | {me['total_line']:g} | |")
    ch_h, ch_a = [], []
    if me.get("open_home_spread") is not None and hs is not None:
        ch_h.append(f"spread {me['open_home_spread']:+g} to {hs:+g}")
        ch_a.append(f"spread {-me['open_home_spread']:+g} to {-hs:+g}")
    if me.get("home_win_prob_open") is not None and wp is not None:
        ch_h.append(f"win {pct(me['home_win_prob_open'])} to {pct(wp)}")
        ch_a.append(f"win {pct(1 - me['home_win_prob_open'])} to {pct(1 - wp)}")
    L.append(f"| Change since opening | {'; '.join(ch_h) or 'not available'} | {'; '.join(ch_a) or 'not available'} |")
    if compact:
        tail = (f" The total opened at {me['open_total']:g}." if me.get("open_total") is not None else "")
        return L + ["", "*Win probability: DraftKings' moneylines with the margin removed. Implied points are a scoring "
                        f"guide, not a score prediction.{tail}*"]
    notes = ["*Win probability comes from DraftKings' moneylines (via ESPN"
             + (f": {home} {me.get('home_ml')}, {away} {me.get('away_ml')}" if me.get("home_ml") else "")
             + ") after removing the margin. Implied points are a scoring guide, not a final-score prediction."]
    if me.get("open_total") is not None and me.get("total_line") is not None:
        notes.append(f"The total opened at {me['open_total']:g} and is {me['total_line']:g} now. Opening = DraftKings' "
                     f"opening line; now = {str(me.get('as_of'))[:16].replace('T', ' ')} UTC.")
    return L + [""] + [f"*{n.lstrip('*')}*" for n in notes]


def scenario_table(run, detail=False) -> list[str]:
    sm = run.get("scenarios_market") or {}
    if sm.get("status") == "ok":
        return market_scenario_table(run, sm, detail)
    mm = margin_model()
    n = mm.get("comfortable_margin", 9)
    shipped = mm.get("shipped")
    L = ["| Result scenario | Estimated likelihood | Opportunity implication |", "|---|---:|---|"]
    for label, impl in SCENARIO_ROWS:
        L.append(f"| {label.format(n=n)} | {'see note' if shipped else 'not estimated'} | {impl} |")
    if sm.get("status"):
        L += ["", f"*No market prices for these scenarios this run ({sm['status']}).*"]
    if shipped:
        note = "Likelihoods from the margin model (provisional)."
    else:
        note = ("Not estimated: our margin model did not pass its pre-registered accuracy test, so these are "
                "labelled analytical scenarios, not forecasts.")
        if detail and mm:
            ll = mm.get("log_loss") or {}
            note += (f" (margin_buckets_v0, fit {mm.get('fit_seasons')}, test {mm.get('test_seasons')}: the empirical "
                     f"model's log loss {ll.get('A_empirical', 0):.3f} beat the baseline's {ll.get('baseline', 0):.3f} but "
                     "missed calibration -- 2022-25 games finished closer than 2018-21; reports/margin_buckets_v0.md.)")
    return L + ["", f"*{note}*"]


def market_scenario_table(run, sm, detail=False) -> list[str]:
    """The result scenarios as the market prices them (research.alt_spread_scenarios): the book's
    alternate spreads at the comfortable-margin cut, margin removed."""
    home, away = teams(run)
    hs = (run.get("market_env") or {}).get("home_spread")
    fav, dog = (home, away) if hs is not None and hs <= 0 else (away, home)
    n, pt = sm["cut"], sm["point"]
    rows = ((f"{fav} (favorite) wins by {n}+ points", sm["favourite_by_cut"], SCENARIO_ROWS[0][1]),
            ("Final margin stays within one score", sm["within_one_score"], SCENARIO_ROWS[1][1]),
            (f"{dog} (underdog) wins by {n}+ points", sm["underdog_by_cut"], SCENARIO_ROWS[2][1]))
    L = ["| Result scenario | Estimated likelihood | Opportunity implication |", "|---|---:|---|"]
    L += [f"| {a} | {pct(b)} | {c} |" for a, b, c in rows]
    pr = sm.get("prices") or {}
    if not detail:
        return L + ["", f"*From DraftKings' {pt:g}-point spreads, margin removed: the market's own estimate. Within one "
                        f"score includes a close win by either team.*"]
    note = (f"From DraftKings' spreads at {pt:g} points (via The Odds API), margin removed: the market's own estimate, "
            f"not a model. {fav} -{pt:g} at {odds(pr.get('favourite', {}).get('minus'))} against {dog} +{pt:g} at "
            f"{odds(pr.get('favourite', {}).get('plus_other'))}; {dog} -{pt:g} at {odds(pr.get('underdog', {}).get('minus'))} "
            f"against {fav} +{pt:g} at {odds(pr.get('underdog', {}).get('plus_other'))}. Within one score includes a "
            f"one-score win by either team.")
    if detail:
        note += f" As of {str(sm.get('as_of'))[:16].replace('T', ' ')} UTC; {sm.get('credits_left')} Odds API credits left."
    return L + ["", f"*{note}*"]


def workload_table(run, compact=False) -> list[str]:
    home, away = teams(run)
    tm, tv = run.get("teams") or {}, run.get("team_volume") or {}
    L = ["| Workload | Market-derived estimate† | Engine average | Season average |", "|---|---:|---:|---:|"]
    for t in (home, away):
        e, v = tm.get(t) or {}, tv.get(t) or {}
        rate = v.get("target_rate")
        m_att = e["market_throws"] / rate if e.get("market_throws") is not None and rate else None
        L.append(f"| {t} pass attempts | {f1(m_att)} | {f1(v.get('our_att'))} | {f1(v.get('att_avg'))} |")
    for t in (home, away):
        e, v = tm.get(t) or {}, tv.get(t) or {}
        L.append(f"| {t} rushing attempts | {f1(e.get('market_runs'))} | {f1(v.get('our_runs'))} | {f1(v.get('runs_avg'))} |")
    if compact:
        return L + ["", "*†From the spread and total, not a posted market. Rushing attempts include quarterback runs and "
                        "scrambles. The engine draws partly on this estimate, so the columns are not independent.*"]
    return L + ["", "*†Derived from the spread and total (the engine's fit of plays and pass rate to them), not a "
                    "posted team-attempts market. Pass attempts exclude sacks; rushing attempts include quarterback "
                    "runs and scrambles. The engine already takes a quarter of its throws and half of its backs' "
                    "carries from this fit, so the columns are not independent forecasts.*"]


def unit_table(run, compact=False) -> list[str]:
    home, away = teams(run)
    U = run.get("units") or {}
    words = (("off_pass", "Passing offense"), ("off_run", "Rushing offense"), ("def_pass", "Passing defense"),
             ("def_run", "Rushing defense"))
    L = [f"| Unit | {home}: rank · grade · score | {away}: rank · grade · score |", "|---|---|---|"]
    for k, w in words:
        cells = []
        for t in (home, away):
            u = (U.get(t) or {}).get(k)
            cells.append(f"{u['rank']} · {u['grade']} · {u['score']:.0f}" if u else "-")
        L.append(f"| {w} | {cells[0]} | {cells[1]} |")
    n = next((u.get("of") for t in U.values() for u in t.values()), 32)
    filt = ("garbage time excluded" if compact else
            run.get("unit_filter") or "garbage-time filter not recorded in this run")
    return L + ["", f"*Rank 1 = strongest unit of {n}. Scores blend EPA and success rate; 50 is average. Weeks 1-"
                    f"{run['week'] - 1}; {filt}. Each unit is graded separately.*"]


def allowed_tables(run) -> list[str]:
    home, away = teams(run)
    pa = run.get("points_allowed") or {}
    if not pa.get(home) or not pa.get(away):
        return ["*Points allowed by position: not included in this run.*"]
    L = ["| Defense | RBs | WRs | TEs |", "|---|---:|---:|---:|"]
    for t in (home, away):
        L.append(f"| {t} | " + " | ".join(f"{pa[t][p]['ppr']:.1f} ({_ordinal(pa[t][p]['rank_most'])} most)"
                                         for p in ("RB", "WR", "TE")) + " |")
    lg = pa.get("_league") or {}
    L.append("| League average | " + " | ".join(f1(lg.get(p)) for p in ("RB", "WR", "TE")) + " |")
    games = sorted({g for g in (pa.get("_games") or {}).values() if g})
    L += ["", f"*PPR per game across the position, including touchdowns; {'/'.join(map(str, games))} games.*", "",
          "What produced it, per game:", "",
          "| Defense | Position | Catches | Receiving yards | Rushing yards | Touchdowns |", "|---|---|---:|---:|---:|---:|"]
    for t in (home, away):
        for p in ("RB", "WR", "TE"):
            d = pa[t][p]
            L.append(f"| {t} | {p} | {f1(d.get('catches'))} | {f1(d.get('rec_yds'))} | {f1(d.get('rush_yds'))} | "
                     f"{f1(d.get('tds'))} |")
    return L


def _ordinal(n):
    n = int(n)
    return f"{n}{'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def personnel_table(reads) -> list[str]:
    rows = reads.get("personnel") or []
    if not rows:
        return ["*No personnel change the analyst judged relevant.*"]
    L = ["| Player / status | What changes | Relevant opportunities |", "|---|---|---|"]
    for r in rows:
        L.append(f"| {_esc(r['player'])} ({_esc(r['status'])}) | {_esc(r['changes'])} | {_esc(r['affects'])} |")
    return L


def if_out_tables(run) -> list[str]:
    recs = run.get("if_out")
    if recs is None:
        return []
    if not recs:
        return ["*No priced player is Questionable: no 'if he's out' branch to show.*"]
    L = []
    for r in recs:
        L += [f"**If {r['player']} ({r['team']} {r['pos']}) is out** (the engine priced the board again without him):", ""]
        if not r.get("ran"):
            L += ["*That re-pricing failed this run; the branch is not quantified.*", ""]
            continue
        if not r.get("moves"):
            L += ["*No other line moves by 1 point or more.*", ""]
            continue
        L += ["| Player | Line | If he plays | If he's out | Change |", "|---|---|---:|---:|---:|"]
        for m in r["moves"]:
            L.append(f"| {m['player']} ({m['team']}) | {m['side']} {float(m['line']):g} {PB.MARKET_WORDS.get(m['market'], m['market'])} | "
                     f"{pct(m['p_plays'])} | {pct(m['p_out'])} | {100 * float(m['move']):+.0f} |")
        L.append("")
    return L


# ---------------------------------------------------------------- the player cards
def table_a(card, compact=False) -> list[str]:
    L = (["| Prop | Line (O/U) | Engine middle | Market Over | Engine Over |", "|---|---|---:|---:|---:|"] if compact else
         ["| Prop | Line · Over / Under prices | Engine's middle (vs the line) | Market Over estimate | Engine Over estimate |",
          "|---|---|---:|---:|---:|"])
    for r in PB.main_rows(card):
        med = r.get("median")
        mid = "-" if med is None else f"{float(med):.1f} ({float(med) - float(r['line']):+.1f})"
        L.append(f"| {PB.MARKET_WORDS.get(r['market'], r['market']).capitalize()} | {float(r['line']):g} · "
                 f"{odds(r.get('price_over'))} / {odds(r.get('price_under'))} | {mid} | {pct(r.get('p_over_book'))} | "
                 f"{pct(r.get('p_over_model'))} |")
    if compact:
        return L
    return L + ["", "*Sleeper prices most lines near even and moves the line instead, so the market's view is mostly "
                    "the line itself: the gap between it and the engine's middle is where the two disagree.*"]


VERDICT_SHORT = {"attainable": "Attainable", "requires a rebound": "Rebound", "requires better gains": "Better gains",
                 "requires more work than the engine expects": "More work"}


def table_b(card, compact=False) -> list[str]:
    rows = [r for r in PB.main_rows(card) if PB.cells_for(card, r["market"])
            and not (compact and r["market"] == "player_rush_reception_yds")]
    if not rows:
        return []
    head = "| Gain reference | " + " | ".join(f"{PB.MARKET_WORDS[r['market']].capitalize()} {float(r['line']):g}" for r in rows) + " |"
    L = [head, "|---|" + "---:|" * len(rows)]
    words = ((("season", "This season"), ("capped", "Trimmed gains"), ("engine", "Engine gains")) if compact else
             (("season", "This season"), ("capped", "Big gains trimmed"), ("engine", "Engine's gain assumption")))
    for key, word in words:
        vals = []
        for r in rows:
            x = (PB.cells_for(card, r["market"])["rows"] or {}).get(key)
            vals.append(f"{x['vol_txt']} at {x['rate_txt']} -> {pct(x['pct'])}" if x else "-")
        if any(v != "-" for v in vals):
            L.append(f"| {word} | " + " | ".join(vals) + " |")
    vals = []
    for r in rows:
        mr = PB.cells_for(card, r["market"]).get("market_row")
        vals.append(f"more than {mr[0]:g} {PB.cells_for(card, r['market'])['unit']} -> {pct(mr[1])}" if mr else "-")
    if any(v != "-" for v in vals):
        L.append(("| Book volume line | " if compact else "| The market's own volume line (engine's chance of more) | ")
                 + " | ".join(vals) + " |")
    vals = [(f"{float(r['market_volume']):.1f} {r.get('unit') or ''}".strip() if r.get("market_volume") is not None else "-")
            for r in rows]
    if any(v != "-" for v in vals):
        L.append(("| Market-implied workload | " if compact else
                  "| Workload consistent with the market price, assuming the engine's gains | ") + " | ".join(vals) + " |")
    vals = [((PB.verdict(card, r["market"]) or {}).get("word") or "-") for r in rows]
    if compact:
        vals = [VERDICT_SHORT.get(v, v) for v in vals]
    L.append("| Verdict | " + " | ".join(vals) + " |")
    if compact:
        return L
    return L + ["", "*Each cell: the workload the line needs at that gain rate, and the engine's chance of reaching that "
                    "workload. The market-consistent workload is a translation of the price at the engine's gains, not a "
                    "published projection: a gap can mean different workload expectations, different gains, or both.*"]


def receiving_comparison(card, compact=False) -> list[str]:
    rec = next((r for r in PB.main_rows(card) if r["market"] == "player_receptions"), None)
    yds = next((r for r in PB.main_rows(card) if r["market"] == "player_reception_yds"), None)
    cy = PB.cells_for(card, "player_reception_yds") if yds else None
    if not rec or not yds or not cy:
        return []
    ref = "capped" if "capped" in cy["rows"] else "season"
    x = cy["rows"].get(ref)
    if not x:
        return []
    word = "the trimmed" if ref == "capped" else "this season's"
    if compact:
        return [f"| Check | Receptions {float(rec['line']):g} | Receiving yards {float(yds['line']):g} |", "|---|---:|---:|",
                f"| Catches needed | {int(rec['line']) + 1} | {x['vol']} at {x['rate_txt']} yards |",
                f"| Engine catches | {cy['proj']:.1f} | {cy['proj']:.1f} |",
                f"| Chance of those catches | {pct(rec.get('p_over_model'))} | {pct(x['pct'])}‡ |",
                f"| Engine Over | {pct(rec.get('p_over_model'))} | {pct(yds.get('p_over_model'))} |",
                f"| Market Over | {pct(rec.get('p_over_book'))} | {pct(yds.get('p_over_book'))} |"]
    L = [f"| Check | Receptions Over {float(rec['line']):g} | Receiving Over {float(yds['line']):g} |", "|---|---:|---:|",
         f"| Required catches | {int(rec['line']) + 1} | {x['vol']} at {x['rate_txt']} yards each ({word} rate) |",
         f"| Engine expected catches | {cy['proj']:.1f} | {cy['proj']:.1f} |",
         f"| Engine chance he makes the required catches | {pct(rec.get('p_over_model'))} | {pct(x['pct'])}‡ |",
         f"| Engine chance of the Over | {pct(rec.get('p_over_model'))} | {pct(yds.get('p_over_model'))} |",
         f"| Market Over estimate | {pct(rec.get('p_over_book'))} | {pct(yds.get('p_over_book'))} |"]
    return L + ["", f"*‡Only the catches: the yards still need {x['rate_txt']} a catch on average. The engine's chance of "
                    "the Over itself is the row below it.*"]


def production_paths(card) -> list[str]:
    c = PB.cells_for(card, "player_rush_reception_yds")
    if not c:
        return []
    L = ["| Production path | Rushing yards | Receiving yards | Combined yards |", "|---|---:|---:|---:|"]
    for key, word in (("capped", "trimmed gains"), ("season", "this season's gains"), ("engine", "the engine's gains")):
        x = c["rows"].get(key)
        m = re.match(r"(\d+) carries \+ (\d+) catches", (x or {}).get("vol_txt") or "")
        if not x or not m or not isinstance(x.get("rate"), list):
            continue
        n_c, n_k = int(m.group(1)), int(m.group(2))
        ry, cy = n_c * float(x["rate"][0]), n_k * float(x["rate"][1])
        L.append(f"| {n_c} carries at {x['rate'][0]:.1f} + {n_k} catches at {x['rate'][1]:.1f} ({word}) | "
                 f"{ry:.1f} | {cy:.1f} | {ry + cy:.1f} |")
    return L + ["", "*Arithmetic illustrations of the workload each gain rate needs, split at the engine's mix of "
                    "carries and catches; not probabilities.*"] if len(L) > 2 else []


def closing_compact(card, p, lg) -> str:
    """The customer version's card close, in the user's order: the line requires -> the engine
    expects -> the matchup supports or challenges. The branches that follow say what to choose. The
    table's numbers are not repeated beyond the requirement itself."""
    mk = PB.market_key(lg["market"])
    vol_line = (next((x for x in card.get("volume") or [] if x.get("market") == mk), {}) or {}).get("line")
    v = PB.verdict(card, mk) if PB._close(vol_line, lg["line"], 1e-9) else None
    word = PB.MARKET_WORDS[mk].capitalize()
    if v:
        gains = "his trimmed gains" if v["ref"] == "capped" else "this season's gains"
        s = [f"{word} {float(lg['line']):g} needs **{v['vol_txt']} at {gains}**, so it {_verdict_phrase(v['word'])}"
             + (" (the Over's requirement; this leg is the Under)." if lg["side"].lower() == "under" else ".")]
    else:
        s = [f"{word} {float(lg['line']):g} has no workload table in this run (the card's table is at its main line)."]
    s.append(f"The engine expects {PB.volume_text(card, mk) or '-'}, based on {p['role_evidence'].rstrip('.')}.")
    s.append(f"The matchup {p['matchup']} it: {p['matchup_reason'].rstrip('.')}.")
    return " ".join(s)


def _verdict_phrase(word):
    return {"attainable": "is attainable"}.get(word, word)


def closing_paragraph(card, p, lg) -> str:
    mk = PB.market_key(lg["market"])
    row = PB.row_for(card, mk, float(lg["line"])) or {}
    pb = row.get("p_over_book")
    med = row.get("median")
    vol_line = (next((x for x in card.get("volume") or [] if x.get("market") == mk), {}) or {}).get("line")
    on_main = PB._close(vol_line, lg["line"], 1e-9)
    v = PB.verdict(card, mk) if on_main else None
    vt = PB.volume_text(card, mk) or "-"
    under = lg["side"].lower() == "under"
    s = [market_sentence(lg["line"], pb, med) + f" The engine expects {vt}, based on {p['role_evidence'].rstrip('.')}."]
    if v:
        lead = "With big gains trimmed" if v["ref"] == "capped" else "At his rate this season"
        s.append(f"{lead}, the Over at {PB.MARKET_WORDS[mk]} {float(lg['line']):g} needs {v['vol_txt']}, which the engine "
                 f"reaches {pct(v['pct'])} of the time: **{v['word']}**" + (" (for the Over; this leg is the Under)." if under else "."))
    elif vol_line is not None:
        s.append(f"(The card's gain-rate table is built at the {float(vol_line):g} line; this leg's "
                 f"{float(lg['line']):g} has no workload table in the run.)")
    s.append(f"This matchup {p['matchup']} the Over's requirement because {p['matchup_reason'].rstrip('.')}.")
    s.append(f"If you expect {lg['if'].rstrip('.')}, {lg['player']} {PB.MARKET_WORDS[mk]} {lg['side'].lower()} "
             f"{float(lg['line']):g} fits; it stops fitting if {lg['fails'].rstrip('.')}.")
    return " ".join(s)


def market_sentence(line, pb, med) -> str:
    """Where the market stands: near an even price, its view is the line itself, read against the
    engine's middle; off even, which side the price favors."""
    line = float(line)
    gap = "" if med is None else f"; the engine's middle is {float(med):.1f} ({float(med) - line:+.1f})"
    if pb is None:
        return f"**The market's line is {line:g}**{gap}."
    if abs(float(pb) - 0.5) < 0.03:
        return f"**The market sets the line at {line:g}, priced near even** ({pct(pb)} for the Over){gap}."
    return f"**The market favors the {'Over' if float(pb) > 0.5 else 'Under'}** at {line:g} ({pct(pb)} for the Over){gap}."


def rushing_vs_combined(card, compact=False) -> list[str]:
    """Rushing alone against rushing + receiving (the user, 2026-10-08): whether the combined line is
    set fairly against its parts, whether the receiving role is showing, and the engine's chances.
    The engine draws rushing and receiving independently, so it holds no game-script trade-off."""
    rows = {r["market"]: r for r in PB.main_rows(card)}
    ru, rec, rr = rows.get("player_rush_yds"), rows.get("player_reception_yds"), rows.get("player_rush_reception_yds")
    if not ru or not rr:
        return []
    have_parts = rec is not None and all(x.get("median") is not None for x in (ru, rec, rr))
    L = ["| Check | Rushing yards | Rushing + receiving yards |", "|---|---:|---:|",
         f"| Line | {float(ru['line']):g} | {float(rr['line']):g} |",
         f"| {'Engine middle' if compact else 'Engine' + chr(39) + 's middle (vs the line)'} | {_mid(ru)} | {_mid(rr)} |",
         f"| {'Engine Over' if compact else 'Engine Over estimate'} | {pct(ru.get('p_over_model'))} | {pct(rr.get('p_over_model'))} |",
         f"| {'Market Over' if compact else 'Market Over estimate'} | {pct(ru.get('p_over_book'))} | {pct(rr.get('p_over_book'))} |"]
    if compact:
        vr, vc = PB.verdict(card, "player_rush_yds"), PB.verdict(card, "player_rush_reception_yds")
        L.append(f"| Needs at trimmed gains | {(vr or {}).get('vol_txt', '-')} | {(vc or {}).get('vol_txt', '-')} |")
        L.append(f"| Verdict | {VERDICT_SHORT.get((vr or {}).get('word'), '-')} | {VERDICT_SHORT.get((vc or {}).get('word'), '-')} |")
    notes = []
    if have_parts:
        book_gap = float(rr["line"]) - float(ru["line"]) - float(rec["line"])
        eng_gap = float(rr["median"]) - float(ru["median"]) - float(rec["median"])
        if compact:
            L += [f"| Combined line vs its parts | | {book_gap:+.1f} |", f"| Engine's gap | | {eng_gap:+.1f} |"]
        else:
            L += [f"| Combined line minus rushing + receiving lines ({float(ru['line']):g} + {float(rec['line']):g}) | | "
                  f"{book_gap:+.1f} |",
                  f"| The same gap in the engine's middles (yards come in bursts, so a sum's middle runs higher) | | "
                  f"{eng_gap:+.1f} |"]
        d = book_gap - eng_gap
        notes.append(f"The combined line is set {abs(d):.1f} yards {'above' if d > 0 else 'below'} what its parts justify"
                     if abs(d) >= 0.5 else "The combined line is set about where its parts justify")
    u = card.get("usage") or {}
    if u.get("tn") is not None:
        notes.append(f"his receiving role: {u['tn']:g} targets last game against {float(u.get('tn_base') or 0):.1f} a game before")
    if compact:
        txt = "; ".join(notes)
        return L + (["", txt[:1].upper() + txt[1:] + "."] if notes else [])
    L += ["", "*" + ("; ".join(notes) + ". " if notes else "") +
          "Combined fits better when its line is set no higher than its parts justify, his receiving role is showing up, "
          "and the script is uncertain (handoffs if his team leads, checkdowns if it trails). The engine draws rushing and "
          "receiving independently, so that script hedge is a judgment the numbers do not hold.*"]
    return L


def _mid(r):
    return "-" if r.get("median") is None else f"{float(r['median']):.1f} ({float(r['median']) - float(r['line']):+.1f})"


def branches(lg, card=None, compact=False) -> list[str]:
    mk = PB.market_key(lg["market"])
    need_out = int(float(lg["line"])) + 1
    side = lg["side"].lower()
    want = side == "over"
    n = next((x for x in lg.get("needs") or [] if x.get("reaches") is want), None)
    L = []
    unit = ((PB.cells_for(card, mk) or {}).get("unit") or "") if card else ""
    units = [u.strip() for u in unit.split("+")] if "+" in unit else [unit]
    if n:
        parts = n.get("parts") or [[n.get("volume"), n.get("rate")]]
        total = sum(float(a) * float(b) for a, b in parts)
        work = " + ".join(f"{float(a):g} {units[k] if k < len(units) else ''} at "
                          f"{f'{100 * float(b):.0f}%' if float(b) <= 1 else f'{float(b):g}'}".replace("  ", " ")
                          for k, (a, b) in enumerate(parts))
        how = (f"{' + '.join(f'{float(a):g} x {float(b):g}' for a, b in parts)} = {total:.1f}, "
               + (f"reaching the {need_out} the Over needs" if want else f"short of the {need_out} the Over needs"))
        if compact:
            # the shown numbers multiply out: a yards rate to two decimals and the total in whole yards
            # (18 carries at 3.73 make about 67); a catch rate as a percent, catches to one decimal
            shown = " + ".join(f"{float(a):g} {units[k] if k < len(units) else ''} at "
                               f"{f'{100 * float(b):.0f}%' if float(b) <= 1 else f'{float(b):.2f}'}".replace("  ", " ")
                               for k, (a, b) in enumerate(parts))
            what = "catches" if mk == "player_receptions" else "yards"
            amount = f"{total:.1f}" if mk == "player_receptions" else f"{total:.0f}"
            L.append(f"- If you expect {shown}, **{PB.MARKET_WORDS[mk]} {side} {float(lg['line']):g}** fits: about "
                     f"{amount} {what}, {'past' if want else 'short of'} the {need_out} the Over needs"
                     f"{' (a hypothetical rate)' if n.get('hypothetical') else ''}. It stops fitting if "
                     f"**{lg['fails'].rstrip('.')}**.")
        else:
            L.append(f"- **If you expect {work}, then {PB.MARKET_WORDS[mk]} {side} {float(lg['line']):g} fits**, because "
                     f"{how}{' (a hypothetical rate)' if n.get('hypothetical') else ''}.")
    elif compact:
        L.append(f"- If {lg['if'].rstrip('.')}, **{PB.MARKET_WORDS[mk]} {side} {float(lg['line']):g}** fits. It stops "
                 f"fitting if **{lg['fails'].rstrip('.')}**.")
    else:
        L.append(f"- **If {lg['if'].rstrip('.')}, then {PB.MARKET_WORDS[mk]} {side} {float(lg['line']):g} fits.**")
    alt = lg["else"].strip().rstrip(".")
    if compact:
        L.append(f"- {alt[:1].upper() + alt[1:]}.")
    else:
        L.append(f"- **{alt[:1].upper() + alt[1:]}.**")
    return L


def player_card(run, reads, p, checks, idx, qa: bool) -> list[str]:
    card = PB.card_for(run, p["player"]) or {}
    L = [f"### {p['player']} · {card.get('slot')}, {card.get('team')}", ""]
    vts = [f"{PB.MARKET_WORDS[r['market']]}: {PB.volume_text(card, r['market'])}" for r in PB.main_rows(card)
           if PB.volume_text(card, r["market"])]
    c_ = not qa
    L += [f"> **Engine workload:** {'; '.join(vts) or '-'}.  ", f"> **Basis:** {p['basis']}", "",
          *table_a(card, c_), "", *table_b(card, c_), ""]
    for extra in (receiving_comparison(card, c_), rushing_vs_combined(card, c_), production_paths(card) if qa else []):
        if extra:
            L += [*extra, ""]
    legs = [reads["legs"][i - 1] for i in idx]
    L += ([closing_compact(card, p, legs[0]), "", p["explanation"], ""] if c_ else
          [p["explanation"], "", closing_paragraph(card, p, legs[0]), ""])
    for lg in legs:
        L += [*branches(lg, card, c_), ""]
    if qa:
        L += ["**Backend.**", ""]
        L.append(f"- Card: {card.get('slot')}, {card.get('team')}; book {card.get('book')}, quote {card.get('quoted')}.")
        for r in PB.main_rows(card):
            c = PB.cells_for(card, r["market"]) or {}
            for k in ("capped", "season", "engine"):
                x = (c.get("rows") or {}).get(k)
                if x and x.get("label"):
                    L.append(f"- {PB.MARKET_WORDS[r['market']]}, the {k} rate's window: {x['label']} (rate {PB._fmt(x.get('rate'))}).")
            if c.get("note"):
                L.append(f"- {PB.MARKET_WORDS[r['market']]}: measured calibration: {c['note']}")
            v = PB.verdict(card, r["market"])
            if v:
                L.append(f"- {PB.MARKET_WORDS[r['market']]} verdict **{v['word']}**: needs {v['need']:g} {v['unit']} at the "
                         f"{v['ref']} rate against the engine's {v['proj']:.1f}"
                         + (f" and {v['last']:g} in his last game played (week {(card.get('usage') or {}).get('week')})"
                            if v["last"] is not None else " (last game's count not in the run)") + ".")
        if card.get("watch"):
            L.append("- The engine's flags: " + "; ".join(card["watch"]) + ".")
        if card.get("matchup"):
            L.append(f"- Matchup context: {card['matchup']}")
        L += ["", "**Checks.**", "", *checks_table([c for c in checks if c["leg"] in idx]), "",
              "**For the reviewer (not machine-checked):** is each condition something the evidence makes possible, "
              "and does the case argue from this player's own rows?", ""]
    return L


def data_card(run, card, qa: bool) -> list[str]:
    """A priced player with no written read: his tables and computed verdicts, said plainly."""
    L = [f"### {card['name']} · {card.get('slot')}, {card.get('team')}", ""]
    vts = [f"{PB.MARKET_WORDS[r['market']]}: {PB.volume_text(card, r['market'])}" for r in PB.main_rows(card)
           if PB.volume_text(card, r["market"])]
    c_ = not qa
    L += [f"> **Engine workload:** {'; '.join(vts) or '-'}.", "", *table_a(card, c_), "", *table_b(card, c_), ""]
    for extra in (receiving_comparison(card, c_), rushing_vs_combined(card, c_), production_paths(card) if qa else []):
        if extra:
            L += [*extra, ""]
    if qa:
        L += ["*No written read for this player: the tables are the market's and the engine's, and the verdicts are "
              "computed from them.*", ""]
    if qa and card.get("watch"):
        L += ["- The engine's flags: " + "; ".join(card["watch"]) + ".", ""]
    return L


SHARED_NOTE = [
    "## How to read the player cards", "",
    "- **Line vs engine middle.** Sleeper prices most props near even and moves the line instead, so the line is the "
    "market's view. The engine's middle is its own forecast; the gap is where the two disagree.",
    "- **Gain references.** The workload a line needs at this season's gains, at his gains with long plays trimmed, "
    "and at the engine's gains, with how often the engine's workload reaches it.",
    "- **Market-implied workload.** The workload at which the engine's chance matches the market's, at the engine's "
    "gains: a translation of the price, not a published projection.",
    "- **Verdict.** Attainable: the engine's workload covers the need. Rebound (requires a rebound): more than his last "
    "game. Better gains (requires better gains): only the engine's gains clear it. More work (requires more work than "
    "the engine expects): none do.",
    "- **Chance of those catches (‡).** Only the catches; the yards still need the stated gain per catch.",
    "- **Combined yards.** The combined line is compared with its two parts. A sum's middle runs a little above the sum "
    "of its parts' middles because yards come in bursts, so the engine's own gap is the fair comparison. The engine "
    "treats rushing and receiving as independent, so a game-script hedge is a judgment, not in the numbers.",
    "- **Cards without a closing paragraph** have no written read: their tables and verdicts are shown as computed.", ""]


def plain_weather(line) -> str:
    """The weather line without the run's internals (the screen threshold, the feed and its time)."""
    t = re.sub(r"\s*\(gusts not included in this run\)", "", line or "")
    t = re.sub(r";\s*below the \d+ mph sustained-wind screen", "", t)
    t = re.sub(r"\s*·\s*NWS, updated [^·]+", " ", t)
    t = re.sub(r"\s*·\s*", " · ", t)
    return t.strip(" ·") or "-"


def external_header(run) -> list[str]:
    """The guide's header: the kickoff line, then 'Updated: markets · injuries · performance'."""
    h = [x for x in header_lines(run) if x.strip()]
    kick = h[0] if h else ""
    me = run.get("market_env") or {}
    srcs = run.get("sources_line") or []
    inj = next((x.split("injury report: ", 1)[-1] for x in srcs if x.startswith("injury report")), None)
    upd = [f"markets {str(me.get('as_of'))[11:16]} UTC" if me.get("as_of") else None,
           f"injuries: {inj}" if inj else None, f"performance through week {run['week'] - 1}"]
    return [META + kick, "", META + "Updated: " + " · ".join(u for u in upd if u)]


def priced_cards(run) -> list[dict]:
    """Every card with at least one priced line, in the run's order (away team first, by slot)."""
    return [c for c in run.get("cards") or [] if PB.main_rows(c)]


def reliability_note(run) -> list[str]:
    lr = run.get("live_record") or {}
    return ["## A note on reliability", "",
            "The market's chance is the best available estimate of a prop's chance. "
            + (f"At Sleeper's real lines (weeks {lr.get('weeks')}, {lr.get('lines'):,} lines) the engine's chances have scored "
               f"worse than the market's (log loss {lr.get('engine_log_loss', 0):.3f} against {lr.get('market_log_loss', 0):.3f}; "
               f"a coin flip scores {lr.get('coin_flip', 0.693):.3f}). " if lr else "")
            + "Read the engine for workload and role -- what a line requires and how often the engine's workload gets "
              "there -- not as a better chance than the market's. Nothing here is a recommendation to bet.", ""]


# ---------------------------------------------------------------- the QA/QC and external versions
META = "%% "      # marks a header line for the PDF's meta style (render_external only)


def render_qa(run, reads, checks, release) -> str:
    """For chat and internal reviewers: the guide's structure, with the backend under each section
    and every check; the full 'where the baseline could miss' table and the inputs at the end."""
    return _document(run, reads, checks, release, qa=True)


def render_external(run, reads) -> str:
    """For an outside reader (the PDF): the same document without the backend -- no checks, no
    model names, no decision numbers, no release internals. One builder for both, so the two
    versions cannot drift apart. Header lines carry the META mark for the PDF's meta style."""
    return _document(run, reads, [], {}, qa=False)


def _document(run, reads, checks, release, qa: bool) -> str:
    home, away = teams(run)
    hdr = header_lines(run) if qa else external_header(run)
    L = [f"# {away.upper()} AT {home.upper()}" + (" · QA/QC" if qa else ""), "", *hdr, ""]
    if qa:
        n_fail = sum(not c["ok"] for c in checks)
        L += [f"Release **{release.get('tag') or 'unknown'}** ({str(release.get('hash') or '')[:12] or 'hash unknown'}, "
              f"{release.get('source') or 'source unknown'}) · run `{run['slug']}` · data cutoff: {cutoff(run)}", "",
              f"**Checks: {len(checks) - n_fail} of {len(checks)} pass.**"
              + ("" if not n_fail else f" {n_fail} FAIL: not publishable until they are fixed."), ""]
    L += ["**Opening game read.** " + reads["opening"], "",
          "## 1. What game does the market expect?", "", *market_table(run, compact=not qa), "",
         reads.get("market_read") or "", "",
          *scenario_table(run, detail=qa), "",
          "## 2. How much passing and rushing should we expect?", "", *workload_table(run, compact=not qa), "",
          reads.get("workload_read") or "", "",
          "## 3. What is each team good and bad at?", "", *unit_table(run, compact=not qa), ""]
    for t in (home, away):
        if (reads.get("unit_reads") or {}).get(t):
            L += [f"> **{t} offense:** {reads['unit_reads'][t]}", ""]
    L += ["## 4. Which personnel changes affect that picture?", "", *personnel_table(reads), "",
          reads.get("personnel_read") or "", "", *if_out_tables(run), ""]
    if qa:
        L += ["Section 4 as the engine reads it (the prices' own statuses):", ""]
        for t, cells_ in (run.get("who_plays") or {}).items():
            for unit, txt in cells_.items():
                L.append(f"- **{t} {unit}:** {txt}")
        L += ["", run.get("who_note") or "", ""]
    L += ["## 5. Where have opposing positions produced?", "", *allowed_tables(run), "", reads.get("allowed_read") or "", "",
          f"**Weather and venue.** {(run.get('weather_line') or '-') if qa else plain_weather(run.get('weather_line'))}", "",
          "**Assumptions worth testing.**", "", *(f"- {a}" for a in reads["assumptions"]), "",
          reads["handoff"], ""]
    if qa:
        L += ["**Checks for the team brief.**", "", *checks_table([c for c in checks if c["leg"] == 0]), ""]
    by_player = {}
    for i, lg in enumerate(reads["legs"], 1):
        by_player.setdefault(lg["player"], []).append(i)
    written = {p["player"].lower(): p for p in reads["players"]}
    cards = priced_cards(run)
    if not qa:
        L += SHARED_NOTE
    for sec in PB.SECTIONS:
        cs = [c for c in cards if PB.section_of(c) == sec]
        if not cs:
            continue
        L += [f"## {sec}", ""]
        for c in cs:
            p = written.get(c["name"].lower())
            L += (player_card(run, reads, p, checks, by_player.get(p["player"], []), qa=qa) if p
                  else data_card(run, c, qa))
    if qa:
        unread = [c["name"] for c in cards if c["name"].lower() not in written]
        L += [f"**Coverage:** {len(cards) - len(unread)} of {len(cards)} priced players have a written read"
              + (f"; data cards only: {', '.join(unread)}." if unread else "."), ""]
    L += reliability_note(run)
    if qa:
        L += ["## QA appendix", "", "### Where the baseline could miss (section 7, in full)", "",
              "| Matchup issue | What the baseline may miss | Separate scenario |", "|---|---|---|",
              *(f"| {_esc(a)} | {_esc(b)} | {_esc(c)} |" for a, b, c in run.get("gaps") or []), "",
              "### Inputs and their state", "", "| Source | Used for | Status | Detail |", "|---|---|---|---|",
              *(f"| {_esc(s_['name'])} | {_esc(s_['purpose'])} | {_esc(s_['status'])} | {_esc(s_['detail'])} |"
                for s_ in run.get("sources") or []), "",
              "### Model states", "", run.get("model_states") or "-", "",
              f"The engine's full report for this run is the reference copy: `report_{run['slug']}.md`, in the same folder.", ""]
    else:
        L += [f"*Data as of: {cutoff(run)}*", ""]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- the agent version
def render_agent(run, reads, checks, release, ci) -> str:
    """For another LLM agent: how the engine works end to end, from the repository to this run's
    inputs, models, tests and checks, and how the read reaches the external reader. The static
    parts are the release's own documents, embedded verbatim."""
    tag = release.get("tag")
    ref = tag or "main"
    res = lambda name: _resource(name) or f"*{name}: DATA MISSING*"
    mm = margin_model()
    L = [f"# Props engine, end to end: {run['away']} at {run['home']}, week {run['week']}", "",
         "*For an LLM agent. Everything below is either this run's own data or a document shipped in "
         "the release that produced it; nothing is summarised from memory.*", "",
         "## 0. Identity", "", "| | |", "|---|---|",
         f"| Repository | {PB.REPO_URL} |",
         f"| Release | {tag or 'unknown'} -- the code at {PB.REPO_URL}/tree/{ref} |",
         f"| Release hash | {release.get('hash') or 'unknown'} (skill/release.py: sha256 over the release's files, LF-normalised) |",
         f"| How it was fetched | {release.get('source') or 'unknown'} |",
         f"| This run | `{run['slug']}`: kickoff {str(run.get('kickoff_utc'))[:16]} UTC, priced "
         f"{run.get('hours_to_kickoff') or 0:.1f} h before it |",
         f"| Data cutoff | {cutoff(run)} |", "",
         res("agent_guide.md").replace("{REF}", ref).replace("{REPO}", PB.REPO_URL), "",
         "## 3. This run's inputs (the run's sources table, verbatim)", "",
         "| Source | Used for | Status | Detail |", "|---|---|---|---|",
         *(f"| {_esc(s['name'])} | {_esc(s['purpose'])} | {_esc(s['status'])} | {_esc(s['detail'])} |"
           for s in run.get("sources") or []), "",
         "### Where each source lives (resources/data_source_matrix.md, verbatim)", "", _demote(res("data_source_matrix.md")), "",
         "## 4. How the engine turns inputs into prices (resources/engine_overview.md, verbatim)", "",
         _demote(res("engine_overview.md")), "",
         "## 5. Validation", "", "### Model states at this run", "", run.get("model_states") or "-", "",
         "### The live record", ""]
    lr = run.get("live_record") or {}
    if lr:
        L += [f"Weeks {lr['weeks']}, {lr['lines']} graded lines at Sleeper's prices: engine log loss {lr['engine_log_loss']:.3f}, "
              f"market {lr['market_log_loss']:.3f} (a coin flip {lr['coin_flip']:.3f}). Per market (lines, Over hit, engine's "
              "average Over, market's): " + "; ".join(
                  f"{PB.MARKET_WORDS.get(m, m)} {v['lines']}, {pct(v['over_hit'])}, {pct(v['engine_over'])}, {pct(v['market_over'])}"
                  for m, v in lr["markets"].items()) + ".", ""]
    L += ["### The margin model behind the scenario table", "",
          (f"margin_buckets_v0 (scripts/fit_margin_model.py, pre-registered in "
           f"docs/plans/2026-10-08-report-format-design.md): shipped **{mm.get('shipped') or 'nothing'}**; test log loss "
           + ", ".join(f"{k} {v:.3f}" for k, v in (mm.get("log_loss") or {}).items())
           + ". Evidence: reports/margin_buckets_v0.md." if mm else "DATA MISSING: no margin model record."), "",
          "### Tests and CI for this release", ""]
    if ci is None:
        L += ["DATA MISSING: the CI results for this release could not be read from GitHub (no network, "
              "or the API refused). The suites are listed in section 2; nothing here says they passed.", ""]
    else:
        L += [f"Read from the GitHub API for {ci.get('ref')} (commit {str(ci.get('sha'))[:12]}"
              + (f"; merged by pull request #{ci['pr']}, whose head commit ran the suites" if ci.get("pr") else
                 "; no pull request found for it, so only the commit's own runs") + "):", "",
              "| Check | Ran on | Result | Run |", "|---|---|---|---|",
              *(f"| {_esc(c['name'])} | {c.get('where')} | {c.get('conclusion') or c.get('status')} | {c.get('url') or '-'} |"
                for c in ci.get("checks") or []), "",
              "The check names map to the suites in section 2 (tests: props/tests and props/tests_ci; root-suite: "
              "tests/ and the release lock; backtest-smoke: the backtest on model changes; commit-hygiene: no "
              "per-run outputs committed; tick: the scheduled props capture, not a test). The test COUNT is not in "
              "the API's answer.", ""]
        if not any(c.get("name") in ("tests", "root-suite") for c in ci.get("checks") or []):
            L += ["DATA MISSING: no test-suite run was found for this release; nothing here says the suites passed.", ""]
    L += ["## 6. From this run to the external reader", "",
          "1. score_game.py priced the game and wrote the report and `run_<slug>.json` (section 2).",
          "2. The analyst (chat) wrote the reads file in the report guide's structure.",
          "3. publish.py checked the reads against the run (below). A failed check renders nothing.",
          "4. publish_render.py rendered the QA/QC version and this file from the same run and reads; the "
          "generated pieces (verdict words, the closing paragraph's computed half, the receptions-vs-yards "
          "comparison, the production paths, the scenario status) come from the run, never from the analyst.", "",
          "### Field map: what each reader-facing number is", "",
          "| On the page | Run field | Meaning |", "|---|---|---|",
          "| Spread, total, implied points | market_env, teams[].implied_points | DraftKings via ESPN at the run's time |",
          "| Win probability | market_env.home_win_prob | the two moneylines' implied chances, scaled to sum to 100% |",
          "| Change since opening | market_env.open_* | DraftKings' opening line |",
          "| Market-derived workload | teams[].market_throws / team_volume[].target_rate, teams[].market_runs | the engine's fit of plays and pass rate to the spread and total, alone |",
          "| Engine / season workload | team_volume[].our_att, our_runs, att_avg, runs_avg | the engine's projection; the season's per-game average |",
          "| Unit rank · grade · score | units[] | EPA and success rate blend, 50 = average, rank 1 = best |",
          "| PPR allowed and its parts | points_allowed[] | per game to each position; parts on the same plays |",
          "| Market / Engine Over estimate | cards[].rows[].p_over_book / p_over_model | no-vig market chance; share of 20,000 simulations |",
          "| Workload needed at a gain rate | cards[].volume[].cells.rows.{season,capped,engine} | vol = ceil(need_out / rate); pct = share of simulations reaching vol |",
          "| Workload consistent with the market price | cards[].rows[].market_volume | the volume at which the engine's chance equals the market's, at the engine's gains |",
          "| Verdict | publish.verdict | attainable / requires a rebound / requires better gains / requires more work than the engine expects, by definition |",
          "| If he's out | if_out[] | the board priced again without a Questionable player |", "",
          "### The reads and their checks", "", "```json",
          json.dumps({k: v for k, v in reads.items() if k != "legs"}, indent=1, ensure_ascii=False), "```", "",
          *checks_table(checks), "",
          f"**{sum(c['ok'] for c in checks)} of {len(checks)} checks pass.** Judgment (whether a condition is "
          "plausible) is not machine-checked.", "",
          "## 7. Reproduce", "", "```bash",
          f"git clone {PB.REPO_URL} && cd Fantasy-football && git checkout {ref}",
          "pip install -r requirements.txt",
          f"python props/engine/scripts/score_game.py --away {run['away']} --home {run['home']} --season {run['season']} --week {run['week']}",
          f"python props/engine/scripts/publish.py --run $NFL_OUT/run_{run['slug']}.json --reads reads.json --out $NFL_OUT",
          "```", "",
          "Prices move with the lines and the inputs' publication times: a re-run reproduces the method and the "
          "checks, not necessarily these exact numbers.", ""]
    return "\n".join(L) + "\n"


def _demote(md: str) -> str:
    """Embedded documents' headings go two levels down, so they nest under this file's sections."""
    return re.sub(r"(?m)^(#{1,4}) ", lambda m: "#" * min(6, len(m.group(1)) + 2) + " ", md)
