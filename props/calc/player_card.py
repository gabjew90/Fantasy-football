"""One card per player for a game read (the user, 2026-10-26; DECISIONS #249): every posted line of his
and both sides in one card, in the four parts -- 1 the lines side by side, 2 this season once, 3 the
matchup (in the game header), 4 does it hold up. Nothing is computed here: every number comes from the
same pieces as the leg card (card.compute, card.line_part, card._parts, card.season_read,
card.holds_up), so the two cannot disagree. The leg card stays for `leg`, `entry` and the screen's rows.
Display only."""

from __future__ import annotations

import re

from . import card as C

ORDER = ["rush_yds", "receptions", "rec_yds", "pass_yds"]
SHORT = C.SHORT_NAME
GROUP = {"rush_yds": "rush", "receptions": "rec", "rec_yds": "rec", "pass_yds": "pass"}
# per group: the season table's columns (header, player_games column) and its rate (header, stat, workload)
COLS = {"rush": [("Carries", "carries"), ("Rush yds", "rush_yds")],
        "rec": [("Targets", "targets"), ("Catches", "receptions"), ("Rec yds", "rec_yds")],
        "pass": [("Comp", "completions"), ("Pass yds", "pass_yds")]}
RATE = {"rush": ("Yds/carry", "rush_yds", "carries", "yards a carry"),
        "rec": ("Yds/target", "rec_yds", "targets", "yards a target"),
        "pass": ("Yds/comp", "pass_yds", "completions", "yards a completion")}
WORDS = {"rush": ("carries", "rushing yards"), "rec": ("targets", "catches", "receiving yards"),
         "pass": ("completions", "passing yards")}
CY_NOTE = "Yards can come from one long catch; catches cannot (a general point)."
NAME = {"rush": "Rushing", "rec": "Receiving", "pass": "Passing"}


def _label(c: dict) -> str:
    return f"{SHORT[c['market']]} {c['line']:g}"


def _row(cells) -> str:
    return "| " + " | ".join(C._cell(x) for x in cells) + " |"


def _counts(S: dict | None, side: str) -> str:
    """'4 of 6' (and '; 2 of 3 without weeks 2 and 5'): how often he went over or under the line."""
    if S is None:
        return "not available"
    a, cl = S["all"], S["clean"]
    text = f"{S[side]} of {a['n']}"
    if S["special_weeks"] and cl:
        text += f"; {S[side + '_clean']} of {cl['n']} {C._without_special(S)}"
    return text


def _small(items: list[dict], rows: list[tuple]) -> list[str]:
    """One short table: a column per line, a row per (label, function of the item)."""
    out = [_row([""] + [_label(g["c"]) for g in items]), "|" + "---|" * (len(items) + 1)]
    return out + [_row([lab] + [fn(g) for g in items]) for lab, fn in rows] + [""]


def lines_part(items: list[dict]) -> list[str]:
    """Part 1 in three short tables, one question each (the user, 2026-10-26: "readability is the
    priority"): what the book says, what each side needs, and his history against it."""
    reads = {id(g): C.season_read(g["pl"], g["c"]) for g in items}
    S0 = next((S for S in reads.values() if S), None)
    scope = C._scope(S0) if S0 else "this season"
    o = {id(g): dict(C.line_part(g["pl"], g["c"], "over")) for g in items}
    many = lambda g: C.SHOW[g["c"]["market"]][1][1]                  # noqa: E731

    def his(g):
        v = next((x for k, x in o[id(g)].items() if k.startswith("His ")), "not available")
        return v.replace(" a game", f" {many(g)}", 1)
    out = ["What the book says", ""]
    out += _small(items, [
        ("Prices", lambda g: f"Over {C.odds.fmt_american(C.price(g['c'], 'over'))} / "
                             f"Under {C.odds.fmt_american(C.price(g['c'], 'under'))}"),
        ("Its split, margin removed", lambda g: o[id(g)]["The book's split at this line, margin removed"]
         .replace(" (the book's numbers)", "")),
        ("Where its 50/50 sits (our math)", lambda g: o[id(g)]["Where the book's 50/50 sits (our math)"]),
        ("Workload it expects (our math)", lambda g: o[id(g)]["Workload the prices imply (our math)"])])
    out += ["What each side needs", ""]
    out += _small(items, [("Over", lambda g: C._bar_cell(g["c"], "over")),
                          ("Under", lambda g: C._bar_cell(g["c"], "under"))])
    out += ["His history", ""]
    last4 = [("Last-4 average", lambda g: f"{C.d1(g['c']['usual'])} {many(g)}" if g["c"]["usual"] is not None
               else "not enough games")] if S0 is None or S0["scope"] == "season" else []   # else the same games
    out += _small(items, last4 + [
        (f"Average {scope}", his),
        (f"Went over the line ({scope})", lambda g: _counts(reads[id(g)], "over"))])
    return out              # no test-results block (the user, 2026-10-26: "don't need this section")


