"""Layer 0's page driver (scripts/prerank_driver.js): the pure parts.

The Edit Pre-Draft Ranks page is what Yahoo's own autopick walks when a pick
is lost, so a wrong reading here is a wrong floor. Runs through node; no
node -> skip, never a false green.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path

import pytest

DRIVER = Path(__file__).resolve().parents[1] / "scripts" / "prerank_driver.js"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None, reason="node not installed")


def run_js(snippet: str):
    harness = textwrap.dedent(
        """
        global.document = { querySelectorAll: () => [], querySelector: () => null,
                            body: { innerText: '' } };
        global.window = global;
        global.HTMLTextAreaElement = function () {};
        """
    )
    code = harness + DRIVER.read_text(encoding="utf-8") + "\n" + snippet
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "run.js"
        script.write_text(code, encoding="utf-8")
        out = subprocess.run([NODE, str(script)], capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        raise AssertionError(out.stderr.strip() or out.stdout.strip())
    return json.loads(out.stdout.strip())


def test_row_text_parses_names_that_contain_a_position_letter():
    """"DK Metcalf" and "J.K. Dobbins" were read as name "D"/"J." with
    position K, so unmatched() reported both missing from My Preferred when
    the import had placed them (2026-09-02). The position is the token
    before the first middle dot, nothing earlier."""
    rows = {
        "dk": "DK MetcalfWR·Pit·Bye 9XRank #76·ADP 85.9",
        "jk": "J.K. DobbinsRB·Den·Bye 10XRank #85·ADP 95.1",
        "cook": "James Cook IIIRB·Buf·Bye 7XRank #9·ADP 9.5",
        "k": "Brandon AubreyK·Dal·Bye 10XRank #120·ADP 130.2",
        "def": "TexansDEF·Hou·Bye 8XRank #140·ADP 150.0",
        "te": "Trey McBrideTE·Ari·Bye 14XRank #31·ADP 26.7",
    }
    r = run_js("console.log(JSON.stringify(Object.fromEntries(Object.entries("
               + json.dumps(rows) + ").map(([k, t]) => [k, PR.parseRowText(t)]))));")
    assert r["dk"] == {"name": "DK Metcalf", "pos": "WR"}
    assert r["jk"] == {"name": "J.K. Dobbins", "pos": "RB"}
    assert r["cook"] == {"name": "James Cook III", "pos": "RB"}
    assert r["k"] == {"name": "Brandon Aubrey", "pos": "K"}
    assert r["def"] == {"name": "Texans", "pos": "DEF"}
    assert r["te"] == {"name": "Trey McBride", "pos": "TE"}


def test_names_normalise_the_same_on_both_sides():
    r = run_js("console.log(JSON.stringify({a: PR.norm('James Cook III', 'RB'), b: PR.norm('James Cook', 'RB'),"
               " d: PR.norm('Houston Texans', 'DEF'), e: PR.norm('Texans', 'DEF')}));")
    assert r["a"] == r["b"]
    assert r["d"] == r["e"] == "TEXANS"
