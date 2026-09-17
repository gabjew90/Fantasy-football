"""The delivered text: short, plain, action-first, silent when there is
nothing to do (2026-09-16 review of the first production samples)."""

from datetime import datetime, timezone

import pytest

from manager import injuries, phone
from manager.store import Store

FORBIDDEN = ("—", "–", "…", " · ", "**", "⚠", "🔴", "🟡", "🟢")


def _clean(text: str):
    for glyph in FORBIDDEN:
        assert glyph not in text, f"{glyph!r} in delivered text: {text!r}"


# ------------------------------------------------------------------ lineup

def test_lineup_nothing_to_do_sends_nothing():
    subject, body, urgent = phone.lineup({}, {"swaps": [], "mode": "ceiling",
                                              "contingency": {"A": "B (RB, 9.0 pts)"}})
    assert subject is None and body == "" and urgent is False


def test_lineup_numbered_actions_plain_words():
    summary = {"swaps": ["Start Kyren Williams over Chase Brown (+2.3 pts)",
                         "Start Jake Ferguson over Hunter Henry (+0.8 pts)"],
               "mode": "ceiling",
               "contingency": {"Kyren Williams": "Chase Brown (RB, 12.1 pts)"},
               "first_lock": "Thu 5:15 PM (BUF)"}
    subject, body, urgent = phone.lineup({}, summary)
    assert subject == "Start Kyren Williams over Chase Brown, and 1 more"
    assert urgent is True, "a +2.3 swap is past the coin-flip line"
    assert body.splitlines()[0] == "Set your lineup:"
    assert "1. Start Kyren Williams over Chase Brown (+2.3 pts)" in body
    assert "2. Start Jake Ferguson" in body
    assert "underdog" in body
    assert "Kyren Williams out: start Chase Brown" in body
    assert body.rstrip().endswith("First lock Thu 5:15 PM (BUF).")
    _clean(body)


def test_lineup_neutral_mode_says_nothing_about_mode():
    _s, body, _u = phone.lineup({}, {"swaps": ["Start A over B (+1.0 pts)"], "mode": "neutral"})
    assert "underdog" not in body and "favorite" not in body


# ----------------------------------------------------------------- waivers

def _adds():
    return [{"name": "Tyler Allgeier", "pos": "RB", "team": "ATL", "cls": "DEPTH",
             "move": "Drop Cam Akers", "drop": "Cam Akers",
             "why": "Robinson is questionable, Allgeier gets the work", "fair": 7, "agg": 12},
            {"name": "Jalen Coker", "pos": "WR", "team": "CAR", "cls": "UPSIDE",
             "move": "Drop Elijah Moore", "drop": "Elijah Moore", "why": "", "fair": 3, "agg": 5}]


def test_waivers_faab_claim_drop_bid_and_deadline():
    subject, body, urgent = phone.waivers(
        {"faab": True}, {"adds": _adds(), "budget": 88, "priority": 4, "teams": 12})
    assert subject == "Claim Tyler Allgeier, drop Cam Akers"
    assert "1. Claim Tyler Allgeier (RB, ATL). Drop Cam Akers. Bid $7 to $12." in body
    assert "   Why: Robinson is questionable, Allgeier gets the work." in body
    assert "2. Claim Jalen Coker (WR, CAR). Drop Elijah Moore. Bid $3 to $5." in body
    assert "Bids lock 7:00 PM PT tonight." in body
    assert "FAAB left: $88." in body
    assert urgent is False
    _clean(body)


def test_waivers_rolling_list_uses_priority_not_bids():
    _s, body, _u = phone.waivers(
        {"faab": False}, {"adds": _adds()[:1], "priority": 3, "teams": 10})
    assert "Bid $" not in body
    assert "Your waiver priority: 3 of 10." in body
    assert body.count("priority") == 1
    assert "Claims process overnight tonight" in body
    assert "FAAB" not in body


