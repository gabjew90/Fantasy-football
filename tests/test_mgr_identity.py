"""Identity resolution: the manager must never manage a stranger's roster.

Before this, draftkit/briefs.py matched me.username against Sleeper DISPLAY
names and fell back to rosters[0] when nothing matched. A renamed manager or a
typo produced a confident brief about someone else's team.
"""
import pytest

from draftkit.sleeper import IdentityError, resolve_my_roster


class _Cfg(dict):
    league_name = "omnibeta"

    def __init__(self, me):
        super().__init__({"me": me})
        self.league_name = "omnibeta"


class _Client:
    def __init__(self, by_username=None, boom=False):
        self._by = by_username or {}
        self._boom = boom

    def user(self, username):
        if self._boom:
            raise RuntimeError("sleeper down")
        return self._by.get(username)


USERS = {"111": "farmerjamal", "222": "bankerkyle", "333": "cbarone"}
ROSTERS = [{"roster_id": 4, "owner_id": "111"},
           {"roster_id": 1, "owner_id": "222"},
           {"roster_id": 7, "owner_id": "333"}]


def test_display_name_miss_raises_instead_of_managing_roster_zero():
    """The whole point: no match must be an error, not rosters[0]."""
    cfg = _Cfg({"username": "renamed_since_august"})
    with pytest.raises(IdentityError) as e:
        resolve_my_roster(cfg, USERS, ROSTERS, _Client())
    assert "matched 0 of 3 rosters" in str(e.value)


def test_user_id_wins_and_survives_a_display_name_change():
    cfg = _Cfg({"username": "whatever_they_call_me_now", "user_id": "111"})
    roster, info = resolve_my_roster(cfg, USERS, ROSTERS, _Client())
    assert roster["roster_id"] == 4 and info["source"] == "me.user_id"


def test_username_lookup_beats_the_display_name_table():
    """The authoritative path: Sleeper's own username -> user_id endpoint."""
    cfg = _Cfg({"username": "farmerjamal"})
    client = _Client({"farmerjamal": {"user_id": "111"}})
    roster, info = resolve_my_roster(cfg, USERS, ROSTERS, client)
    assert roster["roster_id"] == 4 and info["source"] == "username lookup"


def test_display_name_is_the_last_resort_when_the_lookup_is_down():
    cfg = _Cfg({"username": "farmerjamal"})
    roster, info = resolve_my_roster(cfg, USERS, ROSTERS, _Client(boom=True))
    assert roster["roster_id"] == 4 and info["source"] == "display name"


def test_a_stale_user_id_conflicting_with_the_username_is_loud():
    cfg = _Cfg({"username": "farmerjamal", "user_id": "999"})
    client = _Client({"farmerjamal": {"user_id": "111"}})
    with pytest.raises(IdentityError, match="identity conflict"):
        resolve_my_roster(cfg, USERS, ROSTERS, client)


def test_the_error_names_the_league_and_the_candidates():
    """Fixable in one edit, without opening the code."""
    cfg = _Cfg({"username": "nobody"})
    with pytest.raises(IdentityError) as e:
        resolve_my_roster(cfg, USERS, ROSTERS, _Client())
    msg = str(e.value)
    for want in ("omnibeta", "nobody", "bankerkyle", "owner 222",
                 "Set me.user_id in leagues/omnibeta.yaml"):
        assert want in msg


def test_info_carries_the_roster_id_for_the_brief_prefix():
    """A display-name collision is the failure this exists to catch, so the
    delivered body must name the roster id and not only the name."""
    cfg = _Cfg({"username": "farmerjamal", "user_id": "111"})
    _roster, info = resolve_my_roster(cfg, USERS, ROSTERS, _Client())
    assert info["roster_id"] == 4 and info["display"] == "farmerjamal"
