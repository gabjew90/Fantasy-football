"""Reading a reachability check: can this environment reach a data source, and
if not, would an API key help?

The chat container is refused by FantasyPros' keyless partner feed (HTTP 403,
every session). FantasyPros' official API takes the user's key -- held only
in the GitHub secrets -- and would also bring practice participation and
game-status probabilities. Before the user rebuilds the chat skill to carry
that key, the check says which it would be. The requests themselves are made
by the module that owns them (manager/fantasypros.reachability), with the
real fetch's own URL and headers, so the check tests what the commands
actually send; this module only classifies the answers. Stdlib only.

What a 403 can and cannot tell. An HTML block page is a bot wall: a key would
not get past it. A 403 carrying JSON is the server answering, which is what
FantasyPros' API returns to any request without a key -- {"message":
"Forbidden"}, as seen from outside chat on 2026-09-26 -- but an address
block at the same gateway can answer the same way. So a JSON 403 that
matches the no-key answer is "consistent with a missing key", never proof;
only a keyed call settles it.
"""

from __future__ import annotations

NO_KEY_ANSWER = '{"message":"Forbidden"}'      # the API's reply to a keyless request, from outside chat


def evidence(code, content_type: str, body: str) -> str:
    snip = " ".join((body or "").split())[:80]
    return f"HTTP {code}, {content_type or 'no content type'}, body {snip!r}"


def classify(code: int | None, content_type: str, body: str, error: str | None = None) -> tuple[str, str]:
    """(status, what it means -- with the evidence). status is 'fresh' when
    the source answered with data, 'failed' otherwise: the words the session
    log counts."""
    if error is not None:
        return "failed", f"unreachable from here ({error}): neither a key nor a rebuild helps"
    low = (body or "")[:2000].lower()
    walled = "html" in (content_type or "").lower() or "<html" in low or "cloudflare" in low or "captcha" in low
    ev = evidence(code, content_type, body)
    if code == 200:
        return "fresh", f"reachable: it answered ({ev})"
    if code in (401, 403) and walled:
        return "failed", f"a bot wall, an HTML block page: a key would not get past it ({ev})"
    if code in (401, 403) and " ".join((body or "").split()) == NO_KEY_ANSWER:
        return "failed", ("the API's no-key answer, the same one it gives from outside chat: consistent with a "
                          f"missing key, so a key should help -- only a keyed call can rule out an address block ({ev})")
    if code in (401, 403):
        return "failed", f"refused, with an answer unlike the API's no-key reply: a key may not help ({ev})"
    return "failed", f"answered, but not with data ({ev})"


def markdown(rows: list[dict]) -> str:
    L = ["## Can this environment reach the data sources?", "",
         "| Source | Result | What it means |", "|---|---|---|"]
    for r in rows:
        mark = {"fresh": "OK", "absent": "--"}.get(r["status"], "NO")
        L.append(f"| {r['name']} | {mark} | {r['detail']} |")
    return "\n".join(L) + "\n"
