"""Yahoo draft-room pick poller -> local pick file (Keefamania draft day).

Attaches to the user's REAL Chrome (launched with
--remote-debugging-port=9222, see KEEFAMANIA DRAFT.bat) so the logged-in
Yahoo session is reused — no credentials anywhere. Every POLL_S seconds it
extracts the pick list from the draft-room DOM and idempotently replaces the
local pick file the dashboard tracker reads. Manual entry on the dashboard
remains the fallback at all times: if this window prints errors, just click.

The DOM extraction is a best-effort guess until validated in a mock draft
(the item-12 rehearsal); --probe prints what it currently sees so the
selector can be fixed live without restarting anything else.

Usage:
    pip install playwright   (one-time; browsers NOT needed — CDP attach only)
    python scripts/yahoo_draft_poller.py [--probe] [--interval 3]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Extraction runs inside the draft room page. Yahoo's draft client renders
# picks in a results/board pane; we scan likely containers for ordered
# "player name + position" rows and fall back to any element list that looks
# like one. Validated + hardened during the mock rehearsal.
# VALIDATED in the 2026-08-30 live mock rehearsal (full 10-team room):
# the left panel's "Picks" tab is a feed of entries shaped
#   "<pick#> <drafter> <J. Name> [Q|CEL|PUP|IR-R ...] <POS> <Tm> Bye <n>"
# interleaved with join/left chatter. document.title carries the on-clock
# state ("YOUR TURN, DRAFT NOW" / "N picks until your turn" / "Draft
# Complete"). Names are ABBREVIATED — LocalDraft.resolve handles the
# initial+surname form and strips status tags.
EXTRACT_JS = """
async () => {
  const tab = [...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'Picks');
  if (tab) { tab.click(); await new Promise(r => setTimeout(r, 600)); }
  const entries = [];
  document.querySelectorAll('div,li').forEach(e => {
    if (e.children.length > 8) return;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    const m = t.match(/^(\d+) (.{1,25}?) ([A-Z]\.[\w.' -]{1,24}?) (?:Q |D |O |IR |IR-R |CEL |PUP |NA )?(QB|RB|WR|TE|K|DEF) ([A-Za-z]{2,3}) Bye (\d+)$/);
    if (m) entries.push({n: +m[1], name: m[3], pos: m[4]});
  });
  const uniq = {};
  entries.forEach(e => uniq[e.n] = e);
  return {title: document.title, picks: Object.values(uniq)};
}
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=float, default=3.0)
    ap.add_argument("--cdp", default="http://127.0.0.1:9222")
    ap.add_argument("--league", default="keefamania")
    ap.add_argument("--probe", action="store_true",
                    help="print one extraction and exit (selector debugging)")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright not installed: run  pip install playwright  (no browser "
              "download needed — this only attaches to your running Chrome)")
        return 2

    import os
    os.environ["DRAFTKIT_LEAGUE"] = args.league
    from draftkit.config import Config
    from draftkit.picksource import LocalDraft
    import polars as pl

    cfg = Config.load()
    exp = cfg.get("expected") or {}
    tiers = pl.read_csv(cfg.scoped(cfg.root / "tiers.csv"), infer_schema_length=2000)
    board = list(tiers.iter_rows(named=True))
    src = LocalDraft(cfg.path("logs") / f"local_{cfg.league_name}_picks.json",
                     board, int(exp.get("teams", 10)), int(exp.get("rounds", 15)))

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(args.cdp)
        page = None
        for ctx in browser.contexts:
            for pg in ctx.pages:
                if "draftclient" in pg.url or ("fantasysports.yahoo" in pg.url and "draft" in pg.url):
                    page = pg
        if page is None:
            print("no Yahoo draft-room tab found — open the draft room in the "
                  "Chrome window this script attached to, then rerun")
            return 1
        print(f"attached to draft room: {page.url[:80]}")
        seen: dict[int, dict] = {}
        last_n = -1
        while True:
            try:
                out = page.evaluate(EXTRACT_JS)
            except Exception as e:  # noqa: BLE001
                print(f"extract failed ({e.__class__.__name__}) — manual entry "
                      f"on the dashboard still works; retrying")
                time.sleep(args.interval)
                continue
            title = out.get("title", "")
            for e in out.get("picks", []):
                seen[int(e["n"])] = e
            if args.probe:
                print(f"probe: title={title!r}; {len(seen)} picks; "
                      f"first 3: {list(seen.values())[:3]}")
                return 0
            # feed may trim old entries: accumulate by pick number, placeholder
            # any gap so later picks keep the right snake slot
            max_n = max(seen) if seen else 0
            names = [seen[i]["name"] if i in seen else f"Unknown Pick{i}"
                     for i in range(1, max_n + 1)]
            if len(names) != last_n:
                src.set_picks(names)
                last_n = len(names)
                print(f"{time.strftime('%H:%M:%S')} picks: {last_n} | {title[:40]}")
            if "Draft Complete" in title:
                print("draft complete — poller exiting")
                return 0
            # adaptive cadence (mock lesson: rooms can burst 6 picks in 15s
            # when teams autodraft) — tighten near my turn
            m = __import__("re").search(r"(\d+) picks until", title)
            close = ("YOUR TURN" in title or "You are next" in title
                     or (m and int(m.group(1)) <= 3))
            time.sleep(max(1.0, args.interval / 3) if close else args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