def test_waivers_ir_moves_come_first_and_can_stand_alone():
    subject, body, _u = phone.waivers(
        {"faab": True}, {"adds": [], "ir": ["Move A.J. Brown to IR: he is Out, the slot is open."]})
    assert subject == "Move A.J. Brown to IR"
    assert body.startswith("Roster first:\n- Move A.J. Brown to IR")


def test_waivers_nothing_worth_claiming_sends_nothing():
    assert phone.waivers({"faab": True}, {"adds": [], "ir": []})[0] is None


def test_waivers_caps_at_three_claims():
    adds = [dict(_adds()[0], name=f"P{i}") for i in range(6)]
    _s, body, _u = phone.waivers({"faab": True}, {"adds": adds})
    assert "3. Claim P2" in body and "4. Claim" not in body


# ------------------------------------------------------------------- plan

def test_plan_is_deadlines_only():
    jobs = [{"kind": "slate_check", "kickoff": "2026-09-17T17:15:00-07:00", "teams": ["BUF", "MIA"]},
            {"kind": "slate_check", "kickoff": "2026-09-20T10:00:00-07:00", "teams": ["DAL"]},
            {"kind": "waivers", "at": "2026-09-15T18:00:00-07:00"},
            {"kind": "lineup", "at": "2026-09-20T06:00:00-07:00"}]
    ctx = {"league": {"settings": {"trade_deadline": 11}}}
    subject, body = phone.plan(3, jobs, ctx, faab=True)
    assert subject == "Week 3: first lock Thu 5:15 PM (BUF, MIA)"
    assert "Waiver bids: Tuesday 7:00 PM PT." in body
    assert "Thu 5:15 PM: BUF, MIA lock." in body
    assert "Sun 10:00 AM: DAL lock." in body
    assert "Trade deadline: after week 11 games." in body
    # the check schedule itself is not the user's business
    assert "lineup" not in body.lower() and "check" not in body.lower()
    _clean(body)


def test_trade_deadline_from_yahoo_date_and_sleeper_none():
    assert phone.trade_deadline_text({"league": {"trade_deadline": "2026-11-28"}}) == "Sat Nov 28"
    # Yahoo's settings carry the date too (the live Keefamania crash)
    assert phone.trade_deadline_text({"league": {"settings": {"trade_deadline": "2026-11-28"}}}) == "Sat Nov 28"
    assert phone.trade_deadline_text({"league": {"settings": {"trade_deadline": 99}}}) is None
    assert phone.trade_deadline_text({"trade_deadline_text": "week 11"}) == "week 11"


# --------------------------------------------------------------- injuries

def test_injury_change_for_a_starter_going_out_is_act_now_with_replacement():
    changes = [{"pid": "1", "name": "A.J. Brown", "pos": "WR", "old": "Questionable",
                "new": "Out", "note": "Hamstring"}]
    subject, body, urgent = phone.injury_changes(
        changes, {"A.J. Brown": "Jalen Coker (WR, 9.1 pts)"}, {"1"})
    assert urgent is True
    assert subject == "A.J. Brown (WR): Out (Hamstring)"
    assert body == "A.J. Brown (WR): Out (Hamstring). Start Jalen Coker instead, your best bench WR at 9.1 projected."
    _clean(body)


def test_injury_change_on_the_bench_is_informational():
    changes = [{"pid": "2", "name": "Cam Akers", "pos": "RB", "old": "", "new": "Questionable", "note": ""}]
    subject, body, urgent = phone.injury_changes(changes, {}, {"1"})
    assert urgent is False
    assert body == "Cam Akers (RB): Questionable"


def test_injury_starter_questionable_names_the_fallback_without_urgency():
    changes = [{"pid": "1", "name": "Kyren Williams", "pos": "RB", "old": "", "new": "Questionable", "note": "Ankle"}]
    _s, body, urgent = phone.injury_changes(changes, {"Kyren Williams": "Chase Brown (RB, 12.1 pts)"}, {"1"})
    assert urgent is False
    assert body.endswith("If he sits, start Chase Brown.")


