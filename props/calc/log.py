"""The leg log: props/calc/log/legs.jsonl, append only.

A "leg" row is written when the user logs a leg from a card: the line, both
prices, "book expects", the workload needed, his usual workload and the gap.
A "settle" row is appended after the game with the workload he actually got,
the result, and the line near kickoff. Rows are never edited; reading merges
each leg's settle rows in the order written (a later fill adds a line near
kickoff, it never erases the result).
"""

from __future__ import annotations

import datetime as dt
import json
import uuid
from pathlib import Path
from types import MappingProxyType

import pandas as pd

from . import calc, data, names, odds
from .capture import append_jsonl, capture_path, game_majority, game_teams, sleeper_game_agrees
from .checks import DataError, require
from .checks import line_value as _line, multiplier as _mult, number as _num, utc as _utc
from .markets import ARCHIVE_MARKET, stat_col, workload_col

CALC = Path(__file__).resolve().parent
LOG_PATH = CALC / "log" / "legs.jsonl"
ARCHIVE_ROOT = CALC.parent / "record" / "lines"      # the engine workflow's saved lines; read only

KNOWN_TEAMS = set(names.TEAM_NAMES.values())
LEG_FIELDS = ("season", "week", "game_id", "kickoff_utc", "player", "gsis_id", "team", "market", "side",
              "line", "mult_over", "mult_under", "target_rate", "book_expects", "needed", "usual", "gap")


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def log_leg(leg: dict, *, path: Path | None = None, now: str | None = None) -> dict:
    path = path or LOG_PATH          # read at call time, so a test can redirect it
    missing = [f for f in LEG_FIELDS if f not in leg]
    if missing:
        raise ValueError(f"a leg needs {missing}")
    if leg["side"] not in ("over", "under"):
        raise ValueError("side is over or under")
    row = {"kind": "leg", "id": uuid.uuid4().hex[:12], "logged_at_utc": now or _now(), **leg}
    append_jsonl(path, [row])
    return row


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


def read(path: Path | None = None) -> list[dict]:
    """Legs, each merged with all of its settle rows in the order written."""
    path = path or LOG_PATH
    legs, settles = {}, {}
    for r in _rows(path):
        require(r.get("kind") in ("leg", "settle") and r.get("id"), f"{path.name}: a row has no kind or id")
        r = dict(r)
        if r["kind"] == "leg":
            legs[r["id"]] = r
        else:                    # settle rows merge in the order written: a later fill adds, never erases
            settles.setdefault(r["id"], {}).update({k: v for k, v in r.items() if k not in ("kind", "id")})
    return [{**leg, **settles.get(i, {})} for i, leg in legs.items()]


def result(side: str, line: float, actual: float | None) -> str:
    if actual is None:
        return "no stats"
    if actual == line:
        return "push"
    return "won" if (actual > line) == (side == "over") else "lost"


def settle_row(leg: dict, games: pd.DataFrame, kickoff_line: dict | None, now: str | None = None) -> dict:
    """The settle row for one leg of a game that has been played. `games` is
    games_played rows: a player who played with no work has a zero row; one
    with no row did not play (Sleeper drops such a leg)."""
    g = games[(games["game_id"] == leg["game_id"]) & (games["gsis_id"] == leg["gsis_id"])]
    row = {"kind": "settle", "id": leg["id"], "settled_at_utc": now or _now(), "kickoff_line": kickoff_line}
    if g.empty:
        return {**row, "actual_workload": None, "actual": None, "result": "did not play"}
    actual = float(g[stat_col(leg["market"])].sum())
    return {**row, "actual_workload": int(g[workload_col(leg["market"])].sum()), "actual": actual,
            "result": result(leg["side"], float(leg["line"]), actual)}


