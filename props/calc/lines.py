"""The last saved Sleeper quote before kickoff for a leg, read from two files
in one row format: the props record's line history (props/record/lines, the
engine workflow's captures) and calc's own (props/calc/lines, written by
`python -m props.calc capture` with persist's writer; kept out of
props/record, which only the workflow commits).

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


CALC_LINES = Path(__file__).resolve().parent / "lines"


def archive_path(season: int, root: Path | None = None) -> Path:
    """persist's line history, or the same layout under `root` (tests)."""
    if root is None:
        return persist.lines_path(season)
    return root / str(season) / f"line_archive_{season}.jsonl"


def calc_path(season: int, root: Path | None = None) -> Path:
    """calc's own captures, in the line history's row format."""
    return (root or CALC_LINES) / str(season) / f"line_archive_{season}.jsonl"


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

    def __init__(self, roster: pd.DataFrame, *, archive_root: Path | None = None, calc_root: Path | None = None):
        """archive_root / calc_root move the two files (tests); with only
        archive_root given, calc's file is looked for under archive_root/calc."""
        self.roster, self.archive_root = roster, archive_root
        self.calc_root = calc_root or (archive_root / "calc" if archive_root is not None else None)
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

    def find(self, leg: dict, line: float | None = None) -> dict | None:
        """{"source", "at_utc", "line", "mult_over", "mult_under"[, "note"]} or
        None: the newest usable quote before kickoff, or with `line`, the newest
        at that line (the line a bet was made at)."""
        ko_t = _utc(leg.get("kickoff_utc"), "the leg's kickoff time")     # missing: fails loudly
        return self._archive(leg, ko_t, line)

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

    def _archive(self, leg: dict, ko_t, line: float | None = None) -> dict | None:
        season = int(leg["season"])
        files = [p for p in (archive_path(season, self.archive_root), calc_path(season, self.calc_root))
                 if p.exists()]
        if not files:
            return None
        team = names.team_code(leg["team"])
        key = names.norm(leg["player"])
        full = names.TEAM_NAMES.get(team)
        require(full is not None, f"team code {team!r} has no full name for the line archive")
        idxs = [self._index(p) for p in files]
        # rows with an id join by it (DECISIONS #224); rows without one, by name
        # an id row also names its nflverse game; another game's row is not this leg's
        by_id = [r for idx in idxs for r in idx.get((leg["market"], "id", leg["gsis_id"]), [])
                 if r.get("game_id") in (None, leg["game_id"])]
        by_name = [r for idx in idxs for r in idx.get((leg["market"], key), []) if not r.get("gsis_id")]
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
            # a row naming its nflverse game (calc's) is found after a flexed kickoff; any other
            # row has only the kickoff to say which game it is for. Either way it was saved before kickoff now.
            same_game = r.get("game_id") == leg["game_id"] if r.get("gsis_id") and r.get("game_id") else ct == ko_t
            if same_game and rt < ko_t:
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
            if line is not None and po != line:
                continue                   # another line than the one asked for: not a problem, not his bet
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

    def posted(self, game: dict) -> tuple[list[dict], int]:
        """(every player and market with a saved Sleeper quote for this game before kickoff, the
        number of rows that could not be read and were left out). One entry per market and player:
        {"player", "gsis_id", "team", "market"}, from the line history and calc's own captures.
        Players are told apart by id: calc's rows carry one (and Sleeper's short name, "C.
        McCaffrey"); a name-only row (the engine's) gets one from this season's roster of the two
        teams when exactly one player there has that name. The name given is the roster's full
        name, so the card finds him exactly. Which quote a card uses is still find()'s choice; this
        only says which cards the game has (DECISIONS #236)."""
        season, week = int(game["season"]), int(game["week"])
        ko = _utc(game["kickoff_utc"], "the game's kickoff time")
        codes = {names.team_code(game["home_team"]), names.team_code(game["away_team"])}
        full = {names.TEAM_NAMES.get(t) for t in codes}
        require(None not in full, f"game {game['game_id']} names a team with no full name for the line archive")
        r_ = self.roster
        r_ = r_[(r_["season"] == season) & (r_["week"] <= week)].dropna(subset=["gsis_id", "full_name"])
        r_ = r_.sort_values("week").drop_duplicates("gsis_id", keep="last")
        r_ = r_[r_["team"].map(names.team_code).isin(codes)]
        by_id = {g: (n, names.team_code(t)) for g, n, t in zip(r_["gsis_id"], r_["full_name"], r_["team"])}
        by_name: dict = {}
        for g, n in zip(r_["gsis_id"], r_["full_name"]):
            by_name.setdefault(names.norm(n), set()).add(g)
        out: dict = {}
        unread = 0
        for path in (archive_path(season, self.archive_root), calc_path(season, self.calc_root)):
            if not path.exists():
                continue
            for r in self._file(path):
                mk = ARCHIVE_MARKET.get(r.get("market"))
                if r.get("bookmaker") != "sleeper" or mk is None or r.get("season") != season:
                    continue
                if r.get("week") != week or {r.get("home_team"), r.get("away_team")} != full:
                    continue
                if r.get("gsis_id") and r.get("game_id") and r["game_id"] != game["game_id"]:
                    continue
                try:
                    if _utc(r.get("retrieved_at_utc"), "a saved quote's time") >= ko:
                        continue
                except DataError:
                    unread += 1
                    continue
                gsis = r.get("gsis_id")
                if not gsis:
                    ids = by_name.get(names.norm(str(r.get("player", ""))), set())
                    gsis = next(iter(ids)) if len(ids) == 1 else None
                if gsis and gsis in by_id:
                    name, team = by_id[gsis]
                    key = (mk, "id", gsis)
                else:                              # not on either roster by that name: the card resolves it
                    name, team = r.get("player"), (names.team_code(r["team"]) if r.get("team") else None)
                    key = (mk, "name", names.norm(str(r.get("player", ""))))
                out.setdefault(key, {"player": name, "gsis_id": gsis if key[1] == "id" else None,
                                     "team": team, "market": mk})
        return list(out.values()), unread

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


