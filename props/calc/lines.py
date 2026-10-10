"""The last saved Sleeper quote before kickoff for a leg, read from the one
line history the props record keeps (props/record/lines, written through
props/persist.py by the engine workflow and by `python -m props.calc capture`).

Rows that carry a gsis id (calc's captures, DECISIONS #224) join by it; rows
without one (the engine's) join by name, kickoff time and team, and are refused
when a namesake is in the game. A malformed row that could be his raises
DataError; code errors are not caught."""

from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType

import pandas as pd

from . import data, names, odds
from .capture import game_teams
from .checks import DataError, require
from .checks import line_value as _line, multiplier as _mult, number as _num, utc as _utc
from .markets import ARCHIVE_MARKET
from .shared import persist

KNOWN_TEAMS = set(names.TEAM_NAMES.values())
CALC_SNAPSHOT = "calc"          # snapshot_type of calc's own captures (the engine writes "decision")


def archive_path(season: int, root: Path | None = None) -> Path:
    """persist's line history, or the same layout under `root` (tests)."""
    if root is None:
        return persist.lines_path(season)
    return root / str(season) / f"line_archive_{season}.jsonl"


def _rows(path: Path) -> tuple:
    """A JSONL file's rows, read-only. A line that is not a JSON object fails loudly."""
    if not path.exists():
        return ()
    out = []
    with open(path, encoding="utf-8") as fh:
        for i, x in enumerate(fh, 1):
            if not x.strip():
                continue
            try:
                r = json.loads(x)
            except ValueError as ex:
                raise DataError(f"{path.name} line {i} is not valid JSON ({ex})") from ex
            require(isinstance(r, dict), f"{path.name} line {i} is not a JSON object")
            out.append(MappingProxyType(r))
    return tuple(out)


def _price(r, side: str) -> float:
    """Sleeper's multiplier: exact on calc's rows, else from the American price
    (rounded to whole units when it was saved, so within about half a cent)."""
    if r.get("multiplier") is not None:
        return _mult(r["multiplier"], f"an archived {side} multiplier")
    a = _num(r.get("price_american"), f"an archived {side} price")
    try:
        return odds.multiplier_from_american(a)
    except ValueError as ex:
        raise DataError(f"an archived price is not valid American odds ({ex})") from ex


