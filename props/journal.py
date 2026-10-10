"""The bet journal: bets the user actually makes from the research board, each
with the four checklist answers, graded by the Tuesday settle run.

The model's record (props/record) says whether the MODEL beats the book. This
says whether the USER's process does: a role or personnel story, checked
against what the line implies, placed at a price. It is kept apart from the
model's record on purpose -- a handicapped bet is not a model call, and
pooling them would describe neither (DECISIONS #142).

    python props/journal.py add "Dalton Schultz" catches under 4.5 -141 --team HOU --angle return \\
        --change "targets fell to 12% in the one game Collins played" \\
        --implies "4.5 needs ~6.3 targets; with Collins back he got ~4" \\
        --fails "Collins re-aggravates the injury, or HOU trails and throws 45 times"
    # from a scenario run (score_game --assume): the assumption, the two Over
    # chances the 'Your scenario' table shows, and the break-even workload
    python props/journal.py add "Woody Marks" rush_yds over 33.5 -130 --team HOU --angle return \\
        --change ... --implies ... --fails ... --assumption "Woody Marks: carries=14" \\
        --over-board 37% --over-scenario 70% --pays-if "Over above 11.2 carries; Under at 9.2 or fewer"
    # a Sleeper Power Play: one all-or-nothing entry, its legs graded one by one
    python props/journal.py entry --stake 5 --payout 100 --angle role --why "Houston redistributes around Collins" \\
        --leg "Dalton Schultz|rec_yds|under|40.5|HOU" --leg "Woody Marks|rush_yds|under|36.5|HOU" ...
    python props/journal.py list [--open]
    python props/journal.py grade --season 2026
    python props/journal.py summary --season 2026

All three checklist answers are required: a bet that cannot state its change,
its implied workload and its failure case is not logged. So is its angle,
chosen when the bet is logged and never after (injury, role, return, other),
so the summary can say which kind of story actually pays. Stdlib + pandas.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

JOURNAL_ROOT: Path | None = None    # None: beside the record (persist.RECORD_ROOT.parent / "journal")

MARKETS = {
    "catches": "player_receptions", "receptions": "player_receptions", "rec": "player_receptions",
    "rec_yds": "player_reception_yds", "receiving_yards": "player_reception_yds", "rec yds": "player_reception_yds",
    "rush_yds": "player_rush_yds", "rushing_yards": "player_rush_yds", "rush yds": "player_rush_yds",
    "pass_yds": "player_pass_yds", "passing_yards": "player_pass_yds", "pass yds": "player_pass_yds",
    "td": "player_anytime_td", "anytime_td": "player_anytime_td", "anytime td": "player_anytime_td",
}
LABEL = {"player_receptions": "catches", "player_reception_yds": "rec yds", "player_rush_yds": "rush yds",
         "player_pass_yds": "pass yds", "player_anytime_td": "anytime TD",
         "player_rush_reception_yds": "rush+rec yds"}


def journal_path(season: int) -> Path:
    if JOURNAL_ROOT is not None:
        base = JOURNAL_ROOT
    elif os.environ.get("PROPS_JOURNAL_ROOT"):
        base = Path(os.environ["PROPS_JOURNAL_ROOT"])
    else:
        import persist
        base = persist.RECORD_ROOT.parent / "journal"
    return base / f"{season}.jsonl"


def read(season: int) -> list[dict]:
    p = journal_path(season)
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return [json.loads(ln) for ln in fh if ln.strip()]


def write(season: int, rows: list[dict]) -> None:
    """Atomic rewrite, LF line endings, one sorted-key JSON object per line."""
    p = journal_path(season)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    os.replace(tmp, p)


def current_week(season: int, now: dt.datetime | None = None) -> int:
    """The week whose games are next on the schedule; the calendar when the
    schedule cannot be read."""
    now = now or dt.datetime.now(dt.timezone.utc)
    try:
        import guard
        wk = guard._soonest_week(guard.load_games(season), now)
        if wk:
            return int(wk)
    except Exception:  # noqa: BLE001 -- the calendar is the fallback
        pass
    import guard
    return guard.week_from_calendar(now, season)


# the kind of story behind a bet, chosen at log time (DECISIONS #152)
ANGLES = {"injury": "injury redistribution", "role": "role change", "return": "teammate returning",
          "other": "other"}


def _chance(v, name):
    """'70%' or 0.70 -> 0.70; None stays None."""
    if v is None or str(v).strip() == "":
        return None
    t = str(v).strip()
    try:
        x = float(t.rstrip("%"))
    except ValueError:
        raise ValueError(f"--{name} {t} is not a chance (e.g. 70% or 0.70)") from None
    x = x / 100 if (t.endswith("%") or x > 1) else x
    if not 0 <= x <= 1:
        raise ValueError(f"--{name} must be between 0 and 100%")
    return x


def _check_rules(rules) -> None:
    """The assumption must read as --assume rules (props/engine/scripts/scenario.py),
    so a journaled scenario can be run again exactly."""
    import re
    eng = Path(__file__).resolve().parent / "engine" / "scripts"
    if str(eng) not in sys.path:
        sys.path.insert(0, str(eng))
    import scenario
    teams = {r.partition(":")[0].strip().upper() for r in rules
             if re.fullmatch(r"[A-Za-z]{2,3}", r.partition(":")[0].strip())}
    try:
        scenario.parse(rules, teams)
    except ValueError as exc:
        raise ValueError(f"--assumption is not an --assume rule: {exc}") from None


# the volume a market's line turns on: what a volume view is a view of (DECISIONS #226)
VOLUME_UNIT = {"player_receptions": "targets", "player_reception_yds": "targets", "player_rush_yds": "carries"}


def parse_view(view, line_assumes, unit: str | None) -> dict:
    """The volume view behind a bet (DECISIONS #226): 'low/likely/high' or one number, in the market's
    unit, either absolute ('16/19/22') or relative to the workload the line assumes ('+2/+4/+6', every
    value signed). Returns {} without a view, else volume_unit, line_volume, view (as given) and
    view_low / view_likely / view_high resolved. Raises ValueError with a plain reason."""
    if view is None or not str(view).strip():
        if line_assumes not in (None, ""):
            raise ValueError("--line-assumes goes with --view: the workload the line assumes beside yours")
        return {}
    if unit is None:
        raise ValueError("a volume view needs a volume market (catches, rec_yds, rush_yds)")
    parts = [q.strip() for q in str(view).split("/")]
    if len(parts) not in (1, 3) or any(not q for q in parts):
        raise ValueError("--view is low/likely/high or one number, e.g. +2/+4/+6 or 19")
    signed = [q.startswith(("+", "-")) for q in parts]
    if any(signed) and not all(signed):
        raise ValueError("a view relative to the line signs every value, e.g. +2/+4/+6")
    try:
        vals = [float(q) for q in parts]
    except ValueError:
        raise ValueError(f"--view '{view}' is not numbers") from None
    # the read is graded against the line's workload, so a view without it could never be scored
    if line_assumes in (None, ""):
        raise ValueError("a volume view needs --line-assumes (the card's 'The line assumes'): the read is "
                         "graded against it")
    try:
        base = float(line_assumes)
    except (TypeError, ValueError):
        raise ValueError(f"--line-assumes '{line_assumes}' is not a number") from None
    if not all(math.isfinite(v) for v in vals + [base]):
        raise ValueError("--view and --line-assumes are ordinary numbers")
    if base <= 0:
        raise ValueError("--line-assumes is a workload, above zero")
    if all(signed):
        vals = [base + v for v in vals]
    if min(vals) < 0 or (len(vals) == 3 and not vals[0] <= vals[1] <= vals[2]):
        raise ValueError("--view is low/likely/high, smallest first, none below zero")
    lo, mid, hi = (vals * 3)[:3] if len(vals) == 1 else vals
    return {"volume_unit": unit, "line_volume": base, "view": str(view).strip(),
            "view_low": round(lo, 2), "view_likely": round(mid, 2), "view_high": round(hi, 2)}


def make_entry(player: str, market: str, side: str, line, price: int, *, change: str, implies: str,
               fails: str, angle: str, team: str | None = None, book: str = "sleeper", stake: float = 1.0,
               season: int, week: int, now: dt.datetime | None = None, assumption=None,
               over_board=None, over_scenario=None, pays_if: str | None = None,
               view=None, line_assumes=None) -> dict:
    """One journal row, validated. Raises ValueError with a plain reason. view / line_assumes: the volume
    view behind the bet and the workload the line assumes (parse_view, DECISIONS #226)."""
    mk = MARKETS.get(" ".join(str(market).lower().replace("-", " ").split()), MARKETS.get(str(market).lower()))
    if mk is None:
        raise ValueError(f"unknown market '{market}' (catches, rec_yds, rush_yds, pass_yds, td)")
    side_ = str(side).lower()
    if mk == "player_anytime_td":
        if side_ not in ("yes", "no"):
            raise ValueError("an anytime TD bet is 'yes' or 'no'")
        line = None
    else:
        if side_ not in ("over", "under"):
            raise ValueError("a yardage or catches bet is 'over' or 'under'")
        if line is None or str(line).strip() == "":
            raise ValueError("a yardage or catches bet needs its line, e.g. 4.5")
        line = float(line)
    price = int(price)
    if abs(price) < 100:
        raise ValueError(f"price {price} is not American odds (e.g. -125 or +110)")
    for name, val in (("change", change), ("implies", implies), ("fails", fails)):
        if not str(val or "").strip():
            raise ValueError(f"--{name} is required: a bet that cannot state it is not logged")
    angle_ = str(angle or "").strip().lower()
    if angle_ not in ANGLES:
        raise ValueError(f"--angle is required, one of {', '.join(ANGLES)} (chosen now, never after the game)")
    if stake <= 0:
        raise ValueError("stake must be positive (units)")
    # YOUR SCENARIO (DECISIONS #154): the assumption and the chances it gave, so
    # the journal can later say whether your adjustments beat the board's number.
    # The table shows Over chances; the bet's own side is derived here (a push
    # on a whole line is ignored, which moves it by a point at most).
    assumption = [a.strip() for a in (assumption or []) if str(a).strip()]
    ob, osc = _chance(over_board, "over-board"), _chance(over_scenario, "over-scenario")
    if not assumption and (osc is not None or ob is not None or (pays_if or "").strip()):
        raise ValueError("--over-board, --over-scenario and --pays-if come from a scenario run: "
                         "add the --assumption they came from")
    if assumption:
        _check_rules(assumption)
    if mk == "player_anytime_td" and (assumption or osc is not None):
        raise ValueError("touchdowns are not adjusted by a scenario (DECISIONS #153)")
    side_p = (lambda o: None if o is None else (o if side_ == "over" else 1 - o))
    scen = {}
    if assumption:
        scen = {"assumption": "; ".join(assumption), "p_board": side_p(ob), "p_scenario": side_p(osc),
                "pays_if": (pays_if or "").strip() or None}
    vol = parse_view(view, line_assumes, VOLUME_UNIT.get(mk))
    now = now or dt.datetime.now(dt.timezone.utc)
    return {"id": uuid.uuid4().hex[:10], "logged_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "season": int(season), "week": int(week), "player": player.strip(),
            "team": (team or "").upper() or None, "market": mk, "side": side_, "line": line, "price": price,
            "book": book, "stake": float(stake), "change": change.strip(), "implies": implies.strip(),
            "fails": fails.strip(), "angle": angle_, "status": "open", **scen, **vol}


def grade(season: int, stats=None, now: dt.datetime | None = None) -> dict:
    """Grade every open bet whose week has published stats, with settle's own
    stat file, name join and win/push rules. Returns counts."""
    import settle
    rows = read(season)
    counts = {"graded": 0, "void": 0, "check": 0, "unjoined": 0, "unplayed": 0, "open_left": 0}
    if not any(r.get("status") == "open" for r in rows):
        return counts      # nothing to grade: no download, no file written
    if stats is None:
        stats = settle.load_stats(season, HERE / ".cache")
    now = now or dt.datetime.now(dt.timezone.utc)
    for r in rows:
        if r.get("status") != "open":
            continue
        wk = stats[stats["week"] == int(r["week"])]
        if wk.empty:
            counts["unplayed"] += 1
            continue
        nm = settle.norm_name(r["player"])
        team = r.get("team")
        hit = None
        if team:
            m = wk[(wk["team"] == team) & (wk["_name"] == nm)]
            if m.empty:
                m = wk[(wk["team"] == team) & (wk["_loose"] == settle.loose_key(r["player"]))]
            hit = m.iloc[0] if len(m) else None
        if hit is None:
            m = wk[wk["_name"] == nm]
            hit = m.iloc[0] if len(m) == 1 else None
        if hit is None:
            # Absent from the week's stats. nflverse's weekly file has no row for a
            # player who did not play AND none for one who played and recorded
            # nothing -- the book voids the first and pays the second at 0. Never
            # guess: a known name goes to 'check' for `journal resolve`; an
            # unknown one stays open.
            if (stats["_name"] == nm).any():
                r.update(status="check", result="not in the week's stats: did he play?")
                counts["check"] += 1
            else:
                counts["unjoined"] += 1
            continue
        actual = float(hit[settle.MARKET_STAT[r["market"]]])
        if r.get("volume_unit") and r["volume_unit"] in hit and hit[r["volume_unit"]] == hit[r["volume_unit"]]:
            r["actual_volume"] = float(hit[r["volume_unit"]])      # his real targets / carries, for the read's grade
        result, won = settle.settle_row({"market": r["market"], "side": r["side"], "line": r["line"]}, actual)
        pnl = settle.american_pnl(r["price"], won) * float(r.get("stake", 1.0))
        r.update(status="graded" if won is not None else "void", result=result, actual=actual, won=won,
                 pnl_per_100=round(pnl, 2), graded_at_utc=now.strftime("%Y-%m-%dT%H:%M:%SZ"))
        counts["graded" if won is not None else "void"] += 1
    counts["open_left"] = sum(1 for r in rows if r.get("status") == "open")
    write(season, rows)
    counts["late_lines"] = add_late_lines(season)
    return counts


def resolve(season: int, bet_id: str, *, actual: float | None = None, void: bool = False,
            now: dt.datetime | None = None) -> dict:
    """Settle one bet by hand: `actual` (he played; his real stat, 0 included)
    or `void` (he did not play). Returns the updated row."""
    import settle
    if (actual is None) == (not void):
        raise ValueError("give exactly one of --actual or --void")
    rows = read(season)
    hit = [r for r in rows if r["id"] == bet_id]
    if not hit:
        raise ValueError(f"no bet {bet_id} in the {season} journal")
    r = hit[0]
    now = now or dt.datetime.now(dt.timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    if void:
        r.update(status="void", result="dnp", actual=None, won=None, pnl_per_100=0.0, graded_at_utc=stamp)
    else:
        result, won = settle.settle_row({"market": r["market"], "side": r["side"], "line": r["line"]}, float(actual))
        pnl = settle.american_pnl(r["price"], won) * float(r.get("stake", 1.0))
        r.update(status="graded" if won is not None else "void", result=result, actual=float(actual), won=won,
                 pnl_per_100=round(pnl, 2), graded_at_utc=stamp)
    write(season, rows)
    return r


def implied(price: int) -> float:
    """The raw implied chance of an American price (vig included)."""
    return abs(price) / (abs(price) + 100) if price < 0 else 100 / (price + 100)


def late_line(bet: dict, archive: list[dict]) -> dict | None:
    """The last Sleeper quote the capture logged before kickoff for this bet's
    player, market and side (DECISIONS #148). Not the true close -- a capture
    inside the final hour needs speed, which is off -- but the latest line the
    record holds, usually a few hours out."""
    import settle
    nm = settle.norm_name(bet["player"])
    # the archive labels anytime-TD quotes Yes / No, yardage quotes Over / Under
    side = {"over": "Over", "under": "Under", "yes": "Yes", "no": "No"}[bet["side"]]
    best = None
    for q in archive:
        if (q.get("bookmaker") != "sleeper" or q.get("market") != bet["market"]
                or q.get("outcome") != side or settle.norm_name(str(q.get("player", ""))) != nm):
            continue
        if q.get("season") != bet["season"] or int(q.get("week") or -1) != int(bet["week"]):
            continue
        if q.get("commence_time") and q.get("retrieved_at_utc") and \
                q["retrieved_at_utc"] > q["commence_time"].replace("+00:00", "Z"):
            continue
        if best is None or q["retrieved_at_utc"] > best["retrieved_at_utc"]:
            best = q
    if best is None:
        return None
    out = {"late_line": best.get("point"), "late_price": best.get("price_american"),
           "late_at_utc": best.get("retrieved_at_utc")}
    if bet.get("line") is None and best.get("price_american") is not None:
        # anytime TD: no line, so the price is the whole value (late price costs more = value)
        out["clv_points"] = 0.0
        out["clv_price"] = round(implied(int(best["price_american"])) - implied(int(bet["price"])), 4)
    elif bet.get("line") is not None and best.get("point") is not None:
        # positive = the number moved your way: an Over bought below the late
        # line, an Under bought above it
        mv = float(best["point"]) - float(bet["line"])
        out["clv_points"] = round(mv if side == "Over" else -mv, 2)
        if mv == 0 and best.get("price_american") is not None:
            # same line: the late price for your side costs more = you got value
            out["clv_price"] = round(implied(int(best["price_american"])) - implied(int(bet["price"])), 4)
    return out


def read_archive(season: int) -> list[dict]:
    import persist
    p = persist.lines_path(season)
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return [json.loads(ln) for ln in fh if ln.strip()]


def add_late_lines(season: int, archive: list[dict] | None = None) -> int:
    """Stamp the late line on every bet that has none yet; returns how many."""
    rows = read(season)
    archive = read_archive(season) if archive is None else archive
    n = 0
    for r in rows:
        if r.get("late_line") is not None:
            continue
        ll = late_line(r, archive)
        if ll:
            r.update(ll)
            n += 1
    if n:
        write(season, rows)
    return n


def breakeven(price: int) -> float:
    """The win rate a price needs to break even."""
    return abs(price) / (abs(price) + 100) if price < 0 else 100 / (price + 100)


def leg_price(stake: float, payout: float, n: int) -> int:
    """The per-leg American price of an all-or-nothing entry: the n-th root of
    its total return (DECISIONS #159). $5 to win $100 total on 5 legs is 20x,
    1.82x a leg, about -122 -- each leg needs about 54.9% if they are
    independent."""
    if stake <= 0 or payout <= stake or n < 1:
        raise ValueError("an entry needs a positive stake, a total payout above it, and at least one leg")
    m = (payout / stake) ** (1.0 / n)
    return int(round((m - 1) * 100)) if m >= 2 else int(round(-100 / (m - 1)))


def make_power_play(legs, *, stake: float, payout: float, angle: str, why: str, season: int, week: int,
                    after_kickoff: bool = False, now: dt.datetime | None = None) -> list[dict]:
    """One row per leg of a Power Play, sharing an entry id. legs: list of
    (player, market, side, line, team[, angle[, extras]]); extras {view, line_assumes} is the leg's
    volume view (DECISIONS #226). Each leg is priced at the entry's per-leg price so the scorecard can
    grade legs; the entry itself wins only if every leg does."""
    if not str(why or "").strip():
        raise ValueError("--why is required: the entry's reason in a sentence")
    if len(legs) < 2:
        raise ValueError("a Power Play has at least two legs")
    price = leg_price(stake, payout, len(legs))
    eid = "pp" + uuid.uuid4().hex[:8]
    rows = []
    for leg in legs:
        player, market, side, line, team = (list(leg) + [None] * 5)[:5]
        leg_angle = (leg[5] if len(leg) > 5 and leg[5] else angle)
        extra = (leg[6] if len(leg) > 6 and leg[6] else {})
        r = make_entry(player, market, side, line, price, change=why, implies="(entry leg)",
                       fails="any leg misses: the whole entry loses", angle=leg_angle, team=team,
                       stake=1.0, season=season, week=week, now=now,     # a leg is one unit; the dollars are the entry's
                       view=extra.get("view"), line_assumes=extra.get("line_assumes"))
        r.update(entry_id=eid, entry_legs=len(legs), entry_stake=float(stake), entry_payout=float(payout),
                 after_kickoff=bool(after_kickoff))
        rows.append(r)
    return rows


def entries_table(rows: list[dict]) -> list[str]:
    """Power Plays as entries: all-or-nothing, at the real payout."""
    ents = {}
    for r in rows:
        if r.get("entry_id"):
            ents.setdefault(r["entry_id"], []).append(r)
    if not ents:
        return []
    out = ["**Entries** (Sleeper Power Plays: every leg must hit):", "",
           "| Logged | Legs | Stake | Pays (total) | Legs won / graded | Result | Net |", "|---|---|---|---|---|---|---|"]
    for eid, legs in ents.items():
        st, pay = float(legs[0]["entry_stake"]), float(legs[0]["entry_payout"])
        graded = [x for x in legs if x.get("status") == "graded"]
        won = sum(1 for x in graded if x.get("won"))
        paid = legs[0].get("entry_paid")
        if paid is not None:                     # what Sleeper actually paid (a reduced entry, say)
            word = ("won" if paid > st else "refunded" if paid == st else "partly paid" if paid > 0 else "lost")
            res, net = f"{word} (as paid)", float(paid) - st
        elif any(x.get("status") == "graded" and not x.get("won") for x in legs):
            res, net = "lost", -st
        elif all(x.get("status") == "graded" and x.get("won") for x in legs):
            res, net = "won", pay - st
        elif any(x.get("status") in ("void", "check") for x in legs):
            res, net = ("check: a leg was dropped (Sleeper 'Reboot' cuts the entry to fewer picks) or needs a "
                        "box score -- record the payout with `journal entry-paid`"), None
        else:
            res, net = "open", None
        late = " (after kickoff)" if legs[0].get("after_kickoff") else ""
        names = ", ".join(f"{x['player']} {x['side']}" for x in legs)
        out.append(f"| week {legs[0]['week']}{late} | {names} | ${st:g} | ${pay:g} | {won} / {len(graded)} | {res} | "
                   + ("—" if net is None else f"{net:+.2f}") + " |")
    return out + ["", "Entries logged after kickoff are kept but are not clean pre-game decisions; the "
                      "legs are still graded one by one on the scorecard.", ""]


def entry_paid(season: int, entry_id: str, paid: float) -> int:
    """Record what Sleeper actually paid an entry (0 when it lost). A dropped leg
    ('Reboot') cuts a Power Play to fewer picks at a smaller multiple, which only
    the app knows; this settles the entry at the real amount. Returns legs updated."""
    if paid < 0:
        raise ValueError("--paid is what the entry returned, 0 or more")
    rows = read(season)
    n = 0
    for r in rows:
        if r.get("entry_id") == entry_id:
            r["entry_paid"] = float(paid)
            n += 1
    if not n:
        raise ValueError(f"no entry {entry_id} in the {season} journal")
    write(season, rows)
    return n


def entry_void(season: int, entry_id: str, player: str, now: dt.datetime | None = None) -> dict:
    """Void the leg Sleeper dropped ('Reboot') by entry id and player name, the
    two things the user can see in the app. Returns the voided leg."""
    import settle
    rows = read(season)
    want = settle.norm_name(player)
    hit = [r for r in rows if r.get("entry_id") == entry_id and settle.norm_name(r["player"]) == want]
    if not hit:
        raise ValueError(f"no leg for {player} in entry {entry_id}")
    stamp = (now or dt.datetime.now(dt.timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    hit[0].update(status="void", result="dropped by Sleeper (Reboot)", actual=None, won=None, pnl_per_100=0.0,
                  graded_at_utc=stamp)
    write(season, rows)
    return hit[0]


def scenario_table(rows: list[dict]) -> list[str]:
    """Bets logged from a scenario run: what the board said, what your scenario
    said, and what happened. If your adjustments carry information, the win
    rate tracks your number more closely than the board's."""
    sc = [r for r in rows if r.get("assumption") and r.get("p_scenario") is not None]
    if not sc:
        return []
    done = [r for r in sc if r.get("status") == "graded"]
    def mean(rs, k):
        v = [float(r[k]) for r in rs if r.get(k) is not None]
        return "—" if not v else f"{sum(v) / len(v):.0%}"
    lv = [r for r in sc if r.get("clv_points") is not None]
    beat = sum(1 for r in lv if r["clv_points"] > 0 or (r["clv_points"] == 0 and (r.get("clv_price") or 0) > 0))
    won = sum(1 for r in done if r.get("won"))
    out = ["**Your scenarios** (bets logged from a `--assume` run; chances are for the side you bet):", "",
           "| Bets | Graded | The board said | Your scenario said | Won | Beat the late line |",
           "|---|---|---|---|---|---|",
           f"| {len(sc)} | {len(done)} | {mean(sc, 'p_board')} | {mean(sc, 'p_scenario')} | "
           + (f"{won / len(done):.0%} ({won} of {len(done)})" if done else "—")
           + f" | {f'{beat} of {len(lv)}' if lv else '—'} |", "",
           "If your adjustments add information, the win rate lands nearer your number than the board's; "
           "it takes about 100 graded bets to tell. The late-line column shows sooner.", ""]
    return out


def volume_read_table(rows: list[dict]) -> list[str]:
    """YOUR VOLUME READS AGAINST THE LINE (DECISIONS #225, #226): the method rests on the user's view of
    the workload being better informed than the market's, and this is where that gets measured. Per
    graded bet with a view, the line's assumed workload and the actual: whose number landed nearer,
    and whether the view pointed the right way from the line."""
    rs = [r for r in rows if r.get("view_likely") is not None and r.get("line_volume") is not None
          and r.get("actual_volume") is not None]
    if not rs:
        return []
    mine = [abs(r["actual_volume"] - r["view_likely"]) for r in rs]
    line = [abs(r["actual_volume"] - r["line_volume"]) for r in rs]
    closer = sum(1 for a, b in zip(mine, line) if a < b)
    pointed = [r for r in rs if r["view_likely"] != r["line_volume"]]
    # right way = the actual moved off the line in the view's direction; landing on the line is not right
    right = sum(1 for r in pointed if (r["actual_volume"] - r["line_volume"]) * (r["view_likely"] - r["line_volume"]) > 0)
    inside = sum(1 for r in rs if r["view_low"] <= r["actual_volume"] <= r["view_high"])
    out = ["**Your volume reads against the line** (graded bets that logged a view; targets or carries):", "",
           "| Reads | Yours nearer the actual | Your miss / the line's (average) | Pointed the right way from the line | "
           "Actual inside your low-high |", "|---|---|---|---|---|",
           f"| {len(rs)} | {closer} of {len(rs)} | {sum(mine) / len(rs):.1f} / {sum(line) / len(rs):.1f} | "
           + (f"{right} of {len(pointed)}" if pointed else "—") + f" | {inside} of {len(rs)} |", "",
           "The method pays only if your reads beat the line's: nearer the actual more often than not, and "
           "pointing the right way. A few dozen reads say little; read it with the late-line column.", ""]
    return out


def angle_table(rows: list[dict]) -> list[str]:
    """The record split by the angle chosen at log time: which kind of story
    gets the better number, and which wins. Small samples per angle say even
    less than the whole, and the table says so."""
    if not rows:
        return []
    out = ["**By angle** (chosen when the bet was logged):", "",
           "| Angle | Bets | Graded | Won | Win rate | Break-even | Net per $100 | Beat the late line |",
           "|---|---|---|---|---|---|---|---|"]
    order = list(ANGLES) + sorted({r.get("angle") or "untagged" for r in rows} - set(ANGLES))
    for a in order:
        rs = [r for r in rows if (r.get("angle") or "untagged") == a]
        if not rs:
            continue
        done = [r for r in rs if r.get("status") == "graded"]
        settled = [r for r in rs if r.get("status") in ("graded", "void")]
        stake = sum(float(r.get("stake", 1.0)) for r in done)
        wins = sum(1 for r in done if r.get("won"))
        lv = [r for r in rs if r.get("clv_points") is not None]
        beat = sum(1 for r in lv if r["clv_points"] > 0 or (r["clv_points"] == 0 and (r.get("clv_price") or 0) > 0))
        out.append(f"| {ANGLES.get(a, a)} | {len(rs)} | {len(done)} | {wins} | "
                   + (f"{wins / len(done):.0%} | {sum(breakeven(int(r['price'])) for r in done) / len(done):.0%} | "
                      f"{sum(float(r.get('pnl_per_100', 0.0)) for r in settled) / stake:+.1f}" if done and stake
                      else "— | — | —")
                   + f" | {f'{beat} of {len(lv)}' if lv else '—'} |")
    return out + ["", "Each angle is its own small sample: read the late-line column first.", ""]


def summary_md(season: int) -> list[str]:
    """The scorecard's journal section."""
    rows = read(season)
    out = ["## Bet journal", ""]
    if not rows:
        return out + ["No bets logged yet. Log one with `python props/journal.py add ...` (all four "
                      "checklist answers required); it is graded here every Tuesday.", ""]
    done = [r for r in rows if r.get("status") == "graded"]
    n_open = sum(1 for r in rows if r.get("status") == "open")
    n_void = sum(1 for r in rows if r.get("status") == "void")
    n_check = sum(1 for r in rows if r.get("status") == "check")
    out.append(f"{len(rows)} bets logged: {len(done)} graded, {n_void} void (push or did not play), "
               f"{n_open} open" + (f", {n_check} to check (`journal resolve`)" if n_check else "")
               + ". Kept apart from the model's record: these are the user's handicapped bets.")
    out.append("")
    lv = [r for r in rows if r.get("clv_points") is not None]
    if lv:
        beat = sum(1 for r in lv if r["clv_points"] > 0 or (r["clv_points"] == 0 and (r.get("clv_price") or 0) > 0))
        tied = sum(1 for r in lv if r["clv_points"] == 0 and not r.get("clv_price"))
        out += ["**Late-line value, the first number to watch:** "
                f"{beat} of {len(lv)} bets got a better number than the last line Sleeper showed before kickoff "
                f"({beat / len(lv):.0%}; {tied} tied); mean move your way {sum(r['clv_points'] for r in lv) / len(lv):+.2f} "
                "points. Beating the late line shows up in about 100-200 bets; the win rate needs far more. It is the "
                "last line the capture logged (usually a few hours out), not the true close.", ""]
    if done:
        wins = sum(1 for r in done if r.get("won"))
        stake = sum(float(r.get("stake", 1.0)) for r in done)
        net = sum(float(r.get("pnl_per_100", 0.0)) for r in rows if r.get("status") in ("graded", "void"))
        be = sum(breakeven(int(r["price"])) for r in done) / len(done)
        out += ["| Bets | Won | Win rate | Break-even at these prices | Net per $100 staked |", "|---|---|---|---|---|",
                f"| {len(done)} | {wins} | {wins / len(done):.0%} | {be:.0%} | {net / stake:+.1f} |", ""]
        out.append("A few dozen bets say little; about 100 is where the win rate starts to separate from luck.")
        out.append("")
    out += angle_table(rows)
    out += volume_read_table(rows)
    out += scenario_table(rows)
    out += entries_table(rows)
    out += ["| Week | Player | Bet | Angle | Price | Late line | Result | Net | The change | Your scenario |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["week"], r["logged_at_utc"])):
        bet = (f"{r['side']} {LABEL.get(r['market'], r['market'])}" if r.get("line") is None
               else f"{r['side']} {r['line']:g} {LABEL.get(r['market'], r['market'])}")
        res = r.get("status") if r.get("status") != "graded" else ("won" if r.get("won") else "lost")
        net = "" if r.get("pnl_per_100") is None else f"{float(r['pnl_per_100']):+.0f}"
        late = ("—" if r.get("late_line") is None else
                f"{r['late_line']:g} {int(r['late_price']):+d} ({r.get('clv_points', 0):+g})")
        ang = ANGLES.get(r.get("angle"), r.get("angle") or "untagged")
        scn = "—"
        if r.get("assumption"):
            ch = ("" if r.get("p_scenario") is None else
                  f" ({r['p_scenario']:.0%} vs board {r['p_board']:.0%})" if r.get("p_board") is not None
                  else f" ({r['p_scenario']:.0%})")
            scn = f"{r['assumption']}{ch}"
        out.append(f"| {r['week']} | {r['player']} | {bet} | {ang} | {int(r['price']):+d} | {late} | {res} | {net} | "
                   f"{r['change']} | {scn} |")
    return out + [""]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", help="log a bet with its four checklist answers")
    a.add_argument("player"); a.add_argument("market"); a.add_argument("side")
    a.add_argument("line", nargs="?", default=None, help="omit for an anytime TD")
    a.add_argument("price", type=int)
    a.add_argument("--team"); a.add_argument("--book", default="sleeper")
    a.add_argument("--stake", type=float, default=1.0, help="units (default 1)")
    a.add_argument("--angle", required=True, choices=list(ANGLES),
                   help="the kind of story: injury (redistribution), role (change), return (teammate back), other")
    a.add_argument("--change", required=True, help="the verified change in his duties")
    a.add_argument("--implies", required=True, help="the workload the line implies vs what he gets")
    a.add_argument("--fails", required=True, help="how the bet fails")
    a.add_argument("--season", type=int, default=None); a.add_argument("--week", type=int, default=None)
    a.add_argument("--assumption", action="append", default=[],
                   help="from a scenario run: the --assume rule(s) behind this bet (repeatable)")
    a.add_argument("--over-board", default=None, help="the board's Over chance from the scenario table (e.g. 37%%)")
    a.add_argument("--over-scenario", default=None, help="your scenario's Over chance (e.g. 70%%)")
    a.add_argument("--pays-if", default=None, help="the break-even workload cell, as the board shows it")
    a.add_argument("--view", default=None,
                   help="your volume view: low/likely/high or one number, in targets or carries; signed values "
                        "('+2/+4/+6') are relative to --line-assumes")
    a.add_argument("--line-assumes", default=None, type=float,
                   help="the card's 'The line assumes' workload for this line")
    pp = sub.add_parser("entry", help="log a Sleeper Power Play: all-or-nothing legs at the real payout")
    pp.add_argument("--stake", type=float, required=True, help="dollars staked on the entry")
    pp.add_argument("--payout", type=float, required=True, help="the TOTAL the entry pays if every leg hits")
    pp.add_argument("--leg", action="append", required=True,
                    help="'Player|market|side|line|TEAM[|angle][|view=+2/+4/+6][|assumes=15.3]' (line empty for an "
                         "anytime TD), repeatable")
    pp.add_argument("--angle", required=True, choices=list(ANGLES), help="the entry's story (a leg can override)")
    pp.add_argument("--why", required=True, help="the entry's reason in a sentence")
    pp.add_argument("--after-kickoff", action="store_true", help="logged after a leg's game started")
    pp.add_argument("--season", type=int, default=None); pp.add_argument("--week", type=int, default=None)
    ev = sub.add_parser("entry-void", help="void the leg Sleeper dropped ('Reboot') by entry id and player")
    ev.add_argument("entry_id"); ev.add_argument("--player", required=True)
    ev.add_argument("--season", type=int, default=None)
    ep = sub.add_parser("entry-paid", help="record what Sleeper actually paid an entry (0 if it lost)")
    ep.add_argument("entry_id"); ep.add_argument("--paid", type=float, required=True)
    ep.add_argument("--season", type=int, default=None)
    ls = sub.add_parser("list"); ls.add_argument("--season", type=int, default=None)
    ls.add_argument("--open", action="store_true")
    g = sub.add_parser("grade"); g.add_argument("--season", type=int, required=True)
    sm = sub.add_parser("summary"); sm.add_argument("--season", type=int, default=None)
    rv = sub.add_parser("resolve", help="settle a 'check' bet by hand from the box score")
    rv.add_argument("id"); rv.add_argument("--season", type=int, default=None)
    rv.add_argument("--actual", type=float, default=None, help="his real stat (0 if he played and got none)")
    rv.add_argument("--void", action="store_true", help="he did not play")
    args = ap.parse_args(argv)
    season = getattr(args, "season", None) or dt.datetime.now(dt.timezone.utc).year
    if args.cmd == "add":
        line = args.line
        if line is not None and MARKETS.get(args.market.lower()) == "player_anytime_td":
            raise SystemExit("an anytime TD bet has no line: journal add PLAYER td yes PRICE ...")
        try:
            e = make_entry(args.player, args.market, args.side, line, args.price, change=args.change,
                           implies=args.implies, fails=args.fails, angle=args.angle, assumption=args.assumption,
                           over_board=args.over_board, over_scenario=args.over_scenario, pays_if=args.pays_if,
                           view=args.view, line_assumes=args.line_assumes,
                           team=args.team, book=args.book,
                           stake=args.stake, season=season,
                           week=args.week or current_week(season))
        except ValueError as exc:
            print(f"not logged: {exc}", file=sys.stderr)
            return 2
        rows = read(season) + [e]
        write(season, rows)
        ln = "" if e["line"] is None else f"{e['line']:g} "
        print(f"logged {e['id']}: week {e['week']} {e['player']} {e['side']} "
              f"{ln}{LABEL[e['market']]} {e['price']:+d} -> {journal_path(season)}")
        return 0
    if args.cmd == "entry":
        legs = []
        for spec in args.leg:
            parts = [x.strip() for x in spec.split("|")]
            # the leg's volume view rides as key=value fields after the positional ones (DECISIONS #226)
            extra = {}
            while parts and "=" in parts[-1]:
                k, _, v = parts.pop().partition("=")
                k = {"view": "view", "assumes": "line_assumes"}.get(k.strip().lower())
                if k is None or k in extra:
                    print(f"not logged: leg '{spec}' -- the extra fields are view=... and assumes=..., once each",
                          file=sys.stderr)
                    return 2
                extra[k] = v.strip()
            if any("=" in x for x in parts):
                print(f"not logged: leg '{spec}' -- view=... and assumes=... go last", file=sys.stderr)
                return 2
            if len(parts) < 4 or parts[5:] and parts[5] not in ANGLES:
                print(f"not logged: leg '{spec}' -- write it as "
                      "'Player|market|side|line[|TEAM[|angle]][|view=...][|assumes=...]'", file=sys.stderr)
                return 2
            parts += [""] * (6 - len(parts))
            legs.append((parts[0], parts[1], parts[2], parts[3] or None, parts[4] or None, parts[5] or None, extra))
        try:
            rows_ = make_power_play(legs, stake=args.stake, payout=args.payout, angle=args.angle, why=args.why,
                                    season=season, week=args.week or current_week(season),
                                    after_kickoff=args.after_kickoff)
        except ValueError as exc:
            print(f"not logged: {exc}", file=sys.stderr)
            return 2
        write(season, read(season) + rows_)
        print(f"logged entry {rows_[0]['entry_id']}: {len(rows_)} legs, ${args.stake:g} to ${args.payout:g}, "
              f"each leg at {rows_[0]['price']:+d} -> {journal_path(season)}")
        return 0
    if args.cmd == "entry-void":
        try:
            r = entry_void(season, args.entry_id, args.player)
        except ValueError as exc:
            print(f"not voided: {exc}", file=sys.stderr)
            return 2
        print(f"entry {args.entry_id}: {r['player']} voided (dropped by Sleeper)")
        return 0
    if args.cmd == "entry-paid":
        try:
            n = entry_paid(season, args.entry_id, args.paid)
        except ValueError as exc:
            print(f"not recorded: {exc}", file=sys.stderr)
            return 2
        print(f"entry {args.entry_id}: paid ${args.paid:g} ({n} legs)")
        return 0
    if args.cmd == "list":
        for r in read(season):
            if args.open and r.get("status") != "open":
                continue
            print(json.dumps(r, sort_keys=True))
        return 0
    if args.cmd == "resolve":
        try:
            r = resolve(season, args.id, actual=args.actual, void=args.void)
        except ValueError as exc:
            print(f"not resolved: {exc}", file=sys.stderr)
            return 2
        print(f"{r['id']}: {r['status']} ({r.get('result')}), net {r.get('pnl_per_100')}")
        return 0
    if args.cmd == "grade":
        c = grade(season)
        print(f"journal {season}: " + ", ".join(f"{k} {v}" for k, v in c.items()))
        return 0
    print("\n".join(summary_md(season)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
