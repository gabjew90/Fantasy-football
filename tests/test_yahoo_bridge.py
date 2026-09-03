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


# ---------- plan B1 (2026-09-02): the plan carries the engine's numbers ----------

def test_plan_rows_carry_survival_fields_and_depth_tail_leaves_them_empty():
    players = _players()
    state = {"my_slot": 8, "teams": 10, "rounds": 15,
             "drafted": [{"pick_no": n, "name": f"RB Player{n - 1}", "pos": "RB"} for n in range(1, 8)],
             "my_roster": []}
    t = yb.build_tracker(_Cfg(), players, state)
    recs = t.recommendations(top_n=5)
    rows = yb.plan_rows(t, recs, t.urgency_report())
    assert rows and all(set(r) >= {"n", "p", "t", "v", "a", "why", "s", "sr", "e", "b"} for r in rows)
    assert any(isinstance(r["s"], float) and 0.0 <= r["s"] <= 1.0 for r in rows)
    assert any(isinstance(r["sr"], float) for r in rows) and any(isinstance(r["e"], float) for r in rows)
    # without a report the rows still have the keys, empty
    bare = yb.plan_rows(t, recs, None)
    assert all(r["s"] is None and r["e"] is None for r in bare)
    tail = yb.depth_tail(t, rows, 25)
    assert all(r["s"] is None for r in tail[len(rows):])


def test_log_plan_writes_one_structured_event_per_state(tmp_path):
    players = _players()
    state = {"my_slot": 8, "teams": 10, "rounds": 15,
             "drafted": [{"pick_no": n, "name": f"RB Player{n - 1}", "pos": "RB"} for n in range(1, 8)],
             "my_roster": []}
    t = yb.build_tracker(_Cfg(), players, state)
    recs = t.recommendations(top_n=5)
    report = t.urgency_report()
    path = yb.log_plan(t, recs, report, "/draftclient/f1/10505450/8", tmp_path)
    assert path.name == "yahoo_10505450.jsonl"
    yb.log_plan(t, recs, report, "/draftclient/f1/10505450/8", tmp_path)   # same state: no second event
    import json
    events = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]
    rec_events = [e for e in events if e["type"] == "recs"]
    assert len(rec_events) == 1
    ev = rec_events[0]
    assert ev["current_pick"] == 8 and ev["window_start"] == 9 and ev["my_next_pick"] == 13
    assert isinstance(ev["recommendations"][0]["survival"], float)
    assert yb.room_of("mock_10505450") == "10505450" and yb.room_of(None) == "room"


def test_engine_knobs_flow_from_the_config_through_one_list():
    """Plan B3: the Yahoo tracker reads Tracker.ENGINE_KNOBS, not a hand copy."""
    from draftkit.tracker import Tracker

    class _KnobCfg(_Cfg):
        def __init__(self):
            super().__init__()
            self._d["engine"] = {"sims": 50, "pool_min": 20, "need_damp": 0.5, "run_ratio": 2.0,
                                 "autopick_sigma_scale": 0.25}

    t = yb.build_tracker(_KnobCfg(), _players(), {"my_slot": 8, "teams": 10, "rounds": 15,
                                                  "drafted": [], "my_roster": []})
    assert (t.need_damp, t.run_ratio, t.autopick_sigma_scale, t.sims, t.pool_min) == (0.5, 2.0, 0.25, 50, 20)
    assert t.qb_filled_damp == Tracker.qb_filled_damp == 0.05      # absent key: class default
    assert Tracker.need_damp == 0.15 and Tracker.away_slots == frozenset()
    assert {k for k, _ in Tracker.ENGINE_KNOBS} >= {"need_damp", "run_ratio", "survival_shrink", "sims"}


