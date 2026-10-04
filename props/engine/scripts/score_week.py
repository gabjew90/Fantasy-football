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
  slate_research_{season}_wk{W}.csv every priced line's research row (line implies, usage, flags)
  slate_card_{season}_wk{W}.csv     the old card rows, written for the record only, never shown
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
import argparse, os, re as _re, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from score_game import (GAMES_URL, OUT, eastern_to_utc, et_today, fetch,  # noqa: E402
                        refresh_season_inputs)

# The report contains "≥" and other non-cp1252 characters. The Linux
# runner writes UTF-8 by default so this was invisible in CI, while every
# local run died on the final print. Same reconfigure the draftkit CLI does.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):  # pragma: no cover - non-tty streams
        pass


CAL_MARKETS = {"player_receptions", "player_reception_yds"}
MK_LABEL = {"player_receptions": "catches", "player_reception_yds": "rec yds",
            "player_rush_yds": "rush yds", "player_anytime_td": "anytime TD", "player_pass_yds": "pass yds"}


def break_even_cell(x) -> str:
    """The workload each side needs to beat its own price (score_game.break_even_cell,
    read here from the research CSV)."""
    unit = x.get("unit") if isinstance(x.get("unit"), str) else ""
    o, u = x.get("over_needs"), x.get("under_needs")
    if not unit or (o is None or pd.isna(o)) and (u is None or pd.isna(u)):
        return "—"
    over = "Over: beyond the search range" if o is None or pd.isna(o) else f"Over above {o:.1f}"
    under = "Under: beyond the search range" if u is None or pd.isna(u) else f"Under at {u:.1f} or fewer"
    return f"{over} {unit}; {under}"


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


