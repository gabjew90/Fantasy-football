"""Offline DOM tests: the driver's page readers against REAL Yahoo markup.

Until 2026-09-01 the only way to find out whether the driver could read a
Yahoo draft room was to join one -- 25 minutes a try, and the failures were
discovered by drafting badly (mock 11: the expanded stats layout made every
row lookup miss, and the driver drafted four tight ends). These run the same
functions against saved pages in seconds.

Fixtures live in tests/fixtures/yahoo/ and are captured from a live room by
POSTing document.documentElement.outerHTML to the bridge's /fixture route
(CSRF crumbs redacted). jsdom has no innerText; the harness maps it to
textContent, which is close enough for the text these readers key on.
Skipped when node or jsdom is absent -- never a false green.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "scripts" / "draft_driver.js"
FIXTURES = ROOT / "tests" / "fixtures" / "yahoo"
NODE = shutil.which("node")
HAVE_JSDOM = (ROOT / "node_modules" / "jsdom").exists()

pytestmark = pytest.mark.skipif(
    NODE is None or not HAVE_JSDOM, reason="node + jsdom required (npm install)")


def run_in_fixture(fixture: str, snippet: str) -> dict:
    harness = textwrap.dedent(f"""
        const {{ JSDOM }} = require({json.dumps(str(ROOT / "node_modules" / "jsdom"))});
        const fs = require('fs');
        const html = fs.readFileSync({json.dumps(str(FIXTURES / fixture))}, 'utf8');
        const dom = new JSDOM(html, {{ url: 'https://football.fantasysports.yahoo.com/draftclient/f1/1/1' }});
        const w = dom.window;
        // jsdom does not implement innerText. The readers split page text on
        // newlines, which a browser inserts at block boundaries and jsdom's
        // textContent does not -- so emulate that much: a newline after every
        // block-level element and <br>. Hidden-element elision is not emulated.
        const BLOCK = new Set(['DIV','P','LI','UL','OL','TR','TD','TH','TABLE','SECTION','ARTICLE','HEADER','FOOTER','NAV','H1','H2','H3','H4','H5','H6','BR','HR','FORM','BUTTON','LABEL','SPAN_BLOCK']);
        function innerTextOf(node) {{
          let out = '';
          for (const c of node.childNodes) {{
            if (c.nodeType === 3) out += c.nodeValue;
            else if (c.nodeType === 1) {{
              if (c.tagName === 'SCRIPT' || c.tagName === 'STYLE') continue;
              if (c.tagName === 'BR') {{ out += '\\n'; continue; }}
              const t = innerTextOf(c);
              out += BLOCK.has(c.tagName) ? ('\\n' + t + '\\n') : t;
            }}
          }}
          return out;
        }}
        Object.defineProperty(w.HTMLElement.prototype, 'innerText', {{
          get() {{ return innerTextOf(this).replace(/\\n{{2,}}/g, '\\n'); }}, configurable: true }});
        global.window = w; global.document = w.document; global.location = w.location;
        global.HTMLElement = w.HTMLElement; global.Node = w.Node;
        global.sessionStorage = {{ getItem: () => null, setItem: () => {{}} }};
        // title from the fixture's <title>
        // no layout in jsdom: offsetWidth is 0, so anything gated on visibility is not testable here
    """)
    # the driver assigns window.DK; window here is the jsdom window, not global
    code = harness + DRIVER.read_text(encoding="utf-8") + "\nconst DK = window.DK;\n" + snippet
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "t.js"
        f.write_text(code, encoding="utf-8")
        r = subprocess.run([NODE, str(f)], capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise AssertionError((r.stderr or r.stdout)[-2000:])
    return json.loads(r.stdout.strip().splitlines()[-1])


EXPANDED = "draftroom-expanded-onclock-picks.html"


@pytest.mark.skipif(not (FIXTURES / EXPANDED).exists(), reason="fixture not captured")
def test_expanded_layout_rows_are_found_with_their_star_or_draft_button():
    """Mock 11's bug: rows in the expanded stats layout run ~400 chars and the
    lookup capped candidates at 260, so no row with a control ever matched."""
    out = run_in_fixture(EXPANDED, """
        // player TABLE rows (tr), read through the same innerText the driver uses
        const rows = [...document.querySelectorAll('tr')].filter(e => e.querySelector('button'))
          .map(e => (e.innerText || '').replace(/\\s+/g, ' ').trim())
          .filter(t => /Bye \\d+/.test(t) && /\\b(QB|RB|WR|TE)\\b/.test(t));
        const names = [...new Set(rows.map(t => (t.match(/\\b([A-Z])\\.\\s?([A-Za-z'\\-\\.]+(?: (?:Jr\\.|Sr\\.|II|III|IV))?)\\b/) || []).slice(1, 3).join(' ')).filter(s => s.trim()))].slice(0, 6);
        const hits = names.map(n => {
          const [ini, last] = n.split(' ', 2);
          const rest = n.slice(ini.length + 1);
          const entry = { n: ini + '. ' + rest, k: (ini + ' ' + rest.replace(/\\s+(Jr\\.|Sr\\.|II|III|IV)$/, '')).toLowerCase(), p: '', t: '' };
          const row = rows.find(t => new RegExp('\\\\b' + ini + '\\\\.\\\\s?' + rest.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&')).test(t)) || '';
          entry.p = (row.match(/\\b(QB|RB|WR|TE)\\b/) || [])[1] || '';
          const found = DK.findRow(entry);
          return { n, p: entry.p, found: !!found, len: found ? (found.innerText || '').length : null };
        });
        console.log(JSON.stringify({ nRows: rows.length, names, hits, sample: rows[0] ? rows[0].slice(0, 120) : null }));
    """)
    assert out["names"], "fixture has no player rows"
    found = [h for h in out["hits"] if h["found"]]
    assert len(found) >= 3, out
    # (the 260-char regression itself is browser innerText behaviour that jsdom
    # cannot reproduce; ROW_TEXT_CAP is asserted in test_draft_driver instead)


POSTDRAFT = "draftroom-expanded-postdraft-picks.html"


@pytest.mark.parametrize("fixture", [EXPANDED, POSTDRAFT])
def test_picks_panel_parses_with_our_picks_labelled(fixture):
    if not (FIXTURES / fixture).exists():
        pytest.skip("fixture not captured")
    out = run_in_fixture(fixture, """
        const tab = [...document.querySelectorAll('button')].find(b => /^Picks/.test(b.textContent.trim()));
        const picksTabSelected = !!tab && tab.getAttribute('aria-selected') === 'true';
        // jsdom cannot re-render on click, so only read; the reader's own
        // ensureLeftTab click is a no-op here
        const picks = DK.parsePicksPanel();
        console.log(JSON.stringify({ picksTabSelected, n: picks.length, mine: picks.filter(p => p.mine).length,
          first: picks[0] || null }));
    """)
    if out["picksTabSelected"]:
        assert out["n"] >= 5, out
        assert out["mine"] >= 1, "our own picks must carry the You label"
        assert out["first"]["pos"] in ("QB", "RB", "WR", "TE", "K", "DEF")
    else:
        # the panel was on Queue when captured: the honest result is NO picks,
        # never garbage parsed out of the queue list (mock 11 bug 33)
        assert out["n"] == 0, out


@pytest.mark.skipif(not (FIXTURES / EXPANDED).exists(), reason="fixture not captured")
def test_roster_panel_parses():
    out = run_in_fixture(EXPANDED, """
        const r = DK.myRoster();
        console.log(JSON.stringify({ have: r ? r.players.length : null, counts: r ? r.counts : null }));
    """)
    assert out["have"] and out["have"] >= 5, out
    assert sum(out["counts"].values()) == out["have"]


@pytest.mark.skipif(not (FIXTURES / EXPANDED).exists(), reason="fixture not captured")
def test_header_pick_number_is_readable():
    out = run_in_fixture(EXPANDED, """
        console.log(JSON.stringify({ pick: DK.currentPickNo(), live: DK.tableLive() }));
    """)
    assert out["pick"] and out["pick"] > 1
    assert out["live"] is True


SNAPSHOT = "store-snapshot-expanded.json"


@pytest.mark.skipif(not (FIXTURES / SNAPSHOT).exists(), reason="snapshot not captured")
def test_store_state_reads_the_clients_redux_store():
    """The store is the primary state source now (mock 12). This runs
    storeState() over a real snapshot: every pick with team and player ids,
    our own picks flagged from context.managerId, the current pick, the
    clock, and which rivals were away."""
    out = run_in_fixture(EXPANDED, f"""
        const snap = JSON.parse(require('fs').readFileSync({json.dumps(str(FIXTURES / SNAPSHOT))}, 'utf8'));
        DK._setStore({{ getState: () => snap }});
        const s = DK.storeState();
        console.log(JSON.stringify({{
          ok: !!s, my_team: s && s.my_team, n: s && s.drafted.length,
          mine: s && s.drafted.filter(d => d.mine).map(d => d.pick_no + ' ' + d.name + ' ' + d.pos),
          current_pick: s && s.current_pick, on_clock: s && s.on_clock, seconds: s && s.seconds,
          away: s && s.away_teams.length, first: s && s.drafted[0],
          withPos: s && s.drafted.filter(d => d.pos).length,
        }}));
    """)
    assert out["ok"], out
    assert out["my_team"] == "10"
    assert out["n"] >= 100
    assert out["mine"], "our picks must be flagged"
    assert all(m.startswith(("10 ", "11 ", "30 ", "31 ", "50 ", "51 ", "70 ", "71 ", "90 ", "91 ", "110 ", "111 ")) for m in out["mine"]), out["mine"]
    assert out["first"]["pick_no"] == 1
    # the snapshot keeps only the first 400 players' records, so not every
    # pick resolves to a name/position here; most must
    assert out["withPos"] >= 0.5 * out["n"], out
    assert out["current_pick"] >= 100
    assert out["away"] >= 1
