"""FantasyPros preseason projection history from the Wayback Machine, and the
`fpros` arm for the projection backtest (DECISIONS #49).

The 2026 Keefamania sheet is a FantasyPros export with no history in the
repo, so #44/#45 could not gate it. FantasyPros' draft projections page
(nfl/projections/<pos>.php?week=draft) is archived; the page is static
once the season starts (the November 2024 RB capture still shows McCaffrey
at 280.6, his preseason number), so a post-kickoff capture of the draft
page is still the preseason table. Stat columns are the same layout as the
sheet's position tabs (external.SHEET_COLS), scored here in league scoring
so the FPTS column and its unknown scoring never enter.

    venv\\Scripts\\python.exe scripts\\fantasypros_history.py --fetch --seasons 2024,2025
    venv\\Scripts\\python.exe scripts\\fantasypros_history.py --attach keefamania
    venv\\Scripts\\python.exe scripts\\source_gate.py --rows reports/projection_backtest.keefamania.fpros.rows.csv,reports/projection_backtest.omnibeta.fpros.rows.csv --candidate fpros --rivals blend,lines --out reports/fpros_gate.md

Files: data/external/fantasypros_history/fpros_<season>_<pos>.csv, one row
per player with the stat line, the capture timestamp and the archived URL.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from draftkit.external import SHEET_COLS  # noqa: E402
from draftkit.seasondata import score_projection  # noqa: E402

OUT = ROOT / "data" / "external" / "fantasypros_history"
UA = {"User-Agent": "Mozilla/5.0 draftkit-history/1.0"}
# regular-season kickoff (Thursday opener) per season: a capture on or before
# it is a genuine preseason table; after it the draft page is static
KICKOFF = {2023: "20230907", 2024: "20240905", 2025: "20250904"}
POS = ("QB", "RB", "WR", "TE")


def cdx(pos: str, season: int) -> list[tuple[str, str]]:
    """(timestamp, original url) for every 200 capture of the draft page and
    its query variants in the season's Jul-Dec window."""
    q = urllib.parse.urlencode({
        "url": f"fantasypros.com/nfl/projections/{pos.lower()}.php", "matchType": "prefix",
        "from": f"{season}0701", "to": f"{season}1231", "filter": "statuscode:200",
        "fl": "timestamp,original", "output": "json"})
    raw = urllib.request.urlopen(urllib.request.Request("https://web.archive.org/cdx/search/cdx?" + q, headers=UA), timeout=90).read()
    rows = json.loads(raw or b"[]")
    return [(r[0], r[1]) for r in rows[1:] if "week=draft" in r[1]]


def pick_captures(caps: list[tuple[str, str]], season: int) -> list[tuple[str, str, str]]:
    """Candidates in preference order: captures in [Aug 1, kickoff] latest
    first (genuine preseason tables), then captures after kickoff earliest
    first (the draft page is static by then). (timestamp, url, kind)."""
    k = KICKOFF[season]
    pre = sorted([c for c in caps if f"{season}0801" <= c[0][:8] <= k], reverse=True)
    post = sorted([c for c in caps if c[0][:8] > k])
    return [(t, u, "preseason") for t, u in pre] + [(t, u, "post-kickoff static") for t, u in post]


class _Table(HTMLParser):
    """Rows of <table id="data">: header cells and body cells as text."""

    def __init__(self):
        super().__init__()
        self.in_table = self.in_head = self.in_body = self.in_cell = False
        self.head: list[list[str]] = []
        self.rows: list[list[str]] = []
        self.cur: list[str] = []
        self.buf: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table" and a.get("id") == "data":
            self.in_table = True
        if not self.in_table:
            return
        if tag == "thead":
            self.in_head = True
        elif tag == "tbody":
            self.in_body = True
        elif tag == "tr":
            self.cur = []
        elif tag in ("td", "th"):
            self.in_cell = True
            self.buf = []

    def handle_endtag(self, tag):
        if not self.in_table:
            return
        if tag in ("td", "th") and self.in_cell:
            self.in_cell = False
            self.cur.append(re.sub(r"\s+", " ", "".join(self.buf)).strip())
        elif tag == "tr":
            if self.in_head:
                self.head.append(self.cur)
            elif self.in_body and self.cur:
                self.rows.append(self.cur)
        elif tag == "thead":
            self.in_head = False
        elif tag == "tbody":
            self.in_body = False
        elif tag == "table":
            self.in_table = False

    def handle_data(self, data):
        if self.in_cell:
            self.buf.append(data)


def _get(url: str) -> str:
    import gzip
    r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180)
    b = r.read()
    # the raw (id_) route hands back the original bytes, sometimes still
    # gzip-compressed (the December 2024 WR capture); the wrapped route is
    # always decoded
    if b[:2] == bytes([0x1F, 0x8B]):
        b = gzip.decompress(b)
    return b.decode("utf-8", "ignore")


