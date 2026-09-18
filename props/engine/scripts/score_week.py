#!/usr/bin/env python3
"""Score every game of an NFL week and summarise the slate.

  python score_week.py --season 2026 --week 2 [--games DET@BUF,MIN@CHI] [--skip-started]
                       [--source sleeper|oddsapi] [--workdir DIR] [--no-oddsapi-fallback]

Runs scripts/score_game.py once per game with ONE shared workdir, so the nflverse files,
the Sleeper lines pull, the Sleeper player table and the ESPN scoreboard are fetched once
for the whole slate (about 4 s per game after the first). Then it reads every game's
shadow log and bet card back and writes:

  slate_summary_{season}_wk{W}.md   the chat-reply deliverable for a slate question
  slate_survival_{season}_wk{W}.csv one "must-win" pick per game (rule below)
  slate_card_{season}_wk{W}.csv     every STRONG/MODERATE card row across the slate, by EV
  slate_runs_{season}_wk{W}.csv     per-game run status (lines, spread/total, exit code)

Survival rule ("if you could have only one bet in this game and had to win it"):
  1. receptions and receiving yards only (the two markets with a 2025 backtest);
  2. the book must agree: no-vig probability >= 0.55 on the same side;
  3. highest model probability among what remains.
  Fallbacks, in order, if nothing qualifies: no-vig >= 0.50 on calibrated markets;
  any market with no-vig >= 0.50; then the highest calibrated model probability with the
  book disagreeing, flagged. The slate-wide single pick applies the same rule across every
  game, excluding only new-team and Questionable players; depth-role players are eligible
  and their slot is printed so a thin role is visible. This maximises P(win), not EV --
  every survival pick is a heavily juiced favourite side and a bad bet in isolation. It is
  the answer to a different question than the card.

Per-game failures do not stop the slate; they are reported in the runs table.
"""
import argparse, re as _re, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from score_game import GAMES_URL, OUT, eastern_to_utc, fetch  # noqa: E402

CAL_MARKETS = {"player_receptions", "player_reception_yds"}
MK_LABEL = {"player_receptions": "catches", "player_reception_yds": "rec yds",
            "player_rush_yds": "rush yds", "player_anytime_td": "anytime TD"}


def base_tier(t):
    """Card/shadow-log tiers carry parenthetical annotations; strip to STRONG/MODERATE/LEAN/WEAK."""
    return str(t).split(" (")[0].strip() if isinstance(t, str) else ""


def _survival_rank(d):
    """Ordered (frame, floor, rule) attempts for the survival rule on one frame."""
    cal = d[d.market.isin(CAL_MARKETS)]
    return [(cal, 0.55, "calibrated market, book agrees (no-vig >= 55%)"),
            (cal, 0.50, "calibrated market, book agrees (no-vig >= 50%)"),
            (d, 0.50, "any market, book agrees (no-vig >= 50%)")], cal


