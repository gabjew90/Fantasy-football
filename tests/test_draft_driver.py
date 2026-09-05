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


def plan_rows(board: str) -> list[dict]:
    """A compact board pasted back as an engine plan (the local ranker is
    gone; rank() only ever filters a plan)."""
    out = []
    for line in board.splitlines():
        f = line.split("|")
        if len(f) < 4 or not f[0]:
            continue
        out.append({"n": f[0], "p": f[1], "t": f[2], "v": float(f[3] or 0), "why": "w"})
    return out


def rank_with(roster_text: str, board: str = None):
    """Rank the board-as-plan against a stubbed YOUR TEAM panel."""
    board = board or BOARD
    return run_js(
        f"""
        DK.loadCompact({json.dumps(board)});
        DK.loadPlan({json.dumps({"plan": plan_rows(board), "needs": {}, "current_pick": 1})});
        document.body.innerText = {json.dumps(roster_text)};
        console.log(JSON.stringify(DK.rank()));
        """
    )


def panel(players: list[str], of: int = 15) -> str:
    """Build a YOUR TEAM panel like Yahoo renders it."""
    body = " ".join(players)
    return f"YOUR TEAM ({len(players)}/{of}) {body}"


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
        DK.loadPlan({json.dumps({"plan": plan_rows(qb_heavy), "needs": {}, "current_pick": 51})});
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


def test_survival_is_rank_based_not_adp_based():
    """A player who has already FALLEN must not be scored as if he were gone.

    Slot 5 of the bake-off: Jaxon Smith-Njigba was still on the board at pick
    16 with an ADP of 7.2. Absolute-ADP survival read that as near zero, so WR
    looked urgent and the driver spent the pick there -- losing Brock Bowers,
    whom the Python engine took instead while still getting JSN nine picks
    later. Rivals choose from the CURRENT pool, so survival keys on rank among
    the available, where being a faller is exactly what keeps you available.
    """
    r = run_js(
        """
        console.log(JSON.stringify({
          // rank 40 with only 9 picks to go: very likely to last
          deep:    DK.survivalProb(40, 9, 2),
          // rank 1 with 9 picks to go: very likely gone
          topOfBoard: DK.survivalProb(1, 9, 2),
          // right at the boundary
          atEdge:  DK.survivalProb(9, 9, 2),
        }));
        """
    )
    assert r["deep"] > r["atEdge"] > r["topOfBoard"], r
    # calibration keeps everything off the rails
    assert 0.01 <= r["topOfBoard"] < 0.5 < r["deep"] <= 0.99, r
    assert abs(r["atEdge"] - 0.5) < 0.02, r


def test_an_unreadable_adp_refuses_a_colliding_name():
    """Mock 7 drafted Brian Robinson Jr. (grade D) instead of Bijan.

    ADP is the ONLY thing separating them, and the guard was written
    `if (seen != null)` -- so when Yahoo printed no ADP on the row, the check
    silently skipped itself on exactly the row it existed for. For a colliding
    entry an unreadable ADP must REFUSE the row: losing one pick to a safe
    alternative beats handing the slot to a -72 VORP player.
    """
    both = "\n".join([
        "Bijan Robinson|RB|ATL|91.8|1||2.1",
        "Brian Robinson Jr.|RB|ATL|-72.4|1||118.1",
        "Puka Nacua|WR|LAR|69.0|||5.0",
    ])
    r = run_js(
        f"""
        const loaded = DK.loadCompact({json.dumps(both)});
        const bijan = {{k:'b robinson', p:'RB', t:'ATL', a:2.1, n:'Bijan Robinson'}};
        console.log(JSON.stringify({{
          loaded,
          noAdp:    DK.rowMatches(bijan, 'B. Robinson RB Atl Bye 11 ADP: -'),
          blankAdp: DK.rowMatches(bijan, 'B. Robinson RB Atl Bye 11'),
          rightAdp: DK.rowMatches(bijan, 'B. Robinson RB Atl Bye 11 ADP: 3.0'),
          wrongAdp: DK.rowMatches(bijan, 'B. Robinson RB Atl Bye 11 ADP: 119.6'),
          nonColliding: DK.rowMatches(
            {{k:'p nacua', p:'WR', t:'LAR', a:5.0, n:'Puka Nacua'}},
            'P. Nacua Q WR LAR Bye 11'),
        }}));
        """
    )
    assert "1 name collision" in r["loaded"], r["loaded"]
    assert r["noAdp"] is False, "guessed on a colliding name with no ADP"
    assert r["blankAdp"] is False, "guessed on a colliding name with no ADP"
    assert r["rightAdp"] is True
    assert r["wrongAdp"] is False
    # a non-colliding player must NOT be punished for a missing ADP
    assert r["nonColliding"] is True


def test_defense_identity_key_is_consistent_everywhere():
    """A defense is called three different things: the board says "Minnesota
    Vikings", the queue row says "Vikings", the table row says "Vikings DEF".

    Any function that keys defenses differently from other players silently
    stops matching them, which has now cost two separate bugs -- unmatchable
    in the player table (mock 6), then invisible in the queue so
    reconcileStarred marked them gone (mock 7). One key function, everywhere.
    """
    r = run_js(
        """
        console.log(JSON.stringify({
          fromBoard: DK.idKey('Minnesota Vikings', 'DEF'),
          fromQueue: DK.idKey('Vikings', 'DEF'),
          twoWord:   DK.idKey('New England Patriots', 'DEF'),
          fromRow:   DK.idKey('Patriots', 'DEF'),
          player:    DK.idKey('Jahmyr Gibbs', 'RB'),
        }));
        """
    )
    assert r["fromBoard"] == r["fromQueue"] == "vikings", r
    assert r["twoWord"] == r["fromRow"] == "patriots", r
    assert r["player"] == "j gibbs"