class LineLookup:
    """Finds the last quote before kickoff that belongs to a leg's player, team
    and game. One per run: it reads each saved-lines file once and owns its
    caches, so nothing is shared between runs or between rosters.

    Own captures come first (gsis id, team and game id must all agree, and the
    capture's Sleeper game must sit in that game); else the engine workflow's
    archive (name, kickoff time, and his team must be one of the game's two
    teams; never name alone, and refused when a namesake is in the game).
    A malformed saved row raises DataError; code errors are not caught."""

    def __init__(self, roster: pd.DataFrame, *, lines_root: Path | None = None,
                 archive_root: Path | None = None):
        self.roster, self.lines_root = roster, lines_root
        self.archive_root = archive_root or ARCHIVE_ROOT
        self._files: dict = {}
        self._majority: dict = {}
        self._rosters: dict = {}
        self._indexes: dict = {}          # (path, kind) -> index, built once per file

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
        note = None
        try:
            mine = self._own(leg, ko_t)
        except DataError as ex:            # own captures not usable: say why, and try the archive
            mine, note = None, f"own captures not used: {ex}"
        if mine:
            return mine
        try:
            got = self._archive(leg, ko_t)
        except DataError as ex:            # keep the own-capture reason too
            raise DataError(f"{ex}; {note}" if note else str(ex)) from ex
        if got and note:
            got["note"] = "; ".join(x for x in (got.get("note"), note) if x)
        if got is None and note:
            raise DataError(note)
        return got

    def _own(self, leg: dict, ko_t) -> dict | None:
        cap_path = capture_path(int(leg["season"]), self.lines_root)
        team = names.team_code(leg["team"])
        game = {"season": int(leg["season"]), "week": int(leg["week"])}
        mine = self._index(cap_path, "own").get((leg["gsis_id"], leg["market"], leg["game_id"]), [])
        mine = [c for c in mine if names.team_code(c.get("team")) == team]
        timed, bad, refused = [], [], 0
        for c in mine:
            try:
                timed.append((c, _utc(c.get("captured_at_utc"), "a capture time")))
            except DataError as ex:
                bad.append(str(ex))
        # newest first; re-checked on read, not only on write; a bad row is
        # skipped (and reported) so an older good capture can still be used
        for c, at in sorted((x for x in timed if x[1] < ko_t), key=lambda x: x[1], reverse=True):
            try:
                if not (sleeper_game_agrees(c.get("sleeper_game_id"), game)
                        and self._capture_majority(cap_path, c["captured_at_utc"], c.get("sleeper_game_id"))
                        == c["game_id"]):
                    refused += 1           # its Sleeper game is not this game: refused, and said so below
                    continue
                got = {"source": "own capture", "at_utc": c["captured_at_utc"],
                       "line": _line(c.get("line"), "a captured line"),
                       "mult_over": _mult(c.get("mult_over"), "a captured Over multiplier"),
                       "mult_under": _mult(c.get("mult_under"), "a captured Under multiplier")}
            except DataError as ex:
                bad.append(str(ex))
                continue
            if bad or refused:
                got["note"] = _own_note(bad, refused)
            return got
        if bad or refused:
            raise DataError(_own_note(bad, refused))
        return None

    def _index(self, path: Path, kind: str) -> dict:
        """Rows grouped once per file: own captures by (gsis id, market, game
        id); archive rows by (market, normalised name), and by (market, gsis
        id) for rows that carry an id (DECISIONS #224)."""
        key = (path, kind)
        if key not in self._indexes:
            idx: dict = {}
            for r in self._file(path):
                if kind == "own":
                    k = (r.get("gsis_id"), r.get("market"), r.get("game_id"))
                elif kind == "cap_game":
                    k = (r.get("captured_at_utc"), r.get("sleeper_game_id"))
                else:
                    if r.get("bookmaker") != "sleeper" or ARCHIVE_MARKET.get(r.get("market")) is None:
                        continue
                    k = (ARCHIVE_MARKET[r["market"]], names.norm(str(r.get("player", ""))))
                    if r.get("gsis_id"):
                        idx.setdefault((ARCHIVE_MARKET[r["market"]], "id", r["gsis_id"]), []).append(r)
                idx.setdefault(k, []).append(r)
            self._indexes[key] = idx
        return self._indexes[key]

    def _archive(self, leg: dict, ko_t) -> dict | None:
        arch = self.archive_root / str(leg["season"]) / f"line_archive_{leg['season']}.jsonl"
        if not arch.exists():
            return None
        team = names.team_code(leg["team"])
        key = names.norm(leg["player"])
        full = names.TEAM_NAMES.get(team)
        require(full is not None, f"team code {team!r} has no full name for the line archive")
        idx = self._index(arch, "archive")
        # rows with an id join by it (DECISIONS #224); rows without one, by name
        by_id = idx.get((leg["market"], "id", leg["gsis_id"]), [])
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
                ao = _num(pair["Over"].get("price_american"), "an archived Over price")
                au = _num(pair["Under"].get("price_american"), "an archived Under price")
                try:
                    mo, mu = odds.multiplier_from_american(ao), odds.multiplier_from_american(au)
                except ValueError as ex:
                    raise DataError(f"an archived price is not valid American odds ({ex})") from ex
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
            got = {"source": "engine archive", "at_utc": at.isoformat(), "line": po, "mult_over": mo,
                   "mult_under": mu}
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

    def _capture_majority(self, cap_path: Path, captured_at: str, sleeper_game_id) -> str | None:
        """The nflverse game one capture's rows in this Sleeper game belong to
        (game_majority). Only that Sleeper game's rows must be complete; the
        answer, or the failure, is cached."""
        key = (captured_at, sleeper_game_id)
        if key not in self._majority:
            rows = self._index(cap_path, "cap_game").get(key, [])
            broken = [c for c in rows if c.get("gsis_id") and c.get("game_id") and not c.get("team")]
            self._majority[key] = ((f"a capture row of {captured_at} in Sleeper game {sleeper_game_id} "
                                    f"has no team", None) if broken
                                   else (None, game_majority(rows).get(sleeper_game_id)))
        err, got = self._majority[key]
        if err:
            raise DataError(err)           # a fresh exception each time, not one shared object
        return got

    def name_clash(self, leg: dict) -> bool:
        key = (int(leg["season"]), int(leg["week"]))
        if key not in self._rosters:
            self._rosters[key] = data.roster_split(self.roster, *key)     # all positions: see _clash
        return _clash(leg, *self._rosters[key])


