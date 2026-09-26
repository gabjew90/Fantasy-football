"""Can this environment reach a data source, and if not, why?

The chat container is refused by FantasyPros' keyless partner feed (HTTP 403,
every session). FantasyPros' official API takes the user's key -- which only
the GitHub secrets hold -- and would also bring practice participation and
game-status probabilities. Before the user rebuilds the chat skill to carry
that key, this answers whether it would help: an API that REACHES and refuses
for the missing key is fixed by a key; a bot wall (an HTML block page) or no
connection is not. No key is sent, and none is read -- only whether
FANTASYPROS_API_KEY is set, as a boolean.

Stdlib only.
"""

from __future__ import annotations

import os
import urllib.error
import urllib.request

TIMEOUT = 15
PROBES = (
    ("FantasyPros partner feed (keyless projections)",
     "https://partners.fantasypros.com/api/v1/consensus-rankings.php?position=RB&scoring=PPR&type=ros&year=2026"),
    ("FantasyPros API (keyed: projections, injuries, practice)",
     "https://api.fantasypros.com/public/v2/json/nfl/injuries?year=2026&week=1"),
)


def classify(code: int | None, content_type: str, body: str, error: str | None = None) -> tuple[str, str]:
    """(status, what it means). status: 'fresh' when the source answered,
    'failed' otherwise -- the words the session log already counts."""
    if error is not None:
        return "failed", f"unreachable from here ({error}): neither a key nor a rebuild helps"
    low = (body or "")[:2000].lower()
    walled = "html" in (content_type or "").lower() or "<html" in low or "cloudflare" in low or "captcha" in low
    if code == 200:
        return "fresh", "reachable: it answered"
    if code in (401, 403) and walled:
        return "failed", f"HTTP {code} from a bot wall (an HTML block page): a key would not get past it"
    if code in (401, 403):
        return "failed", (f"HTTP {code} as data (not a block page): the server was reached and refused the "
                          "request as unauthorised -- a key is what it wants")
    return "failed", f"HTTP {code}: answered, but not with data"


def probe(url: str) -> tuple[str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "nfl-research/1.0 (reachability check)",
                                               "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return classify(r.status, r.headers.get("Content-Type", ""), r.read(4096).decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        body = e.read(4096).decode("utf-8", "replace") if e.fp else ""
        return classify(e.code, e.headers.get("Content-Type", "") if e.headers else "", body)
    except Exception as e:  # noqa: BLE001 -- the point is to report it
        return classify(None, "", "", f"{type(e).__name__}: {e}"[:120])


def run() -> list[dict]:
    """One row per probe, in the session log's input shape."""
    rows = [{"name": name, "source": url.split("?")[0], "status": st, "detail": what, "age_h": 0.0}
            for name, url in PROBES for st, what in [probe(url)]]
    rows.append({"name": "FANTASYPROS_API_KEY in this environment", "source": "environment",
                 "status": "fresh" if os.environ.get("FANTASYPROS_API_KEY") else "failed",
                 "detail": "set" if os.environ.get("FANTASYPROS_API_KEY") else "not set", "age_h": 0.0})
    return rows


def markdown(rows: list[dict]) -> str:
    L = ["## Can this environment reach the data sources?", "",
         "| Source | Result | What it means |", "|---|---|---|"]
    for r in rows:
        L.append(f"| {r['name']} | {'OK' if r['status'] == 'fresh' else 'NO'} | {r['detail']} |")
    return "\n".join(L) + "\n"