def fetch_table(ts: str, url: str) -> tuple[list[str], list[list[str]]]:
    """The wrapped capture first (Wayback decodes it and rewrites only URLs,
    never table text), the raw id_ route as the fallback."""
    for u in (f"https://web.archive.org/web/{ts}/{url}", f"https://web.archive.org/web/{ts}id_/{url}"):
        p = _Table()
        p.feed(_get(u))
        if p.rows:
            return (p.head[-1] if p.head else []), p.rows
    raise SystemExit(f"no table#data rows in capture {ts} of {url}")


def split_name(cell: str) -> tuple[str, str]:
    """'Josh Allen BUF' -> ('Josh Allen', 'BUF'); a name without a team tag
    comes back with an empty team."""
    parts = cell.split()
    if len(parts) >= 2 and re.fullmatch(r"[A-Z]{2,3}", parts[-1]):
        return " ".join(parts[:-1]), parts[-1]
    return cell, ""


def fetch(seasons: list[int]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for season in seasons:
        for pos in POS:
            caps = cdx(pos, season)
            got = None
            for ts, url, kind in pick_captures(caps, season):
                try:
                    head, rows = fetch_table(ts, url)
                except SystemExit as e:
                    print(f"  skip {ts}: {e}", flush=True)
                    continue
                got = (ts, url, kind, head, rows)
                break
            if not got:
                print(f"{season} {pos}: no usable draft-page capture", flush=True)
                continue
            ts, url, kind, head, rows = got
            cols = SHEET_COLS[pos]
            out = OUT / f"fpros_{season}_{pos}.csv"
            with open(out, "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(["name", "team", *cols, "fpts_page", "snapshot", "kind", "url"])
                n = 0
                for r in rows:
                    if len(r) < 1 + len(cols):
                        continue
                    name, team = split_name(r[0])
                    nums = [x.replace(",", "") for x in r[1:1 + len(cols)]]
                    fpts = r[1 + len(cols)].replace(",", "") if len(r) > 1 + len(cols) else ""
                    w.writerow([name, team, *nums, fpts, ts, kind, url])
                    n += 1
            print(f"{season} {pos}: {n} players, capture {ts} ({kind}), header {head}", flush=True)


def norm(name: str) -> str:
    n = re.sub(r"\s+(Jr\.?|Sr\.?|III|II|IV|V)$", "", name.strip())
    return re.sub(r"[^a-z]", "", n.lower())


def attach(league: str) -> None:
    """Add an `fpros` column to the league's backtest rows: the FantasyPros
    preseason line for season T of each pair, scored in league scoring, a
    17-game season total like the other arms. Unmatched rows stay null so
    source_gate's common-set rule handles them."""
    from draftkit.config import Config
    cfg = Config.load(league=league)
    scoring = {k: float(v) for k, v in (cfg.get("scoring") or (cfg.get("expected") or {}).get("scoring") or {}).items()}
    src = ROOT / "reports" / f"projection_backtest.{league}.rows.csv"
    rows = pl.read_csv(src, infer_schema_length=10000)
    lines: dict[tuple[str, str, str], float] = {}
    for f in sorted(OUT.glob("fpros_*_*.csv")):
        season, pos = f.stem.split("_")[1:3]
        for r in csv.DictReader(open(f, encoding="utf-8", newline="")):
            try:
                line = {c: float(r[c]) for c in SHEET_COLS[pos] if r.get(c) not in (None, "")}
            except ValueError:
                continue
            lines[(season, pos, norm(r["name"]))] = float(score_projection(line, scoring))
    if not lines:
        raise SystemExit("no history files: run --fetch first")
    vals = []
    for r in rows.iter_rows(named=True):
        t = str(r["pair"]).split("->")[-1]
        vals.append(lines.get((t, r["pos"], norm(r["name"]))))
    out = rows.with_columns(pl.Series("fpros", vals, dtype=pl.Float64))
    dst = src.with_name(f"projection_backtest.{league}.fpros.rows.csv")
    out.write_csv(dst)
    by_pair = out.group_by("pair").agg(pl.len().alias("rows"), pl.col("fpros").is_not_null().sum().alias("fpros"))
    print(f"{league}: {out.height} rows, {out['fpros'].is_not_null().sum()} with an fpros line -> {dst.name}")
    print(by_pair.sort("pair"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--seasons", default="2024,2025")
    ap.add_argument("--attach", default=None, metavar="LEAGUE")
    a = ap.parse_args()
    if a.fetch:
        fetch([int(s) for s in a.seasons.split(",")])
    if a.attach:
        attach(a.attach)
    if not a.fetch and not a.attach:
        ap.error("--fetch and/or --attach LEAGUE")


if __name__ == "__main__":
    main()
