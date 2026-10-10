"""Player matching. An ID join comes first (Sleeper id -> gsis id); a name is
only a fallback, and only together with the team. Book names differ from
nflverse names ("Joshua"/"Josh", "C.McCaffrey"), so the fallback compares a
normalised full name, then first initial + surname. A name that matches no
one, or more than one player, is a miss: the caller logs it, never guesses."""

from __future__ import annotations

import re
import unicodedata

SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}
# Formal first name -> the short form nflverse or the book may use instead.
NICKNAMES = {
    "joshua": "josh", "christopher": "chris", "matthew": "matt", "michael": "mike",
    "nicholas": "nick", "nathaniel": "nate", "daniel": "dan", "benjamin": "ben",
    "william": "will", "robert": "rob", "jonathan": "jon", "zachary": "zach",
    "cameron": "cam", "gabriel": "gabe", "kenneth": "ken", "patrick": "pat",
    "joseph": "joe", "samuel": "sam", "thomas": "tom", "alexander": "alex",
    "jeffrey": "jeff", "jeffery": "jeff", "anthony": "tony", "timothy": "tim",
    "mitchell": "mitch",
}
# Sleeper / book team codes that differ from nflverse's.
TEAM_ALIASES = {"LAR": "LA", "JAC": "JAX", "WSH": "WAS"}
# nflverse code -> the full name the engine workflow's line archive uses.
TEAM_NAMES = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens", "BUF": "Buffalo Bills",
    "CAR": "Carolina Panthers", "CHI": "Chicago Bears", "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns",
    "DAL": "Dallas Cowboys", "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars", "KC": "Kansas City Chiefs",
    "LV": "Las Vegas Raiders", "LAC": "Los Angeles Chargers", "LA": "Los Angeles Rams", "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings", "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers", "SF": "San Francisco 49ers",
    "SEA": "Seattle Seahawks", "TB": "Tampa Bay Buccaneers", "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}


def team_code(team: str | None) -> str:
    t = (team or "").strip().upper()
    return TEAM_ALIASES.get(t, t)


def _tokens(name: str) -> list[str]:
    s = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode()
    s = s.lower().replace(".", ". ")
    s = re.sub(r"[^a-z\s-]", "", s).replace("-", " ")
    toks = [t for t in s.split() if t]
    while len(toks) > 1 and toks[-1] in SUFFIXES:
        toks.pop()
    # "A.J. Brown" -> ["aj", "brown"]: leading single letters followed by more
    # single letters are one first name (AJ, CJ, TJ), not an abbreviation
    lead = 0
    while lead < len(toks) - 1 and len(toks[lead]) == 1:
        lead += 1
    if lead >= 2:
        toks = ["".join(toks[:lead])] + toks[lead:]
    return toks


def norm(name: str) -> str:
    """'Joshua Palmer Jr.' -> 'josh palmer'; "Ja'Marr Chase" -> 'jamarr chase'."""
    toks = _tokens(name)
    if toks:
        toks[0] = NICKNAMES.get(toks[0], toks[0])
    return " ".join(toks)


def initial_key(name: str) -> str:
    """First initial + surname: 'C.McCaffrey' and 'Christian McCaffrey' -> 'c mccaffrey'."""
    toks = _tokens(name)
    if len(toks) < 2:
        return ""
    return f"{toks[0][0]} {''.join(toks[1:])}"


def abbreviated(name: str) -> bool:
    """'C.McCaffrey' or 'C. McCaffrey': the first name given as one letter."""
    toks = _tokens(name)
    return len(toks) >= 2 and len(toks[0]) == 1


def could_be(listed: str, given: str) -> bool:
    """Whether `given` could name the `listed` player: the same normalised name,
    or, for an abbreviated `given` ('C. Smith'), the same initial and surname."""
    if norm(listed) == norm(given):
        return True
    return abbreviated(given) and initial_key(listed) == initial_key(given)


def match(name: str, team: str | None, candidates: list[dict], *,
          allow_initial: bool = False) -> tuple[str | None, str]:
    """(gsis_id, how) for `name` on `team` among candidates [{gsis_id, name, team}].
    how is "name" or "initial" on a match, else "miss: <reason>". The first
    initial + surname key is tried only when `name` is itself abbreviated, or
    when the caller allows it (a name the user typed with its team, whose card
    then shows the full name it resolved to). For automatic matching a full
    name that matches no one is a miss, never a teammate who happens to share
    the initial and surname (Carl Smith is not Chris Smith)."""
    t = team_code(team)
    if not t:
        return None, "miss: no team to check the name against"
    pool = [c for c in candidates if team_code(c.get("team")) == t]
    keys = ((("name", norm), ("initial", initial_key)) if abbreviated(name) or allow_initial
            else (("name", norm),))
    for how, key in keys:
        k = key(name)
        if not k:
            continue
        hits = {c["gsis_id"] for c in pool if key(c.get("name", "")) == k}
        if len(hits) == 1:
            return hits.pop(), how
        if len(hits) > 1:
            return None, f"miss: {len(hits)} players on {t} match {name!r}"
    return None, f"miss: no player on {t} matches {name!r}"
