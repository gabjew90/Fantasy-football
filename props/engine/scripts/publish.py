"""Publish a game read in three versions from ONE run and ONE set of written reads (DECISIONS #217).

    python publish.py --run OUT/run_2026_wk05_TB_DAL.json --reads reads.json --out OUT
                      [--which qa,agent] [--release-tag T --release-hash H --release-source S]
                      [--check-only] [--no-ci]

The run file is what score_game.py writes beside its report (write_run_export): every card's
numbers, section 4's players, section 7's gaps, the sources table. The reads file is what chat
writes: a game thesis and, per leg, the condition, the case, how it fails, the volume x efficiency
it needs and every number it cites (schema: resources/agent_guide.md, "The reads file").

THE CHECK RUNS FIRST. Every leg must be on the board at its side and line; every volume x
efficiency is recomputed against the whole number the Over needs; every cited number must be the
run's at the precision written; every number in the prose must trace to a cite, a need or the line;
injuries must match section 4; betting words and "the probability" are refused. A failed check
renders nothing: the failures print (exit 3) for chat to fix. Judgment -- whether a condition is
plausible -- is not machine-checked; the QA version lists it for the human reviewer.

Outputs (in --out): <slug>_qa.md (the QA/QC version, for chat and internal reviewers) and
<slug>_agent.md (the whole pipeline for another LLM agent). The external PDF comes with the
user's format guide. Informational only: nothing here reads or moves a price.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
REPO_URL = "https://github.com/gabjew90/Fantasy-football"
READS_VERSION = 1

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
# spans whose numbers are labels, not claims
EXEMPT = [re.compile(p, re.I) for p in (
    r"\bweeks? \d+(?:\s*(?:-|–|to|and)\s*\d+)?", r"\b20\d\d\b", r"\b\d+(?:st|nd|rd|th)\b",
    r"\b80% range\b", r"\b\d+-leg\b", r"\b(?:WR|RB|TE|QB)\d\b", r"\b\d+x\b")]
NUM = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(%?)(?![\w])")
TEXT_FIELDS = ("condition", "case", "fails")


class ReadsError(ValueError):
    """The reads file cannot be read as the schema says."""


# ---------------------------------------------------------------- loading
def load_run(path) -> dict:
    run = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if run.get("export_version") != 1:
        raise ReadsError(f"{path}: run export version {run.get('export_version')!r}, this publish reads 1")
    return run


def load_reads(path) -> dict:
    reads = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if reads.get("reads_version") != READS_VERSION:
        raise ReadsError(f"reads_version must be {READS_VERSION}")
    if not isinstance(reads.get("legs"), list) or not reads["legs"]:
        raise ReadsError("reads need at least one leg")
    for i, lg in enumerate(reads["legs"], 1):
        miss = [k for k in ("player", "market", "side", "line", *TEXT_FIELDS) if lg.get(k) in (None, "")]
        if miss:
            raise ReadsError(f"leg {i}: missing {', '.join(miss)}")
        if str(lg["side"]).lower() not in ("over", "under"):
            raise ReadsError(f"leg {i}: side must be over or under")
        if market_key(lg["market"]) is None:
            raise ReadsError(f"leg {i}: unknown market {lg['market']!r} (use one of {', '.join(sorted(MARKET_ALIASES))})")
        for c in lg.get("cite") or []:
            _valid_cite(c, f"leg {i}")
        for n in lg.get("needs") or []:
            if not isinstance(n.get("reaches"), bool):
                raise ReadsError(f"leg {i}: every need says reaches true or false")
    for c in reads.get("cite") or []:
        _valid_cite(c, "game")
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


def cells_for(card, market):
    v = next((v for v in card.get("volume") or [] if v.get("market") == market), None)
    return (v or {}).get("cells")


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


# ---------------------------------------------------------------- the check
def check(run, reads) -> list[dict]:
    """Every mechanical check, one dict each: {leg, check, stated, run, ok, detail}. leg 0 is the
    game (the thesis and its cites)."""
    out = []

    def add(leg, kind, stated, value, ok, detail=""):
        out.append({"leg": leg, "check": kind, "stated": stated, "run": value, "ok": bool(ok), "detail": detail})

    inj = {str(i.get("name", "")).lower(): i for i in run.get("injuries") or []}
    game_ok_numbers = _game_numbers(run)
    # ---- the game ----
    for c in reads.get("cite") or []:
        v = resolve(str(c.get("field")), run, {}, None, None)
        ok = matches(c.get("value"), v)
        add(0, "cite", f"{c.get('field')} = {c.get('value')}", _fmt(v), ok, "" if ok else "not the run's number")
        if ok:
            game_ok_numbers.append(float(v))
    for kind, text in (("thesis", reads.get("thesis")), *(("note", n) for n in reads.get("notes") or [])):
        _text_checks(add, 0, kind, text, game_ok_numbers, inj, [])
    # ---- the legs ----
    for i, lg in enumerate(reads["legs"], 1):
        mk, line = market_key(lg["market"]), float(lg["line"])
        card = card_for(run, lg["player"])
        if card is None:
            add(i, "on the board", lg["player"], "-", False, "no card for this player in the run (check the name)")
            continue
        row = row_for(card, mk, line)
        if row is None:
            have = sorted({f"{MARKET_WORDS.get(r['market'], r['market'])} {r['line']:g}" for r in card.get("rows") or []
                           if r.get("market") and isinstance(r.get("line"), (int, float))})
            add(i, "on the board", f"{MARKET_WORDS[mk]} {line:g}", "; ".join(have) or "no lines", False,
                "not on the board at this line")
            continue
        add(i, "on the board", f"{lg['player']} {MARKET_WORDS[mk]} {lg['side']} {line:g}",
            f"{row.get('book')} {row.get('line'):g}", True)
        cells = cells_for(card, mk)
        need_out = math.floor(line) + 1
        allowed = [line, need_out]
        rates = {k: r.get("rate") for k, r in ((cells or {}).get("rows") or {}).items()}
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
            v = resolve(f, run, card, row, cells)
            ok = matches(c.get("value"), v)
            add(i, "cite", f"{f} = {c.get('value')}", _fmt(v), ok, "" if ok else "not the run's number")
            if ok:
                allowed.append(float(v))
        for j in lg.get("injuries") or []:
            nm = str(j.get("player", "")).lower()
            have = inj.get(nm)
            run_st = (have or {}).get("status") or ("practice only" if have and have.get("practice") else "not listed")
            stated = str(j.get("status", "")).strip()
            ok = stated.lower() == run_st.lower()
            add(i, "injury", f"{j.get('player')}: {stated}", run_st, ok, "" if ok else "section 4 says otherwise")
        cited_inj = {str(j.get("player", "")).lower() for j in lg.get("injuries") or []}
        for k in TEXT_FIELDS:
            _text_checks(add, i, k, lg.get(k), allowed + game_ok_numbers, inj, cited_inj)
    return out


def _rates_match(bs, r) -> bool:
    """The need's rates against one card row's rate: one rate, or a carries + catches pair in that
    order (yards a carry, then yards a catch). Catch rates within 0.005, yards within 0.05."""
    if r is None:
        return False
    rs = r if isinstance(r, list) else [r]
    return len(bs) == len(rs) and all(_close(b, x, 0.005 if float(x) <= 1 else 0.05) for b, x in zip(bs, rs))


def _game_numbers(run):
    me = run.get("market_env") or {}
    nums = [me.get("total_line")]
    if me.get("home_spread") is not None:
        nums += [me["home_spread"], abs(me["home_spread"])]
    for t in (run.get("teams") or {}).values():
        nums += [t.get("implied_points"), t.get("targets"), t.get("carries")]
    return [n for n in nums if n is not None]


def _text_checks(add, leg, kind, text, allowed, inj, cited_inj):
    if not text:
        return
    for rx, what in BANNED:
        m = rx.search(text)
        if m:
            add(leg, "language", f"{kind}: '{m.group(0)}'", "-", False, f"{what} is not allowed: the board is a research sheet")
    clean = text
    for rx in EXEMPT:
        clean = rx.sub(" ", clean)
    for m in NUM.finditer(clean):
        tok = m.group(1) + m.group(2)
        ok = any(_num_ok(tok, a) for a in allowed)
        if not ok:
            add(leg, "number traced", f"{kind}: {tok}", "-", False,
                "a number in the prose that no cite, need or line accounts for")
    low = text.lower()
    for nm, row in inj.items():
        if not nm or nm in cited_inj:
            continue
        last = _last_name(nm)
        named = nm in low or (last and re.search(rf"\b{re.escape(last)}\b", low))
        if named:
            add(leg, "injury named", f"{kind}: {row.get('name')}", row.get("status") or "practice only", False,
                "the prose names a player on section 4 without an injuries entry to check it")


def _last_name(nm: str) -> str | None:
    """'jonathan mingo' -> 'mingo'; suffixes dropped; None when too short to search alone."""
    parts = [p for p in re.split(r"\s+", nm.strip()) if p.strip(".") not in ("jr", "sr", "ii", "iii", "iv", "v")]
    last = parts[-1].strip(".") if len(parts) > 1 else None
    return last if last and len(last) >= 4 else None


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


# ---------------------------------------------------------------- shared pieces
def legs_resolved(run, reads):
    for i, lg in enumerate(reads["legs"], 1):
        mk = market_key(lg["market"])
        card = card_for(run, lg["player"]) or {}
        row = row_for(card, mk, float(lg["line"])) if card else None
        yield i, lg, mk, card, row, cells_for(card, mk) if card else None


def support_table(row, cells, side) -> list[str]:
    """The leg's numbers, the card's rows in the card's words (research.prop_table's vocabulary)."""
    if not row:
        return ["*Not on the board in this run.*"]
    pct = lambda v: "-" if v is None else f"{100 * float(v):.0f}%"
    odds = lambda v: "-" if v is None else (f"+{int(v)}" if float(v) > 0 else f"{int(v)}")
    L = ["| | |", "|---|---:|",
         f"| Market's chance of the Over (the best available estimate) | **{pct(row.get('p_over_book'))}** |",
         f"| Engine's chance of the Over | {pct(row.get('p_over_model'))} |",
         f"| Price: Over / Under | {odds(row.get('price_over'))} / {odds(row.get('price_under'))} |",
         f"| Engine's forecast: middle; 80% range | {_r0(row.get('median'))}; {_r0(row.get('p10'))}-{_r0(row.get('p90'))} |"]
    if cells:
        L.append(f"| The Over needs | {cells['need_out']} |")
        L.append(f"| Engine's volume | {cells['proj']:.1f} {cells['unit']} |")
    if row.get("market_volume") is not None:
        L.append(f"| Market-implied volume (at the engine's efficiency) | {float(row['market_volume']):.1f} {row.get('unit') or ''} |")
    for k, word in (("capped", "At his luck-capped rate"), ("season", "At his rate this season"),
                    ("engine", "At the engine's rate")):
        r = ((cells or {}).get("rows") or {}).get(k)
        if r:
            L.append(f"| {word} | {r['vol_txt']} at {r['rate_txt']} -> {pct(r['pct'])} |")
    if cells and cells.get("market_row"):
        L.append(f"| The market's own volume line | more than {cells['market_row'][0]:g} {cells['unit']} -> {pct(cells['market_row'][1])} |")
    if cells and cells.get("need_txt"):
        L.append(f"| At the engine's volume, the line needs | {cells['need_txt']} |")
    if cells and cells.get("beat"):
        L.append(f"| His games this season that beat that | {cells['beat'][0]} of {cells['beat'][1]} |")
    if side == "under":
        L.append("| The Under wins | below the line; on a whole-number line a result AT the line is a push |")
    return L


def _r0(v):
    return "-" if v is None else f"{float(v):.0f}"


def role_table(card) -> list[str]:
    u = card.get("usage") or {}
    if not u:
        return []
    pct = lambda v: "-" if v is None else f"{100 * float(v):.0f}%"
    num = lambda v: "-" if v is None else f"{float(v):.1f}".rstrip("0").rstrip(".")
    L = [f"| Role (week {u.get('week')} vs his {u.get('n_base')} games before) | Last game | Before |", "|---|---:|---:|"]
    for k, word, f in (("snap", "Snap share", pct), ("ts", "Target share", pct), ("cs", "Carry share", pct),
                       ("tn", "Targets", num), ("cn", "Carries", num)):
        if u.get(k) is not None:
            L.append(f"| {word} | {f(u.get(k))} | {f(u.get(k + '_base'))} |")
    return L


def checks_table(checks) -> list[str]:
    L = ["| Check | The read says | The run says | Result |", "|---|---|---|---|"]
    for c in checks:
        res = "pass" if c["ok"] else f"**FAIL**: {c['detail']}"
        L.append(f"| {c['check']} | {_esc(c['stated'])} | {_esc(c['run'])} | {res} |")
    return L


def cutoff(run) -> str:
    """The report's data-cutoff line without its list-item label."""
    return re.sub(r"^-?\s*\*\*Data cutoff:\*\*\s*", "", run.get("data_cutoff") or "") or "-"


