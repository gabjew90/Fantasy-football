"""FantasyPros: a third projection source, and the expert panel behind it.

WHY A THIRD SOURCE, AND WHAT IT IS AND IS NOT WORTH.

Adding a source shrinks the disagreement BETWEEN sources. That was never the
big term. Measured against this repo's own out-of-sample backtest
(reports/projection_backtest.<league>.md, the `lines` arm scored on actuals),
the top-36 MAE on a season total runs 59-69 points at RB and 65-85 at WR in a
full-PPR league, while ESPN and Sleeper sit 16-21 points apart. The shops
agree with each other several times more closely than any of them agrees with
the season that actually happens.

So this is NOT here to sharpen a point estimate. It is here because:

  * IT IS GENUINELY INDEPENDENT. After removing the level difference, it sits
    12-16 points from our two-source consensus at the top of the board --
    about as far as ESPN and Sleeper sit from each other. It is not a scaled
    copy, so it earns its place in the mean.
  * IT COVERS K AND DST, WHICH NOTHING ELSE DOES. The Sleeper request names
    QB/RB/WR/TE only and the draft sheet left with the draft, so kickers and
    defences had NO consensus at all. Note what this does and does not buy:
    they arrive at n=1, and consensus.apply needs min_sources=2, so the
    projections are still NOT re-based -- Eddy Pineiro stays on his August
    board number with a FantasyPros opinion recorded beside it. What it buys
    today is evidence where there was none (waiver_brief._stale_reserve can
    finally see a shelved kicker); re-basing needs a second K/DEF source.
  * IT CARRIES THE PANEL, NOT JUST A NUMBER. `type=draft` is ~149 experts
    with per-player best/worst/sd and FantasyPros' own tier numbers. Ranks
    are the half of the instrument that has measured skill (top-36 Spearman
    0.59-0.63 at RB against an MAE that is useless), so the tier gate is
    built on these rather than on our own points.

IT RUNS HOT, AND THAT HAS TO COME OUT. Top-36 ratios against our consensus
are RB 1.116, WR 1.096, TE 1.102 -- implying about 15.3 of 17 games. It looks
like a full-health number where our sources carry an availability haircut.
consensus.build already rescales every source by a median ratio, which
handles it; the danger is only if this source is allowed to BOUND the common
population used to fit those ratios, which is why build() fits per source
against Sleeper rather than over a global intersection.

ON THE ENDPOINT. api.fantasypros.com/v2 is partner-gated and returns an
identical AWS `ForbiddenException` for a real key, a bogus key and no key at
all, so a developer key buys nothing there. partners.fantasypros.com serves
the same payload -- the one the public ranking pages embed as `ecrData` --
and needs no key. No key is sent from here, so there is none to leak.

ROS RANKS ARE A THREE-PERSON PANEL. `type=ros` carries points for every
position but its rank fields come from 3 experts, so a 0.00 rank_std there
means three people agreed, not that the market is settled. Ranks come from
`type=draft` (~149 experts) instead, and the freshness limit is recorded on
the way out rather than papered over.
"""

from __future__ import annotations

import logging
import time as _time

import requests

log = logging.getLogger("manager")

URL = "https://partners.fantasypros.com/api/v1/consensus-rankings.php"
TTL = 6 * 3600
TIMEOUT = 30

# FantasyPros positions -> ours. DST is a team unit; Sleeper keys those by the
# team abbreviation, not a player id, so it matches on team and never on name.
POSITIONS = {"QB": "QB", "RB": "RB", "WR": "WR", "TE": "TE", "K": "K", "DST": "DEF"}

# Where the two feeds spell a franchise differently. Sleeper on the right.
TEAM_ALIAS = {"JAC": "JAX", "LA": "LAR", "WSH": "WAS", "OAK": "LV", "SD": "LAC"}

# `type=ros` is the only one that publishes rest-of-season POINTS; `type=draft`
# is the only one that publishes TIERS and a panel worth the name.
ROS, DRAFT, WEEKLY = "ros", "draft", "weekly"