def test_team_defenses_can_be_matched_at_all():
    """Mock 6 finished with an EMPTY defense slot and two kickers.

    The board calls them "Houston Texans", which keys to "h texans", so the
    matcher looked for "H. Texans". Yahoo renders the row as plain "Texans
    DEF Bye 8" -- no initial -- so no defense could EVER match and the driver
    was structurally incapable of drafting one. Yahoo's fallback then padded
    the last picks with a second kicker and a third TE.
    """
    r = run_js(
        """
        console.log(JSON.stringify({
          texans:   DK.rowMatches({k:'h texans', p:'DEF', n:'Houston Texans'},
                                  'Texans DEF Bye 8 ADP: 93.4'),
          rams:     DK.rowMatches({k:'l rams', p:'DEF', n:'Los Angeles Rams'},
                                  'Rams DEF Bye 11 ADP: 111.0'),
          wrongTeam:DK.rowMatches({k:'h texans', p:'DEF', n:'Houston Texans'},
                                  'Broncos DEF Bye 10 ADP: 93.7'),
          notADef:  DK.rowMatches({k:'h texans', p:'DEF', n:'Houston Texans'},
                                  'T. Texans WR Hou Bye 8 ADP: 93.4'),
        }));
        """
    )
    assert r["texans"] is True, "a team defense still cannot be matched"
    assert r["rams"] is True
    assert r["wrongTeam"] is False
    assert r["notADef"] is False


def test_availability_is_not_scraped_from_page_text():
    """Regression: an earlier driver regexed the whole page for drafted names,
    which swept in the UNDRAFTED player table and marked everyone gone.
    A page listing available players must not shrink the candidate set."""
    r = run_js(
        f"""
        DK.loadCompact({json.dumps(BOARD)});
        DK.loadPlan({json.dumps({"plan": plan_rows(BOARD), "needs": {}, "current_pick": 1})});
        document.body.innerText = {json.dumps(
            panel(["P. Nacua WR LAR Bye 11"])
            + " Brock Bowers TE LVR Bye 8 Josh Allen QB Buf Bye 7"
        )};
        console.log(JSON.stringify(DK.rank()));
        """
    )
    names = [c["n"] for c in r["top"]]
    # rank() returns one candidate per position, so TE is represented by the
    # best TE. The point of the regression is that the TE slot is still
    # OFFERED at all -- the old page-scraping bug wiped the whole board.
    assert any(c["p"] == "TE" for c in r["top"]), names
    assert "Trey McBride" in names, names


def test_json_load_path_marks_name_collisions_too():
    """The JSON load() path never built the collision set, so the Bijan/Brian
    Robinson guard in rowMatches was silently OFF whenever the board came
    from the bridge rather than a compact paste (found 2026-09-01)."""
    out = run_js(
        """
        const r = DK.load([
          {n: 'Bijan Robinson', p: 'RB', t: 'ATL', v: 119.8, a: 2.1},
          {n: 'Brian Robinson Jr.', p: 'RB', t: 'ATL', v: -72.4, a: 118.1},
          {n: 'Puka Nacua', p: 'WR', t: 'LAR', v: 93.0, a: 3.0},
        ], {teams: 10});
        console.log(JSON.stringify({r}));
        """
    )
    assert out["r"] == "loaded 3 players, 1 name collision(s)"


def test_row_lookup_cap_covers_the_expanded_stats_layout():
    """Mock 11: rows in Yahoo's expanded stats layout run ~400 chars; a
    260-char cap on candidate elements meant no row with a control ever
    matched and every recommended player was recorded gone."""
    src = DRIVER.read_text(encoding="utf-8")
    import re
    m = re.search(r"const ROW_TEXT_CAP = (\d+);", src)
    assert m, "ROW_TEXT_CAP must exist"
    assert int(m.group(1)) >= 1000
    assert "if (x.length > 260) return false;" not in src


# ---------- mock 13 (2026-09-02): the banner is not the state ----------

def _fake_store(picks, my_team="6", away=False, current_pick=None):
    """A Redux-shaped store the driver's storeState() can read. picks are
    (pick_no, teamId, first, last, pos)."""
    by_id = {str(100 + i): {"fname": f, "lname": l, "primary_pos": pos, "team_abbr": "XX", "bye": 7}
             for i, (_n, _t, f, l, pos) in enumerate(picks)}
    order = [{"id": n, "teamId": str(t), "playerId": str(100 + i)}
             for i, (n, t, _f, _l, _p) in enumerate(picks)]
    made = len(picks)
    return {
        "draftPicks": {"order": order}, "players": {"byId": by_id},
        "draftOrder": {"currentPick": made if current_pick is None else current_pick - 1, "currentTeam": "1"},
        "league": {"managers": {"6": {"id": "6", "teamId": my_team, "away": away, "loggedin": True},
                                "3": {"id": "3", "teamId": "3", "away": True, "loggedin": True}}},
        "context": {"managerId": "6"}, "countdown": {"seconds": 30},
    }


def test_autopick_state_comes_from_the_store_not_the_banner():
    """Yahoo's "put into autopick mode" notice is an inert banner that stays
    up after autodraft is switched back off. Mock 13 acted on it: the driver
    clicked the Autodraft TOGGLE every cycle (off, on, off, on) for two
    rounds and stood itself down on every turn. With a store, its away flag
    is the state; the banner only matters when there is no store."""
    picks = [(1, 1, "Jahmyr", "Gibbs", "RB"), (6, 6, "Christian", "McCaffrey", "RB")]
    r = run_js(
        f"""
        const banner = 'You have been put into autopick mode due to inactivity.';
        document.body.innerText = banner;
        const noStore = DK.autopickArmed();
        DK._setStore({{ getState: () => ({json.dumps(_fake_store(picks, away=False))}) }});
        const storeOff = DK.autopickArmed();
        DK._setStore({{ getState: () => ({json.dumps(_fake_store(picks, away=True))}) }});
        const storeOn = DK.autopickArmed();
        console.log(JSON.stringify({{ noStore, storeOff, storeOn, banner: DK.bannerSaysArmed() }}));
        """
    )
    assert r["noStore"] is True, "without a store the banner is all we have"
    assert r["storeOff"] is False, "store says not away: the banner must not stand the driver down"
    assert r["storeOn"] is True
    assert r["banner"] is True


