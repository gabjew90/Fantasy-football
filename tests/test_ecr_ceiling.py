"""Expert panel ranks: ceiling, which is what a bench add is actually for."""

import pytest

from manager import ecr


class FakeStore:
    def __init__(self):
        self.d = {}

    def get(self, k, default=None):
        return self.d.get(k, default)

    def set(self, k, v):
        self.d[k] = v


CSV = (
    "ecr_type,player,pos,ecr,sd,best,worst,scrape_date\n"
    "rp,Kayshon Boutte,WR,65.88,8.18,50,101,2026-09-04\n"
    "ro,Kayshon Boutte,WR,169.75,26.05,121,277,2026-09-04\n"
    "rp,Dontayvion Wicks,WR,69.64,10.49,46,103,2026-09-04\n"
    "rp,Michael Wilson,WR,39.5,5.52,28,52,2026-09-04\n"
    "rp,Josh Allen,LB,12.0,2.0,8,20,2026-09-04\n"
    "dp,Kayshon Boutte,WR,40.0,5.0,20,60,2026-09-04\n"
    "rp,Justin Jefferson,WR,1.0,0.5,1,3,2026-09-04\n"
    "ro,Justin Jefferson,WR,2.0,0.8,1,4,2026-09-04\n"
    "rp,Justin Jefferson,LB,30.0,4.0,20,45,2026-09-04\n"
    "ro,Justin Jefferson,LB,90.0,9.0,70,120,2026-09-04\n"
)


def _patch(monkeypatch):
    class R:
        text = CSV

        @staticmethod
        def raise_for_status():
            return None

    monkeypatch.setattr(ecr.requests, "get", lambda url, timeout=30: R())


def test_positional_rank_is_what_is_kept(monkeypatch):
    _patch(monkeypatch)
    t, _ = ecr.fetch()
    b = t["kayshon boutte"]
    assert b["ecr"] == 65.88, "overall rank overwrote the positional one"
    assert b["best"] == 50 and b["worst"] == 101
    assert b["overall"] == 169.75


def test_dynasty_rows_are_ignored(monkeypatch):
    _patch(monkeypatch)
    t, _ = ecr.fetch()
    assert t["kayshon boutte"]["best"] == 50, "a dynasty row leaked into redraft"


def test_a_dead_feed_is_a_note_not_a_crash(monkeypatch):
    def boom(url, timeout=30):
        raise ConnectionError("down")

    monkeypatch.setattr(ecr.requests, "get", boom)
    t, note = ecr.fetch()
    assert t == {} and "DATA MISSING" in note


def test_the_store_caches(monkeypatch):
    calls = []

    class R:
        text = CSV

        @staticmethod
        def raise_for_status():
            return None

    monkeypatch.setattr(ecr.requests, "get",
                        lambda url, timeout=30: (calls.append(1), R())[1])
    s = FakeStore()
    ecr.fetch(s)
    ecr.fetch(s)
    assert len(calls) == 1


def test_position_must_agree_or_a_linebacker_inherits_the_quarterback(monkeypatch):
    _patch(monkeypatch)
    ctx = {"players": {"1": {"full_name": "Josh Allen", "position": "QB"},
                       "2": {"full_name": "Josh Allen", "position": "LB"}}}
    out, _ = ecr.by_sleeper_id(ctx)
    assert "1" not in out, "the QB was matched to the linebacker's panel row"
    assert "2" not in out, "IDP rows are not ranked at all"


def test_an_idp_namesake_does_not_overwrite_the_receivers_ranks(monkeypatch):
    """Review 2026-09-10: the file carries IDP rows and the table is keyed by
    name. Justin Jefferson the linebacker came after the receiver and
    overwrote his ecr and overall; by_sleeper_id then dropped the WR on the
    position check, and accepts() saw an UNRANKED starter."""
    _patch(monkeypatch)
    t, _ = ecr.fetch()
    jj = t["justin jefferson"]
    assert jj["pos"] == "WR" and jj["ecr"] == 1.0 and jj["overall"] == 2.0
    ctx = {"players": {"7": {"full_name": "Justin Jefferson", "position": "WR"}}}
    out, _ = ecr.by_sleeper_id(ctx)
    assert out["7"]["overall"] == 2.0


def test_annotate_reports_the_range_and_is_silent_without_one():
    assert ecr.annotate(None) == ""
    assert ecr.annotate({"best": None}) == ""
    out = ecr.annotate({"pos": "WR", "ecr": 65.9, "best": 50, "worst": 101})
    assert "WR66" in out and "best WR50" in out and "worst WR101" in out


def test_ceiling_beats_runs_backwards_because_these_are_ranks():
    wicks = {"pos": "WR", "best": 46}
    boutte = {"pos": "WR", "best": 50}
    assert ecr.ceiling_beats(wicks, boutte) is True, "lower rank is the better ceiling"
    assert ecr.ceiling_beats(boutte, wicks) is False


def test_ceiling_never_compares_across_positions():
    """K3 is a smaller number than WR46 and means nothing next to it. The
    first upside board sorted every position together and produced five
    kickers."""
    kicker = {"pos": "K", "best": 3}
    receiver = {"pos": "WR", "best": 46}
    assert ecr.ceiling_beats(kicker, receiver) is False


def test_a_missing_side_is_not_a_win():
    assert ecr.ceiling_beats({"pos": "WR", "best": 10}, None) is False
    assert ecr.ceiling_beats(None, {"pos": "WR", "best": 10}) is False