def scoring_slug(scoring: dict) -> str:
    """PPR / HALF / STD from the league's own reception value.

    FantasyPros publishes three presets and nothing between them. A league
    scoring receptions at anything else gets the nearest preset and a note --
    silently serving a half-PPR number into a full-PPR league would move
    every pass-catcher by 30 points and look like a projection change.
    """
    rec = float((scoring or {}).get("rec", 0.0) or 0.0)
    if rec >= 0.75:
        return "PPR"
    return "HALF" if rec >= 0.25 else "STD"


def _rows(pos: str, slug: str, season, kind: str, week: int | None = None):
    params = {"position": pos, "scoring": slug, "type": kind, "year": season}
    if kind == WEEKLY:
        params["week"] = int(week or 1)
    r = requests.get(URL, params=params, timeout=TIMEOUT,
                     headers={"User-Agent": "draftkit/1.0 (fantasy manager)"})
    r.raise_for_status()
    body = r.json()
    return body.get("players") or [], body


def _num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f


def _index_by_name(index):
    """normalised name -> [sleeper_id], and team -> sleeper_id for defences."""
    from draftkit.ids import normalize_name
    by_norm: dict[str, list[str]] = {}
    by_team: dict[str, str] = {}
    for pid, d in (index or {}).items():
        if not isinstance(d, dict):
            continue
        pos = d.get("position")
        if pos == "DEF":
            tm = (d.get("team") or "").upper()
            if tm:
                by_team[tm] = str(pid)
            continue
        nm = d.get("full_name") or d.get("last_name")
        if nm and pos:
            by_norm.setdefault(normalize_name(nm), []).append(str(pid))
    return by_norm, by_team


def fetch(scoring: dict, season, index, kind: str = ROS, week: int | None = None,
          store=None) -> tuple[dict[str, dict], str | None]:
    """sleeper_id -> {pts, ecr, best, worst, sd, tier, pos, owned}. Plus a note.

    `best`/`worst` are RANKS, so lower is better -- the same convention
    manager.ecr uses, and the opposite of every points field in the repo.

    Degrades to ({}, "DATA MISSING: ...") rather than raising. A projection
    source that cannot be reached must not take the brief down with it, and a
    silent empty dict would let the consensus quietly drop to two sources
    without saying so.
    """
    from draftkit.ids import normalize_name

    slug = scoring_slug(scoring)
    ckey = f"fantasypros:{kind}:{slug}:{season}:{week or 0}"
    if store is not None:
        cached = store.get(ckey)
        if cached and _time.time() - cached.get("ts", 0) < TTL:
            return cached["data"], cached.get("note")

    if not index:
        return {}, "DATA MISSING: fantasypros unmatched (no player index)"

    by_norm, by_team = _index_by_name(index)
    out: dict[str, dict] = {}
    stamps, ambiguous, unmatched = [], 0, 0
    failed: list[str] = []
    for fp_pos, our_pos in POSITIONS.items():
        try:
            rows, body = _rows(fp_pos, slug, season, kind, week)
        except Exception as e:  # noqa: BLE001
            # KEEP WHAT WE HAVE. A timeout on DST -- the last of six -- used
            # to discard 446 skill rows already parsed and drop the consensus
            # to two sources for that build. injuries() in this same module
            # degrades partially; these two must not disagree.
            failed.append(f"{fp_pos} ({e.__class__.__name__})")
            continue
        if body.get("last_updated"):
            stamps.append(str(body["last_updated"]))
        for row in rows:
            if our_pos == "DEF":
                tm = (row.get("player_team_id") or "").upper()
                pid = by_team.get(TEAM_ALIAS.get(tm, tm))
            else:
                # index.get, NOT index[x]. _index_by_name stringifies ids
                # into by_norm; subscripting the caller's dict with a key we
                # coerced turns an int-keyed index into a KeyError instead of
                # a clean miss. _espn avoids this by not stringifying at all.
                cand = [x for x in by_norm.get(
                    normalize_name(row.get("player_name") or ""), [])
                    if (index.get(x) or {}).get("position") == our_pos]
                if len(cand) > 1:
                    # AMBIGUOUS NAMES ARE DROPPED, NOT GUESSED -- the same
                    # rule _espn follows. A wrong match does not show up as a
                    # missing player, it shows up as a lineup change.
                    ambiguous += 1
                    continue
                pid = cand[0] if cand else None
            if not pid:
                unmatched += 1
                continue
            out[pid] = {
                # The FantasyPros id, which the keyed injuries endpoint needs
                # to filter on. Carried here because THIS feed is uncapped and
                # that one is not: the crosswalk is free, the bulk pull is not.
                "fp_id": row.get("player_id"),
                "yahoo_id": row.get("player_yahoo_id"),
                "pts": _num(row.get("r2p_pts")),
                "ecr": _num(row.get("rank_ecr")),
                "best": _num(row.get("rank_min")),
                "worst": _num(row.get("rank_max")),
                "sd": _num(row.get("rank_std")),
                "tier": _num(row.get("tier")),
                "pos": our_pos,
                "pos_rank": row.get("pos_rank"),
                "owned": _num(row.get("player_owned_avg")),
                "experts": body.get("total_experts"),
            }

    # THE DIAGNOSTIC HAS TO SURVIVE AN EMPTY RESULT. "matched no players" on
    # its own sends you looking at the network when the answer is that every
    # row hit an ambiguous name, which is a player-index problem instead.
    why = (f", {ambiguous} ambiguous names dropped" if ambiguous else "") +           (f", {unmatched} unmatched" if unmatched else "")
    if failed:
        why += f", NO DATA for {', '.join(failed)}"
    if not out:
        # DO NOT CACHE AN EMPTY RESULT. A momentarily malformed player index
        # fails every name join, and caching that for the 6h TTL keeps the
        # consensus on two sources long after the index recovers.
        return out, f"DATA MISSING: fantasypros matched no players{why}"
    note = (f"fantasypros {kind} {slug}: {len(out)} players" + why
            + (f", updated {sorted(stamps)[-1]}" if stamps else ""))
    if failed:
        note = "⚠ " + note
    if store is not None:
        store.set(ckey, {"ts": _time.time(), "data": out, "note": note})
    return out, note


