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
EXTRACT_JS = """
() => {
  const out = [];
  const seen = new Set();
  const rows = document.querySelectorAll(
    '[class*="draft-result"] li, [class*="DraftResults"] li, ' +
    '[class*="pick-list"] li, [class*="Picks"] li, table tbody tr');
  rows.forEach(r => {
    const t = (r.innerText || '').replace(/\\s+/g, ' ').trim();
    const m = t.match(/([A-Z][\\w.'-]+(?: [A-Z][\\w.'-]+)+)\\s*[\\u2013-]?\\s*[A-Za-z]{2,3}\\s*-\\s*(QB|RB|WR|TE|K|DEF)/);
    if (m && !seen.has(m[1])) { seen.add(m[1]); out.push({name: m[1], pos: m[2]}); }
  });
  return out;
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
        last_n = -1
        while True:
            try:
                picks = page.evaluate(EXTRACT_JS)
            except Exception as e:  # noqa: BLE001
                print(f"extract failed ({e.__class__.__name__}) — manual entry "
                      f"on the dashboard still works; retrying")
                time.sleep(args.interval)
                continue
            if args.probe:
                print(f"probe: {len(picks)} picks seen; first 5: {picks[:5]}")
                return 0
            if len(picks) != last_n:
                src.set_picks([p["name"] for p in picks])
                last_n = len(picks)
                print(f"{time.strftime('%H:%M:%S')} picks: {last_n}"
                      + (f" (latest: {picks[-1]['name']})" if picks else ""))
            time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