def test_away_teams_become_away_slots_through_drafted_team_ids():
    """Plan B5: the page reports away TEAM ids; drafted entries with team ids
    map them to snake slots. Without team ids (DOM path) nothing is guessed."""
    drafted = [{"pick_no": 1, "name": "RB Player0", "pos": "RB", "team_id": "7"},
               {"pick_no": 2, "name": "RB Player1", "pos": "RB", "team_id": "3"},
               {"pick_no": 19, "name": "RB Player2", "pos": "RB", "team_id": "3"}]   # slot 2 in round 2 (10 teams)
    state = {"my_slot": 8, "teams": 10, "rounds": 15, "drafted": drafted, "my_roster": [],
             "away_teams": ["3", "9"]}
    assert yb.away_slots_from_state(state, 10) == frozenset({2})          # team 3 -> slot 2; team 9 unseen
    t = yb.build_tracker(_Cfg(), _players(), state)
    assert t.away_slots == frozenset({2})
    rivals = t._rival_states(4, 8)
    assert [r["autopick"] for r in rivals] == [False, False, False, False]  # slots 4-7 are human
    assert any(r["autopick"] for r in t._rival_states(1, 4))                # slot 2 is on autopick
    dom = dict(state, drafted=[{"pick_no": 1, "name": "RB Player0", "pos": "RB"}])
    assert yb.away_slots_from_state(dom, 10) == frozenset()


def test_plan_detail_records_state_needs_every_market_and_the_full_plan(tmp_path):
    """The scrutiny sidecar (stress mocks 2026-09-02): one record per bridge
    call carrying what the page sent, the engine needs, every market's
    numbers with named top survivals, the recs and the whole plan."""
    players = _players()
    state = {"my_slot": 8, "teams": 10, "rounds": 15, "current_pick": 28, "on_clock": False,
             "drafted": [{"pick_no": 1, "name": "RB Player0", "pos": "RB", "team_id": "1"}],
             "my_roster": [{"name": "T. Player0", "pos": "TE"}], "away_teams": ["3"]}
    t = yb.build_tracker(_Cfg(), players, state)
    recs = t.recommendations(top_n=5)
    report = t.urgency_report()
    plan = yb.plan_rows(t, recs, report)
    d = yb.plan_detail(t, recs, report, plan, state)
    assert d["type"] == "plan_detail" and d["current_pick"] == 28 and d["my_slot"] == 8
    assert d["state_in"]["drafted"] == 1 and d["state_in"]["my_roster"] == ["T. Player0 (TE)"]
    assert d["state_in"]["away_teams"] == ["3"]
    assert d["needs"]["TE"] == 0 and len(d["plan"]) == len(plan) and len(d["recs"]) == len(recs)
    assert d["markets"], "every market the report priced"
    for mkt, m in d["markets"].items():
        assert {"best_now", "e_best_next", "urgency", "top_survival", "pool"} <= set(m)
        for row in m["top_survival"]:
            assert row["name"] and 0.0 <= row["s"] <= 1.0
    path = yb.log_plan_detail(t, recs, report, plan, state, "/draftclient/f1/424242/8", tmp_path)
    yb.log_plan_detail(t, recs, report, plan, state, "/draftclient/f1/424242/8", tmp_path)
    assert path.name == "yahoo_424242.plans.jsonl"
    assert len(path.read_text(encoding="utf-8").splitlines()) == 2, "no dedupe: every call is an event"


# ---------- review 2026-09-02: the bridge reconciles DOWN, the store beats the panel, the seat is checked ----------

def test_feed_entries_at_or_past_the_header_pick_are_dropped_and_said():
    """One spurious panel line used to leave current_pick one ahead of the
    header for the rest of the room; the page's gate then refused every click."""
    players = _players()
    drafted = [{"pick_no": n, "name": f"RB Player{n - 1}", "pos": "RB"} for n in range(1, 8)]
    drafted.append({"pick_no": 8, "name": "WR Player0", "pos": "WR"})        # numbered AT the pick on the clock
    state = {"my_slot": 8, "teams": 10, "rounds": 15, "current_pick": 8, "drafted": drafted, "my_roster": []}
    t = yb.build_tracker(_Cfg(), players, state)
    assert t.current_pick == 8
    assert any("dropped 1 feed entries" in w for w in t.warnings), t.warnings