def points(scoring: dict, season, index, store=None
           ) -> tuple[dict[str, float], str | None]:
    """The consensus seam's shape: sleeper_id -> season points.

    Rest-of-season, because that is what an in-season decision is about and
    the only `type` that publishes points for all six positions.
    """
    rows, note = fetch(scoring, season, index, kind=ROS, store=store)
    if not rows:
        return {}, note
    return ({pid: r["pts"] for pid, r in rows.items() if r.get("pts")}, note)


# ---------------------------------------------------------------- injuries
#
# WHAT THIS ADDS THAT WE DID NOT ALREADY HAVE.
#
# Sleeper's player index carries `injury_status` for 776 players and
# `injury_body_part` for 698, so the LABEL was never missing. What is missing
# is everything behind it: `practice_participation` and `practice_description`
# are null on all 776 rows, and there has never been a number anywhere.
#
# The label on its own is close to uninformative, and measurably so. On the
# week-1 report Rome Odunze is flagged Questionable at a 0.31 chance of
# playing while George Kittle carries NO status at 0.76 -- the flag and the
# probability disagree in both directions. Meanwhile "Questionable" does
# nothing at all in this engine today: it prints next to a name, and no
# projection, lineup or depth calculation reads it.
#
# THIS MODULE ONLY SUPPLIES THE NUMBER. Multiplying projections by it would
# move every lineup in both leagues, and that is a modelling decision nothing
# has measured yet, so it is deliberately not made here.
#
# TWO SEPARATE LIMITS, AND THEY PULL IN OPPOSITE DIRECTIONS.
#
#   1. TEN ROWS PER RESPONSE. There are 219 injuries and no paging: `limit`,
#      `offset` and `page` are all ignored. `player_ids` filters server-side,
#      so a batch returns only the injured players among the ids asked about.
#      This argues for SMALL batches.
#   2. ABOUT TWELVE CALLS BEFORE A 429. Measured, not documented: the
#      thirteenth identical request returns "Too Many Requests" with no
#      Retry-After header. Asking about 182 rostered players eight at a time
#      is 23 calls and dies two thirds of the way through. This argues for
#      LARGE batches.
#
# Large wins, because truncation is DETECTABLE and rate limiting is not. The
# response carries `count` as the true number of matches -- the unfiltered
# call reports count 219 while returning ten rows -- so a truncated batch
# announces itself and can be split and retried, paying an extra call only
# where one is actually needed. A 429 just loses the rest of the run.

