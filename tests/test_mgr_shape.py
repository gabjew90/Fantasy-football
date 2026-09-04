"""League shape from data, not literals.

draftkit/briefs.py carried Omnibeta's starting lineup as module constants
(SLOTS + FLEX = 2) and the manager imported them, so a 10-team one-flex league
had its lineup optimised into ten starters. tests/test_multileague.py's guard
greps names and ids only, so shape literals slipped through.
"""
import pytest

from draftkit.shape import LeagueShape, shape_for, starting_slots

OMNIBETA = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "K", "DEF",
            "BN", "BN", "BN", "BN", "BN"]
KEEFAMANIA = ["QB", "WR", "WR", "RB", "RB", "TE", "W/R/T", "K", "DEF",
              "BN", "BN", "BN", "BN", "BN", "BN", "IR", "IR"]


class _Cfg(dict):
    def __init__(self, roster, name="omnibeta"):
        super().__init__({"expected": {"roster": roster}})
        self.league_name = name


def test_omnibeta_shape_matches_the_retired_literals():
    """The defaults-to-today proof: the derived shape must equal the constants
    it replaces, or this change moves live Omnibeta numbers."""
    s = starting_slots(OMNIBETA)
    assert s.slots == {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1}
    assert s.flex == 2 and s.bench == 5 and s.n_starters == 10


def test_one_flex_league_starts_nine():
    """Keefamania: W/R/T is one flex, IR carries no lineup slot."""
    s = starting_slots(KEEFAMANIA)
    assert s.slots == {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1}
    assert s.flex == 1 and s.bench == 6 and s.n_starters == 9


def test_the_two_leagues_do_not_have_the_same_shape():
    """The bug in one line: one literal cannot serve both."""
    assert starting_slots(OMNIBETA).n_starters != starting_slots(KEEFAMANIA).n_starters


def test_superflex_is_its_own_slot_not_a_quarterback():
    s = starting_slots(["QB", "SUPER_FLEX", "RB", "BN"])
    assert s.slots["QB"] == 1 and s.superflex == 1 and s.n_starters == 3


def test_unknown_starting_slot_is_loud():
    with pytest.raises(ValueError, match="unrecognised roster slots"):
        starting_slots(["QB", "RB", "WOMBAT"])


def test_live_roster_positions_win_over_the_yaml():
    cfg = _Cfg(OMNIBETA)
    shape, warns = shape_for(cfg, {"roster_positions": KEEFAMANIA})
    assert shape.flex == 1 and "sleeper" in shape.source
    assert warns and "disagrees" in warns[0]


def test_agreement_is_silent():
    cfg = _Cfg(OMNIBETA)
    shape, warns = shape_for(cfg, {"roster_positions": OMNIBETA})
    assert warns == [] and shape.n_starters == 10


def test_yaml_is_the_fallback_when_the_league_object_is_bare():
    cfg = _Cfg(KEEFAMANIA, name="keefamania")
    shape, warns = shape_for(cfg, {})
    assert shape.flex == 1 and "keefamania.yaml" in shape.source


def test_no_shape_anywhere_is_a_loud_error_not_a_guess():
    with pytest.raises(ValueError, match="no roster shape"):
        shape_for(_Cfg([]), {})


def test_shape_is_hashable_and_frozen():
    """It is passed around as a value; nothing downstream may mutate it."""
    s = starting_slots(OMNIBETA)
    with pytest.raises(Exception):
        s.flex = 3  # type: ignore[misc]
    assert isinstance(s, LeagueShape)


# --- shape independence: the same code, two leagues, two legal lineups -------
# The defect this whole module exists to remove was a ten-starter lineup being
# set in a nine-starter league. These assert the OUTPUT changes with the shape,
# which a re-hardcoded literal cannot fake.

def _roster():
    def p(pid, pos, wk):
        return {"sleeper_id": pid, "name": f"{pos} {pid}", "pos": pos,
                "weekly": wk, "team": "SFO"}
    return [p("q1", "QB", 22), p("q2", "QB", 18),
            p("r1", "RB", 16), p("r2", "RB", 15), p("r3", "RB", 13),
            p("w1", "WR", 14), p("w2", "WR", 12), p("w3", "WR", 11),
            p("t1", "TE", 10), p("t2", "TE", 6),
            p("k1", "K", 8), p("d1", "DEF", 7)]


def test_a_one_flex_league_starts_nine_and_a_two_flex_league_starts_ten():
    from draftkit.lineup import optimal_lineup
    roster = _roster()
    one = starting_slots(KEEFAMANIA)
    two = starting_slots(OMNIBETA)
    assert one.n_starters == 9 and two.n_starters == 10
    l1 = optimal_lineup(roster, one.slots, flex_slots=one.flex_slots)
    l2 = optimal_lineup(roster, two.slots, flex_slots=two.flex_slots)
    assert len(l1) == 9 and len(l2) == 10
    # the extra flex is a real decision, not a repeated player
    assert {p["sleeper_id"] for p in l1} < {p["sleeper_id"] for p in l2}
    assert len({p["sleeper_id"] for p in l2}) == 10


