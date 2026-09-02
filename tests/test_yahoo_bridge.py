"""The Yahoo bridge runs the REAL engine; the page only actuates.

These cover the translation layer between Yahoo's vocabulary and the engine's,
which is where a silent mistranslation can disable a guardrail without
throwing anything.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("yb", ROOT / "scripts" / "yahoo_bridge.py")
yb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(yb)


KEEFAMANIA_ROSTER = ["QB", "WR", "WR", "RB", "RB", "TE", "W/R/T", "K", "DEF",
                     "BN", "BN", "BN", "BN", "BN", "BN", "IR", "IR"]


def test_yahoo_slot_names_map_to_engine_slots():
    """Yahoo calls the flex "W/R/T" and lists IR slots that are never drafted.

    Feeding that list to snake.roster_slots_from_draft_settings (which reads
    Sleeper's slots_* keys) returned an EMPTY map, so my_needs() came back all
    zeros and every need-aware guardrail quietly switched off -- no error, no
    warning, just a worse draft.
    """
    got = yb.slots_from_yahoo_roster(KEEFAMANIA_ROSTER)
    assert got["QB"] == 1
    assert got["RB"] == 2
    assert got["WR"] == 2
    assert got["TE"] == 1
    assert got["FLEX"] == 1, "W/R/T must become the engine's FLEX slot"
    assert got["K"] == 1
    assert got["DEF"] == 1
    assert got["BN"] == 6
    assert "IR" not in got or got.get("IR", 0) == 0, "IR is never drafted"


def test_starters_exclude_bench_and_ir():
    got = yb.slots_from_yahoo_roster(KEEFAMANIA_ROSTER)
    starters = sum(v for k, v in got.items() if k != "BN")
    assert starters == 9, got          # 9 starters, 6 bench, 2 IR undrafted


def test_flex_aliases_all_recognised():
    for alias in ("W/R/T", "WRT", "FLEX", "W/R"):
        got = yb.slots_from_yahoo_roster(["QB", alias])
        assert got["FLEX"] == 1, alias


def test_player_key_matches_how_yahoo_renders_a_row():
    """The engine holds full names; Yahoo prints "J. Gibbs". Suffixes are
    dropped so "Brian Thomas Jr." and "B. Thomas Jr." agree."""
    assert yb.key("Jahmyr Gibbs") == "j gibbs"
    assert yb.key("Brian Thomas Jr.") == yb.key("B. Thomas Jr.".replace("B.", "Brian"))
    assert yb.key("Patrick Mahomes II") == "p mahomes"
    assert yb.key("Ja'Marr Chase") == "j chase"


def test_pick_slot_is_derived_from_pick_number():
    """Yahoo's pick feed gives the player and the pick NUMBER, never whose
    pick it was. The bridge used to read d["slot"], which defaulted to 0, so
    no pick was attributed to us -- my_pos_counts() came back empty and the
    engine recommended a SECOND QB in round 4 against a round-10 gate. Caught
    live in a mock.

    In a snake the slot is fully determined by the pick number, so derive it.
    """
    from draftkit import snake
    teams = 10
    # 10-team snake: round 1 runs 1..10, round 2 runs 20..11 backwards
    assert snake.pick_to_round_slot(1, teams) == (1, 1)
    assert snake.pick_to_round_slot(10, teams) == (1, 10)
    assert snake.pick_to_round_slot(11, teams) == (2, 10)   # turn: back-to-back
    assert snake.pick_to_round_slot(20, teams) == (2, 1)
    assert snake.pick_to_round_slot(21, teams) == (3, 1)


def test_our_picks_are_attributed_to_us():
    """The roster the engine sees must contain exactly our own picks."""
    from draftkit import snake
    teams, my_slot = 10, 10
    feed = [{"pick_no": n, "name": f"P{n}", "pos": "RB"} for n in range(1, 22)]
    ours = [d["pick_no"] for d in feed
            if snake.pick_to_round_slot(d["pick_no"], teams)[1] == my_slot]
    assert ours == [10, 11], ours      # slot 10 picks back-to-back at the turn


# ---------- mock 11 (2026-09-01): reconciling the page's three views ----------

class _Cfg:
    """Minimal stand-in for draftkit.config.Config: only .get() is used."""
    def __init__(self):
        self._d = {
            "expected": {"teams": 10, "rounds": 15, "roster": KEEFAMANIA_ROSTER},
            "engine": {"sims": 50, "pool_min": 20},
            "guardrails": {"qb2_earliest_round": 10, "te2_fall_picks": 12},
        }

    def get(self, k, default=None):
        return self._d.get(k, default)


def _players():
    out, i = [], 0
    for pos, n in (("QB", 6), ("RB", 12), ("WR", 12), ("TE", 6), ("K", 3), ("DEF", 3)):
        for j in range(n):
            i += 1
            out.append({"sleeper_id": str(i), "name": f"{pos} Player{j}", "pos": pos,
                        "team": "XX", "vorp": 100.0 - i, "vorp_flex": 90.0 - i,
                        "proj_pts": 300.0 - i, "adp": float(i), "adp_delta": 0.0,
                        "tier": 1, "pos_rank": j + 1, "value_rank": i,
                        "cliff_flag": False, "upside_flag": False,
                        "proj_source": "blend", "backs_up": "", "backs_up_pos": "",
                        "starter_fragility_label": "", "starter_exp_games": None,
                        "starter_avail": None})
    return out


def test_roster_panel_attributes_picks_the_feed_left_unlabelled():
    """The Picks panel's "You" label is missing on autopicks and after a
    reload the panel holds only the last few picks. The roster panel is
    authoritative for what WE hold, so it is a second attribution source."""
    players = _players()
    state = {"my_slot": 8, "teams": 10, "rounds": 15,
             # feed knows two of our picks but labels neither "You"
             "drafted": [{"pick_no": 8, "name": "TE Player0", "pos": "TE"},
                         {"pick_no": 13, "name": "TE Player1", "pos": "TE"}],
             "my_roster": [{"name": "T. Player0", "pos": "TE"},
                           {"name": "T. Player1", "pos": "TE"}]}
    t = yb.build_tracker(_Cfg(), players, state)
    assert t._my_pos_counts() == {"TE": 2}
    assert t.my_needs()["TE"] == 0


def test_roster_players_missing_from_the_feed_are_still_our_picks():
    players = _players()
    state = {"my_slot": 8, "teams": 10, "rounds": 15,
             "drafted": [{"pick_no": 71, "name": "RB Player9", "pos": "RB"}],
             "my_roster": [{"name": "T. Player0", "pos": "TE"},
                           {"name": "Q. Player0", "pos": "QB"}]}
    t = yb.build_tracker(_Cfg(), players, state)
    assert t._my_pos_counts() == {"TE": 1, "QB": 1}


def test_header_pick_number_is_authoritative_for_where_we_are():
    """A feed of three picks after a reload must not make the engine believe
    it is pick 4 in round 1."""
    players = _players()
    state = {"my_slot": 8, "teams": 10, "rounds": 15, "current_pick": 74,
             "drafted": [{"pick_no": n, "name": f"RB Player{n - 71}", "pos": "RB"}
                         for n in (71, 72, 73)],
             "my_roster": []}
    t = yb.build_tracker(_Cfg(), players, state)
    assert t.current_pick == 74
    # fillers remove nobody real from the board
    assert all(p["sleeper_id"] not in t.state.drafted_ids
               for p in players if p["name"] not in ("RB Player0", "RB Player1", "RB Player2"))


def test_depth_tail_obeys_the_guardrails():
    """The tail past the engine's named candidates used to be raw VORP order
    with nothing said about position. With two tight ends rostered it offered
    TE3 and TE4; the page took both."""
    players = _players()
    state = {"my_slot": 8, "teams": 10, "rounds": 15, "current_pick": 28,
             "drafted": [],
             "my_roster": [{"name": "T. Player0", "pos": "TE"},
                           {"name": "T. Player1", "pos": "TE"},
                           {"name": "Q. Player0", "pos": "QB"}]}
    t = yb.build_tracker(_Cfg(), players, state)
    tail = yb.depth_tail(t, [], 40)
    positions = {x["p"] for x in tail}
    assert "TE" not in positions, "never a third tight end"
    assert "QB" not in positions, "no QB2 before the round gate"
    assert "K" not in positions and "DEF" not in positions, "K/DEF wait for the end"
    assert positions <= {"RB", "WR"}


def test_merge_feed_keeps_the_union_across_partial_views():
    """The Picks panel virtualises and a reload shows only the last few picks;
    the bridge outlives both and keeps every pick it has ever been shown."""
    mem = {}
    yb.merge_feed(mem, [{"pick_no": 1, "name": "A", "pos": "RB"},
                        {"pick_no": 2, "name": "B", "pos": "WR"}])
    got = yb.merge_feed(mem, [{"pick_no": 9, "name": "C", "pos": "TE"}])
    assert [d["pick_no"] for d in got] == [1, 2, 9]


def test_merge_feed_never_forgets_and_learns_the_you_label():
    mem = {}
    yb.merge_feed(mem, [{"pick_no": 8, "name": "T. McBride", "pos": "TE"}])
    got = yb.merge_feed(mem, [{"pick_no": 8, "name": "T. McBride", "pos": "TE", "mine": True}])
    assert got[0]["mine"] is True
    # a later unlabelled view does not strip the label
    got = yb.merge_feed(mem, [{"pick_no": 8, "name": "T. McBride", "pos": "TE"}])
    assert got[0]["mine"] is True


def test_merge_feed_ignores_garbage_pick_numbers():
    mem = {}
    got = yb.merge_feed(mem, [{"pick_no": "x", "name": "A", "pos": "RB"},
                              {"pick_no": None, "name": "B", "pos": "RB"},
                              {"pick_no": "3", "name": "C", "pos": "RB"}])
    assert [d["pick_no"] for d in got] == ["3"]


# ---------- mock 13 (2026-09-02): first-initial keys collide ----------

def _two_browns():
    players = _players()
    base = dict(players[20])
    for i, (name, vorp) in enumerate((("Amon-Ra St. Brown", 77.4), ("A.J. Brown", 35.9))):
        players.append(dict(base, sleeper_id=f"b{i}", name=name, pos="WR", team="XX",
                            vorp=vorp, vorp_flex=vorp, proj_pts=200.0 + vorp, adp=5.0 + 12 * i))
    return players


def test_two_players_with_the_same_initial_and_surname_are_both_drafted():
    """Yahoo prints "A. Brown" for Amon-Ra St. Brown AND A.J. Brown. Keying
    the board on first-initial + surname kept only the higher-VORP one, so
    A.J. Brown (pick 17 of mock 13) was never marked drafted and led the
    engine's plan for the next thirty picks. The store hands us FULL names;
    match on those first and fall back to the initial key only for the
    panel's abbreviated text."""
    players = _two_browns()
    state = {"my_slot": 6, "teams": 10, "rounds": 15, "current_pick": 46,
             "drafted": [{"pick_no": 5, "name": "Amon-Ra St. Brown", "pos": "WR"},
                         {"pick_no": 17, "name": "A.J. Brown", "pos": "WR"}],
             "my_roster": []}
    t = yb.build_tracker(_Cfg(), players, state)
    assert {"b0", "b1"} <= t.state.drafted_ids
    assert not any(p["name"] == "A.J. Brown" for p in t.remaining("WR"))


def test_abbreviated_name_resolves_to_the_undrafted_namesake():
    """The Picks panel only ever says "A. Brown". When one namesake is already
    gone, the abbreviated pick is the other one -- never a second copy of the
    one we already saw leave."""
    players = _two_browns()
    state = {"my_slot": 6, "teams": 10, "rounds": 15, "current_pick": 20,
             "drafted": [{"pick_no": 5, "name": "Amon-Ra St. Brown", "pos": "WR"},
                         {"pick_no": 17, "name": "A. Brown", "pos": "WR"}],
             "my_roster": []}
    t = yb.build_tracker(_Cfg(), players, state)
    assert {"b0", "b1"} <= t.state.drafted_ids


def test_roster_attribution_does_not_bleed_across_namesakes():
    """We hold A.J. Brown; a rival took Amon-Ra. The rival's pick must not be
    attributed to us just because both render as "A. Brown"."""
    players = _two_browns()
    state = {"my_slot": 6, "teams": 10, "rounds": 15, "current_pick": 20,
             "drafted": [{"pick_no": 5, "name": "Amon-Ra St. Brown", "pos": "WR"},
                         {"pick_no": 15, "name": "A.J. Brown", "pos": "WR"}],
             "my_roster": [{"name": "A.J. Brown", "pos": "WR"}]}
    t = yb.build_tracker(_Cfg(), players, state)
    mine = {x["player_id"] for x in t.state.picks if x["draft_slot"] == 6}
    assert mine == {"b1"}, mine