def slate_pick_order(ok):
    """Candidates for the slate-wide single pick, best first: no role flag, book not disagreeing,
    then the rule's own order (backtested market at >= 55%, then >= 50%, then any-market
    fallbacks) before model probability."""
    top = ok[(~ok.new_team.astype(bool)) & (~ok.questionable.astype(bool))
             & (~ok.rule.str.contains("DISAGREES"))].copy()
    top["rule_rank"] = [0 if (m in CAL_MARKETS and "55%" in r) else 1 if m in CAL_MARKETS else 2
                        for m, r in zip(top.market, top.rule)]
    return top.sort_values(["rule_rank", "p_model"], ascending=[True, False])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=None)
    ap.add_argument("--week", type=int, default=None)
    ap.add_argument("--games", default="", help="comma list AWAY@HOME; default = every game in the week")
    ap.add_argument("--skip-started", action="store_true", help="skip games whose kickoff has passed")
    ap.add_argument("--source", choices=["sleeper", "oddsapi"], default=None,
                    help="default: score_game decides (Sleeper; DraftKings for a TD-only run when credits allow)")
    ap.add_argument("--date", default=None, help="only games on this date (YYYY-MM-DD); sets season and week")
    ap.add_argument("--today", action="store_true", help="only today's games")
    ap.add_argument("--markets", default="", help="passed to score_game: receptions, rec_yds, rush_yds, td")
    ap.add_argument("--no-oddsapi-fallback", action="store_true")
    ap.add_argument("--workdir", default=str(Path.home() / "nfl_wd"))
    ap.add_argument("--extra", default="", help="extra args passed through to score_game.py, quoted")
    a = ap.parse_args()

    wd = Path(a.workdir); wd.mkdir(parents=True, exist_ok=True)
    (wd / "logs").mkdir(exist_ok=True)
    games = pd.read_csv(fetch(GAMES_URL, wd / "games.csv"))
    if a.today:
        a.date = et_today()          # games.csv dates are US Eastern; the host clock may be UTC
    if a.date:
        on = games[(games.gameday == a.date) & (games.game_type == "REG")]
        if on.empty:
            nxt = games[(games.gameday > a.date) & (games.game_type == "REG")].gameday.min()
            sys.exit(f"no regular-season games on {a.date}" + (f"; the next game day is {nxt}" if isinstance(nxt, str) else ""))
        a.season, a.week = int(on.season.iloc[0]), int(on.week.iloc[0])
    if a.season is None:
        a.season = int(games[games.gameday.notna()].season.max())
    if a.week is None:
        # first week of the season with an unplayed game
        gs = games[(games.season == a.season)]
        unplayed = gs[gs.result.isna()]
        a.week = int(unplayed.week.min()) if not unplayed.empty else int(gs.week.max())
    W = games[(games.season == a.season) & (games.week == a.week) & (games.game_type == "REG")].copy()
    if a.date:
        W = W[W.gameday == a.date]
    if a.games:
        alias = {"LAR": "LA", "WSH": "WAS", "JAC": "JAX", "LVR": "LV"}
        want = set()
        for g_ in a.games.split(","):
            if "@" in g_:
                aw, hm = (alias.get(x.strip().upper(), x.strip().upper()) for x in g_.split("@", 1))
                want.add(f"{aw}@{hm}")
        W = W[(W.away_team + "@" + W.home_team).isin(want)]
    W["kick_utc"] = [eastern_to_utc(g, t) if isinstance(t, str) else pd.NaT for g, t in zip(W.gameday, W.gametime)]
    W = W.sort_values(["kick_utc", "away_team"])
    now_utc = datetime.now(timezone.utc)
    if a.skip_started:
        W = W[[(k is pd.NaT) or (k > now_utc) for k in W.kick_utc]]
    if W.empty:
        sys.exit(f"no games for {a.season} week {a.week} after filters")

    print(f"slate: {a.season} week {a.week}, {len(W)} games, source={a.source}, workdir={wd}")
    # ONE VERSION OF THE INPUTS PER SLATE. Refresh the current-season files once,
    # here, then pin every per-game run to them; otherwise a refresh age passing
    # mid-slate prices the early games on one injury report and the late games on
    # another. The ages print to this process's stdout, which is the log a
    # scheduled run keeps (the per-game output goes to files under the workdir).
    input_ages = refresh_season_inputs(a.season, wd)
    print("inputs, hours old: " + ", ".join(f"{k} {v}" for k, v in input_ages.items()))
    child_env = dict(os.environ, NFL_FETCH_MAX_AGE_S=str(7 * 86400))
    runs = []
    for _, g in W.iterrows():
        A, H = g.away_team, g.home_team
        cmd = [sys.executable, str(HERE / "score_game.py"), "--away", A, "--home", H,
               "--season", str(a.season), "--week", str(a.week), "--workdir", str(wd)]
        if a.source:
            cmd += ["--source", a.source]
        if a.markets:
            cmd += ["--markets", a.markets]
        if a.no_oddsapi_fallback:
            cmd.append("--no-oddsapi-fallback")
        if a.extra:
            cmd += a.extra.split()
        t0 = time.time()
        log_path = wd / "logs" / f"{A}_{H}.log"
        with open(log_path, "w", encoding="utf-8") as fh:
            rc = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, env=child_env).returncode
        secs = round(time.time() - t0, 1)
        # errors="replace": this log is parsed for the spread/total, and a
        # slate must not die because one game's report held a character the
        # host codepage cannot represent.
        txt = Path(log_path).read_text(encoding="utf-8", errors="replace")
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
    research = []
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
                             line=pick.line, tier=tier, market=pick.market, new_team=bool(pick.new_team),
                             questionable=bool(pick.questionable), rule=rule, book=pick.book))
        if bc.exists() and r["status"] == "ok":
            c = pd.read_csv(bc); c["game"] = r["game"]; cards.append(c)
        rf = OUT / f"research_{a.season}_wk{a.week:02d}_{A}_{H}.csv"
        if rf.exists() and r["status"] == "ok":
            x = pd.read_csv(rf)
            if len(x):
                research.append(x.assign(game=r["game"]))
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

    # ---------- cross-game TD parlays: one leg per game, legs past the floor on their own ----------
    import td_builder as TB
    boards = []
    for r in runs:
        A, H = r["game"].split("@")
        f = OUT / f"td_board_{a.season}_wk{a.week:02d}_{A}_{H}.csv"
        if f.exists() and r["status"] != "FAILED":
            b = pd.read_csv(f)
            if {"p_blend", "p_market"} <= set(b.columns):
                boards.append(b.assign(game=r["game"]))
    TBOARD = pd.concat(boards, ignore_index=True) if boards else pd.DataFrame()
    TLEGS = TB.candidate_legs(TBOARD) if len(TBOARD) else pd.DataFrame()
    TPAR = TB.build(TBOARD) if len(TBOARD) else pd.DataFrame()
    if len(TPAR):
        TPAR.to_csv(OUT / f"parlay_builder_{a.season}_wk{a.week:02d}.csv", index=False)

    # ---------- summary markdown (this is the chat-reply deliverable for a slate question) ----------
    L = [f"# {a.season} Week {a.week} slate", "",
         f"*{len(runs)} games scored {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%MZ')}, prices from "
         f"{'The Odds API' if a.source == 'oddsapi' else 'Sleeper Picks' if a.source == 'sleeper' else 'Sleeper Picks by default (a TD-only run may use The Odds API when credits allow)'}"
         f"{', Odds API fallback allowed' if a.source == 'sleeper' and not a.no_oddsapi_fallback else ''}. "
         "Model opinion, not validated against closing lines. Lines for games more than a day out will move; re-run inside 90 minutes of kickoff.*", "",
         "*nflverse inputs, hours old at scoring: " + ", ".join(f"{k} {v}" for k, v in input_ages.items()) + ".*", "",
         "## Runs", "", "| Game | Kickoff (UTC) | Roof | Spread | Total | Lines | Status |", "|---|---|---|---|---|---|---|"]
    for r in runs:
        L.append(f"| {r['game']} | {r['kickoff_utc']} | {r['roof']} | {r['spread'] or '—'} | {r['total'] or '—'} | {r['n_lines']} | {r['status']}{(' — ' + r['error']) if r['error'] else ''} |")
    # The must-win picks and the cross-game TD parlays are still computed and
    # written (slate_survival_*.csv, parlay_builder_*.csv) but not shown: no
    # picks until the record shows the model adds weight beside the book's
    # price (DECISIONS #142, the user's call 2026-10-03).
    RS = pd.concat(research, ignore_index=True) if research else pd.DataFrame()
    if len(RS):
        RS.to_csv(OUT / f"slate_research_{a.season}_wk{a.week:02d}.csv", index=False)
        flagged = RS[RS["flags"].fillna("").str.contains("role up|role down")]
        L += ["", "## Research leads across the slate", "",
              "*Not picks. The role-shift pattern (snaps moved while targets had not caught up yet) -- the projection "
              "already moves his target share for it since props-v1.29; before that it beat or "
              "missed the model's next-week projection in 2022-25 (reports/role_shift_check.md); whether the BOOK also "
              "reacts late is what the bet journal decides. 'Line implies' is the targets per game at which the line is a "
              "fair 50/50; 'pays at this price' is the workload each side needs to beat its own price.*", "",
              "| Game | Player | Prop | Line | Line implies | Pays at this price if he gets | Last game | Flags |",
              "|---|---|---|---|---|---|---|---|"]
        if len(flagged):
            for _, x in flagged.sort_values(["game", "player"]).iterrows():
                imp = (f"{x.implied:.1f} {x.unit} (we project {x.projected:.1f})"
                       if pd.notna(x.implied) and pd.notna(x.projected) else "—")
                last = (f"snaps {100*x.snap:.0f}% (earlier {100*x.snap_base:.0f}%), targets {100*x.ts:.0f}% "
                        f"(earlier {100*x.ts_base:.0f}%)" if pd.notna(x.snap) else "—")
                L.append(f"| {x.game} | {x.player} ({x.team}) | {MK_LABEL.get(x.market, x.market)} | {x.line:g} | "
                         f"{imp} | {break_even_cell(x)} | {last} | {x['flags']} |")
        else:
            L.append("| — | no receiving role-shift flags this slate | | | | | | |")

        L += ["", "## Notes by game", "",
              "| Game | Lines | Role-shift flags | New-team players | Teammates out or back | Sleeper depth-rank gaps |",
              "|---|---|---|---|---|---|"]
        rank_by_game = {r["game"]: r.get("rank_gaps", 0) for r in runs}
        lines_by_game = {r["game"]: r["n_lines"] for r in runs}
        by_game = {g: x for g, x in RS.groupby("game", sort=False)}
        for g in [r["game"] for r in runs if r["game"] in by_game]:  # kickoff order
            x = by_game[g]
            fl = x["flags"].fillna("")
            n_role = x[fl.str.contains("role up|role down")].player.nunique()
            n_new = x[fl.str.contains("new team")].player.nunique()
            notes = sorted({part.strip() for f in fl for part in f.split(";")
                            if part.strip().endswith(" out") or " active (missed" in part})
            L.append(f"| {g} | {lines_by_game.get(g, 0)} | {n_role} | {n_new} | {'; '.join(notes) or '—'} | "
                     f"{rank_by_game.get(g, 0)} |")
        thin = [r["game"] for r in runs if 0 < r["n_lines"] < 24]
        L += ["", "*A thin board (under ~24 posted lines) means a narrower set of starters was priced, not a cleaner read"
              + (": " + ", ".join(thin) + "." if thin else ".") + " Sleeper depth-rank gaps are logged, never acted on.*",
              "", "*Calibration: no market has been validated against sportsbook lines. Receptions and receiving yards have a "
              "2025 walk-forward behind them (resources/calibration_2025.csv), but it places lines at fixed offsets from the "
              "model\u2019s own median across every player-week, so it measures distributional self-consistency, not whether the "
              "model beats a book on the calls it would actually make. Since props-v1.20 the 2022-25 yardage harness finds receptions, receiving yards and rushing yards unbiased and calibrated on outcomes (a model 85% wins about 84-85%). "
              "Team TD totals are anchored to the same-book spread and total.*"]
    L += ["", "Per-game guides, cards, ladders, parlays and shadow logs are in the outputs folder under each game's name."]
    md = "\n".join(L)
    (OUT / f"slate_summary_{a.season}_wk{a.week:02d}.md").write_text(
        md, encoding="utf-8")
    print("\n" + md)


if __name__ == "__main__":
    main()
