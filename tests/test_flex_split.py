"""Plan 2026-09-02 A4: the flex split is derived per league and stored in
its yaml; the bench allowance raises RB/WR demand by the absence factor."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import derive_flex_split as DFS  # noqa: E402
from draftkit import onboard as OB  # noqa: E402
from draftkit.bench import ABSENT_WEEKS, BYE_WEEKS, FANTASY_WEEKS  # noqa: E402

ROSTER_10 = ["QB", "WR", "WR", "RB", "RB", "TE", "W/R/T", "K", "DEF", "BN", "BN", "BN", "BN", "BN", "BN", "IR", "IR"]


# ---------- format_key ----------

@pytest.mark.parametrize("rec,key", [(1.0, "full"), (1.5, "full"), (0.5, "half"), (0.0, "half"), (None, "half")])
def test_format_key_follows_the_adp_key_rule(rec, key):
    assert OB.format_key({"rec": rec} if rec is not None else {}) == key
    assert OB.format_key(None) == "half"


# ---------- resolution order ----------

def test_resolution_order_yaml_then_format_then_legacy():
    yaml_split = {"RB": 0.7, "WR": 0.3, "TE": 0.0, "derived": "2026-09-02", "board": "tiers.x.csv"}
    assert OB.resolve_flex_split({"rec": 1.0}, yaml_split) == {"RB": 0.7, "WR": 0.3, "TE": 0.0}
    assert OB.resolve_flex_split({"rec": 1.0}, None) == OB.FLEX_SPLIT_BY_FORMAT["full"]
    assert OB.resolve_flex_split({"rec": 0.5}, None) == OB.FLEX_SPLIT_BY_FORMAT["half"]
    assert OB.resolve_flex_split(None, None) == OB.FLEX_SPLIT
    # an empty / all-zero yaml block is not a split; fall through
    assert OB.resolve_flex_split({"rec": 0.5}, {"RB": 0, "WR": 0, "TE": 0}) == OB.FLEX_SPLIT_BY_FORMAT["half"]


def test_no_scoring_no_split_is_byte_identical_to_the_legacy_call():
    """tests/test_multileague.py pins the 45/45/10 numbers; the new keywords
    must not move them when absent."""
    positions = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "K", "DEF", "BN"]
    assert OB.derive_baselines(12, positions) == {"QB": 12, "RB": 35, "WR": 35, "TE": 14, "K": 12, "DEF": 12}


def test_yaml_split_drives_the_baselines():
    b = OB.derive_baselines(10, ROSTER_10, scoring={"rec": 0.5}, flex_split={"RB": 0.8, "WR": 0.2, "TE": 0.0})
    assert (b["RB"], b["WR"], b["TE"]) == (28, 22, 10)      # 2.8 / 2.2 / 1.0 (floored at teams)


# ---------- bench allowance ----------

def test_bench_allowance_raises_rb_wr_only_by_the_absence_factor():
    split = {"RB": 0.5, "WR": 0.5, "TE": 0.0}
    base, _ = OB.slot_counts(ROSTER_10, split)
    with_b, _ = OB.slot_counts(ROSTER_10, split, bench_allowance=True)
    for pos in ("RB", "WR"):
        want = base[pos] * (1 + (ABSENT_WEEKS[pos] + BYE_WEEKS) / FANTASY_WEEKS)
        assert with_b[pos] == pytest.approx(want)
        assert with_b[pos] > base[pos]
    for pos in ("QB", "TE", "K", "DEF"):
        assert with_b[pos] == base[pos]
    assert OB.bench_allowance_factor("TE") == 1.0


# ---------- the walk ----------

def _p(name, pos, pts):
    return {"name": name, "pos": pos, "proj_pts": pts}


def test_walk_on_a_synthetic_two_team_board():
    """2 teams x (1 RB, 1 WR, 1 TE, 1 FLEX): the dedicated starters go first,
    then the two flex slots take the best of what is left -- one RB and one
    WR here, no TE."""
    board = [_p("rb1", "RB", 300), _p("rb2", "RB", 280), _p("rb3", "RB", 200), _p("rb4", "RB", 100),
             _p("wr1", "WR", 290), _p("wr2", "WR", 270), _p("wr3", "WR", 190), _p("wr4", "WR", 90),
             _p("te1", "TE", 200), _p("te2", "TE", 150), _p("te3", "TE", 80),
             _p("qb1", "QB", 400)]
    res = DFS.flex_walk(board, 2, {"QB": 1, "RB": 1, "WR": 1, "TE": 1, "FLEX": 1})
    assert res["shares"] == {"RB": 0.5, "WR": 0.5, "TE": 0.0}
    assert res["n_flex"] == 2 and res["last"] == {"RB": "rb3", "WR": "wr3"}


def test_walk_without_a_flex_slot_is_all_zero():
    res = DFS.flex_walk([_p("rb1", "RB", 1)], 2, {"RB": 1})
    assert res["shares"] == {"RB": 0.0, "WR": 0.0, "TE": 0.0} and res["n_flex"] == 0


# ---------- --write round trip ----------

def test_write_round_trips_the_yaml_block_without_touching_other_keys(tmp_path):
    y = tmp_path / "x.yaml"
    body = "# comment kept\nleague_id: \"1\"\nreplacement_baselines:\n  RB: 24   # inline comment\n\nexpected:\n  teams: 10\n"
    y.write_text(body, encoding="utf-8")
    block = DFS.yaml_block({"RB": 0.8, "WR": 0.2, "TE": 0.0}, "tiers.x.csv", "2026-09-02")
    assert DFS.write_split(y, block) == "appended"
    text = y.read_text(encoding="utf-8")
    assert text.startswith(body) and text.endswith(block)
    import yaml
    d = yaml.safe_load(text)
    fs = d["flex_split"]
    assert (fs["RB"], fs["WR"], fs["TE"], fs["board"]) == (0.8, 0.2, 0.0, "tiers.x.csv")
    assert str(fs["derived"]) == "2026-09-02"          # yaml may parse the date as a date object
    assert d["replacement_baselines"] == {"RB": 24} and d["expected"] == {"teams": 10}
    # second write replaces in place, other keys untouched, one block only
    block2 = DFS.yaml_block({"RB": 0.6, "WR": 0.4, "TE": 0.0}, "tiers.y.csv", "2026-09-03")
    assert DFS.write_split(y, block2) == "replaced"
    text2 = y.read_text(encoding="utf-8")
    assert text2.count("flex_split:") == 1 and text2.startswith(body) and "tiers.y.csv" in text2 and "tiers.x.csv" not in text2


# ---------- onboard writes the format fallback ----------

def test_onboard_writes_the_format_fallback_split(tmp_path, monkeypatch):
    lg = {"name": "Test League", "season": 2026, "draft_id": "d1",
          "settings": {"num_teams": 12}, "scoring_settings": {"rec": 1.0},
          "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "K", "DEF", "BN", "BN"]}
    monkeypatch.setattr(OB, "get_json", lambda url: lg)
    out = OB.onboard("1", "me", root=tmp_path)
    import yaml
    d = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert d["flex_split"]["RB"] == pytest.approx(OB.FLEX_SPLIT_BY_FORMAT["full"]["RB"], abs=1e-3)
    assert d["flex_split"]["derived"] == "format-fallback-full"
    # baselines came through the same split: RB 2 + 2 x 0.333 = 2.667 -> 32, WR 2 + 1.333 -> 40
    assert (d["replacement_baselines"]["RB"], d["replacement_baselines"]["WR"], d["replacement_baselines"]["TE"]) == (32, 40, 12)
    assert "derive_flex_split.py" in out.read_text(encoding="utf-8")