def test_sweep_changes_structured_once_with_note(tmp_path):
    store = Store(tmp_path / "kv.json")
    players = {"1": {"injury_body_part": "Hamstring"}}
    ctx = {"my_rid": 1, "players": players,
           "roster_players": {1: [{"sleeper_id": "1", "name": "A.J. Brown", "pos": "WR", "status": ""}]}}
    assert injuries.sweep_changes(ctx, store) == []
    ctx["roster_players"][1][0]["status"] = "Out"
    rows = injuries.sweep_changes(ctx, store)
    assert rows == [{"pid": "1", "name": "A.J. Brown", "pos": "WR", "old": "", "new": "Out", "note": "Hamstring"}]
    # same status again: nothing, and the snapshot has advanced
    assert injuries.sweep_changes(ctx, store) == []


# ------------------------------------------------------------------ ledger

def test_ledger_nothing_graded_sends_nothing():
    assert phone.ledger(2, {"graded": 0})[0] is None


def test_ledger_terse():
    grades = {"graded": 3, "win_prob": 0.62,
              "lineup": {"chosen_pts": 121.4, "efficiency": 0.93, "left_on_bench": 9.1},
              "scout": {"graded": True, "won": 1, "actual_margin": 12.5},
              "waiver_add": [{"delta": 4.0}, {"delta": -2.0}]}
    subject, body = phone.ledger(2, grades)
    assert subject == "Week 2 graded"
    assert "Lineup: 121.4 points, 93% of the best you could have started (9.1 left on the bench)." in body
    assert "Result: won by 12.5; the model had you winning." in body
    assert "Waiver calls: 1 of 2 recommended adds outscored the drop that week." in body
    _clean(body)


def test_lineup_small_edge_is_a_brief_and_capitalised():
    subject, body, urgent = phone.lineup({}, {"swaps": ["start Harold Fannin over Devaughn Vele (+0.6 pts)"]})
    assert subject == "Start Harold Fannin over Devaughn Vele"
    assert urgent is False


def test_plain_why_turns_usage_shorthand_into_words():
    assert (phone.plain_why("target share 21%; targets 6; carries 0; rec yds 38; snaps 82%", "WR")
            == "Last week: 21% of targets and 82% of snaps")
    assert (phone.plain_why("target share 7%; targets 2; carries 7; rec yds 5; snaps 41%", "RB")
            == "Last week: 7 carries and 7% of targets")
    assert (phone.plain_why("target share 0%; targets 0; carries 3; rec yds 0; snaps 100%", "QB")
            == "Last week: 100% of snaps and 3 carries")
    assert (phone.plain_why("target share 14% -> 21%; snaps 70% -> 82%", "WR")
            == "Last week: 21% of targets, up from 14% and 82% of snaps, up from 70%")
    assert phone.plain_why("inherits role: Tank Dell (IR) on HOU") == "Tank Dell is on IR, he inherits the role"
    assert phone.plain_why("2,410 Sleeper adds/24h") == "2,410 managers added him in the last day"


def test_waivers_same_drop_twice_becomes_a_fallback_and_no_dashes():
    adds = [dict(_adds()[0], drop="Devaughn Vele", move="Drop Devaughn Vele"),
            dict(_adds()[1], drop="Devaughn Vele", move="Drop Devaughn Vele"),
            dict(_adds()[1], name="DeeJay Dallas", drop=None,
                 move="No clean drop — only claim if you value him over your worst bench spot")]
    _s, body, _u = phone.waivers({"faab": False}, {"adds": adds, "priority": 9, "teams": 10})
    assert "1. Claim Tyler Allgeier (RB, ATL). Drop Devaughn Vele." in body
    assert "2. Claim Jalen Coker (WR, CAR). Drop Devaughn Vele if claim 1 misses." in body
    assert "3. Claim DeeJay Dallas (WR, CAR). No obvious drop, only claim him if he beats your worst bench player." in body
    _clean(body)