def test_a_pick_is_verified_against_the_store_not_the_roster_count():
    """At pick 135 of mock 13 Yahoo's autopick took Cam Little the instant
    the turn opened; our Seattle click was rejected, the roster count still
    grew by one, and the log said 'Seattle, verified'. The store knows which
    player landed at OUR pick number."""
    picks = [(1, 1, "Jahmyr", "Gibbs", "RB"), (6, 6, "Cam", "Little", "K")]
    r = run_js(
        f"""
        DK._setStore({{ getState: () => ({json.dumps(_fake_store(picks))}) }});
        const turn = DK.storeState().drafted.find(d => d.mine).pick_no;
        console.log(JSON.stringify({{
          turn,
          other:   DK.pickLandedStore({{ n: 'Seattle Seahawks', p: 'DEF' }}, turn),
          ours:    DK.pickLandedStore({{ n: 'Cam Little', p: 'K' }}, turn),
          pending: DK.pickLandedStore({{ n: 'Seattle Seahawks', p: 'DEF' }}, turn + 9),
        }}));
        """
    )
    assert r["other"] is False, "someone else's player at our pick must not verify our click"
    assert r["ours"] is True
    assert r["pending"] is None, "no pick recorded at that number yet: unknown, not false"
    # and without a store the answer is unknown, so the roster-count check still applies
    r2 = run_js("console.log(JSON.stringify({ x: DK.pickLandedStore({ n: 'Cam Little', p: 'K' }, 6) }));")
    assert r2["x"] is None


# ---------- client actions (2026-09-02): the no-DOM pick path ----------

def _store_with(picks, my_team="6", players=None, current_pick=None):
    """A Redux-shaped store: picks are (pick_no, teamId, playerId); players is
    {pid: (first, last, pos, team)}."""
    players = players or {}
    by_id = {pid: {"fname": f, "lname": l, "primary_pos": pos, "team_abbr": t, "bye": 7}
             for pid, (f, l, pos, t) in players.items()}
    order = [{"id": n, "teamId": str(t), "playerId": str(pid)} for n, t, pid in picks]
    made = len(picks)
    return {"draftPicks": {"order": order}, "players": {"byId": by_id},
            "draftOrder": {"currentPick": made if current_pick is None else current_pick - 1, "currentTeam": "6"},
            "league": {"managers": {"6": {"id": "6", "teamId": my_team, "away": False, "loggedin": True}}},
            "context": {"managerId": "6"}, "countdown": {"seconds": 30}}


PLAYERS = {"100": ("Christian", "McCaffrey", "RB", "SF"), "101": ("Bijan", "Robinson", "RB", "ATL"),
           "102": ("Brian", "Robinson", "RB", "ATL"), "103": ("Amon-Ra", "St. Brown", "WR", "DET"),
           "104": ("A.J.", "Brown", "WR", "PHI")}


def test_player_id_comes_from_the_store_and_refuses_ambiguity():
    r = run_js(
        f"""
        DK._setStore({{ getState: () => ({json.dumps(_store_with([], players=PLAYERS))}) }});
        console.log(JSON.stringify({{
          cmc: DK.playerIdFor({{ n: 'Christian McCaffrey', p: 'RB', t: 'SFO' }}),
          bijan: DK.playerIdFor({{ n: 'Bijan Robinson', p: 'RB', t: 'ATL' }}),
          brian: DK.playerIdFor({{ n: 'Brian Robinson Jr.', p: 'RB', t: 'ATL' }}),
          ajb: DK.playerIdFor({{ n: 'A.J. Brown', p: 'WR', t: 'PHI' }}),
          wrongpos: DK.playerIdFor({{ n: 'Christian McCaffrey', p: 'WR', t: 'SFO' }}),
          unknown: DK.playerIdFor({{ n: 'Nobody Here', p: 'RB', t: 'FA' }}),
        }}));
        """
    )
    assert r["cmc"] == "100"
    # the two Robinsons share initial, surname, position AND team: the store
    # keys are full names, so they resolve; the two Browns likewise
    assert r["bijan"] == "101" and r["brian"] == "102" and r["ajb"] == "104"
    assert r["wrongpos"] is None and r["unknown"] is None


def test_pick_via_action_reports_landed_only_when_the_store_records_our_pick():
    """makePick is called with the store's id; success is the store showing
    THAT player at OUR pick number. A different player there means autopick
    beat us ('notours'); silence means 'timeout' and the click path follows."""
    r = run_js(
        f"""
        const base = {json.dumps(_store_with([(5, 1, "101")], players=PLAYERS, current_pick=6))};
        let state = JSON.parse(JSON.stringify(base));
        DK._setStore({{ getState: () => state }});
        DK.loadCompact("Christian McCaffrey|RB|SFO|122.8|1|");
        const calls = [];
        // 1) the action lands: the store gains our pick with the same id
        DK._setActions({{ makePick: (pid) => {{ calls.push(pid);
          state.draftPicks.order.push({{ id: 6, teamId: "6", playerId: pid }}); state.draftOrder.currentPick = 6; }} }});
        const cand = {{ n: 'Christian McCaffrey', p: 'RB', t: 'SFO', v: 122.8 }};
        (async () => {{
          const landed = await DK.pickViaAction(cand, 1500);
          // 2) someone else's pick appears at our number
          state = JSON.parse(JSON.stringify(base)); DK._setStore({{ getState: () => state }});
          DK._setActions({{ makePick: (pid) => {{ state.draftPicks.order.push({{ id: 6, teamId: "6", playerId: "102" }}); state.draftOrder.currentPick = 6; }} }});
          const notours = await DK.pickViaAction(cand, 1500);
          // 3) nothing happens
          state = JSON.parse(JSON.stringify(base)); DK._setStore({{ getState: () => state }});
          DK._setActions({{ makePick: () => {{}} }});
          const timeout = await DK.pickViaAction(cand, 600);
          // 4) no actions at all / no id
          DK._setActions(null);
          const noaction = await DK.pickViaAction(cand, 300);
          DK._setActions({{ makePick: () => {{}} }});
          const noid = await DK.pickViaAction({{ n: 'Nobody Here', p: 'RB', t: 'FA' }}, 300);
          console.log(JSON.stringify({{ calls, landed, notours, timeout, noaction, noid }}));
        }})();
        """
    )
    assert r["calls"] == ["100"], "makePick must be called with the store's id for the candidate"
    assert r["landed"]["status"] == "landed" and r["landed"]["pid"] == "100"
    assert r["notours"]["status"] == "notours" and r["notours"]["landed"] == "Brian Robinson"
    assert r["timeout"]["status"] == "timeout"
    assert r["noaction"]["status"] == "noaction" and r["noid"]["status"] == "noid"