def season_part(items: list[dict]) -> tuple[str, list[str]]:
    """Part 2: a table per stat group he is priced in (rushing, receiving, passing), the special games
    marked * and named under the tables, then each group's averages with and without them."""
    reads = [(g, C.season_read(g["pl"], g["c"])) for g in items]
    reads = [(g, S) for g, S in reads if S is not None]
    if reads:                                  # every line reads the same games; one that does not is left out
        n0 = len(reads[0][0]["pl"].perf)
        reads = [(g, S) for g, S in reads if len(S["rows"]) == n0]
    if not reads:
        return "**2 · This season**", [f"No games before week {items[0]['pl'].week}."]
    g0, S0 = reads[0]
    perf = g0["pl"].perf.reset_index(drop=True)
    season = g0["pl"].season
    groups = [x for x in ("rush", "rec", "pass") if any(GROUP[g["c"]["market"]] == x for g, _ in reads)]
    # each table stars the games its own lines count as special (a receiver out is special for his
    # catches, not his carries), so a table's "Without *" row matches its lines' parts 1 and 4
    gread = {x: next(S for g, S in reads if GROUP[g["c"]["market"]] == x) for x in groups}
    weeks, notes = [], []
    special = {x: [gread[x]["rows"][i]["special"] for i in range(len(perf))] for x in groups}
    like = {x: [gread[x]["rows"][i]["like"] for i in range(len(perf))] if gread[x]["tonight"] else None
            for x in groups}
    for i, (_, r) in enumerate(perf.iterrows()):
        why = []
        for x in groups:
            why += [n for n in gread[x]["rows"][i]["notes"] if n not in why]
        wk = f"Week {int(r['week'])}" if int(r["season"]) == season else f"{int(r['season'])} week {int(r['week'])}"
        weeks.append(wk)
        starred = [x for x in groups if special[x][i]]
        if why:
            only = (f" ({' and '.join(NAME[x].lower() for x in starred)} only)"
                    if starred and len(starred) < len(groups) else "")
            notes.append(f"{wk}{' *' if starred else ''}: {'; '.join(why)}{only}")
    out = []
    if S0["scope"] != "season":
        k = S0["n_season"]
        out += [f"Only {k} game{'' if k == 1 else 's'} this season, so these are his last {S0['all']['n']}"
                + (", back into last season." if S0["spans_seasons"] else "."), ""]
    for x in groups:
        head = ["Week", "Opp"] + [h for h, _ in COLS[x]] + [RATE[x][0], "Snaps"]
        out += [NAME[x], "", _row(head), "|" + "---|" * len(head)]
        for i, (_, r) in enumerate(perf.iterrows()):
            _, stat, work, _ = RATE[x]
            snap = r.get("snap_pct")
            out.append(_row([weeks[i].removeprefix("Week ") + (" *" if special[x][i] else ""), r.get("opp") or "-"]
                            + [C._num(float(r[col])) for _, col in COLS[x]]
                            + [C.d1(float(r[stat]) / float(r[work])) if float(r[work]) else "-",
                               f"{C.half_up(float(snap) * 100, '1'):.0f}%" if snap is not None and snap == snap else "-"]))
        out += _average_rows(x, perf, special[x], like[x], weeks) + [""]
    if notes:
        out += [C.notes_head(any(like[x] is not None for x in groups)), ""] + [f"- {n}" for n in notes] + [""]
    today = []
    for g, _ in reads:
        today += [x for x in g["pl"].today if x not in today]
    if today:
        out += ["Out today:", ""] + [f"- {x}" for x in today] + [""]
    title = "**2 · This season**" if S0["scope"] == "season" else "**2 · His last games**"
    return title, out


def _average_rows(group: str, perf, special: list[bool], like: list[bool] | None = None,
                  weeks: list[str] | None = None) -> list[str]:
    """The table's last rows: his average over every game, and the second average -- the games like
    tonight when some share an absence with tonight's (like), else the games without a star."""
    p = perf.reset_index(drop=True)
    _, stat, work, _ = RATE[group]

    def row(label, rows):
        n, tot = len(rows), float(rows[work].sum())
        return _row([label, ""] + [C.d1(float(rows[col].sum()) / n) for _, col in COLS[group]]
                    + [C.d1(float(rows[stat].sum()) / tot) if tot else "-", ""])
    out = [row(f"Average ({len(p)})", p)]
    if like is not None:
        if any(like):
            wk = [w.removeprefix("Week ") for w, x in zip(weeks or [], like) if x]
            label = f"Like tonight, wk {', '.join(wk)}" if wk else "Like tonight"
            out.append(row(f"{label} ({sum(like)})", p[like]))
        return out
    keep = [not x for x in special]
    if any(special) and any(keep):
        out.append(row(f"Without * ({sum(keep)})", p[keep]))
    return out