def test_my_own_pick_numbered_past_the_header_is_kept():
    players = _players()
    drafted = [{"pick_no": n, "name": f"RB Player{n - 1}", "pos": "RB"} for n in range(1, 8)]
    drafted.append({"pick_no": 8, "name": "WR Player0", "pos": "WR", "mine": True})
    state = {"my_slot": 8, "teams": 10, "rounds": 15, "current_pick": 8, "drafted": drafted, "my_roster": []}
    t = yb.build_tracker(_Cfg(), players, state)
    assert t._my_pos_counts() == {"WR": 1}
    assert any("over-count" in w for w in t.warnings)


def test_merge_feed_lets_the_store_correct_a_panel_misread():
    mem = {}
    yb.merge_feed(mem, [{"pick_no": 9, "name": "A. Brown", "pos": "WR", "mine": True}])        # panel view
    got = yb.merge_feed(mem, [{"pick_no": 9, "name": "Amon-Ra St. Brown", "pos": "WR", "team_id": "4"}])
    assert got[0]["name"] == "Amon-Ra St. Brown" and got[0]["team_id"] == "4"
    assert got[0]["mine"] is True, "a mine flag learned earlier survives the correction"
    # a second panel view never undoes the store's entry
    got = yb.merge_feed(mem, [{"pick_no": 9, "name": "A. Brown", "pos": "WR"}])
    assert got[0]["name"] == "Amon-Ra St. Brown"


def test_seat_is_taken_from_my_own_picks_when_the_url_slot_disagrees():
    """A room reshuffled us from slot 3 to slot 10 at the bell; our flagged
    picks fall on the real seat and the survival window must use it."""
    players = _players()
    drafted = [{"pick_no": n, "name": f"RB Player{n - 1}", "pos": "RB"} for n in range(1, 21)]
    for n in (10, 11):                                   # slot 10 picks 10 and 11 in a 10-team snake
        drafted[n - 1] = dict(drafted[n - 1], mine=True, team_id="7")
    state = {"my_slot": 3, "teams": 10, "rounds": 15, "current_pick": 21, "drafted": drafted, "my_roster": []}
    t = yb.build_tracker(_Cfg(), players, state)
    assert t.my_slot == 10
    assert t._my_pos_counts() == {"RB": 2}
    assert any("my_slot 3 disagrees" in w for w in t.warnings), t.warnings


def test_roster_unknown_past_my_first_turn_is_a_named_warning():
    players = _players()
    drafted = [{"pick_no": n, "name": f"RB Player{n - 1}", "pos": "RB"} for n in range(1, 12)]
    state = {"my_slot": 8, "teams": 10, "rounds": 15, "current_pick": 12, "drafted": drafted, "my_roster": []}
    t = yb.build_tracker(_Cfg(), players, state)
    assert any("MY ROSTER UNKNOWN" in w for w in t.warnings), t.warnings
    # an unresolved drafted name is reported, never dropped in silence
    state2 = dict(state, drafted=drafted + [{"pick_no": 12, "name": "Nobody Real", "pos": "WR"}], current_pick=13)
    t2 = yb.build_tracker(_Cfg(), players, state2)
    assert t2.unresolved and any("matched no board player" in w for w in t2.warnings)


def test_depth_tail_applies_must_fill_not_only_the_position_caps():
    """Two picks left, K and DEF open: the tail must be K/DEF only."""
    players = _players()
    mine = ([{"name": "QB Player0", "pos": "QB"}] + [{"name": f"RB Player{i}", "pos": "RB"} for i in range(6)]
            + [{"name": f"WR Player{i}", "pos": "WR"} for i in range(5)] + [{"name": "TE Player0", "pos": "TE"}])
    assert len(mine) == 13
    state = {"my_slot": 8, "teams": 10, "rounds": 15, "current_pick": 133, "drafted": [], "my_roster": mine}
    t = yb.build_tracker(_Cfg(), players, state)
    tail = yb.depth_tail(t, [], 40)
    assert tail and {x["p"] for x in tail} <= {"K", "DEF"}, [x["p"] for x in tail]