def test_keep_alive_prefers_set_away_status_and_verifies_it():
    r = run_js(
        f"""
        const s = {json.dumps(_store_with([], players=PLAYERS))};
        s.league.managers["6"].away = true;
        DK._setStore({{ getState: () => s }});
        // heartbeat parked far away so this test isolates the clear path
        DK.loadCompact("Christian McCaffrey|RB|SFO|122.8|1|", {{ heartbeatSec: 99999 }});
        const calls = [];
        DK._setActions({{ setAwayStatus: (v) => {{ calls.push(v); s.league.managers["6"].away = v; }} }});
        (async () => {{
          const out = await DK.keepAlive();
          console.log(JSON.stringify({{ calls, out, awayNow: s.league.managers["6"].away }}));
        }})();
        """
    )
    assert r["calls"] == [False]
    assert r["out"]["action"] is True and r["out"]["cleared"] is True
    assert r["awayNow"] is False


def test_keep_alive_sends_a_periodic_not_away_heartbeat():
    """Mock 20: on the action path nothing we do counts as user activity, so
    Yahoo's idle timer flagged us away at 16 minutes and autopicked pick 129
    the instant the turn opened -- before keepAlive could react. Clearing
    after the fact is too late, so keepAlive sends setAwayStatus(false) on a
    timer whether or not the flag is up, and never more often than that."""
    r = run_js(
        f"""
        const s = {json.dumps(_store_with([], players=PLAYERS))};
        DK._setStore({{ getState: () => s }});
        DK.loadCompact("Christian McCaffrey|RB|SFO|122.8|1|", {{ heartbeatSec: 1 }});
        const calls = [];
        DK._setActions({{ setAwayStatus: (v) => {{ calls.push([v, Date.now()]); }} }});
        (async () => {{
          const a = await DK.keepAlive();          // first call sets the baseline, no beat yet
          const b = await DK.keepAlive();          // within the interval: nothing
          await new Promise(r => setTimeout(r, 1100));
          const c = await DK.keepAlive();          // interval elapsed: one beat
          const d = await DK.keepAlive();          // and not again until the next interval
          console.log(JSON.stringify({{ n: calls.length, values: calls.map(x => x[0]), a, b, c, d,
            logged: DK.logs(10).filter(l => /^\S+ heartbeat: setAwayStatus/.test(String(l))).length }}));
        }})();
        """
    )
    assert r["values"] == [False], r
    assert r["n"] == 1 and r["logged"] == 1
    assert all(r[k]["away"] is False for k in ("a", "b", "c", "d"))


def test_heartbeat_that_throws_waits_for_the_next_interval():
    """Review 2026-09-02: the timestamp was only advanced after a successful
    call, so a throwing thunk retried every ~1 s cycle and its note evicted
    the whole 400-line log within minutes."""
    r = run_js(
        f"""
        const s = {json.dumps(_store_with([], players=PLAYERS))};
        DK._setStore({{ getState: () => s }});
        DK.loadCompact("Christian McCaffrey|RB|SFO|122.8|1|", {{ heartbeatSec: 1 }});
        let calls = 0;
        DK._setActions({{ setAwayStatus: () => {{ calls++; throw new Error('boom'); }} }});
        (async () => {{
          await DK.keepAlive();                       // baseline
          await new Promise(r => setTimeout(r, 1100));
          await DK.keepAlive();                       // due: one throwing attempt
          await DK.keepAlive();                       // NOT retried within the interval
          await DK.keepAlive();
          console.log(JSON.stringify({{ calls,
            threw: DK.logs(20).filter(l => /heartbeat threw/.test(String(l))).length }}));
        }})();
        """
    )
    assert r["calls"] == 1 and r["threw"] == 1


def test_trail_dump_composes_every_pick_manager_and_our_records_from_the_store():
    """The complete trail per mock (2026-09-02) must come from the driver, not
    a console snippet: picks carry team ids, managers carry nickname/away,
    and our retained pick records ride along."""
    r = run_js(
        f"""
        const s = {json.dumps(_store_with([(1, "1", "100"), (2, "6", "101")], players=PLAYERS))};
        s.league.managers["1"] = {{ id: "1", teamId: "1", away: true, nickname: "raymond" }};
        DK._setStore({{ getState: () => s }});
        DK.loadCompact("Christian McCaffrey|RB|SFO|122.8|1|", {{ teams: 10 }});
        // a record the way draftTop makes one, from a decision-time list
        const top = [{{ n: 'Christian McCaffrey', p: 'RB', v: 122.8, why: 'w1' }}, {{ n: 'Bijan Robinson', p: 'RB', v: 100, why: 'w2' }}];
        global.fetch = async (url, opts) => ({{ json: async () => ({{ ok: true, path: 'saved:' + JSON.parse(opts.body).room }}) }});
        (async () => {{
          const d = DK.trailDump({{ room_name: 'Test Room' }});
          const posted = await DK.trail({{ room_name: 'Test Room' }});
          console.log(JSON.stringify({{ picks: d.picks, managers: d.managers, my_team: d.my_team,
            teams: d.teams, room_name: d.room_name, recs: d.our_records.length, posted }}));
        }})();
        """
    )
    assert [p["pick_no"] for p in r["picks"]] == [1, 2]
    assert r["picks"][0]["team_id"] == "1" and r["picks"][1]["team_id"] == "6"
    assert r["managers"]["1"]["away"] is True and "nickname" in r["managers"]["1"]
    assert r["my_team"] == "6" and r["teams"] == 10 and r["room_name"] == "Test Room"
    assert r["posted"]["ok"] is True and r["posted"]["path"].startswith("saved:")


def test_plan_survival_fields_ride_through_the_ranked_list():
    """Plan B1: the bridge's s / sr / e per candidate must survive
    rankFromPlan so pick records keep them structured."""
    board = "Christian McCaffrey|RB|SFO|122.8|1|" + chr(10) + "Bijan Robinson|RB|ATL|100|1|"
    plan = {"plan": [{"n": "Christian McCaffrey", "p": "RB", "t": "SFO", "v": 122.8, "a": 1, "why": "w",
                      "s": 0.7, "sr": 0.86, "e": 80.5},
                     {"n": "Bijan Robinson", "p": "RB", "t": "ATL", "v": 100, "a": 4, "why": "w2"}],
            "needs": {"RB": 2}, "current_pick": 3}
    js = [
        "document.body.innerText = 'YOUR TEAM (0/15) ';",
        "DK.loadCompact(" + json.dumps(board) + ", {teams: 10});",
        "DK.loadPlan(" + json.dumps(plan) + ");",
        "const out = DK.rank();",
        "console.log(JSON.stringify({src: out.source, top: out.top.map(x => ({n: x.n, s: x.s, sr: x.sr, e: x.e}))}));",
    ]
    r = run_js(chr(10).join(js))
    assert r["src"] == "engine"
    assert r["top"][0] == {"n": "Christian McCaffrey", "s": 0.7, "sr": 0.86, "e": 80.5}
    assert r["top"][1] == {"n": "Bijan Robinson", "s": None, "sr": None, "e": None}


