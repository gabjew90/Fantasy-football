"""Publish a game read from ONE run and ONE written reads file (DECISIONS #217, #218).

    python publish.py --run OUT/run_2026_wk05_TB_DAL.json --reads reads.json --out OUT
                      [--which qa,agent] [--release-tag T --release-hash H --release-source S]
                      [--check-only] [--no-ci]

The run file is what score_game.py writes beside its report (write_run_export): every card's
numbers, the team brief's tables as data, section 4's players, section 7's gaps, the sources. The
reads file is what chat writes, in the structure of the user's report guide
(docs/plans/2026-10-08-report-format-design.md; schema in resources/agent_guide.md): the opening
read, a narration per team section, the personnel rows, the assumptions and the handoff; and per
player the workload basis, the explanation, the role evidence, the matchup verdict, and per leg
the condition, the failure, the alternative, the volume x efficiency it needs and its cites.

THE CHECK RUNS FIRST (publish.check). A failed check renders nothing: the failures print (exit 3)
for chat to fix. Judgment -- whether a condition is plausible -- is not machine-checked; the QA
version leaves it to the reviewer. The renders are in publish_render.py. Informational only:
nothing here reads or moves a price.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
REPO_URL = "https://github.com/gabjew90/Fantasy-football"
READS_VERSION = 2

MARKET_ALIASES = {
    "receptions": "player_receptions", "catches": "player_receptions",
    "rec yds": "player_reception_yds", "receiving yards": "player_reception_yds",
    "rush yds": "player_rush_yds", "rushing yards": "player_rush_yds",
    "rush+rec yds": "player_rush_reception_yds", "rushing + receiving yards": "player_rush_reception_yds",
    "pass yds": "player_pass_yds", "passing yards": "player_pass_yds",
}
MARKET_WORDS = {"player_receptions": "receptions", "player_reception_yds": "receiving yards",
                "player_rush_yds": "rushing yards", "player_rush_reception_yds": "rushing + receiving yards",
                "player_pass_yds": "passing yards"}
MARKET_ORDER = ("player_pass_yds", "player_receptions", "player_reception_yds", "player_rush_yds",
                "player_rush_reception_yds")
# the guide's player sections: each player once, in his main market's section (user, 2026-10-08)
SECTIONS = ("Passing", "Receiving", "Rushing and combined yards")
SECTION_OF_POS = {"QB": "Passing", "WR": "Receiving", "TE": "Receiving", "RB": "Rushing and combined yards",
                  "FB": "Rushing and combined yards", "HB": "Rushing and combined yards"}
# row aliases: a cite's field -> (where, key); "row" is the leg's research row, "cells" its volume cells
ROW_ALIASES = {"market_p": ("row", "p_over_book"), "engine_p": ("row", "p_over_model"), "push": ("row", "p_push"),
               "price_over": ("row", "price_over"), "price_under": ("row", "price_under"),
               "median": ("row", "median"), "p10": ("row", "p10"), "p90": ("row", "p90"),
               "market_volume": ("row", "market_volume"), "market_catches": ("row", "market_catches"),
               "proj_volume": ("cells", "proj"), "need_rate": ("cells", "need_rate"),
               "need_out": ("cells", "need_out")}
# the Under's own side: the market's no-vig Under is 1 - its Over; the engine's Under excludes a push
UNDER_ALIASES = {"market_p_under": lambda row: None if row.get("p_over_book") is None else 1 - float(row["p_over_book"]),
                 "engine_p_under": lambda row: None if row.get("p_over_model") is None
                 else 1 - float(row["p_over_model"]) - float(row.get("p_push") or 0)}
# refused anywhere in a read: the board is a research sheet (DECISIONS #142); the market's chance is
# the best available estimate, never "the probability" (#215)
BANNED = [
    (re.compile(r"\b(best|top|strong|great|good|the|a|my) (play|bet|pick|value)s?\b", re.I), "pick language"),
    (re.compile(r"\blean(s|ing|ed)?\b", re.I), "a lean"),
    (re.compile(r"\bedges?\b", re.I), "an edge"),
    (re.compile(r"\b(\+?EV|expected value)\b"), "expected value"),
    (re.compile(r"\bkelly\b", re.I), "Kelly"),
    (re.compile(r"\bstakes?\b", re.I), "a stake"),
    (re.compile(r"\blocks?\b(?! in)", re.I), "a lock"),
    (re.compile(r"\b(value|smash|hammer|fade)\b", re.I), "pick language"),
    (re.compile(r"\bthe probability\b", re.I), "'the probability' (say the best available estimate)"),
    (re.compile(r"\bguarantee", re.I), "a guarantee"),
    (re.compile(r"\b(take|hit|pound|slam|love|like|bet|back|play|grab|ride) (the )?(over|under)s?\b", re.I),
     "telling the reader which side to take"),
    (re.compile(r"\b(i|we)('d| would| really)? (like|love)\b", re.I), "a preference stated as a pick"),
]
# the card's verdict words, by definition (the user, 2026-10-08): never chosen by the writer
VERDICTS = ("attainable", "requires a rebound", "requires better gains", "requires more work than the engine expects")
# spans whose numbers are labels, not claims
EXEMPT = [re.compile(p, re.I) for p in (
    r"\bweeks? \d+(?:\s*(?:-|–|to|and)\s*\d+)?", r"\b20\d\d\b", r"\b\d+(?:st|nd|rd|th)\b",
    r"\b80% range\b", r"\b\d+-leg\b", r"\b(?:WR|RB|TE|QB)\d\b", r"\b\d+x\b")]
NUM = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(%?)(?![\w])")
LEG_TEXT = ("if", "fails", "else")
PLAYER_TEXT = ("basis", "explanation", "role_evidence", "matchup_reason")
GAME_TEXT = ("opening", "market_read", "workload_read", "personnel_read", "allowed_read", "handoff")


class ReadsError(ValueError):
    """The reads file cannot be read as the schema says."""


# ---------------------------------------------------------------- loading
def load_run(path) -> dict:
    run = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if run.get("export_version") != 1:
        raise ReadsError(f"{path}: run export version {run.get('export_version')!r}, this publish reads 1")
    return run


def load_reads(path) -> dict:
    """The reads file, validated, with its legs flattened (each leg carries its player's name)."""
    return validate(json.loads(Path(path).read_text(encoding="utf-8-sig")))


def validate(reads: dict) -> dict:
    """A reads dict as the schema says, or ReadsError; returns a copy whose legs are flattened."""
    reads = json.loads(json.dumps(reads))
    if reads.get("reads_version") != READS_VERSION:
        raise ReadsError(f"reads_version must be {READS_VERSION} (the report guide's structure)")
    players = reads.get("players")
    if not isinstance(players, list) or not players:
        raise ReadsError("reads need at least one player")
    for k in ("opening", "handoff"):
        if not reads.get(k):
            raise ReadsError(f"the reads need {k!r}")
    if not isinstance(reads.get("assumptions"), list) or not 2 <= len(reads["assumptions"]) <= 3:
        raise ReadsError("the reads need two or three assumptions worth testing")
    legs = []
    for pi, p in enumerate(players, 1):
        if not p.get("player"):
            raise ReadsError(f"player {pi}: missing player")
        miss = [k for k in PLAYER_TEXT if not p.get(k)]
        if miss:
            raise ReadsError(f"{p['player']}: missing {', '.join(miss)}")
        if p.get("matchup") not in ("supports", "challenges"):
            raise ReadsError(f"{p['player']}: matchup must be 'supports' or 'challenges'")
        if not isinstance(p.get("legs"), list) or not p["legs"]:
            raise ReadsError(f"{p['player']}: at least one leg")
        for c in p.get("cite") or []:
            _valid_cite(c, p["player"])
        for lg in p["legs"]:
            where = f"{p['player']} {lg.get('market')} {lg.get('line')}"
            miss = [k for k in ("market", "side", "line", *LEG_TEXT) if lg.get(k) in (None, "")]
            if miss:
                raise ReadsError(f"{where}: missing {', '.join(miss)}")
            if str(lg["side"]).lower() not in ("over", "under"):
                raise ReadsError(f"{where}: side must be over or under")
            if market_key(lg["market"]) is None:
                raise ReadsError(f"{where}: unknown market {lg['market']!r} (use one of {', '.join(sorted(MARKET_ALIASES))})")
            for c in lg.get("cite") or []:
                _valid_cite(c, where)
            for n in lg.get("needs") or []:
                if not isinstance(n.get("reaches"), bool):
                    raise ReadsError(f"{where}: every need says reaches true or false")
            legs.append({**lg, "player": p["player"]})
    for c in reads.get("cite") or []:
        _valid_cite(c, "game")
    for r in reads.get("personnel") or []:
        if not r.get("player") or not r.get("status") or not r.get("changes") or not r.get("affects"):
            raise ReadsError("each personnel row needs player, status, changes and affects")
    reads["legs"] = legs
    return reads


def _valid_cite(c, where):
    if not isinstance(c, dict) or not c.get("field"):
        raise ReadsError(f"{where}: a cite needs a field and a value")
    try:
        parse_stated(c.get("value"))
    except ReadsError as ex:
        raise ReadsError(f"{where}: cite {c.get('field')}: {ex}") from None


def market_key(m) -> str | None:
    m = str(m).strip().lower()
    return m if m in MARKET_WORDS else MARKET_ALIASES.get(m)


# ---------------------------------------------------------------- lookups
def card_for(run, player):
    want = str(player).strip().lower()
    hits = [c for c in run.get("cards") or [] if str(c.get("name", "")).lower() == want]
    return hits[0] if len(hits) == 1 else None


def row_for(card, market, line):
    rows = [r for r in card.get("rows") or [] if r.get("market") == market and _close(r.get("line"), line, 1e-9)]
    if not rows:
        return None
    pref = [r for r in rows if r.get("book") == card.get("book")]
    return (pref or rows)[0]


def main_rows(card) -> list[dict]:
    """The card's props: the first book's row per market, in the board's order."""
    seen = {}
    for r in sorted(card.get("rows") or [], key=lambda r: r.get("book") != card.get("book")):
        seen.setdefault(r.get("market"), r)
    return [seen[m] for m in MARKET_ORDER if m in seen]


def cells_for(card, market):
    v = next((v for v in card.get("volume") or [] if v.get("market") == market), None)
    return (v or {}).get("cells")


def volume_text(card, market):
    v = next((v for v in card.get("volume") or [] if v.get("market") == market), None)
    return (v or {}).get("volume_text")


def section_of(card) -> str:
    return SECTION_OF_POS.get(str(card.get("pos") or "").upper(), "Receiving")


def resolve(path: str, run, card, row, cells):
    """The run's value at a cite's field: an alias (market_p ...), row.<key>.pct|vol|rate for a
    volume-chance row, card.<path> into the player's card, game.<path> into the run."""
    if path in UNDER_ALIASES:
        return UNDER_ALIASES[path](row or {})
    if path in ROW_ALIASES:
        where, key = ROW_ALIASES[path]
        src = row if where == "row" else cells
        return (src or {}).get(key)
    m = re.fullmatch(r"row\.(capped|season|engine)\.(pct|vol|rate)", path)
    if m:
        r = ((cells or {}).get("rows") or {}).get(m.group(1))
        return None if r is None else r.get(m.group(2))
    if path in ("market_line", "market_line_pct"):
        mr = (cells or {}).get("market_row")
        return None if not mr else mr[0 if path == "market_line" else 1]
    root, _, rest = path.partition(".")
    obj = {"card": card, "game": run}.get(root)
    if obj is None:
        root, rest, obj = "card", path, card
    for part in rest.split("."):
        if isinstance(obj, dict):
            obj = obj.get(part)
        elif isinstance(obj, list) and part.isdigit() and int(part) < len(obj):
            obj = obj[int(part)]
        else:
            return None
    return obj


# ---------------------------------------------------------------- what the run computes for the card
def last_volume(card, market):
    """His last game's workload in the unit the market's volume counts: targets for receptions,
    carries for rushing; None where the run does not carry it (catches, completions, touches)."""
    u = card.get("usage") or {}
    return {"player_receptions": u.get("tn"), "player_rush_yds": u.get("cn")}.get(market)


def verdict(card, market) -> dict | None:
    """The card's verdict word by its definition (the user, 2026-10-08), checked in this order:
    - requires better gains: at the trimmed (or, for receptions, this season's) rate the line needs
      more than the engine's projected workload, and only the engine's own rate clears at it;
    - requires more work than the engine expects: no rate clears at the engine's workload;
    - requires a rebound: the engine's workload clears, but the need is above his last game's;
    - attainable: the need is at or below the engine's workload (and his last game's, if known)."""
    c = cells_for(card, market)
    if not c or not c.get("rows"):
        return None
    ref = "capped" if "capped" in c["rows"] else ("season" if "season" in c["rows"] else None)
    if ref is None:
        return None
    need, proj = float(c["rows"][ref]["vol"]), float(c["proj"])
    eng = c["rows"].get("engine")
    last = last_volume(card, market)
    if need > proj + 1e-9:
        word = "requires better gains" if eng and float(eng["vol"]) <= proj + 1e-9 else VERDICTS[3]
    elif last is not None and need > float(last) + 1e-9:
        word = "requires a rebound"
    else:
        word = "attainable"
    return {"word": word, "ref": ref, "need": need, "proj": proj, "last": last, "unit": c.get("unit"),
            "vol_txt": c["rows"][ref]["vol_txt"], "rate_txt": c["rows"][ref]["rate_txt"], "pct": c["rows"][ref]["pct"]}


# ---------------------------------------------------------------- number matching
def _close(a, b, tol):
    try:
        return a is not None and b is not None and abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return False


def parse_stated(v):
    """(number, is_percent, decimals) from a cite's value as written: 0.72, 9, "50%", "7.4"."""
    s = str(v).strip()
    pct = s.endswith("%")
    s = s.rstrip("%").strip()
    if not re.fullmatch(r"-?\d+(?:\.\d+)?", s):
        raise ReadsError(f"value {v!r} is not a number")
    dec = len(s.split(".")[1]) if "." in s else 0
    return float(s), pct, dec


def matches(stated, computed) -> bool:
    """The run's number, rounded to the precision the read wrote it at, equals what the read says
    ("50%" against 0.5043; 7.4 against 7.43; 9 against 9)."""
    if computed is None or isinstance(computed, (dict, list, str, bool)):
        return False
    n, pct, dec = parse_stated(stated)
    if not pct and 0 < abs(float(computed)) < 1 and dec < 2:
        return False          # a chance or a share written 0.5 spans 45-55%: write it as a percent
    c = float(computed) * (100 if pct else 1)
    return abs(c - n) <= 0.5 * 10 ** -dec + 1e-9


def _fmt(x, pct=False):
    if x is None:
        return "-"
    if isinstance(x, (list, tuple)):
        return " + ".join(_fmt(v) for v in x)
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return str(x)
    return f"{100 * x:.1f}%" if pct else (f"{x:g}" if float(x).is_integer() else f"{x:.3f}".rstrip("0"))


def _num_ok(tok, allowed):
    """A prose number against one allowed run value, units kept apart: '79%' traces only to a
    fraction (0.787), '9.2' only to a count or a yardage, never across. Within a unit the prose may
    round (10 for 10.4); WHICH quantity it names is the reviewer's to judge."""
    try:
        a = float(allowed)
    except (TypeError, ValueError):
        return False
    is_fraction = 0 < abs(a) < 1
    if tok.endswith("%"):
        return is_fraction and matches(tok, a)
    return not is_fraction and matches(tok, a)


def game_numbers(run) -> list[float]:
    """Every number the team brief's tables show (the frame a game narration may quote): the
    spread, total, implied points, win chances and their openers; the workload columns; the unit
    scores and ranks; the points allowed, their ranks, parts and the league averages."""
    me = run.get("market_env") or {}
    nums = []
    for k in ("total_line", "open_total", "home_win_prob", "home_win_prob_open"):
        if me.get(k) is not None:
            nums.append(me[k])
    for k in ("home_win_prob", "home_win_prob_open"):
        if me.get(k) is not None:
            nums.append(1 - me[k])
    for k in ("home_spread", "open_home_spread"):
        if me.get(k) is not None:
            nums += [me[k], abs(me[k])]
    if me.get("home_spread") is not None and me.get("open_home_spread") is not None:
        nums.append(abs(me["home_spread"] - me["open_home_spread"]))
    if me.get("total_line") is not None and me.get("open_total") is not None:
        nums.append(abs(me["total_line"] - me["open_total"]))
    tv = run.get("team_volume") or {}
    for t, e in (run.get("teams") or {}).items():
        nums += [e.get("implied_points"), e.get("targets"), e.get("carries"), e.get("market_runs")]
        rate = (tv.get(t) or {}).get("target_rate")
        if e.get("market_throws") is not None and rate:
            nums.append(e["market_throws"] / rate)
    for v in tv.values():
        for k in ("our_att", "our_runs", "att_avg", "runs_avg", "games"):
            nums.append((v or {}).get(k))
    for t, units in (run.get("units") or {}).items():
        for u in units.values():
            nums += [u.get("score"), u.get("rank"), u.get("of")]
    pa = run.get("points_allowed") or {}
    for t, pos in pa.items():
        if t.startswith("_"):
            continue
        for d in pos.values():
            nums += [d.get(k) for k in ("ppr", "rank_most", "catches", "rec_yds", "rush_yds", "tds")]
    nums += list((pa.get("_league") or {}).values()) + [pa.get("_n")]
    lr = run.get("live_record") or {}
    nums += [lr.get("engine_log_loss"), lr.get("market_log_loss"), lr.get("lines"), lr.get("coin_flip")]
    return [float(n) for n in nums if isinstance(n, (int, float)) and not isinstance(n, bool)]


# ---------------------------------------------------------------- the check
def check(run, reads) -> list[dict]:
    """Every mechanical check, one dict each: {leg, check, stated, run, ok, detail}. leg 0 is the
    game; legs are numbered in the reads' order."""
    out = []

    def add(leg, kind, stated, value, ok, detail=""):
        out.append({"leg": leg, "check": kind, "stated": stated, "run": value, "ok": bool(ok), "detail": detail})

    inj = {str(i.get("name", "")).lower(): i for i in run.get("injuries") or []}
    game_ok, game_cites = game_numbers(run), []
    # ---- the game ----
    for c in reads.get("cite") or []:
        v = resolve(str(c.get("field")), run, {}, None, None)
        ok = matches(c.get("value"), v)
        add(0, "cite", f"{c.get('field')} = {c.get('value')}", _fmt(v), ok, "" if ok else "not the run's number")
        if ok:
            game_ok.append(float(v))
            game_cites.append(float(v))
    n_sent = count_sentences(reads.get("opening"))
    add(0, "opening read", f"{n_sent} sentences", "three", n_sent == 3, "" if n_sent == 3 else "the guide asks for three")
    qb_out = {str(v).split(" starts for ")[-1].lower() for v in (run.get("qb_change") or {}).values()}
    named_inj = set()
    for r in reads.get("personnel") or []:
        nm = str(r["player"]).lower()
        have = inj.get(nm)
        run_st = (have or {}).get("status") or ("practice only" if have and have.get("practice") else
                                                ("Out" if nm in qb_out else "not listed"))
        ok = str(r["status"]).strip().lower() == run_st.lower()
        add(0, "personnel", f"{r['player']}: {r['status']}", run_st, ok, "" if ok else "section 4 says otherwise")
        named_inj.add(nm)
    texts = [(k, reads.get(k)) for k in GAME_TEXT] + [(f"unit read {t}", v) for t, v in (reads.get("unit_reads") or {}).items()]
    texts += [(f"assumption {i}", a) for i, a in enumerate(reads.get("assumptions") or [], 1)]
    texts += [(f"personnel {r['player']}", f"{r['changes']} {r['affects']}") for r in reads.get("personnel") or []]
    for kind, text in texts:
        _text_checks(add, 0, kind, text, game_ok, inj, named_inj)
    # ---- the players and their legs ----
    by_player = {}
    for i, lg in enumerate(reads["legs"], 1):
        by_player.setdefault(lg["player"], []).append(i)
    for p in reads.get("players") or []:
        card = card_for(run, p["player"])
        idx = by_player.get(p["player"], [])
        if card is None:
            for i in idx:
                add(i, "on the board", p["player"], "-", False, "no card for this player in the run (check the name)")
            continue
        p_cites = list(game_cites)                # the game CITES, not the brief's tables
        for c in p.get("cite") or []:
            f = str(c.get("field"))
            v = resolve(f, run, card, None, None)
            ok = matches(c.get("value"), v)
            add(idx[0], "cite", f"{f} = {c.get('value')}", _fmt(v), ok, "" if ok else "not the run's number")
            if ok:
                p_cites.append(float(v))
        p_allowed = list(p_cites)
        leg_allowed = {}
        cited_inj = set(named_inj) | {str(j.get("player", "")).lower() for j in p.get("injuries") or []}
        for j in p.get("injuries") or []:
            _injury_check(add, idx[0], j, inj)
        verdicts = set()
        for i in idx:
            lg = reads["legs"][i - 1]
            allowed, v = _check_leg(add, i, run, card, lg, inj)
            leg_allowed[i] = allowed
            p_allowed += allowed
            if v:
                verdicts.add(v["word"])
            cited_inj |= {str(j.get("player", "")).lower() for j in lg.get("injuries") or []}
        for i in idx:
            lg = reads["legs"][i - 1]
            for k in LEG_TEXT:
                _text_checks(add, i, k, lg.get(k), leg_allowed.get(i, []) + p_cites, inj, cited_inj, verdicts)
        for k in PLAYER_TEXT:
            _text_checks(add, idx[0], k, p.get(k), p_allowed, inj, cited_inj, verdicts)
    return out


ABBREV = re.compile(r"\b(Jr|Sr|St|Mr|Dr|vs|No)\.", re.I)


def count_sentences(text) -> int:
    """Sentences in a paragraph; 'Jr.', 'St.', 'vs.' and the like do not end one."""
    t = ABBREV.sub(lambda m: m.group(1), str(text or "").strip())
    return len([s for s in re.split(r"(?<=[.!?])\s+", t) if s])


def _injury_check(add, i, j, inj):
    nm = str(j.get("player", "")).lower()
    have = inj.get(nm)
    run_st = (have or {}).get("status") or ("practice only" if have and have.get("practice") else "not listed")
    stated = str(j.get("status", "")).strip()
    ok = stated.lower() == run_st.lower()
    add(i, "injury", f"{j.get('player')}: {stated}", run_st, ok, "" if ok else "section 4 says otherwise")


def _check_leg(add, i, run, card, lg, inj):
    """One leg's checks; returns (the numbers its prose may quote, its verdict)."""
    mk, line = market_key(lg["market"]), float(lg["line"])
    row = row_for(card, mk, line)
    if row is None:
        have = sorted({f"{MARKET_WORDS.get(r['market'], r['market'])} {r['line']:g}" for r in card.get("rows") or []
                       if r.get("market") and isinstance(r.get("line"), (int, float))})
        add(i, "on the board", f"{MARKET_WORDS[mk]} {line:g}", "; ".join(have) or "no lines", False,
            "not on the board at this line")
        return [], None
    add(i, "on the board", f"{lg['player']} {MARKET_WORDS[mk]} {lg['side']} {line:g}",
        f"{row.get('book')} {row.get('line'):g}", True)
    cells = cells_for(card, mk)
    need_out = math.floor(line) + 1
    allowed = [line, need_out]
    v = verdict(card, mk) if _close(row.get("line"), (next((x for x in card.get("volume") or []
                                                            if x.get("market") == mk), {}) or {}).get("line"), 1e-9) else None
    if v:
        allowed += [v["need"], v["proj"], v["pct"]] + ([v["last"]] if v["last"] is not None else [])
    rates = {k: r.get("rate") for k, r in ((cells or {}).get("rows") or {}).items()}
    for k, r in ((cells or {}).get("rows") or {}).items():
        allowed += [r.get("vol"), r.get("pct")] + (r.get("rate") if isinstance(r.get("rate"), list) else [r.get("rate")])
    if cells:
        allowed += [cells.get("proj"), cells.get("need_rate")] + list(cells.get("market_row") or [])
    for k in ("p_over_book", "p_over_model", "median", "p10", "p90", "market_volume", "market_catches"):
        allowed.append(row.get(k))
    for n in lg.get("needs") or []:
        parts = n.get("parts") or [[n.get("volume"), n.get("rate")]]
        try:
            parts = [(float(a), float(b)) for a, b in parts]
        except (TypeError, ValueError):
            add(i, "volume x efficiency", json.dumps(n), "-", False, "needs volume and rate numbers")
            continue
        total = sum(a * b for a, b in parts)
        reaches = total >= need_out - 1e-9
        stated = n.get("reaches")
        txt = " + ".join(f"{a:g} x {b:g}" for a, b in parts) + f" = {total:.2f}"
        add(i, "volume x efficiency", f"{txt}: {'reaches' if stated else 'short of'} {need_out}",
            f"{'reaches' if reaches else 'short of'} {need_out}", stated is reaches,
            "" if stated is reaches else "the read says the opposite of the arithmetic")
        for a, b in parts:
            allowed += [a, b, round(a * b, 1)]
        if n.get("hypothetical"):
            add(i, "rate source", " + ".join(f"{b:g}" for _a, b in parts), "hypothetical (labelled)", True)
        else:
            hit = [k for k, r in rates.items() if _rates_match([b for _a, b in parts], r)]
            add(i, "rate source", " + ".join(f"{b:g}" for _a, b in parts), ", ".join(hit) or "not a card rate",
                bool(hit), "" if hit else ("the rate is not one of the card's rows (a carries + catches need lists "
                                           "carries first); mark the need hypothetical or use a card rate"))
            for k in hit:
                # the card's exact rate decides: a rounded rate must not flip the verdict
                exact = rates[k] if isinstance(rates[k], list) else [rates[k]]
                t_card = sum(a * float(r) for (a, _b), r in zip(parts, exact))
                if (t_card >= need_out - 1e-9) is not reaches:
                    add(i, "rate rounding", txt, f"at the card's {k} rate: {t_card:.2f}, "
                        f"{'reaches' if t_card >= need_out - 1e-9 else 'short of'} {need_out}", False,
                        "the rounded rate flips the verdict; use the card's rate to more decimals")
        allowed += [total, round(total, 1)]
    for c in lg.get("cite") or []:
        f = str(c.get("field"))
        val = resolve(f, run, card, row, cells)
        ok = matches(c.get("value"), val)
        add(i, "cite", f"{f} = {c.get('value')}", _fmt(val), ok, "" if ok else "not the run's number")
        if ok:
            allowed.append(float(val))
    for j in lg.get("injuries") or []:
        _injury_check(add, i, j, inj)
    return [a for a in allowed if isinstance(a, (int, float)) and not isinstance(a, bool)], v


def _rates_match(bs, r) -> bool:
    """The need's rates against one card row's rate: one rate, or a carries + catches pair in that
    order (yards a carry, then yards a catch). Catch rates within 0.005, yards within 0.05."""
    if r is None:
        return False
    rs = r if isinstance(r, list) else [r]
    return len(bs) == len(rs) and all(_close(b, x, 0.005 if float(x) <= 1 else 0.05) for b, x in zip(bs, rs))


def _text_checks(add, leg, kind, text, allowed, inj, cited_inj, verdicts=None):
    if not text:
        return
    for rx, what in BANNED:
        m = rx.search(text)
        if m:
            add(leg, "language", f"{kind}: '{m.group(0)}'", "-", False, f"{what} is not allowed: the board is a research sheet")
    low = text.lower()
    if verdicts is not None:
        for w in VERDICTS:
            if w in low and w not in verdicts:
                add(leg, "verdict word", f"{kind}: '{w}'", ", ".join(sorted(verdicts)) or "none computed", False,
                    "the verdict words are computed from the card, not chosen")
    clean = text
    for rx in EXEMPT:
        clean = rx.sub(" ", clean)
    for m in NUM.finditer(clean):
        tok = m.group(1) + m.group(2)
        if not any(_num_ok(tok, a) for a in allowed):
            add(leg, "number traced", f"{kind}: {tok}", "-", False,
                "a number in the prose that no cite, need, line or table accounts for")
    for nm, row in inj.items():
        if not nm or nm in cited_inj:
            continue
        last = _last_name(nm)
        named = nm in low or (last and re.search(rf"\b{re.escape(last)}\b", low))
        if named:
            add(leg, "injury named", f"{kind}: {row.get('name')}", row.get("status") or "practice only", False,
                "the prose names a player on section 4 without an injuries or personnel entry to check it")


def _last_name(nm: str) -> str | None:
    """'jonathan mingo' -> 'mingo'; suffixes dropped; None when too short to search alone."""
    parts = [p for p in re.split(r"\s+", nm.strip()) if p.strip(".") not in ("jr", "sr", "ii", "iii", "iv", "v")]
    last = parts[-1].strip(".") if len(parts) > 1 else None
    return last if last and len(last) >= 4 else None


# ---------------------------------------------------------------- the CI read (agent version)
def ci_results(repo_url, ref, get=None):
    """The GitHub check runs for a release: the suites ran on the head of the pull request that
    merged it; the tag's commit carries what ran on main. Both are reported, each labelled. None
    when GitHub cannot be read (DATA MISSING, never a guessed pass)."""
    import urllib.request
    api = "https://api.github.com/repos/" + repo_url.split("github.com/", 1)[1]
    get = get or (lambda u: json.loads(urllib.request.urlopen(
        urllib.request.Request(u, headers={"Accept": "application/vnd.github+json", "User-Agent": "nfl-publish"}),
        timeout=20).read().decode("utf-8")))

    def runs_at(sha, where):
        rs = get(f"{api}/commits/{sha}/check-runs?per_page=100").get("check_runs") or []
        return [{"name": r.get("name"), "status": r.get("status"), "conclusion": r.get("conclusion"),
                 "url": r.get("html_url"), "where": where} for r in rs]
    try:
        sha = get(f"{api}/commits/{ref}")["sha"]
        prs = get(f"{api}/commits/{sha}/pulls") or []
        pr = next((p for p in prs if p.get("merged_at")), prs[0] if prs else None)
        checks = (runs_at(pr["head"]["sha"], f"pull request #{pr['number']} head") if pr else []) \
            + runs_at(sha, "the tag's commit")
        return {"ref": ref, "sha": sha, "pr": pr["number"] if pr else None, "checks": checks}
    except Exception:  # noqa: BLE001 -- any failure is DATA MISSING, said so in the file
        return None


# ---------------------------------------------------------------- command line
def main(argv=None) -> int:
    import publish_render as PR
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--run", required=True, help="run_<slug>.json from score_game.py")
    ap.add_argument("--reads", required=True, help="the reads file (resources/agent_guide.md, 'The reads file')")
    ap.add_argument("--out", required=True)
    ap.add_argument("--which", default="qa,agent,pdf", help="comma list: qa, agent, pdf")
    ap.add_argument("--release-tag")
    ap.add_argument("--release-hash")
    ap.add_argument("--release-source")
    ap.add_argument("--check-only", action="store_true", help="print the checks; render nothing")
    ap.add_argument("--no-ci", action="store_true", help="do not read the CI results from GitHub")
    a = ap.parse_args(argv)
    try:
        run, reads = load_run(a.run), load_reads(a.reads)
    except (ReadsError, OSError, json.JSONDecodeError) as ex:
        print(f"PUBLISH: {ex}", file=sys.stderr)
        return 2
    rep_path = Path(a.run).with_name(f"report_{run['slug']}.md")
    if rep_path.exists():
        cut = next((x.strip() for x in rep_path.read_text(encoding="utf-8").splitlines()
                    if x.strip().startswith("- **Data cutoff:**")), None)
        if cut and run.get("data_cutoff") and cut != run["data_cutoff"]:
            print(f"PUBLISH: {Path(a.run).name} is not the run behind {rep_path.name} (their data cutoffs differ: "
                  f"the run export failed or is older); run `props game` again", file=sys.stderr)
            return 2
    checks = check(run, reads)
    fails = [c for c in checks if not c["ok"]]
    print(f"checks: {len(checks) - len(fails)} of {len(checks)} pass")
    for c in fails:
        print(f"  FAIL leg {c['leg']} {c['check']}: {c['stated']} -- run: {c['run']} -- {c['detail']}")
    if fails or a.check_only:
        return 3 if fails else 0
    release = {"tag": a.release_tag, "hash": a.release_hash, "source": a.release_source}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    which = {w.strip() for w in a.which.split(",") if w.strip()}
    if "qa" in which:
        p = out / f"{run['slug']}_qa.md"
        p.write_text(PR.scrub(PR.render_qa(run, reads, checks, release)), encoding="utf-8")
        print(f"wrote {p}")
    if "agent" in which:
        ci = None if a.no_ci or not a.release_tag else ci_results(REPO_URL, a.release_tag)
        p = out / f"{run['slug']}_agent.md"
        p.write_text(PR.scrub(PR.render_agent(run, reads, checks, release, ci)), encoding="utf-8")
        print(f"wrote {p}")
    if "pdf" in which:
        import publish_pdf as PDF
        if not PDF.available():
            print("PDF skipped: the reportlab package is not installed (pip install reportlab); "
                  "the QA and agent versions are written", file=sys.stderr)
        else:
            p = PDF.build(PR.scrub(PR.render_external(run, reads)), out / f"{run['slug']}.pdf",
                          title=f"{run['away']} at {run['home']}, week {run['week']}")
            print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