def test_a_superflex_slot_starts_the_second_quarterback():
    """Neither current league has one, so this is the guard that the slot is
    filled rather than silently dropped if a league ever adds it."""
    from draftkit.lineup import optimal_lineup
    sf = starting_slots(["QB", "RB", "RB", "WR", "WR", "TE", "W/R/T",
                         "SUPER_FLEX", "K", "DEF", "BN", "BN"])
    assert sf.superflex == 1 and sf.n_starters == 10
    got = optimal_lineup(_roster(), sf.slots, flex_slots=sf.flex_slots)
    ids = [p["sleeper_id"] for p in got]
    assert "q2" in ids, "the second QB is the best superflex body and was dropped"
    assert len(ids) == len(set(ids)) == 10


def test_a_rec_flex_is_filled_before_the_open_flex():
    """Nested eligibility: W/T is inside W/R/T, so spending the loose slot
    first can strand the tight one empty. Fill order is not cosmetic."""
    from draftkit.lineup import optimal_lineup
    sh = starting_slots(["QB", "RB", "RB", "WR", "WR", "TE", "REC_FLEX",
                         "W/R/T", "K", "DEF", "BN"])
    assert sh.rec_flex == 1 and sh.flex == 1

    # Built so the WRONG order is detectable. After the dedicated slots fill,
    # exactly one WR/TE body is left (w3) and he is also the best remaining
    # flex body. Filling the open flex first takes him and strands the rec_flex
    # empty at nine starters; filling the rec_flex first seats him there and
    # the open flex still has r2, for the legal ten.
    def p(pid, pos, wk):
        return {"sleeper_id": pid, "name": f"{pos} {pid}", "pos": pos,
                "weekly": wk, "team": "SFO"}
    roster = [p("q1", "QB", 22), p("r1", "RB", 16), p("r2", "RB", 15),
              p("r3", "RB", 13), p("r4", "RB", 20), p("w1", "WR", 25),
              p("w2", "WR", 24), p("w3", "WR", 18), p("t1", "TE", 10),
              p("k1", "K", 8), p("d1", "DEF", 7)]
    got = {q["sleeper_id"] for q in optimal_lineup(roster, sh.slots,
                                                   flex_slots=sh.flex_slots)}
    assert len(got) == sh.n_starters == 10, "the rec_flex was stranded empty"
    assert {"w3", "r2"} <= got


def test_every_production_call_site_passes_flex_slots_by_name():
    """The lineup tests above call optimal_lineup with flex_slots= as a
    keyword and passed while production was broken: a mechanical edit across a
    dozen call sites had left the eligibility sets in the `flex` POSITIONAL,
    where they reached int() and raised three frames down on the first live
    run. Two guards, because the convention is the thing that has to hold.
    """
    import inspect

    from draftkit import briefs, lineup, playoffs
    from manager import lineup_opt, scout, trade_radar, waiver_brief

    for mod in (briefs, playoffs, lineup, lineup_opt, scout, trade_radar, waiver_brief):
        src = inspect.getsource(mod)
        assert 'ctx["slots"], ctx["flex_slots"]' not in src, (
            f"{mod.__name__}: flex_slots is sitting in the `flex` positional")
        assert ", flex, flex_slots)" not in src, (
            f"{mod.__name__}: forward flex_slots by name")

    # and the mistake is now named rather than surfacing as a TypeError about
    # tuples from inside int()
    with pytest.raises(TypeError, match="Eligibility sets go to `flex_slots`"):
        lineup.optimal_lineup(_roster(), starting_slots(OMNIBETA).slots,
                              starting_slots(OMNIBETA).flex_slots)


def test_a_ctx_shaped_call_drives_the_manager_lineup_path():
    """The call as production makes it, through the ctx keys the manager
    actually reads. No test covered this seam, which is how the positional
    bug reached a live run instead of a red suite."""
    from draftkit.lineup import optimal_lineup
    shape = starting_slots(OMNIBETA)
    ctx = {"slots": shape.slots, "flex": shape.flex, "flex_slots": shape.flex_slots}
    got = optimal_lineup(_roster(), ctx["slots"], flex_slots=ctx["flex_slots"])
    assert len(got) == shape.n_starters == 10


def test_the_flex_vocabulary_is_eligibility_not_a_name():
    """onboard puts W/T (a WR/TE slot) in FLEX_NAMES and W/R (a WR/RB slot) in
    REC_FLEX_NAMES. Reusing those buckets for a lineup would let a RB start in
    a receiver flex, so shape keeps its own exact table."""
    from draftkit.shape import FLEX_ELIGIBILITY
    assert FLEX_ELIGIBILITY["W/T"] == frozenset(("WR", "TE"))
    assert FLEX_ELIGIBILITY["W/R"] == frozenset(("RB", "WR"))
    assert FLEX_ELIGIBILITY["W/R/T"] == frozenset(("RB", "WR", "TE"))


def test_an_unknown_flex_kind_needs_no_new_field():
    """The generalisation this refactor bought: a WR/RB flex is a slot with an
    eligibility set, not a fourth counter, and n_starters counts it."""
    sh = starting_slots(["QB", "RB", "WR", "TE", "W/R", "K", "DEF", "BN"])
    assert sh.flex == 0 and sh.rec_flex == 0 and sh.superflex == 0
    assert len(sh.flex_slots) == 1 and sh.n_starters == 7