# ---------- review 2026-09-02: the engine path's own guardrail context ----------

def test_te2_rule_is_computed_without_the_local_ranker():
    """te2Ok used to read S.ctx, which only the local fallback rank() sets, so
    on the engine path (a plan loaded, rank() never reaching the local branch)
    every engine-recommended second TE was refused. The rule now reads the
    board and the current pick directly."""
    board = chr(10).join(["Trey McBride|TE|ARI|60|1||10", "Brock Bowers|TE|LV|58|1||12",
                          "Sam LaPorta|TE|DET|40|||30", "George Kittle|TE|SF|38|||34",
                          "Mark Andrews|TE|BAL|30|||50", "TJ Hockenson|TE|MIN|28|||55",
                          "Jake Ferguson|TE|DAL|10|||90"])
    js = [
        "document.body.innerText = 'ROUND 5, PICK 41 YOUR TEAM (4/15) ';",
        "DK.loadCompact(" + json.dumps(board) + ", {teams: 10, te2FallPicks: 12});",
        "const a = DK.top6TeFell();                       // McBride 31 picks past ADP 10 at pick 41",
        "DK.loadCompact(" + json.dumps(board) + ", {teams: 10, te2FallPicks: 40});",
        "const b = DK.top6TeFell();                       // nobody has fallen 40",
        "console.log(JSON.stringify({a, b}));",
    ]
    r = run_js(chr(10).join(js))
    assert r["a"] is True and r["b"] is False


def test_roster_view_prefers_the_store_and_the_header_count():
    """The round / picksLeft that drive K/DEF timing came from the roster
    panel regex, which cannot parse "A. St. Brown"; the store's roster and
    the header count are both available and now win."""
    r = run_js(
        f"""
        const s = {json.dumps(_store_with([(1, "1", "100"), (2, "6", "103"), (3, "6", "104")], players=PLAYERS))};
        DK._setStore({{ getState: () => s }});
        document.body.innerText = 'YOUR TEAM (3/15) A. St. Brown WR Det Bye 8 A. Brown WR Phi Bye 5';
        DK.loadCompact("Christian McCaffrey|RB|SFO|122.8|1|", {{ teams: 10 }});
        const v = DK.rosterView();
        console.log(JSON.stringify({{ have: v.have, source: v.source, counts: v.counts, header: v.headerHave,
                                      keys: v.players.map(p => p.k) }}));
        """
    )
    assert r["source"] == "store" and r["have"] == 3
    assert r["counts"] == {"WR": 2}
    assert r["keys"] == ["a brown", "a brown"]      # the board key is initial + LAST token; the collision guard handles the rest


def test_no_plan_ever_means_no_page_ranking_only_the_queue_and_yahoo():
    """The local VONA ranker is gone (review 2026-09-04). With no engine plan
    ever received, rank() reports source none and an empty top, labelled, so
    draftTop declines and the queue / Yahoo list take the pick."""
    r = run_js(
        f"""
        const s = {json.dumps(_store_with([(1, "1", "100"), (2, "2", "101")], players=PLAYERS))};
        DK._setStore({{ getState: () => s }});
        document.body.innerText = 'ROUND 1, PICK 3 YOUR TEAM (0/15) ';
        DK.loadCompact(["Christian McCaffrey|RB|SFO|122.8|1||1", "Bijan Robinson|RB|ATL|100|1||2",
                        "Brian Robinson Jr.|RB|WAS|20|||80", "Amon-Ra St. Brown|WR|DET|60|||5"].join(String.fromCharCode(10)), {{ teams: 10 }});
        const r = DK.rank();
        console.log(JSON.stringify({{ source: r.source, top: r.top, err: r.err }}));
        """
    )
    assert r["source"] == "none" and r["top"] == []
    assert "no engine plan" in r["err"]


def test_a_dropped_plan_is_ranked_stale_minus_players_the_store_says_are_drafted():
    """When the gate drops the plan (bridge unreachable), the last engine plan
    is kept as stale and ranked minus everyone drafted since -- the engine's
    own opinion from seconds ago, not a page-side ranking. Stress mock
    2026-09-02 (bridge killed at pick 78) is the case: the store's drafted
    list is authoritative and must be excluded."""
    r = run_js(
        f"""
        const s = {json.dumps(_store_with([(1, "1", "100"), (2, "2", "101")], players=PLAYERS))};
        DK._setStore({{ getState: () => s }});
        document.body.innerText = 'ROUND 1, PICK 3 YOUR TEAM (0/15) ';
        DK.loadCompact(["Christian McCaffrey|RB|SFO|122.8|1||1", "Bijan Robinson|RB|ATL|100|1||2",
                        "Brian Robinson Jr.|RB|WAS|20|||80", "Amon-Ra St. Brown|WR|DET|60|||5"].join(String.fromCharCode(10)), {{ teams: 10 }});
        DK.loadPlan({{ current_pick: 3, calls: 7, needs: {{}}, plan: [
          {{ n: 'Christian McCaffrey', p: 'RB', why: 'top' }}, {{ n: 'Bijan Robinson', p: 'RB', why: 'second' }},
          {{ n: 'Amon-Ra St. Brown', p: 'WR', why: 'third' }}, {{ n: 'Brian Robinson Jr.', p: 'RB', why: 'fourth' }} ] }});
        DK._stashPlan();
        const r = DK.rank();
        console.log(JSON.stringify({{ source: r.source, top: r.top.map(x => x.n), whys: r.top.map(x => x.why), stale: r.stale, planStatus: DK.planStatus() }}));
        """
    )
    assert r["source"] == "stale-plan"
    assert r["top"] == ["Amon-Ra St. Brown", "Brian Robinson Jr."], r
    assert all(w.startswith("STALE PLAN (engine plan from pick 3") for w in r["whys"]), r["whys"]
    assert r["stale"]["pick"] == 3
    assert r["planStatus"]["have"] is False      # the live plan slot is empty until the bridge answers again