def _own_note(bad: list, refused: int) -> str:
    parts = []
    if bad:
        parts.append(f"skipped {len(bad)} unreadable capture rows ({bad[0]})")
    if refused:
        parts.append(f"refused {refused} own captures whose Sleeper game is not this game")
    return "; ".join(parts)


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


def settle(season: int, games: pd.DataFrame, roster: pd.DataFrame, *, ready: set,
           path: Path | None = None, kickoffs: dict | None = None, **kw) -> dict:
    """Append a settle row for every unsettled leg of `season` whose own game
    is in `games` (games_played rows: the game has been played and loaded).
    `ready` (required) is the set of games that may be settled: play-by-play
    loaded and a final score on the schedule. A game seen only in snap counts,
    or with a stale play-by-play, is never settled on zeros.
    `roster` (weekly rosters) is required: it rules out a namesake before an
    archive line is trusted. `kickoffs` (game id -> the schedule's kickoff now)
    replaces the kickoff saved when the leg was logged, so a flexed game finds
    its real line near kickoff. Returns {"settled": new legs settled, "filled":
    legs settled earlier whose missing line near kickoff was found now,
    "unmatched": [new legs with no matched line, with why], "still_missing":
    [legs settled earlier whose line is still missing, with why]}."""
    path = path or LOG_PATH
    played_games = set(games["game_id"]) & set(ready)
    rows, unmatched, still_missing, filled = [], [], [], 0
    lookup = LineLookup(roster, **kw)          # each saved-lines file read once for the whole run
    for leg in read(path):
        # a settled leg is taken again to fill a line near kickoff that was
        # missing (when its result counts), or when he "did not play": that
        # rests on snap counts that can load late, so it is re-checked each run
        redo = leg.get("result") in ("won", "lost") and leg.get("kickoff_line") is None
        recheck = leg.get("result") == "did not play"
        if ((leg.get("result") and not (redo or recheck)) or leg["season"] != season
                or leg["game_id"] not in played_games):
            continue
        if not redo:
            row = settle_row(leg, games, None)
            if recheck and row["result"] == "did not play":
                continue                   # still no sign he played: nothing new
            if row["result"] not in ("won", "lost"):         # void: its line near kickoff does not matter
                rows.append(row)
                continue
        why = "no matching line"
        if kickoffs and kickoffs.get(leg["game_id"]):    # the game's kickoff now (a flexed game moves)
            leg = {**leg, "kickoff_utc": kickoffs[leg["game_id"]]}
        try:
            kl = lookup.find(leg)
        except DataError as ex:            # a data problem with one leg never stops the rest
            kl, why = None, str(ex)
        if redo and kl is None:
            still_missing.append(f"{leg['id']} ({leg['player']}): {why}")   # nothing new to write
            continue
        if kl is None:
            unmatched.append(f"{leg['id']} ({leg['player']}): {why}")
        if redo:                 # only the line near kickoff is new; the result stands as first settled
            filled += 1
            rows.append({"kind": "settle", "id": leg["id"], "filled_at_utc": _now(), "kickoff_line": kl})
        else:
            rows.append({**row, "kickoff_line": kl})
    append_jsonl(path, rows)
    return {"settled": len(rows) - filled, "filled": filled, "unmatched": unmatched,
            "still_missing": still_missing}


def gap_group(gap: float, edges: list[float]) -> str:
    lo = None
    for e in edges:
        if gap <= e:
            return f"{e} or less" if lo is None else f"{lo} to {e}"
        lo = e
    return f"more than {edges[-1]}"


def status_group(side: str, status: str | None) -> str:
    """Where a leg with no gap goes in the summary (calc.side_result)."""
    if status is None:
        return "no gap (logged without a status)"
    r = calc.side_result(side, status)
    if r == "ok":
        return "no gap (no usual workload)"
    return f"{side.capitalize()} wins at any workload" if r == "always" else "out of reach"


def _mean(xs: list) -> float | None:
    xs = [float(x) for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def summary(season: int, edges: list[float], *, path: Path | None = None) -> list[dict]:
    """Settled legs (won or lost) grouped by market and gap: how many, how many
    won, the average break-even of the side played, needed vs actual workload.
    A leg with no gap (its search hit an end of its range) is grouped by side
    and search result (status_group)."""
    legs = [x for x in read(path or LOG_PATH) if x["season"] == season and x.get("result") in ("won", "lost")]
    groups: dict[tuple, list] = {}
    for x in legs:
        grp = (gap_group(float(x["gap"]), edges) if x.get("gap") is not None
               else status_group(x["side"], x.get("needed_status")))
        groups.setdefault((x["market"], grp), []).append(x)
    out = []
    for (market, grp), xs in sorted(groups.items()):
        be = [1 / (x["mult_over"] if x["side"] == "over" else x["mult_under"]) for x in xs]
        out.append({"market": market, "gap": grp, "legs": len(xs),
                    "won": sum(x["result"] == "won" for x in xs),
                    "break_even": sum(be) / len(be),
                    "needed": _mean([x.get("needed") for x in xs]),
                    "actual": _mean([x.get("actual_workload") for x in xs])})
    return out
