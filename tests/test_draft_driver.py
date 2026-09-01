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
    out = subprocess.run(
        [NODE, "-e", code], capture_output=True, text=True, timeout=30
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


def test_second_te_only_if_top_six():
    """TE2 allowed only for a board top-6 TE. Bowers qualifies."""
    r = rank_with(panel([
        "T. McBride TE Ari Bye 14",
        "P. Nacua WR LAR Bye 11",
    ]))
    assert "Brock Bowers" in [c["n"] for c in r["top"]]


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