def test_board_key_matches_the_drivers_key_for_awkward_names():
    """The exporter's key() and the driver's idKey() must agree, or a board row
    never matches its store/panel rendering. Mock 25: the exporter dropped
    hyphens ("j smithnjigba") while the driver spaced them ("j njigba"), so a
    drafted Smith-Njigba stayed "available" to the local ranker."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("ebj", Path(__file__).resolve().parents[1] / "scripts" / "export_board_json.py")
    ebj = importlib.util.module_from_spec(spec); spec.loader.exec_module(ebj)
    names = ["Jaxon Smith-Njigba", "Amon-Ra St. Brown", "Ja'Marr Chase", "Brian Robinson Jr.", "Patrick Mahomes II",
             "Wan'Dale Robinson", "Marvin Harrison Jr.", "T.J. Hockenson", "Kenneth Walker III", "De'Von Achane", "Bijan Robinson"]
    r = run_js("console.log(JSON.stringify(" + json.dumps(names) + ".map(n => DK.idKey(n, 'RB'))));")
    py = [ebj.key(n) for n in names]
    assert r == py, list(zip(names, py, r))


def test_pick_verification_uses_our_pick_number_even_without_a_team_id():
    """Mock 25, identity masked: our makePick landed Tracy at 118, but
    pickLandedStore needed my_team and returned null, so the click path took
    a roster-count increase (Sutton's click, rejected by Yahoo) as proof and
    recorded the wrong player. The entry at OUR pick number decides."""
    r = run_js(
        f"""
        const s = {json.dumps(_store_with([(1, "1", "100"), (2, "6", "101")], players=PLAYERS))};
        s.context.managerId = null;                      // the store cannot say which team we are
        DK._setStore({{ getState: () => s }});
        DK.loadCompact("Bijan Robinson|RB|ATL|100|1|" + String.fromCharCode(10) + "Christian McCaffrey|RB|SFO|122.8|1|", {{ teams: 10 }});
        console.log(JSON.stringify({{
          my_team: DK.storeState().my_team,
          landed: DK.pickLandedStore({{ n: 'Bijan Robinson', p: 'RB' }}, 2),
          other: DK.pickLandedStore({{ n: 'Christian McCaffrey', p: 'RB' }}, 2),
          notyet: DK.pickLandedStore({{ n: 'Bijan Robinson', p: 'RB' }}, 3),
        }}));
        """
    )
    assert r["my_team"] is None
    assert r["landed"] is True and r["other"] is False and r["notyet"] is None


# ---------- refit study instrumentation (DECISIONS #35) ----------

def test_timing_label_is_the_corrected_rule():
    """instant = the picker took <= 2.5 s (this pick's first sight minus the
    previous pick's) AND the previous poll was <= 2 s earlier; human = took
    >= 8 s; else unknown. The first pick of a room has no predecessor."""
    r = run_js("console.log(JSON.stringify(["
               "DK.timingLabel(1000, 900), DK.timingLabel(2500, 1800), DK.timingLabel(2500, 2600),"
               "DK.timingLabel(5000, 900), DK.timingLabel(8000, 900), DK.timingLabel(20000, 900),"
               "DK.timingLabel(null, 900), DK.timingLabel(1000, null)]));")
    assert r == ["instant", "instant", "unknown", "unknown", "human", "human", "unknown", "unknown"]


def test_store_state_stamps_first_sight_and_carries_yahoo_ranks():
    """Each drafted entry carries Yahoo's o_rank / avg_pick / psr_rank and a
    first-sight stamp (time since the previous pick, poll gap, away set)
    taken the FIRST time the pick was seen -- later reads do not move it."""
    r = run_js(
        f"""
        const s = {json.dumps(_store_with([(1, "1", "100")], players=PLAYERS))};
        s.players.byId["100"].o_rank = 6; s.players.byId["100"]["average-pick"] = "5.8"; s.players.byId["100"].psr_rank = 15;
        s.players.byId["101"].o_rank = 2; s.players.byId["101"]["average-pick"] = "2.0";
        s.countdown.seconds = 29; s.league.managers["9"] = {{ id: "9", teamId: "9", away: true }};
        DK._setStore({{ getState: () => s }});
        const a = DK.storeState();
        // the second pick appears on the very next poll: the picker took ~0 s -> instant
        s.draftPicks.order.push({{ id: 2, teamId: "2", playerId: "101" }});
        s.countdown.seconds = 12; s.draftOrder.currentPick = 2;
        const b = DK.storeState();
        const c = DK.storeState();
        console.log(JSON.stringify({{
          first: {{ o_rank: a.drafted[0].o_rank, avg_pick: a.drafted[0].avg_pick, psr: a.drafted[0].psr_rank, clock: a.drafted[0].clock_left, label: a.drafted[0].label, since: a.drafted[0].since_prev_ms }},
          again: {{ clock: c.drafted[0].clock_left, label: c.drafted[0].label }},
          second: {{ clock: b.drafted[1].clock_left, label: b.drafted[1].label, since: b.drafted[1].since_prev_ms, gapKnown: b.drafted[1].poll_gap_ms != null, o_rank: b.drafted[1].o_rank }},
          awayAt: DK.trailDump().picks[0].away_teams_at,
        }}));
        """
    )
    assert r["first"]["o_rank"] == 6 and r["first"]["avg_pick"] == 5.8 and r["first"]["psr"] == 15
    assert r["first"]["clock"] == 29 and r["first"]["label"] == "unknown" and r["first"]["since"] is None   # no predecessor
    assert r["again"]["clock"] == 29 and r["again"]["label"] == "unknown", "the stamp is taken once"
    assert r["second"]["clock"] == 12 and r["second"]["label"] == "instant" and r["second"]["since"] <= 2500 and r["second"]["gapKnown"] and r["second"]["o_rank"] == 2
    assert r["awayAt"] == ["9"]


def test_players_snapshot_posts_yahoo_ranks_once_per_room():
    r = run_js(
        f"""
        const s = {json.dumps(_store_with([], players=PLAYERS))};
        for (const [id, p] of Object.entries(s.players.byId)) {{ p.o_rank = +id - 99; p["average-pick"] = String(+id - 98); p.psr_rank = 3; }}
        s.context.leagueId = "777";
        DK._setStore({{ getState: () => s }});
        const posts = [];
        global.fetch = async (url, opts) => {{ posts.push({{ url, body: JSON.parse(opts.body) }}); return {{ json: async () => ({{ ok: true, path: "saved" }}) }}; }};
        (async () => {{
          const snap = DK.playersSnapshot();
          const a = await DK.postPlayersSnapshot();
          const b = await DK.postPlayersSnapshot();
          console.log(JSON.stringify({{ n: snap.n, kind: snap.kind, room: snap.room, first: snap.players.find(p => p.id === "100"),
            posted: posts.length, url: posts[0].url.slice(-8), again: b.already === true, ref: DK.trailDump().players_snapshot_ref }}));
        }})();
        """
    )
    assert r["n"] == len(PLAYERS) and r["kind"] == "players_snapshot" and r["room"] == "777"
    assert r["first"]["o_rank"] == 1 and r["first"]["avg_pick"] == 2 and r["first"]["pos"] == "RB" and r["first"]["name"] == "Christian McCaffrey"
    assert r["posted"] == 1 and r["url"] == "/players" and r["again"] is True
    assert r["ref"] == "players_777.json"


# ---------- the live trail panel (docs/plans/2026-09-03-live-trail-hud-plan.md) ----------

def test_narrate_appends_time_stamped_lines_and_mirrors_into_the_log():
    r = run_js("DK.narrate('info', 'one'); DK.narrate('picked', 'two'); const t = DK.narration();"
               "console.log(JSON.stringify({ n: t.length, kinds: t.map(x => x.kind), texts: t.map(x => x.text), ts: t[0].ts,"
               " logged: DK.logs(10).filter(l => /NARR (info|picked) (one|two)/.test(String(l))).length }));")
    assert r["n"] == 2 and r["kinds"] == ["info", "picked"] and r["texts"] == ["one", "two"]
    assert r["ts"].endswith("Z") and "T" in r["ts"]
    assert r["logged"] == 2


def test_plain_english_pick_reads_like_the_scrutiny_report():
    r = run_js("console.log(JSON.stringify(["
               "DK.plainEnglishPick({ drafted: 'Trey McBride', pos: 'TE', s: 0.79, why: 'waiting likely costs ~6 pts at TE (best option now 78, ~72 by your next turn) · 79% chance', top_proj_available: { n: 'Josh Allen' } }),"
               "DK.plainEnglishPick({ drafted: 'Drake Maye', pos: 'QB', s: 0.88, why: 'safe to wait on QB · 88% chance', top_proj_available: { n: 'Drake Maye' } }),"
               "DK.plainEnglishPick({ drafted: 'Rico Dowdle', pos: 'RB', why: 'bench insurance: covers 3 RB starters ~9.6 wks/season · +10.0/wk over the wire (Josh Jacobs) ≈ 96 pts · HANDCUFF: backs up your Jaylen Warren', attempted: ['X:action-timeout'] }),"
               "]));")
    assert r[0].startswith("chose Trey McBride (TE): waiting would likely cost about 6 points at TE, 79% to still be there next turn")
    assert "top projection left was Josh Allen, passed on purpose" in r[0]
    assert r[1].startswith("chose Drake Maye (QB): nothing urgent") and "passed on purpose" not in r[1]
    assert r[2].startswith("lineup full, so Rico Dowdle (RB) is insurance: covers 3 RB starter(s) about 9.6 weeks")
    assert "backs up one of our starters" in r[2] and "skipped first: X:action-timeout" in r[2]


def test_fingerprint_diff_names_missing_and_new_parts():
    r = run_js("const base = { store_keys: ['a', 'b', 'players'], pick_keys: ['id', 'playerId', 'teamId'], action_names: ['makePick', 'setAwayStatus'] };"
               "const now = { store_keys: ['a', 'players', 'zzz'], pick_keys: ['id', 'playerId', 'teamId'], action_names: ['makePick'] };"
               "console.log(JSON.stringify({ same: DK.fingerprintDiff(base, base), diff: DK.fingerprintDiff(now, base), none: DK.fingerprintDiff(null, base) }));")
    assert r["same"] == []
    assert any(d.startswith("store_keys: missing b; new zzz") for d in r["diff"])
    assert any(d.startswith("action_names: missing setAwayStatus") for d in r["diff"])
    assert r["none"] == ["no baseline to compare"]




def test_sleep_falls_back_to_settimeout_without_a_worker_and_reports_its_mode():
    """node has no Worker: the throttle-proof sleep must degrade to
    setTimeout, still wait, and say so in sleepMode. (In Chrome the Blob
    worker path is live; mock 30's tab confirmed a 500 ms sleep in 508 ms
    while hidden.)"""
    r = run_js("const t0 = Date.now(); DK._sleep(120).then(() => console.log(JSON.stringify({ waited: Date.now() - t0, mode: DK.sleepMode() })));")
    assert r["waited"] >= 100
    assert r["mode"].startswith("timeout")


def test_fingerprint_diff_ignores_pick_keys_before_the_first_pick():
    r = run_js("const base = { store_keys: ['a'], pick_keys: ['id', 'playerId', 'teamId'] };"
               "console.log(JSON.stringify({ empty: DK.fingerprintDiff({ store_keys: ['a'], pick_keys: [] }, base),"
               " changed: DK.fingerprintDiff({ store_keys: ['a'], pick_keys: ['id'] }, base) }));")
    assert r["empty"] == []
    assert any(d.startswith("pick_keys: missing") for d in r["changed"])


def test_pair_arithmetic_rides_through_the_ranked_list():
    """The field that decides the pick must reach the page, not just the why
    string. `pair` was absent from the plan->candidate mapping, so every mock
    ever recorded carried pair:null on every pick -- directly under a comment
    promising the numbers were kept structured. Sibling of the survival test
    above, and of the proj_band drop in yahoo_bridge.load_players: a
    hand-maintained field list that silently forgets an upstream addition."""
    board = "Christian McCaffrey|RB|SFO|122.8|1|" + chr(10) + "Bijan Robinson|RB|ATL|100|1|"
    pair = {"own": 58.6, "partner": "WR", "partner_pts": 70.7,
            "total": 129.3, "pick_cost": 0.0}
    plan = {"plan": [{"n": "Christian McCaffrey", "p": "RB", "t": "SFO", "v": 122.8, "a": 1,
                      "why": "w", "s": 0.7, "sr": 0.86, "e": 80.5, "b": 122.8, "pair": pair},
                     {"n": "Bijan Robinson", "p": "RB", "t": "ATL", "v": 100, "a": 4, "why": "w2"}],
            "needs": {"RB": 2}, "current_pick": 3}
    js = [
        "document.body.innerText = 'YOUR TEAM (0/15) ';",
        "DK.loadCompact(" + json.dumps(board) + ", {teams: 10});",
        "DK.loadPlan(" + json.dumps(plan) + ");",
        "const out = DK.rank();",
        "console.log(JSON.stringify({top: out.top.map(x => ({n: x.n, pair: x.pair, b: x.b}))}));",
    ]
    r = run_js(chr(10).join(js))
    assert r["top"][0]["pair"] == pair, r["top"][0]
    assert r["top"][0]["b"] == 122.8
    # a row the planner never scored says so with null rather than inventing one
    assert r["top"][1]["pair"] is None
    assert r["top"][1]["b"] is None


def test_preflight_refuses_a_room_whose_size_disagrees_with_dk_load():
    """Room 10712781 (2026-09-04) was a 14-team room injected with teams: 10.
    Nothing refused it: my picks fell on 9, 20, 37 while the engine computed a
    10-team snake, and every ADP-keyed quantity ran 10-team ADP against a
    210-pick draft. The store's draftOrder.order is the full pick order, so its
    length over rounds is the team count with no guessing."""
    board = "Christian McCaffrey|RB|SFO|122.8|1|" + chr(10) + "Bijan Robinson|RB|ATL|100|1|"
    picks = [(1, 1, "Jahmyr", "Gibbs", "RB"), (6, 6, "Christian", "McCaffrey", "RB")]
    base = _fake_store(picks)
    js = [
        "DK.loadCompact(" + json.dumps(board) + ", {teams: 10, rounds: 15});",
        "const base = " + json.dumps(base) + ";",
        "const withOrder = (n) => { const s = JSON.parse(JSON.stringify(base));"
        "  s.draftOrder.order = Array.from({length: n}, (_, i) => ({id: i + 1, teamId: String((i % 14) + 1)})); return s; };",
        "DK._setStore({ getState: () => withOrder(210) }); const fourteen = DK.roomSizeCheck();",
        "DK._setStore({ getState: () => withOrder(150) }); const ten = DK.roomSizeCheck();",
        "DK._setStore({ getState: () => base }); const noOrder = DK.roomSizeCheck();",
        "console.log(JSON.stringify({ fourteen, ten, noOrder }));",
    ]
    r = run_js(chr(10).join(js))
    assert r["fourteen"] == {"order_len": 210, "teams_implied": 14, "teams_mismatch": True}, r["fourteen"]
    assert r["ten"] == {"order_len": 150, "teams_implied": 10, "teams_mismatch": False}, r["ten"]
    # a store that carries no pick order is not evidence of a mismatch; the
    # other preflight checks carry the verdict
    assert r["noOrder"]["teams_mismatch"] is False and r["noOrder"]["order_len"] is None, r["noOrder"]


# ---------- review 2026-09-04: the page ranks nothing itself; the queue still guards ----------

def test_queue_plan_applies_the_guardrails_to_the_engines_plan():
    """The local ranker is gone, so the page never ranks. The QUEUE planner
    still checks each engine row against the roster it would hold by then
    (guardrailOk): no third QB, no second QB before the gate, no K or DEF
    until the last two picks. A plan that lists them anyway (a stale plan,
    say) must not put them in the queue."""
    board = "\n".join([
        "Josh Allen|QB|BUF|39.7|||20.1",
        "Jalen Hurts|QB|PHI|27.0|||56.4",
        "Brandon Aubrey|K|DAL|9.0|||140.0",
        "Ravens|DEF|BAL|8.0|||141.0",
        "Jaylen Warren|RB|PIT|9.3|1||77.0",
        "Courtland Sutton|WR|DEN|-1.7|||105.2",
        "Kenneth Gainwell|RB|TB|4.0|||120.0",
    ])
    r = run_js(
        f"""
        DK.loadCompact({json.dumps(board)});
        DK.loadPlan({json.dumps({"plan": plan_rows(board), "needs": {}, "current_pick": 44})});
        document.body.innerText = {json.dumps(panel([
            "P. Mahomes QB KC Bye 6", "R. Rice WR KC Bye 5", "D. Adams WR LAR Bye 11",
            "J. Williams RB Dal Bye 14", "T. McBride TE Ari Bye 14",
        ]))};
        console.log(JSON.stringify({{ plan: DK.planQueue(null, null, 8), rank: DK.rank().top.map(x => x.n) }}));
        """
    )
    queued = r["plan"]
    assert not any(q.endswith("|QB") for q in queued), f"a second QB before the gate was queued: {queued}"
    assert not any(q.endswith("|K") or q.endswith("|DEF") for q in queued), f"K/DEF queued with 10 picks left: {queued}"
    assert any(q.endswith("|RB") or q.endswith("|WR") for q in queued), queued
    # rank() itself hands the plan through untouched (minus mine/drafted): the
    # engine owns the guardrails on the pick, the queue owns them on the queue
    assert "Jalen Hurts" in r["rank"]


def test_stale_plan_still_feeds_the_queue_planner():
    """With the bridge gone, the queue is planned from the stale plan, so
    Yahoo's autopick draws from the engine's last opinion, not its default
    list."""
    board = "\n".join(["Jaylen Warren|RB|PIT|9.3|1||77.0", "Courtland Sutton|WR|DEN|-1.7|||105.2",
                        "Kenneth Gainwell|RB|TB|4.0|||120.0"])
    r = run_js(
        f"""
        DK.loadCompact({json.dumps(board)});
        DK.loadPlan({json.dumps({"plan": plan_rows(board), "needs": {}, "current_pick": 88})});
        document.body.innerText = {json.dumps(panel(["P. Mahomes QB KC Bye 6", "R. Rice WR KC Bye 5"]))};
        DK._stashPlan();
        console.log(JSON.stringify({{ plan: DK.planQueue(null, null, 5), status: DK.planStatus().have }}));
        """
    )
    assert r["status"] is False
    assert r["plan"] == ["Jaylen Warren|RB", "Courtland Sutton|WR", "Kenneth Gainwell|RB"]