def rates_part(items: list[dict]) -> list[str]:
    """The leg cards' rate tables, one short table per line: the rate each side needs at his last-4
    workload beside his rates and what the opponent has allowed."""
    out = []
    for g in items:
        pl, c = g["pl"], g["c"]
        if c["usual"] is None:
            out += [f"{_label(c)}: no recent average.", ""]
            continue
        po, pu = C._parts(pl, c, "over"), C._parts(pl, c, "under")
        span = po["window"].split("(", 1)[1].rstrip(")")          # "16 games, 10 from last season"
        u = po["rate_long"]
        bare = lambda t: t.replace(f" {u}", "").replace(u, "")      # noqa: E731 -- the title names the unit
        out += [_row([f"{_label(c)} at {C.d1(c['usual'])} {po['many']}", C.RATE_TITLE[c["market"]]]), "|---|---|",
                _row(["Over needs", bare(po["need_text"])]),
                _row(["Under needs", bare(pu["need_text"])]),
                _row([f"His longer-run rate ({span})", bare(po["assumed_text"])]),
                _row(["This season", bare(po["season_rate"])]),
                _row(["Opponent has allowed", bare(C._opp_cell(g["shown"].get("opp_row"), u))]), ""]
    return out


def holds_part(items: list[dict]) -> list[str]:
    """Part 4 as one grid: a row per factor, a column per line (the same rows on every card)."""
    cols = []
    for g in items:
        sh = g["shown"]
        cols.append(C.holds_up(g["pl"], g["c"], "over", opp=sh["opp"], game_lines=sh.get("game_lines"),
                               opp_row=sh.get("opp_row"), grades=sh.get("grades"), qb_today=sh.get("qb_today", ""),
                               scoring=sh.get("scoring"), fixed_spread=g["c"]["script_spread"]))
    out = [_row(["What the card shows"] + [_label(g["c"]) for g in items]), "|" + "---|" * (len(items) + 1)]
    for i, f in enumerate(C.FACTORS):
        out.append(_row([f] + [C.grid_cell(col[i][1], col[i][2]) for col in cols]))
    return out + ["", C.HOLDS_NOTE]


def _short(cond: str) -> str:
    """The leg card's condition, shortened for a table cell: the comparison basis is said once below it."""
    cond = re.sub(r"^He needs ", "", cond)
    cond = cond.replace(" than his recent average", "").replace(" than his longer-run rate at his recent workload", "")
    cond = cond.replace(" than his longer-run rate", "").replace(" at his recent workload", "")
    cond = cond.replace("His recent workload and rate meet the bar, with ", "met, with ")
    cond = cond.replace("His recent workload clears the bar, with ", "met, with ")
    cond = cond.replace("His recent workload and rate both meet the bar.", "met")
    cond = cond.replace("His recent workload meets the bar.", "met")
    cond = cond.replace("His recent workload is there; he needs ", "workload met; needs ")
    cond = cond.replace("At his longer-run rate, he needs ", "at his longer-run rate, ")
    return cond.rstrip(".")


def needs_part(items: list[dict], sides: list[str]) -> list[str]:
    """What needs to be true, per line and side, in one short table."""
    out = [_row([""] + [sd.title() for sd in sides]), "|" + "---|" * (len(sides) + 1)]
    for g in items:
        cells = []
        for sd in sides:
            P = C._parts(g["pl"], g["c"], sd)
            cells.append(_short(C.condition(g["c"]["market"], sd, P["work_ask"], P["rate_ask"], P["reached"],
                                            len(P["rows"]), P["split"])) or "-")
        out.append(_row([_label(g["c"])] + cells))
    return out + ["", "Against his last-4 average workload and his longer-run rate."]


def render_md(items: list[dict], others: list[str], sides: list[str]) -> str:
    """items: build_card's results (ready, with pl, c, shown, md_footer) for one player, any order;
    others: the not-enough or no-quote lines' one-line reasons."""
    items = sorted(items, key=lambda g: ORDER.index(g["c"]["market"]))
    st = items[0]["stub"]
    out = [f"**{st['player']} · {st['team']}**", "", " · ".join(_label(g["c"]) for g in items), ""]
    checks = []
    for g in items:
        n = g["shown"].get("line_note")
        if n and n not in checks:
            checks.append(n)
    out += [f"Check first: {x}." for x in checks] + ([""] if checks else [])
    out += ["**1 · The lines**", ""] + lines_part(items)
    if {"receptions", "rec_yds"} <= {g["c"]["market"] for g in items}:
        out += [CY_NOTE, ""]
    out += [f"- {x}" for x in others] + ([""] if others else [])
    title, season = season_part(items)
    out += [title, ""] + season
    out += ["**Rates at his last-4 workload**", ""] + rates_part(items)
    out += ["Part 3, the matchup, is in the game header above.", ""]
    out += ["**4 · Does it hold up**", ""] + holds_part(items) + [""]
    out += ["What needs to be true", ""] + needs_part(items, sides) + [""]
    feet = []
    for g in items:
        f = g.get("md_footer")
        if f and f not in feet:
            feet.append(f)
    out += [f"_{f}_" for f in feet]
    return "\n".join(out).rstrip("\n")