# --------------------------------------------------------------- rationale

def test_lineup_swap_carries_a_why_line():
    facts = {"start Harold Fannin over Devaughn Vele (+0.6 pts)": {
        "in": "Harold Fannin", "in_pts": 10.2, "in_vegas": None, "in_status": "",
        "out": "Devaughn Vele", "out_pts": 9.6, "out_vegas": "implied 29 (+5%)", "out_status": "",
        "spread": 44.0}}
    _s, body, _u = phone.lineup({}, {"swaps": list(facts), "facts": facts, "mode": "neutral"})
    assert body.splitlines()[1] == "1. Start Harold Fannin over Devaughn Vele (+0.6 pts)"
    assert body.splitlines()[2] == ("   Why: Fannin projects 10.2, Vele 9.6. Vele's team is in the higher scoring game, "
                                    "29 points implied, but Fannin still projects higher. The sources disagree by 44 on "
                                    "these two, so this is close to a coin flip.")
    _clean(body)


def test_swap_why_names_the_deciding_fact():
    base = {"in": "Kyren Williams", "in_pts": 14.0, "out": "Chase Brown", "out_pts": 12.1,
            "in_vegas": None, "out_vegas": None, "in_status": "", "out_status": "", "spread": 3.0}
    assert phone.swap_why(base) == "Williams projects 14, Brown 12.1"
    assert phone.swap_why(dict(base, out_status="Questionable")) == "Williams projects 14, Brown 12.1. Brown is Questionable"
    assert phone.swap_why(dict(base, in_vegas="implied 28 (+5%)")).endswith("Williams's team is in a high scoring game, 28 points implied")
    assert phone.swap_why(dict(base, in_vegas="implied 16 (-5%)")).endswith("Williams's game is a low scoring one, 16 points implied, and he still projects higher")
    assert phone.swap_why(dict(base, out_vegas="implied 16 (-5%)")).endswith("Brown's game is a low scoring one, 16 points implied")
    assert phone.swap_why(dict(base, spread=30.0), "ceiling").endswith("close to a coin flip and the higher ceiling wins it")
    assert phone.swap_why({"in": "Bo Nix", "in_pts": 18.0, "out": None, "out_pts": None}) == "Nix projects 18 and the slot was empty"


def test_add_why_gives_worth_and_bid_logic():
    a = {"name": "Wan'Dale Robinson", "pos": "WR", "cls": "breakout", "drop": "Kaelon Black",
         "why": "target share 21%; targets 6; carries 0; rec yds 38; snaps 82%",
         "ros": 128.4, "drop_ros": 40.2, "ecr": {"pos": "WR", "ecr": 62, "best": 60},
         "fair": 14, "agg": 32, "rivals": [], "contingent": False}
    assert phone.add_why(a, faab=True) == [
        "Why: Last week: 21% of targets and 82% of snaps. Robinson projects 128 points the rest of the way, Black 40. "
        "Experts have him WR62, best case WR60. Starter upside.",
        "Bid: no rival is forced to bid here, so the low end should land him."]
    assert phone.add_why(dict(a, rivals=[80, 55]), faab=True)[1] ==         "Bid: rivals with a need at WR hold $80 and $55, so lean to the high end."
    assert phone.add_why(dict(a, contingent=True, cls="league_winner"), faab=True)[1] ==         "Bid: he backs up a downed starter, so pay the high end."
    rolling = phone.add_why(dict(a, contingent=True), faab=False)
    assert len(rolling) == 2 and rolling[1].startswith("He backs up a downed starter")
    assert len(phone.add_why(dict(a, ecr=None, why="", ros=None), faab=False)) == 1


def test_surname_keeps_suffix():
    assert phone._last("Marvin Harrison Jr.") == "Harrison Jr."
    assert phone._last("Bijan Robinson") == "Robinson"
