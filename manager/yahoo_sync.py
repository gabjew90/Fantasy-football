"""Pull the Yahoo resources the manager reads and commit them, so the
scheduled jobs need no Yahoo secret.

Yahoo's OAuth needs a sign-in on the machine that runs it, and the user is
not pasting refresh tokens into GitHub. So the machine that signed in does
the reading: this job fetches every resource YahooSource asks for and
writes each payload under state/<league>/yahoo/, one file per resource
with the time it was fetched. The .bat that runs it commits and pushes
state/, exactly as the Vegas snapshot job does. On Actions, yahoo_api.get
finds no credentials and answers from these files instead; YahooSource
reports their age so a stale sync is visible in every brief.

Resources, and why each: settings (scoring, roster shape, playoff and
waiver rules), teams/roster (every roster with slots and designations),
teams (waiver priority), standings (records), scoreboard for this week
(matchups) and last week (the ledger's actuals), transactions (trade
watch, the FAAB accounting).
"""

from __future__ import annotations

import logging
import time

from . import yahoo_api

log = logging.getLogger("manager")


def resources(league_id: str, week: int) -> list[str]:
    key = f"league/nfl.l.{league_id}"
    paths = [f"{key}/settings", f"{key}/teams/roster", f"{key}/teams", f"{key}/standings",
             f"{key}/scoreboard;week={int(week)}", f"{key}/transactions;count=50"]
    if int(week) > 1:
        paths.append(f"{key}/scoreboard;week={int(week) - 1}")
    return paths


def sync(cfg, week: int, get=None, directory=None) -> dict:
    """Fetch and write every resource. Returns {path: 'ok' | 'FAILED: why'}.
    A failure on one resource does not stop the others: an old file that
    still reads is better than a missing one."""
    get = get or yahoo_api.get
    league_id = str(getattr(cfg, "league_id", None) or cfg.get("league_id"))
    out: dict[str, str] = {}
    t0 = time.time()
    for path in resources(league_id, week):
        try:
            payload = get(path)
            yahoo_api.write_cached(path, payload, directory)
            out[path] = "ok"
        except Exception as e:  # noqa: BLE001
            out[path] = f"FAILED: {e.__class__.__name__}: {str(e)[:100]}"
            log.warning("yahoo-sync: %s -> %s", path, out[path])
    ok = sum(1 for v in out.values() if v == "ok")
    log.info("yahoo-sync: %d/%d resources in %.1fs", ok, len(out), time.time() - t0)
    return out