def _esc(s):
    return str(s).replace("|", "/").replace("\n", " ")


SECRET_PATTERNS = [re.compile(r"(?i)\b(api[_-]?key|apikey|access[_-]?token|token|secret|password|key)=[^&\s|)]+"),
                   re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{32}(?![0-9a-fA-F])")]


def scrub(text: str) -> str:
    """Key-shaped strings out of anything this writes: a query-string credential (apiKey=...) and a
    bare 32-hex key (the Odds API's shape). The 64-hex release hash is left alone."""
    text = SECRET_PATTERNS[0].sub(lambda m: m.group(1) + "=<redacted>", text)
    return SECRET_PATTERNS[1].sub("<redacted>", text)


# ---------------------------------------------------------------- the QA/QC version
def render_qa(run, reads, checks, release, report_md: str | None = None) -> str:
    """For chat and internal reviewers: the read as the external reader gets it, plus the backend
    under each leg -- every number with its source field, every check, the inputs and their age."""
    away, home, wk = run["away"], run["home"], run["week"]
    n_fail = sum(not c["ok"] for c in checks)
    me = run.get("market_env") or {}
    L = [f"# {away} at {home}, week {wk}: QA/QC read", "",
         f"Release **{release.get('tag') or 'unknown'}** ({str(release.get('hash') or '')[:12] or 'hash unknown'}, "
         f"{release.get('source') or 'source unknown'}) · run `{run['slug']}` · kickoff {str(run.get('kickoff_utc'))[:16]} UTC "
         f"({run.get('hours_to_kickoff') or 0:.1f} h after the run)", "",
         f"**Checks: {len(checks) - n_fail} of {len(checks)} pass.**"
         + ("" if not n_fail else f" {n_fail} FAIL: this read is not publishable until they are fixed."), "",
         "Judgment is not machine-checked: whether each condition is plausible, and whether the case "
         "follows from the evidence, is the reviewer's to judge (below, per leg).", "",
         "## The game", "", reads.get("thesis") or "*No thesis written.*", "",
         "| Frame | |", "|---|---|",
         f"| Spread / total | {home} {me.get('home_spread'):+g} / {me.get('total_line'):g} ({me.get('book')}, {str(me.get('as_of'))[:16]} UTC) |"
         if me.get("home_spread") is not None and me.get("total_line") is not None else "| Spread / total | not posted |"]
    for t, e in (run.get("teams") or {}).items():
        L.append(f"| {t} | implied {_fmt(e.get('implied_points'))} points; about {float(e.get('targets') or 0):.0f} throws, "
                 f"{float(e.get('carries') or 0):.0f} runs, {float((e.get('pass_td') or 0) + (e.get('rush_td') or 0)):.1f} "
                 f"offensive touchdowns (touchdowns {e.get('td_anchor')}-anchored) |")
    game_checks = [c for c in checks if c["leg"] == 0]
    L += ["", *(checks_table(game_checks) if game_checks else []), ""]
    for i, lg, mk, card, row, cells in legs_resolved(run, reads):
        L += [f"## Leg {i}: {lg['player']} {MARKET_WORDS.get(mk, mk)} {lg['side']} {float(lg['line']):g}", "",
              f"**If** {lg['condition']}", "", f"**The case.** {lg['case']}", "", f"**How it fails.** {lg['fails']}", "",
              *support_table(row, cells, str(lg["side"]).lower()), ""]
        rt = role_table(card)
        if rt:
            L += [*rt, ""]
        L += ["**Backend.**", ""]
        if card:
            L.append(f"- Card: {card.get('slot')}, {card.get('team')}; book {card.get('book')}, quote {card.get('quoted')}.")
            for k in ("capped", "season", "engine"):
                r = ((cells or {}).get("rows") or {}).get(k)
                if r and r.get("label"):
                    L.append(f"- The {k} rate's window: {r['label']} (rate {_fmt(r.get('rate'))}).")
            if cells and cells.get("note"):
                L.append(f"- Measured calibration for this market: {cells['note']}")
            if card.get("watch"):
                L.append("- The engine's flags: " + "; ".join(card["watch"]) + ".")
            if card.get("matchup"):
                L.append(f"- Matchup context: {card['matchup']}")
        if row:
            if row.get("implied") is not None:
                L.append(f"- Line implies (the {row.get('unit') or 'volume'} at which this line is a coin flip): "
                         f"{float(row['implied']):.1f}.")
            if row.get("market_edge") in ("min", "max"):
                L.append(f"- The market-implied search hit its {row['market_edge']} bound: the market's volume is outside it.")
            if row.get("flags"):
                L.append(f"- Research flags: {row['flags']}.")
        L += ["", "**Checks for this leg.**", "", *checks_table([c for c in checks if c["leg"] == i]), "",
              "**For the reviewer (not machine-checked):** is the condition something the evidence above makes "
              "possible, and does the case argue from this player's own rows?", ""]
    L += ["## Who plays (section 4)", ""]
    for t, cells_ in (run.get("who_plays") or {}).items():
        for unit, txt in cells_.items():
            L.append(f"- **{t} {unit}:** {txt}")
    L += ["", run.get("who_note") or "", "", "## Where the baseline could miss (section 7)", "",
          "| Matchup issue | What the baseline may miss | Separate scenario |", "|---|---|---|",
          *(f"| {_esc(a)} | {_esc(b)} | {_esc(c)} |" for a, b, c in run.get("gaps") or []), "",
          "## Inputs and their state", "", "| Source | Used for | Status | Detail |", "|---|---|---|---|",
          *(f"| {_esc(s['name'])} | {_esc(s['purpose'])} | {_esc(s['status'])} | {_esc(s['detail'])} |"
            for s in run.get("sources") or []), "",
          f"**Data cutoff:** {cutoff(run)}", "", "## Model states", "", run.get("model_states") or "-", ""]
    if report_md:
        L += ["## The engine's full report", "",
              "The game read above is a selection. The engine's report for this run is the reference copy: "
              f"`report_{run['slug']}.md`, in the same folder.", ""]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- the agent version
def render_agent(run, reads, checks, release, ci) -> str:
    """For another LLM agent: how the engine works end to end, from the repository to this run's
    inputs, models, tests and checks, and how the read reaches the external reader. The static
    parts are the release's own documents (agent_guide.md, engine_overview.md,
    data_source_matrix.md), embedded verbatim, so this file never restates them."""
    tag = release.get("tag")
    ref = tag or "main"
    res = lambda p: (ENGINE / "resources" / p).read_text(encoding="utf-8") if (ENGINE / "resources" / p).exists() else f"*{p}: DATA MISSING*"
    L = [f"# Props engine, end to end: {run['away']} at {run['home']}, week {run['week']}", "",
         "*For an LLM agent. Everything below is either this run's own data or a document shipped in "
         "the release that produced it; nothing is summarised from memory.*", "",
         "## 0. Identity", "", "| | |", "|---|---|",
         f"| Repository | {REPO_URL} |",
         f"| Release | {tag or 'unknown'} -- the code at {REPO_URL}/tree/{ref} |",
         f"| Release hash | {release.get('hash') or 'unknown'} (skill/release.py: sha256 over the release's files, LF-normalised) |",
         f"| How it was fetched | {release.get('source') or 'unknown'} |",
         f"| This run | `{run['slug']}`: kickoff {str(run.get('kickoff_utc'))[:16]} UTC, priced "
         f"{run.get('hours_to_kickoff') or 0:.1f} h before it |",
         f"| Data cutoff | {cutoff(run)} |", ""]
    L += [res("agent_guide.md").replace("{REF}", ref).replace("{REPO}", REPO_URL), ""]
    L += ["## 3. This run's inputs (the run's sources table, verbatim)", "",
          "| Source | Used for | Status | Detail |", "|---|---|---|---|",
          *(f"| {_esc(s['name'])} | {_esc(s['purpose'])} | {_esc(s['status'])} | {_esc(s['detail'])} |"
            for s in run.get("sources") or []), "",
          "### Where each source lives (resources/data_source_matrix.md, verbatim)", "",
          _demote(res("data_source_matrix.md")), ""]
    L += ["## 4. How the engine turns inputs into prices (resources/engine_overview.md, verbatim)", "",
          _demote(res("engine_overview.md")), ""]
    L += ["## 5. Validation", "", "### Model states at this run", "", run.get("model_states") or "-", "",
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
              "The check names map to the suites in section 2 (tests: props/tests and props/tests_ci; "
              "root-suite: tests/ and the release lock; backtest-smoke: the backtest on model changes; "
              "commit-hygiene: no per-run outputs committed; tick: the scheduled props capture, not a test). "
              "The test COUNT is not in the API's answer.", ""]
        if not any(c.get("name") in ("tests", "root-suite") for c in ci.get("checks") or []):
            L += ["DATA MISSING: no test-suite run was found for this release; nothing here says the suites passed.", ""]
    L += ["## 6. From this run to the external reader", "",
          "1. score_game.py priced the game and wrote the report and `run_<slug>.json` (section 2).",
          "2. The analyst (chat) wrote the reads file: a thesis and, per leg, a condition, the case, how it "
          "fails, the volume x efficiency it needs and every number it cites.",
          "3. publish.py checked the reads against the run (below). A failed check renders nothing.",
          "4. publish.py rendered the QA/QC version and this file from the same run and reads; the external "
          "PDF renders from them too.", "",
          "### Field map: what each reader-facing number is", "",
          "| On the page | Run field | Meaning |", "|---|---|---|",
          "| Market's chance of the Over | cards[].rows[].p_over_book | the book's Over and Under prices with the cut removed, scaled to 100% |",
          "| Engine's chance | cards[].rows[].p_over_model | share of 20,000 simulated games over the line (a push counts as not over) |",
          "| The Over needs | cards[].volume[].cells.need_out | floor(line) + 1 |",
          "| Engine's volume | cards[].volume[].cells.proj | mean of the simulated targets / catches / carries / completions |",
          "| Market-implied volume | cards[].rows[].market_volume | the volume at which the engine's chance equals the market's, at the engine's efficiency |",
          "| At his luck-capped / season / engine rate | cards[].volume[].cells.rows.{capped,season,engine} | vol = ceil(need_out / rate); pct = share of simulations reaching vol |",
          "| Role table | cards[].usage | last game vs the games before: snap, target and carry shares, counts |",
          "| Injuries | injuries[], who_plays | section 4: the prices' own status (Sleeper fills a missed practice) |", "",
          "### The reads and their checks", "", "```json", json.dumps(reads, indent=1, ensure_ascii=False), "```", "",
          *checks_table(checks), "",
          f"**{sum(c['ok'] for c in checks)} of {len(checks)} checks pass.** Judgment (whether a condition "
          "is plausible) is not machine-checked.", ""]
    L += ["## 7. Reproduce", "", "```bash",
          f"git clone {REPO_URL} && cd Fantasy-football && git checkout {ref}",
          "pip install -r requirements.txt",
          f"python props/engine/scripts/score_game.py --away {run['away']} --home {run['home']} --season {run['season']} --week {run['week']}",
          f"python props/engine/scripts/publish.py --run $NFL_OUT/run_{run['slug']}.json --reads reads.json --out $NFL_OUT",
          "```", "",
          "Prices move with the lines and the inputs' publication times: a re-run reproduces the method and "
          "the checks, not necessarily these exact numbers.", ""]
    return "\n".join(L) + "\n"


def _demote(md: str) -> str:
    """Embedded documents' headings go two levels down, so they nest under this file's sections."""
    return re.sub(r"(?m)^(#{1,4}) ", lambda m: "#" * min(6, len(m.group(1)) + 2) + " ", md)


def ci_results(repo_url, ref, get=None):
    """The GitHub check runs for a release: on the tag's commit, or -- the props CI runs on pull
    requests, not on main -- on the head of the pull request that merged it. None when GitHub
    cannot be read (DATA MISSING, never a guessed pass)."""
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
        # the suites run on the pull request's head; the merge commit carries what ran on main
        # (the scheduled capture, the push checks) -- both are reported, each labelled
        prs = get(f"{api}/commits/{sha}/pulls") or []
        pr = next((p for p in prs if p.get("merged_at")), prs[0] if prs else None)
        checks = (runs_at(pr["head"]["sha"], f"pull request #{pr['number']} head") if pr else []) \
            + runs_at(sha, "the tag's commit")
        return {"ref": ref, "sha": sha, "pr": pr["number"] if pr else None, "checks": checks}
    except Exception:  # noqa: BLE001 -- any failure is DATA MISSING, said so in the file
        return None


# ---------------------------------------------------------------- command line
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--run", required=True, help="run_<slug>.json from score_game.py")
    ap.add_argument("--reads", required=True, help="the reads file (resources/agent_guide.md, 'The reads file')")
    ap.add_argument("--out", required=True)
    ap.add_argument("--which", default="qa,agent", help="comma list: qa, agent")
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
        rep = Path(a.run).with_name(f"report_{run['slug']}.md")
        p = out / f"{run['slug']}_qa.md"
        p.write_text(scrub(render_qa(run, reads, checks, release, rep.read_text(encoding="utf-8") if rep.exists() else None)),
                     encoding="utf-8")
        print(f"wrote {p}")
    if "agent" in which:
        ci = None if a.no_ci or not a.release_tag else ci_results(REPO_URL, a.release_tag)
        p = out / f"{run['slug']}_agent.md"
        p.write_text(scrub(render_agent(run, reads, checks, release, ci)), encoding="utf-8")
        print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