API = "https://api.fantasypros.com/public/v2/json"
BATCH = 40               # 182 rostered players in 5 calls, not 23
MAX_CALLS = 10           # stay under the measured ~12 before a 429
INJURY_TTL = 3 * 3600


def _api_key():
    import os
    return os.environ.get("FANTASYPROS_API_KEY") or None


def _injury_page(fp_ids, season, week, key):
    """Returns (rows, truncated). `truncated` when the cap hid matches."""
    r = requests.get(f"{API}/nfl/injuries", timeout=TIMEOUT,
                     headers={"x-api-key": key},
                     params={"year": season, "week": int(week or 1),
                             "include_probabilities": "true",
                             "player_ids": ":".join(str(i) for i in fp_ids)})
    r.raise_for_status()
    body = r.json() or {}
    rows = body.get("injuries") or []
    try:
        total = int(body.get("count"))
    except (TypeError, ValueError):
        total = len(rows)
    return rows, total > len(rows)


def _row(x) -> dict:
    practice = [x.get("practice_1"), x.get("practice_2"), x.get("practice_3")]
    return {
        "status": (x.get("status") or "").strip() or None,
        # NONE IS NOT ZERO. A player with no published probability is usually
        # one nobody asked about; defaulting him to zero benches a healthy
        # starter, which is a far worse error than saying "unknown".
        "play_prob": _num(x.get("probability_of_playing")),
        "practice": [p for p in practice if p],
        "ir_weeks": list(x.get("ir_weeks") or []),
        "injury": (x.get("injury_type") or "").strip() or None,
    }


def injuries(rows: dict, season, week, store=None
             ) -> tuple[dict[str, dict], str | None]:
    """sleeper_id -> {status, play_prob, practice, ir_weeks, injury}.

    `rows` is the output of fetch(), which is where the FantasyPros ids come
    from -- that feed is uncapped and unkeyed, so the crosswalk is free while
    this call is not. Pass only the players you actually care about.

    Degrades to a PARTIAL result with a note rather than raising: half the
    injury reports is better than none, and silently returning half is worse
    than either.
    """
    key = _api_key()
    if not key:
        return {}, ("DATA MISSING: no FANTASYPROS_API_KEY, so injury "
                    "probabilities are unavailable — Sleeper still supplies "
                    "the status label")

    by_fp: dict[str, str] = {}
    for pid, r in (rows or {}).items():
        if r.get("fp_id") is not None:
            by_fp.setdefault(str(r["fp_id"]), pid)
    if not by_fp:
        return {}, "DATA MISSING: fantasypros injuries (no id crosswalk)"

    ids = sorted(by_fp)
    # KEYED ON WHO WAS ASKED ABOUT, NOT HOW MANY. Two leagues rostering the
    # same NUMBER of players shared an entry and got each other's reports;
    # within one league a 1-for-1 trade left the count identical, so the
    # acquired player showed no injury and the departed one still did.
    import hashlib
    fingerprint = hashlib.sha1(":".join(ids).encode()).hexdigest()[:16]
    ckey = f"fantasypros:injuries:{season}:{week}:{len(ids)}:{fingerprint}"
    if store is not None:
        cached = store.get(ckey)
        if cached and _time.time() - cached.get("ts", 0) < INJURY_TTL:
            return cached["data"], cached.get("note")

    out: dict[str, dict] = {}
    queue = [ids[i:i + BATCH] for i in range(0, len(ids), BATCH)]
    calls, asked, split, note = 0, 0, 0, None
    while queue:
        batch = queue.pop(0)
        if calls >= MAX_CALLS:
            note = (f"⚠ fantasypros injuries: stopped at {MAX_CALLS} calls with "
                    f"{sum(len(b) for b in queue) + len(batch)} of {len(ids)} "
                    f"players unasked — the free tier 429s at about twelve")
            break
        try:
            page, truncated = _injury_page(batch, season, week, key)
            calls += 1
        except Exception as e:  # noqa: BLE001
            note = (f"⚠ fantasypros injuries: stopped after {asked} of "
                    f"{len(ids)} players ({e.__class__.__name__})")
            break
        if truncated and len(batch) > 1:
            # More matches than the cap returned. Halve it and re-ask, so a
            # busy batch costs an extra call instead of losing players.
            mid = len(batch) // 2
            queue[:0] = [batch[:mid], batch[mid:]]
            split += 1
            continue
        asked += len(batch)
        for x in page:
            pid = by_fp.get(str(x.get("player_id")))
            if pid:
                out[pid] = _row(x)

    if note is None:
        note = (f"fantasypros injuries: {len(out)} reports over {asked} players "
                f"in {calls} calls" + (f", {split} batch(es) split" if split else ""))
    if store is not None:
        store.set(ckey, {"ts": _time.time(), "data": out, "note": note})
    return out, note


