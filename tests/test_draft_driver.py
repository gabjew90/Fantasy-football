"""The in-page draft driver's guardrails must match draftkit/tracker.py.

The driver (scripts/draft_driver.js) is the only sanctioned copy of
`_pos_allowed`, because the Yahoo draft loop cannot afford a Python
round-trip per pick. A copy that silently diverges is exactly the failure
this repo already hit once in the two-pick planner, so it gets a test.

We run the JS through node when available. No node -> skip, never a false
green.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path

import pytest

DRIVER = Path(__file__).resolve().parents[1] / "scripts" / "draft_driver.js"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None, reason="node not installed")


def run_js(snippet: str):
    """Load the driver with a DOM stub and evaluate a snippet."""
    harness = textwrap.dedent(
        """
        // minimal DOM so the IIFE can define itself; the pure functions under
        // test never touch it.
        global.document = {
          title: '',
          body: { innerText: '' },
          querySelector: () => null,
          querySelectorAll: () => [],
        };
        global.window = global;
        """
    )
    code = harness + DRIVER.read_text(encoding="utf-8") + "\n" + snippet
    # Via a temp file, not `node -e`: the driver outgrew Windows' command-line
    # length limit and CreateProcess started failing with WinError 206.
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "run.mjs"
        script.write_text(code, encoding="utf-8")
        out = subprocess.run(
            [NODE, str(script)], capture_output=True, text=True, timeout=30
        )
    if out.returncode != 0:
        raise AssertionError(out.stderr.strip() or out.stdout.strip())
    return json.loads(out.stdout.strip())


BOARD = "\n".join(
    [
        "Christian McCaffrey|RB|SFO|122.8|1|",
        "Trey McBride|TE|ARI|69.3||",
        "Brock Bowers|TE|LVR|68.5||",
        "Josh Allen|QB|BUF|39.7||",
        "Jalen Hurts|QB|PHI|27.0||",
        "Brock Purdy|QB|SFO|19.0||",
        "Houston Texans|DEF|HOU|18.0||",
        "Brandon Aubrey|K|DAL|13.5||",
        "Jaylen Warren|RB|PIT|9.3|1|",
        "Deep Sleeper|WR|FA|-30.0||",
    ]
)


def rank_with(roster_text: str):
    """Rank against a stubbed YOUR TEAM panel."""
    return run_js(
        f"""
        DK.loadCompact({json.dumps(BOARD)});
        document.body.innerText = {json.dumps(roster_text)};
        console.log(JSON.stringify(DK.rank()));
        """
    )


def panel(players: list[str], of: int = 15) -> str:
    """Build a YOUR TEAM panel like Yahoo renders it."""
    body = " ".join(players)
    return f"YOUR TEAM ({len(players)}/{of}) {body}"


def test_never_a_third_qb():
    """The exact mistake from the 2026-08-31 mock: two QBs rostered, a third
    still queued because ranking ignored the guardrail."""
    r = rank_with(panel([
        "J. Hurts QB Phi Bye 10",
        "T. Lawrence QB Jax Bye 7",
        "P. Nacua WR LAR Bye 11",
    ]))
    names = [c["n"] for c in r["top"]]
    assert "Brock Purdy" not in names, f"3rd QB offered: {names}"


def test_no_qb2_before_round_gate():
    """qb2_earliest_round is 10 for keefamania; a 2nd QB in round 4 is out."""
    r = rank_with(panel([
        "J. Hurts QB Phi Bye 10",
        "P. Nacua WR LAR Bye 11",
        "C. McCaffrey RB SF Bye 8",
    ]))
    assert r["round"] == 4
    assert "Josh Allen" not in [c["n"] for c in r["top"]]


def test_k_and_def_locked_until_last_two_picks():
    r = rank_with(panel(["P. Nacua WR LAR Bye 11"]))
    names = [c["n"] for c in r["top"]]
    assert "Brandon Aubrey" not in names
    assert "Houston Texans" not in names


def test_k_and_def_open_in_last_two_picks():
    """13 rostered -> 2 picks left -> K/DEF become legal and, being the only
    unfilled starters, must rank first."""
    letters = "ABCDEFGHIJKLM"
    roster = [f"{c}. Filler{c} WR LAR Bye 11" for c in letters]
    r = rank_with(panel(roster))
    assert r["picksLeft"] == 2, r["counts"]
    names = [c["n"] for c in r["top"][:2]]
    assert "Brandon Aubrey" in names and "Houston Texans" in names, names


def test_last_pick_is_reserved_for_an_unfilled_kicker():
    """One pick left, K still open: nothing but a kicker may be offered, even
    though McCaffrey's VORP dwarfs Aubrey's. Otherwise the draft ends with an
    empty mandatory slot."""
    letters = "ABCDEFGHIJKLMN"
    roster = [f"{c}. Filler{c} WR LAR Bye 11" for c in letters]
    roster.append("H. Texans DEF Hou Bye 8")
    r = rank_with(panel(roster[:14]))
    assert r["picksLeft"] == 1
    assert {c["p"] for c in r["top"]} <= {"K", "DEF"}, r["top"][:4]


def test_second_te_must_beat_the_best_flex_alternative():
    """A 2nd TE can only start in FLEX, competing with the RB/WR who would
    otherwise hold that slot. Mock 4 took McBride AND Bowers in three rounds
    and entered round 4 with no running back, because "top-6 TE" alone was
    too easy a gate.

    With McCaffrey (122.8) on the board, Bowers (68.5) must NOT be offered.
    """
    r = rank_with(panel([
        "T. McBride TE Ari Bye 14",
        "P. Nacua WR LAR Bye 11",
    ]))
    assert "Brock Bowers" not in [c["n"] for c in r["top"]], \
        "TE2 offered while a far better flex option was available"


def test_second_te_is_allowed_when_it_clearly_beats_the_flex_field():
    """The gate is a margin, not a ban: strip the strong RB/WR out and the
    elite TE2 becomes the right FLEX play again."""
    thin = "\n".join([
        "Trey McBride|TE|ARI|69.3|||26.7",
        "Brock Bowers|TE|LVR|68.5|||21.2",
        "Jaylen Warren|RB|PIT|9.3|1||77.0",
        "Courtland Sutton|WR|DEN|-1.7|||105.2",
    ])
    r = run_js(
        f"""
        DK.loadCompact({json.dumps(thin)});
        document.body.innerText = {json.dumps(panel([
            "T. McBride TE Ari Bye 14",
            "P. Nacua WR LAR Bye 11",
        ]))};
        console.log(JSON.stringify(DK.rank()));
        """
    )
    assert "Brock Bowers" in [c["n"] for c in r["top"]], \
        "elite TE2 blocked even though the flex field was weak"


def test_need_weighting_beats_similar_vorp():
    """A player filling an open starter slot outranks a comparable one who
    fills nothing.

    Deliberately NOT asserted: that an open slot beats a far better player.
    With 9 picks left and deep QB supply, taking elite TE Bowers (68.5) over
    QB Allen (39.7) is correct, and qb2_earliest_round=10 says QB is not
    urgent. Need-weighting is a tiebreak, not an override -- the override
    case is must-fill, covered by the K/DEF test.
    """
    roster = [
        "C. McCaffrey RB SF Bye 8",
        "J. Warren RB Pit Bye 9",
        "P. Nacua WR LAR Bye 11",
        "A. Brown WR NE Bye 11",
        "T. McBride TE Ari Bye 14",
        "B. Bowers TE LV Bye 8",
        "J. Waddle WR Den Bye 10",
    ]
    r = rank_with(panel(roster))
    assert r["need"]["QB"] == 1
    # both TEs rostered -> QB is the only open starter among live candidates
    assert r["top"][0]["p"] == "QB", r["top"][:3]


def test_rostered_players_are_never_reoffered():
    r = rank_with(panel([
        "C. McCaffrey RB SF Bye 8",
        "T. McBride TE Ari Bye 14",
    ]))
    names = [c["n"] for c in r["top"]]
    assert "Christian McCaffrey" not in names
    assert "Trey McBride" not in names


def test_a_dead_ui_is_never_read_as_players_being_drafted():
    """Mock 2 regression. The driver searched while the right panel was on the
    Queue tab, so no player row could ever match. It read every miss as
    "drafted" and marked 36 elite players gone, wrecking the board.

    A miss only means "gone" when the table is provably rendering players.
    """
    r = run_js(
        """
        console.log(JSON.stringify({
          liveMiss:  DK.classifyMiss(false, true),
          deadMiss:  DK.classifyMiss(false, false),
          found:     DK.classifyMiss(true,  true),
        }));
        """
    )
    assert r["liveMiss"] == "gone"          # table up, player absent -> drafted
    assert r["deadMiss"] == "uinotready"    # table down -> conclude NOTHING
    assert r["found"] == "found"


def test_a_queued_player_is_never_re_starred():
    """The star is a TOGGLE: clicking it again removes the player from the
    queue. Mock 2 re-starred the 5th entry every cycle, flipping them in and
    out, so the queue never held more than four."""
    r = run_js(
        """
        DK.reset();
        DK._markStarred('Jonathan Taylor|RB');
        console.log(JSON.stringify({
          already: DK._isStarred('Jonathan Taylor|RB'),
          other:   DK._isStarred('Bijan Robinson|RB'),
          cleared: (DK.reset(), DK._starred().length),
        }));
        """
    )
    assert r["already"] is True
    assert r["other"] is False
    assert r["cleared"] == 0


def test_row_must_match_team_not_just_name_and_position():
    """Mock 2 queued "J. Taylor NA RB Jax" for Jonathan Taylor of INDIANAPOLIS.
    findRow's comment claimed it checked team; the code only checked name and
    position."""
    r = run_js(
        """
        DK.loadCompact('Jonathan Taylor|RB|IND|77.8||' + '|3.0');
        console.log(JSON.stringify({
          right: DK.rowMatches({k:'j taylor', p:'RB', t:'IND', a:3.0},
                               'J. Taylor RB Ind Bye 7 ADP: 3.2'),
          wrong: DK.rowMatches({k:'j taylor', p:'RB', t:'IND', a:3.0},
                               'J. Taylor NA RB Jax Bye 7 ADP: -'),
        }));
        """
    )
    assert r["right"] is True
    assert r["wrong"] is False, "a Jacksonville back matched an Indianapolis one"


def test_same_name_same_team_collision_is_split_by_adp():
    """Bijan Robinson and Brian Robinson Jr. are both ATL RBs keyed
    "b robinson". Only ADP separates them, and getting it wrong swaps a
    +91.8 VORP player for a -72.4 one."""
    r = run_js(
        """
        console.log(JSON.stringify({
          bijanOnBijanRow: DK.rowMatches({k:'b robinson',p:'RB',t:'ATL',a:2.1},
                              'B. Robinson RB Atl Bye 11 ADP: 3.0'),
          bijanOnBrianRow: DK.rowMatches({k:'b robinson',p:'RB',t:'ATL',a:2.1},
                              'B. Robinson RB Atl Bye 11 ADP: 119.6'),
          brianOnBrianRow: DK.rowMatches({k:'b robinson',p:'RB',t:'ATL',a:118.1},
                              'B. Robinson RB Atl Bye 11 ADP: 119.6'),
        }));
        """
    )
    assert r["bijanOnBijanRow"] is True
    assert r["bijanOnBrianRow"] is False, "queued the wrong Robinson"
    assert r["brianOnBrianRow"] is True


def test_team_aliases_normalise_across_yahoo_and_board_spellings():
    r = run_js(
        """
        console.log(JSON.stringify({
          sfo: DK.normTeam('SFO') === DK.normTeam('SF'),
          jac: DK.normTeam('JAC') === DK.normTeam('Jax'),
          gbp: DK.normTeam('GBP') === DK.normTeam('GB'),
          nep: DK.normTeam('NEP') === DK.normTeam('NE'),
          diff: DK.normTeam('LAC') === DK.normTeam('LAR'),
        }));
        """
    )
    assert r["sfo"] and r["jac"] and r["gbp"] and r["nep"]
    assert r["diff"] is False, "LAC and LAR must stay distinct"


def test_a_pick_is_only_success_if_the_roster_actually_grew():
    """Mock 3 logged 'drafted Bijan Robinson' twice while the roster showed
    neither. The click path silently no-opped and the QUEUE was quietly making
    every real pick, so the log hid the failure being hunted."""
    r = run_js(
        """
        console.log(JSON.stringify({
          grew:    DK.pickLanded({have:2,of:15}, {have:3,of:15}),
          same:    DK.pickLanded({have:2,of:15}, {have:2,of:15}),
          missing: DK.pickLanded({have:2,of:15}, null),
          noBase:  DK.pickLanded(null, {have:3,of:15}),
        }));
        """
    )
    assert r["grew"] is True
    assert r["same"] is False, "a no-op click reported as a successful pick"
    assert r["missing"] is False and r["noBase"] is False


def test_autopick_banner_is_detected():
    """Once armed, Yahoo drafts the instant the turn opens. Racing it with
    clicks only burns the clock -- and an expired clock is what arms it."""
    r = run_js(
        """
        const on = 'You have been put into autopick mode due to inactivity.';
        document.body.innerText = on;
        const armed = DK.autopickArmed();
        document.body.innerText = 'YOUR TEAM (3/15)';
        console.log(JSON.stringify({armed, clear: DK.autopickArmed()}));
        """
    )
    assert r["armed"] is True
    assert r["clear"] is False


def test_a_queued_player_who_becomes_illegal_is_no_longer_ranked():
    """Mock 3 queued Mahomes AND Hurts in round 5. Both were legal at QB
    count 0, but the instant the first landed the second was an illegal QB2
    that autopick would take. rank() must stop offering him, which is what
    pruneQueue keys off."""
    before = rank_with(panel(["P. Nacua WR LAR Bye 11"]))
    assert "Jalen Hurts" in [c["n"] for c in before["top"]], "QB1 should be legal"

    after = rank_with(panel([
        "P. Nacua WR LAR Bye 11",
        "J. Allen QB Buf Bye 7",
    ]))
    assert after["round"] == 3
    assert "Jalen Hurts" not in [c["n"] for c in after["top"]], \
        "a second QB stayed rankable before qb2_earliest_round"


def test_starred_memo_releases_players_taken_by_someone_else():
    """Mock 3's queue drained 5 -> 2 -> 1 and then Yahoo's own fallback list
    took over and handed us a THIRD tight end.

    Cause: the "already starred" memo (which stops us toggling a player back
    out) never released entries. A player who left the queue without joining
    our roster was drafted by a rival, but stayed memoised, so syncQueue
    skipped them forever and could not refill. The guardrail violation came
    from starvation, not from bad ranking.
    """
    r = run_js(
        f"""
        DK.loadCompact({json.dumps(BOARD)});
        DK.reset();
        DK._markStarred('Josh Allen|QB');       // still queued
        DK._markStarred('Brock Bowers|TE');     // rival took him
        DK._markStarred('Trey McBride|TE');     // we drafted him
        const dropped = DK.reconcileStarredWith(
          ['j allen|QB'],        // what the queue still shows
          ['t mcbride|TE']       // what our roster holds
        );
        console.log(JSON.stringify({{
          dropped,
          keptAllen:   DK._isStarred('Josh Allen|QB'),
          keptMcBride: DK._isStarred('Trey McBride|TE'),
          freedBowers: !DK._isStarred('Brock Bowers|TE'),
        }}));
        """
    )
    assert r["keptAllen"] is True, "a still-queued player must stay memoised"
    assert r["keptMcBride"] is True, "a rostered player must stay memoised"
    assert r["freedBowers"] is True, "a rival's pick must free the queue slot"
    assert r["dropped"] == ["Brock Bowers|TE"]


def test_queue_rows_parse_with_the_on_clock_draft_prefix():
    """Mock 4, found by screenshotting the screen while on the clock: the
    moment it is your turn Yahoo prefixes every queue row with its own
    "Draft" button. The anchored regex then matched nothing and the driver
    reported an EMPTY queue while five players sat plainly in it -- so it
    believed it had nothing to fall back on at the one moment that counts.
    """
    r = run_js(
        """
        console.log(JSON.stringify({
          plain:  DK.parseQueueRow('T. McBride TE Ari Bye 14 ADP: 26.5'),
          onClock:DK.parseQueueRow('Draft T. McBride TE Ari Bye 14 ADP: 26.5'),
          status: DK.parseQueueRow('Draft W. Robinson Q WR Ten Bye 9 ADP: 130.6'),
          junk:   DK.parseQueueRow('Autodraft will pick from queue'),
        }));
        """
    )
    assert r["plain"] == "t mcbride|TE"
    assert r["onClock"] == "t mcbride|TE", "on-clock rows must still parse"
    assert r["status"] == "w robinson|WR"
    assert r["junk"] is None


def test_queue_plan_does_not_stack_one_position():
    """Mock 4 queued FIVE quarterbacks in round 6. Only one was legally
    draftable (QB2 is gated until round 10), so the moment one landed the
    other four were pruned and the queue collapsed -- starvation by a new
    route.

    The queue is a PLAN for the next N picks, so each candidate must be
    checked against a roster already holding everything queued ahead of it.
    """
    qb_heavy = "\n".join([
        "Josh Allen|QB|BUF|39.7|||20.1",
        "Jalen Hurts|QB|PHI|27.0|||56.4",
        "Brock Purdy|QB|SFO|19.0|||98.3",
        "Bo Nix|QB|DEN|14.2|||98.8",
        "Jared Goff|QB|DET|8.1|||141.6",
        "Jaylen Warren|RB|PIT|9.3|1||77.0",
        "Courtland Sutton|WR|DEN|-1.7|||105.2",
    ])
    r = run_js(
        f"""
        DK.loadCompact({json.dumps(qb_heavy)});
        document.body.innerText = {json.dumps(panel([
            "R. Rice WR KC Bye 5",
            "D. Adams WR LAR Bye 11",
            "J. Williams RB Dal Bye 14",
            "T. McBride TE Ari Bye 14",
            "B. Bowers TE LV Bye 13",
        ]))};
        console.log(JSON.stringify({{plan: DK.planQueue(null, null, 6)}}));
        """
    )
    plan = r["plan"]
    qbs = [p for p in plan if p.endswith("|QB")]
    assert len(qbs) <= 1, f"queue stacked {len(qbs)} QBs: {plan}"
    assert any(p.endswith("|RB") or p.endswith("|WR") for p in plan), \
        f"queue held no runnable/receiving option: {plan}"


def test_availability_is_not_scraped_from_page_text():
    """Regression: an earlier driver regexed the whole page for drafted names,
    which swept in the UNDRAFTED player table and marked everyone gone.
    A page listing available players must not shrink the candidate set."""
    r = run_js(
        f"""
        DK.loadCompact({json.dumps(BOARD)});
        document.body.innerText = {json.dumps(
            panel(["P. Nacua WR LAR Bye 11"])
            + " Brock Bowers TE LVR Bye 8 Josh Allen QB Buf Bye 7"
        )};
        console.log(JSON.stringify(DK.rank()));
        """
    )
    names = [c["n"] for c in r["top"]]
    assert "Brock Bowers" in names, names
