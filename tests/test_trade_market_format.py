"""FantasyCalc must be queried in the league's own format.

Regression for 2026-09-07: the URL hardcoded numTeams=12&ppr=1, so Keefamania
(10-team, half PPR) was priced on Omnibeta's market with nothing to indicate
it. Wrong values that look right are worse than missing ones.
"""

import pytest

from manager import market, trade_radar


class FakeStore:
    def __init__(self):
        self.d = {}

    def get(self, k, default=None):
        return self.d.get(k, default)

    def set(self, k, v):
        self.d[k] = v


OMNIBETA = {"rosters": [{}] * 12, "slots": {"QB": 1}, "cfg": {"scoring": {"rec": 1.0}}}
KEEFAMANIA = {"rosters": [{}] * 10, "slots": {"QB": 1},
              "cfg": {"expected": {"scoring": {"rec": 0.5}}}}

ROW = [{"player": {"sleeperId": "4034"}, "value": 5000, "overallRank": 3,
        "positionRank": 1, "trend30Day": -270, "maybeRosterPercent": 99.1,
        "maybeTradeFrequency": 0.4}]


def _patch(monkeypatch, seen):
    class R:
        @staticmethod
        def raise_for_status():
            return None

        @staticmethod
        def json():
            return ROW

    # the client moved to manager.market on 2026-09-08 so manager.marginal
    # can price trades on the same values; trade_radar re-exports it
    monkeypatch.setattr(market.requests, "get",
                        lambda url, params=None, timeout=20:
                        (seen.append(dict(params or {})), R())[1])


def test_league_format_reads_teams_and_ppr_from_the_league():
    # the 4th field is isDynasty, added when the client moved to
    # manager.market (redraft returns 199 players, dynasty 423)
    assert trade_radar.league_format(OMNIBETA) == (12, 1.0, 1, False)
    assert trade_radar.league_format(KEEFAMANIA) == (10, 0.5, 1, False)


def test_superflex_asks_for_two_quarterbacks():
    sf = dict(OMNIBETA, slots={"QB": 1, "SUPER_FLEX": 1})
    assert trade_radar.league_format(sf)[2] == 2


def test_the_two_leagues_produce_different_queries(monkeypatch):
    seen = []
    _patch(monkeypatch, seen)
    trade_radar.market(FakeStore(), OMNIBETA)
    trade_radar.market(FakeStore(), KEEFAMANIA)
    assert seen[0]["numTeams"] == 12 and seen[0]["ppr"] == 1.0
    assert seen[1]["numTeams"] == 10 and seen[1]["ppr"] == 0.5
    assert seen[0] != seen[1]


def test_only_parameters_the_api_honours_are_sent(monkeypatch):
    """Measured 2026-09-08: the endpoint SILENTLY IGNORES unknown keys --
    teMultiplier and numStarters return byte-identical values to a bogus
    parameter. Sending one would advertise support that does not exist."""
    seen = []
    _patch(monkeypatch, seen)
    trade_radar.market(FakeStore(), OMNIBETA)
    assert set(seen[0]) == {"isDynasty", "numQbs", "numTeams", "ppr"}


def test_cache_is_keyed_by_format_so_leagues_cannot_share_values(monkeypatch):
    seen = []
    _patch(monkeypatch, seen)
    store = FakeStore()
    trade_radar.market(store, OMNIBETA)
    trade_radar.market(store, KEEFAMANIA)
    assert len(seen) == 2, "the second league was served the first league's market"


def test_sentiment_fields_survive(monkeypatch):
    seen = []
    _patch(monkeypatch, seen)
    rows, note = trade_radar.market(FakeStore(), OMNIBETA)
    assert note is None
    r = rows["4034"]
    # value alone cannot tell buy-low from sell-high; the trend can
    assert r["value"] == 5000
    assert r["trend30"] == -270
    assert r["rostered"] == pytest.approx(99.1)
    assert r["trade_freq"] == pytest.approx(0.4)


def test_values_still_returns_the_flat_shape_the_body_consumes(monkeypatch):
    seen = []
    _patch(monkeypatch, seen)
    vals, note = trade_radar.values(FakeStore(), OMNIBETA)
    assert vals == {"4034": 5000} and note is None


def test_an_outage_is_a_data_missing_line_not_a_crash(monkeypatch):
    def boom(url, params=None, timeout=20):
        raise ConnectionError("down")

    monkeypatch.setattr(market.requests, "get", boom)
    vals, note = trade_radar.values(FakeStore(), OMNIBETA)
    assert vals == {} and "DATA MISSING" in note