# --------------------------------------------------------------- crosswalk

def crosswalk(scoring: dict, season, index, store=None
              ) -> tuple[dict, str | None]:
    """Identity for a league whose rosters arrive as bare names.

    Returns {"by_yahoo": {yahoo_id: sleeper_id},
             "by_name":  {normalised name: [(sleeper_id, pos, team)]}}

    BE HONEST ABOUT WHAT THIS IS WORTH. fetch() resolves a FantasyPros row to
    a sleeper_id BY NAME, so `by_yahoo` is a name-mediated link, not an
    independent one. It does not make the Sleeper side exact.

    What it does buy, which is real:

      * A SECOND NAME SPELLING, WHICH MEASURED ZERO AND IS KEPT ANYWAY.
        draftkit.ids.normalize_name already strips punctuation and
        generational suffixes, so "Harold Fannin Jr." against "Harold Fannin"
        ALREADY matches -- suffixes were the obvious guess and they are not
        the gap. What is left is genuinely different renderings of one person
        ("Marquise Brown" against "Hollywood Brown"). On the Keefamania
        scrape of 2026-09-09 that population is EMPTY: 131 players resolved
        with the crosswalk and 131 without it. So this buys nothing today. It
        is kept because it costs one dict on a fetch the consensus already
        makes, and it is the path a renaming would otherwise take down
        silently -- but do not cite it as a benefit until it rescues someone.
      * TEAM, SO AMBIGUITY IS RESOLVABLE. yahoo.load currently takes cand[0]
        on a duplicate name, which silently prices the wrong Mike Williams.
        A team code turns that guess into a decision.
      * A PLACE FOR THE EXACT JOIN TO LAND. The scrape is `POS|Name|Owner`
        today. If it is ever widened to carry Yahoo's own player id, this
        table is already the other half and the name matching drops out
        entirely. That is the upgrade worth making; this is not a substitute
        for it.
    """
    rows, note = fetch(scoring, season, index, kind=ROS, store=store)
    if not rows:
        return {"by_yahoo": {}, "by_name": {}}, note

    from draftkit.ids import normalize_name
    by_yahoo: dict[str, str] = {}
    by_name: dict[str, list[tuple[str, str, str]]] = {}
    for pid, r in rows.items():
        yid = r.get("yahoo_id")
        if yid:
            by_yahoo.setdefault(str(yid), pid)
        d = (index.get(pid) or {}) if hasattr(index, "get") else {}
        nm = d.get("full_name") or d.get("last_name")
        if nm:
            by_name.setdefault(normalize_name(nm), []).append(
                (pid, r.get("pos") or d.get("position") or "",
                 (d.get("team") or "").upper()))
    return ({"by_yahoo": by_yahoo, "by_name": by_name},
            f"{note}; crosswalk {len(by_yahoo)} yahoo ids")