class LineLookup:
    """Finds the last quote before kickoff that belongs to a leg's player, team
    and game. One per run: it reads the line history once and owns its caches,
    so nothing is shared between runs or between rosters."""

    def __init__(self, roster: pd.DataFrame, *, archive_root: Path | None = None):
        self.roster, self.archive_root = roster, archive_root
        self._files: dict = {}
        self._rosters: dict = {}
        self._indexes: dict = {}          # path -> index, built once per file

    def _file(self, path: Path) -> tuple:
        """A file's rows, read once per run; a file that cannot be read is
        reported once and not re-read for every leg."""
        if path not in self._files:
            try:
                self._files[path] = _rows(path)
            except DataError as ex:
                self._files[path] = str(ex)
        got = self._files[path]
        if isinstance(got, str):
            raise DataError(got)
        return got

    def find(self, leg: dict) -> dict | None:
        """{"source", "at_utc", "line", "mult_over", "mult_under"[, "note"]} or None."""
        ko_t = _utc(leg.get("kickoff_utc"), "the leg's kickoff time")     # missing: fails loudly
        return self._archive(leg, ko_t)

    def _index(self, path: Path) -> dict:
        """Sleeper rows of the four markets, grouped once per file by (market,
        normalised name), and by (market, "id", gsis id) for rows that carry an
        id (DECISIONS #224)."""
        if path not in self._indexes:
            idx: dict = {}
            for r in self._file(path):
                if r.get("bookmaker") != "sleeper" or ARCHIVE_MARKET.get(r.get("market")) is None:
                    continue
                mk = ARCHIVE_MARKET[r["market"]]
                if r.get("gsis_id"):
                    idx.setdefault((mk, "id", r["gsis_id"]), []).append(r)
                idx.setdefault((mk, names.norm(str(r.get("player", "")))), []).append(r)
            self._indexes[path] = idx
        return self._indexes[path]

    def _archive(self, leg: dict, ko_t) -> dict | None:
        arch = archive_path(int(leg["season"]), self.archive_root)
        if not arch.exists():
            return None
        team = names.team_code(leg["team"])
        key = names.norm(leg["player"])
        full = names.TEAM_NAMES.get(team)
        require(full is not None, f"team code {team!r} has no full name for the line archive")
        idx = self._index(arch)
        # rows with an id join by it (DECISIONS #224); rows without one, by name
        # an id row also names its nflverse game; another game's row is not this leg's
        by_id = [r for r in idx.get((leg["market"], "id", leg["gsis_id"]), [])
                 if r.get("game_id") in (None, leg["game_id"])]
        by_name = [r for r in idx.get((leg["market"], key), []) if not r.get("gsis_id")]
        best: dict = {}
        for r in by_id + by_name:
            wk, teams_ok = r.get("week"), bool(r.get("home_team") and r.get("away_team"))
            if isinstance(wk, int) and wk != leg["week"]:
                continue                   # another week: whatever else is wrong with it, not this leg's row
            if teams_ok and full not in (r.get("home_team"), r.get("away_team")):
                if not {r["home_team"], r["away_team"]} <= KNOWN_TEAMS:     # could be his team, misspelled
                    raise DataError(f"a week-{leg['week']} archive row for {leg['player']} names a team this "
                                    f"tool does not know ({r['home_team']!r} / {r['away_team']!r}); "
                                    f"add it to names.TEAM_NAMES")
                continue                   # another team's game: not his row, so not his problem
            # from here the row could be his for this week: it must be complete
            if not teams_ok:
                raise DataError(f"a saved archive row for {leg['player']} names no teams")
            if not isinstance(wk, int):
                raise DataError(f"a saved archive row for {leg['player']} has no usable week ({wk!r})")
            # his rows for this week must be readable; another week's bad row does not block this one
            what = f"a saved week-{leg['week']} archive row for {leg['player']}"
            ct = _utc(r.get("commence_time"), f"{what}: kickoff")
            rt = _utc(r.get("retrieved_at_utc"), f"{what}: time")
            if ct == ko_t and rt < ko_t:
                side = r.get("outcome")
                require(side in ("Over", "Under"), f"{what}: outcome {side!r} is not Over or Under")
                best.setdefault(rt, {})[side] = r             # keyed by the parsed time, not its text
        passed, bad = 0, []
        for at in sorted(best, reverse=True):
            pair = best[at]
            if "Over" not in pair or "Under" not in pair:
                passed += 1                # a one-sided snapshot: passed over, and said so
                continue
            try:
                po = _line(pair["Over"].get("point"), "an archived line")
                pu = _line(pair["Under"].get("point"), "an archived line")
                mo, mu = _price(pair["Over"], "Over"), _price(pair["Under"], "Under")
            except DataError as ex:        # a bad snapshot is skipped and reported; an older one may be fine
                bad.append(str(ex))
                continue
            if po != pu:
                passed += 1                # the two sides at different lines
                continue
            # the archive has names, not ids: a name-joined quote is refused when a
            # namesake is in the game (checked only once a usable quote exists)
            if not (pair["Over"].get("gsis_id") and pair["Under"].get("gsis_id")) and self.name_clash(leg):
                raise DataError(f"a saved quote for {leg['player']} was found but refused: another player in "
                                f"{leg['game_id']} has the same name, and those archive rows have names, not ids")
            who = "your capture" if pair["Over"].get("snapshot_type") == CALC_SNAPSHOT else "the engine's capture"
            got = {"source": who, "at_utc": at.isoformat(), "line": po, "mult_over": mo, "mult_under": mu}
            notes = ([f"passed over {passed} newer archive snapshots that were one-sided or split"] if passed else [])
            notes += [f"skipped {len(bad)} unreadable archive snapshots ({bad[0]})"] if bad else []
            if notes:
                got["note"] = "; ".join(notes)
            return got
        if passed or bad:                  # quotes were saved, none usable: say why, not "no line"
            why = ([f"{passed} saved archive snapshots were one-sided or split"] if passed else [])
            why += [f"{len(bad)} were unreadable ({bad[0]})"] if bad else []
            raise DataError("; ".join(why))
        return None

    def name_clash(self, leg: dict) -> bool:
        key = (int(leg["season"]), int(leg["week"]))
        if key not in self._rosters:
            self._rosters[key] = data.roster_split(self.roster, *key)     # all positions: see _clash
        return _clash(leg, *self._rosters[key])


def line_near_kickoff(leg: dict, roster: pd.DataFrame, **kw) -> dict | None:
    """LineLookup(roster, **kw).find(leg), for a single lookup."""
    return LineLookup(roster, **kw).find(leg)


def name_clash(leg: dict, roster: pd.DataFrame) -> bool:
    """Whether another player on either team of the leg's game shares his
    normalised name, among the players on each team's latest published roster
    up to that week. Raises unless both teams have a roster on file."""
    return LineLookup(roster).name_clash(leg)


def _clash(leg: dict, r: pd.DataFrame, ambiguous: pd.DataFrame) -> bool:
    teams = game_teams(leg["game_id"])
    require(len(teams) == 2, f"game id {leg['game_id']!r} does not name two teams")
    r = r[r["team"].isin(teams)]
    missing = teams - set(r["team"])
    require(not missing, f"no {leg['season']} roster on file for {sorted(missing)}; cannot rule out a namesake")
    # a team's roster is on file if anyone is listed (checked above, all
    # positions); namesakes are skill players only: a practice-squad DB who
    # shares a receiver's name is no namesake for his line
    require("position" in r.columns, "weekly rosters have no position column; cannot limit namesakes")
    r = r[r["position"].isin(data.SKILL)]
    key = names.norm(leg["player"])
    # a player listed on two teams that week (set aside), one of them in this
    # game, who could be him: refuse rather than guess
    if data.set_aside_namesake(ambiguous, leg["player"], teams=teams, other_than=leg["gsis_id"]):
        return True
    # a listed player with no gsis id still counts as someone else with that name
    return any((not isinstance(g, str) or g != leg["gsis_id"]) and names.norm(str(n)) == key
               for g, n in zip(r["gsis_id"], r["full_name"]))