def survival_pick(d):
    """Apply the survival rule to one game's shadow-log frame. Returns (row, rule) or (None, reason).

    Role-flagged players (new team, Questionable) are excluded on the first pass, the same
    exclusion the slate-wide single pick applies, so the two scopes cannot disagree about
    who is eligible. Only if no unflagged line qualifies at any tier does the rule re-run on
    the full frame; the rule string then says so and the row is flagged in the summary.
    """
    if d.empty:
        return None, "no priced lines"
    clean = d[(~d.new_team.astype(bool)) & (~d.questionable.astype(bool))]
    for frame, suffix in ((clean, ""), (d, " [role-flagged fallback: no unflagged line qualified]")):
        if frame.empty:
            continue
        tries, cal = _survival_rank(frame)
        for f, floor, rule in tries:
            c = f[f.p_novig >= floor]
            if not c.empty:
                return c.sort_values("p_model", ascending=False).iloc[0], rule + suffix
        if not cal.empty:
            return (cal.sort_values("p_model", ascending=False).iloc[0],
                    "calibrated market, BOOK DISAGREES (weakest class)" + suffix)
    return None, "no calibrated-market lines"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=None)
    ap.add_argument("--week", type=int, default=None)
    ap.add_argument("--games", default="", help="comma list AWAY@HOME; default = every game in the week")
    ap.add_argument("--skip-started", action="store_true", help="skip games whose kickoff has passed")
    ap.add_argument("--source", choices=["sleeper", "oddsapi"], default="sleeper")
    ap.add_argument("--no-oddsapi-fallback", action="store_true")
    ap.add_argument("--workdir", default=str(Path.home() / "nfl_wd"))
    ap.add_argument("--extra", default="", help="extra args passed through to score_game.py, quoted")
    a = ap.parse_args()

    wd = Path(a.workdir); wd.mkdir(parents=True, exist_ok=True)
    (wd / "logs").mkdir(exist_ok=True)
    games = pd.read_csv(fetch(GAMES_URL, wd / "games.csv"))
    if a.season is None:
        a.season = int(games[games.gameday.notna()].season.max())
    if a.week is None:
        # first week of the season with an unplayed game
        gs = games[(games.season == a.season)]
        unplayed = gs[gs.result.isna()]
        a.week = int(unplayed.week.min()) if not unplayed.empty else int(gs.week.max())
    W = games[(games.season == a.season) & (games.week == a.week) & (games.game_type == "REG")].copy()
    if a.games:
        want = {g.strip().upper() for g in a.games.split(",")}
        W = W[(W.away_team + "@" + W.home_team).isin(want)]
    W["kick_utc"] = [eastern_to_utc(g, t) if isinstance(t, str) else pd.NaT for g, t in zip(W.gameday, W.gametime)]
    W = W.sort_values(["kick_utc", "away_team"])
    now_utc = datetime.now(timezone.utc)
    if a.skip_started:
        W = W[[(k is pd.NaT) or (k > now_utc) for k in W.kick_utc]]
    if W.empty:
        sys.exit(f"no games for {a.season} week {a.week} after filters")

    print(f"slate: {a.season} week {a.week}, {len(W)} games, source={a.source}, workdir={wd}")
    runs = []
    for _, g in W.iterrows():
        A, H = g.away_team, g.home_team
        cmd = [sys.executable, str(HERE / "score_game.py"), "--away", A, "--home", H,
               "--season", str(a.season), "--week", str(a.week), "--workdir", str(wd),
               "--source", a.source]
        if a.no_oddsapi_fallback:
            cmd.append("--no-oddsapi-fallback")
        if a.extra:
            cmd += a.extra.split()
        t0 = time.time()
        log_path = wd / "logs" / f"{A}_{H}.log"
        with open(log_path, "w") as fh:
            rc = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT).returncode
        secs = round(time.time() - t0, 1)
        txt = open(log_path).read()
        spread = total = None
        m_ = _re.search(r"spread/total from .*?: (\w+ [+-]?[\d.]+), total ([\d.]+)", txt) \
            or _re.search(r"Market spread/total \(DK\).*?\| ok \| (\w+ [+-]?[\d.]+), total ([\d.]+)", txt)
        if m_:
            spread, total = m_.group(1), m_.group(2)
        sl = OUT / f"shadow_log_{a.season}_wk{a.week:02d}_{A}_{H}.csv"
        n_lines = len(pd.read_csv(sl)) if sl.exists() and rc == 0 else 0
        status = "ok" if rc == 0 else "FAILED"
        if rc == 0 and n_lines == 0:
            status = "no prices"
        err = ""
        if rc != 0:
            tail = [l for l in txt.strip().splitlines() if l.strip()]
            err = tail[-1][:160] if tail else "see log"
        m_rank = _re.search(r"depth-rank disagreements with Sleeper: (.+)", txt)
        rank_gaps = len(m_rank.group(1).split(";")) if m_rank else 0
        runs.append(dict(game=f"{A}@{H}", kickoff_utc=g.kick_utc.strftime("%a %m-%d %H:%MZ") if g.kick_utc is not pd.NaT else "TBD",
                         roof=g.roof if isinstance(g.roof, str) else "", spread=spread, total=total,
                         n_lines=n_lines, status=status, secs=secs, rank_gaps=rank_gaps, error=err))
        print(f"  {A}@{H:4s} {status:9s} lines={n_lines:3d} {secs:5.1f}s {err}")
    R = pd.DataFrame(runs)
    R.to_csv(OUT / f"slate_runs_{a.season}_wk{a.week:02d}.csv", index=False)

    # ---------- aggregate ----------
    surv, cards, unders = [], [], 0
    for r in runs:
        A, H = r["game"].split("@")
        sl = OUT / f"shadow_log_{a.season}_wk{a.week:02d}_{A}_{H}.csv"
        bc = OUT / f"bet_card_{a.season}_wk{a.week:02d}_{A}_{H}.csv"
        d = pd.read_csv(sl) if sl.exists() and r["status"] != "FAILED" else pd.DataFrame()
        pick, rule = survival_pick(d)
        if pick is None:
            surv.append(dict(game=r["game"], pick="none", rule=rule))
        else:
            tier = str(pick.tier).split(" (")[0] if isinstance(pick.tier, str) else ""
            surv.append(dict(game=r["game"], player=pick.player, team=pick.team, slot=str(pick.slot),
                             prop=f"{pick.side} {pick.line:g} {MK_LABEL.get(pick.market, pick.market)}"
                                  if pd.notna(pick.line) else f"{pick.side} {MK_LABEL.get(pick.market, pick.market)}",
                             price=int(pick.price), p_model=round(float(pick.p_model), 3),
                             p_novig=round(float(pick.p_novig), 3),
                             model_mean=round(float(pick.model_mean), 2) if pd.notna(pick.model_mean) else None,
                             line=pick.line, tier=tier, new_team=bool(pick.new_team),
                             questionable=bool(pick.questionable), rule=rule, book=pick.book))
        if bc.exists() and r["status"] == "ok":
            c = pd.read_csv(bc); c["game"] = r["game"]; cards.append(c)
    S = pd.DataFrame(surv)
    S.to_csv(OUT / f"slate_survival_{a.season}_wk{a.week:02d}.csv", index=False)
    C = pd.concat(cards, ignore_index=True) if cards else pd.DataFrame()
    if not C.empty:
        # Sort key: tier first, then BACKTESTED markets (receptions / receiving yards) ahead of
        # rushing and anytime TD, then EV. Sorting on EV alone floats the unvalidated markets to
        # the top of the card, which reads as "best plays" when they are the least supported ones.
        C["tier_base"] = C.tier.map(base_tier)
        C["tier_rank"] = C.tier_base.map({"STRONG": 0, "MODERATE": 1, "LEAN": 2, "WEAK": 3}).fillna(4)
        C["validated_rank"] = (~C.market.isin(CAL_MARKETS)).astype(int)
        C = C.sort_values(["tier_rank", "validated_rank", "ev_per_100"], ascending=[True, True, False])
        C.to_csv(OUT / f"slate_card_{a.season}_wk{a.week:02d}.csv", index=False)

    # ---------- summary markdown (this is the chat-reply deliverable for a slate question) ----------
    L = [f"# {a.season} Week {a.week} slate", "",
         f"*{len(runs)} games scored {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%MZ')}, prices from "
         f"{'Sleeper Picks' if a.source == 'sleeper' else 'The Odds API'}"
         f"{' (Odds API fallback allowed)' if a.source == 'sleeper' and not a.no_oddsapi_fallback else ''}. "
         "Model opinion, not validated against closing lines. Lines for games more than a day out will move; re-run inside 90 minutes of kickoff.*", "",
         "## Runs", "", "| Game | Kickoff (UTC) | Roof | Spread | Total | Lines | Status |", "|---|---|---|---|---|---|---|"]
    for r in runs:
        L.append(f"| {r['game']} | {r['kickoff_utc']} | {r['roof']} | {r['spread'] or '—'} | {r['total'] or '—'} | {r['n_lines']} | {r['status']}{(' — ' + r['error']) if r['error'] else ''} |")
    L += ["", "## One must-win pick per game", "",
          "*Rule: receptions/receiving yards only, book no-vig >= 55% on the same side, then highest model probability. "
          "Players who changed teams or are Questionable are excluded, the same exclusion the slate-wide pick applies; "
          "a row marked 'role-flagged fallback' is a game where no unflagged line qualified. "
          "These maximise P(win), not EV; every one is a juiced favourite side. Sleeper requires 2+ leg entries, and "
          "alternate lines two units past the median beat any posted line for this objective.*", "",
          "| Game | Pick | Price | Model | Book (no-vig) | Model mean vs line | Tier | Flags |", "|---|---|---|---|---|---|---|---|"]
    for s in surv:
        if s.get("pick") == "none":
            L.append(f"| {s['game']} | none | | | | | | {s['rule']} |"); continue
        flags = []
        if s["new_team"]: flags.append("new team")
        if s["questionable"]: flags.append("Questionable")
        if "DISAGREES" in s["rule"]: flags.append("book disagrees")
        if "50%" in s["rule"]: flags.append("book near coin flip")
        if "role-flagged fallback" in s["rule"]: flags.append("role-flagged fallback")
        if s.get("slot") in ("RB2", "WR3", "proxy") or str(s.get("slot", "")).startswith("proxy"): flags.append(f"depth role ({s['slot']})")
        L.append(f"| {s['game']} | {s['player']} ({s['team']}) **{s['prop']}** | {s['price']:+d} | {s['p_model']:.0%} | {s['p_novig']:.0%} | "
                 f"{s['model_mean']} vs {s['line']:g} | {s['tier']} | {', '.join(flags)} |" if pd.notna(s['line']) else
                 f"| {s['game']} | {s['player']} ({s['team']}) **{s['prop']}** | {s['price']:+d} | {s['p_model']:.0%} | {s['p_novig']:.0%} | — | {s['tier']} | {', '.join(flags)} |")
    if not S.empty and "p_model" in S:
        ok = S[S.get("pick", pd.Series(dtype=str)) != "none"] if "pick" in S else S
        ok = ok.dropna(subset=["p_model"]) if "p_model" in ok else ok
        if not ok.empty:
            # slate-wide single pick: same rule as the per-game pick, applied across every
            # game -- no role-change flag (new team / Questionable), book on the same side,
            # then highest model probability. Depth-role players are eligible; their slot is
            # printed so a thin role is visible rather than silently excluded.
            top = ok[(~ok.new_team) & (~ok.questionable)
                     & (~ok.rule.str.contains("DISAGREES"))].sort_values("p_model", ascending=False)
            if not top.empty:
                t = top.iloc[0]
                L += ["", f"**Single pick across the slate:** {t.player} ({t.team}) {t.prop} at {int(t.price):+d} in {t.game} "
                          f"— model {t.p_model:.0%}, book {t.p_novig:.0%}; {t.slot}, no role-change flag, book on the same side."
                          + (f" Note: {t.slot} usage is the most volatile input in the model, so this is the "
                             "highest-probability pick on the slate, not the most stable role on it."
                             if t.slot in ("RB2", "WR3", "proxy") else "")]
    if not C.empty:
        sm = C[C.tier_base.isin(["STRONG", "MODERATE"])]
        n_s = int((sm.tier_base == "STRONG").sum()); n_m = int((sm.tier_base == "MODERATE").sum())
        L += ["", f"## Slate card: STRONG and MODERATE legs ({n_s} STRONG, {n_m} MODERATE, of {len(C)} card rows)", "",
              "*Sorted by tier, then backtested markets (receptions, receiving yards) ahead of rushing and anytime TD, "
              "then EV. A MODERATE row cleared the edge floor but failed the prior-vs-market test: this season's share "
              "runs above the blend on an Under call, or below it on an Over, so part of the edge is the model's prior "
              "against a role the book may already have repriced.*", "",
              "| Tier | Game | Player | Prop | Line | Odds | Model | No-vig | Edge | EV/$100 | Note |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for _, c in sm.iterrows():
            ann = str(c.tier).split(" (", 1)[1].rstrip(")") if isinstance(c.tier, str) and " (" in c.tier else ""
            if "share runs above" in ann:
                ann = "share runs above blend"
            elif "share runs below" in ann:
                ann = "share runs below blend"
            base_note = c.note if isinstance(c.note, str) and c.note else ""
            if ann.startswith("share runs"):  # the annotation already says it; don't say it twice
                base_note = "; ".join(x for x in base_note.split("; ") if x != "prior-vs-market gap")
            note = "; ".join(x for x in [base_note, ann] if x)
            L.append(f"| {c.tier_base} | {c.game} | {c.player} ({c.team}) | {c.side} {c.prop} | {c.line if pd.notna(c.line) else '—'} | {int(c.price):+d} | "
                     f"{c.model_p:.0%} | {c.novig_p:.0%} | {c.edge_pts:+.0f} | {c.ev_per_100:+.0f} | {note} |")
        n_u = int((C.side == "Under").sum()); n_o = int((C.side == "Over").sum())
        L += ["", f"Board: {len(C)} card rows across the slate, {n_u} Under / {n_o} Over. "
                  "The Under lean is unresolved until logged results settle it."]

        # ---------- trust notes, one line per game, computed not narrated ----------
        L += ["", "## Trust notes by game", "",
              "| Game | Lines | STRONG | MODERATE | WEAK | New-team rows | Book disagrees (STRONG) | Sleeper depth-rank gaps |",
              "|---|---|---|---|---|---|---|---|"]
        rank_by_game = {r["game"]: r.get("rank_gaps", 0) for r in runs}
        lines_by_game = {r["game"]: r["n_lines"] for r in runs}
        by_game = {g: c for g, c in C.groupby("game", sort=False)}
        for g in [r["game"] for r in runs if r["game"] in by_game]:  # kickoff order, not card order
            c = by_game[g]
            st = c[c.tier_base == "STRONG"]
            new_rows = int(c.note.fillna("").str.contains("new team").sum()) if "note" in c else 0
            disagree = int((st.novig_p < 0.47).sum())
            L.append(f"| {g} | {lines_by_game.get(g, 0)} | {int((c.tier_base == 'STRONG').sum())} | "
                     f"{int((c.tier_base == 'MODERATE').sum())} | {int((c.tier_base == 'WEAK').sum())} | "
                     f"{new_rows} | {disagree} | {rank_by_game.get(g, 0)} |")
        thin = [r["game"] for r in runs if 0 < r["n_lines"] < 24]
        L += ["", "*A thin board (under ~24 posted lines) means a narrower set of starters was priced, not a cleaner read"
              + (": " + ", ".join(thin) + "." if thin else "."),
              "A high WEAK count means role turnover or a large model-book gap is doing the work; where the book disagrees "
              "on our side, 'the book knows something the model doesn't' is a live explanation and those rows grade as "
              "their own bucket at the week-8 review. Sleeper depth-rank gaps are logged, never acted on.*",
              "", "*Calibration: receptions and receiving yards are the only markets with a backtest behind them "
              "(2025, resources/calibration_2025.csv: realized hit rate within 2.6 points of stated in every 50-90% bucket; "
              "the 90%+ tail runs about 4 points optimistic). Rushing yards and anytime TD have no backtest. Team TD totals "
              "are anchored to the same-book spread and total.*"]
    L += ["", "Per-game guides, cards, ladders, parlays and shadow logs are in the outputs folder under each game's name."]
    md = "\n".join(L)
    (OUT / f"slate_summary_{a.season}_wk{a.week:02d}.md").write_text(md)
    print("\n" + md)


if __name__ == "__main__":
    main()
