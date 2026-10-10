"""The calculator's own messages (DECISIONS #235, the 2026-10-10 chat test on LV at NE): a failed
download is one line and exit 1, never a traceback; capture's counts add up."""
from __future__ import annotations

import urllib.error

from core import fetch as F
from props.calc import __main__ as CLI
from props.calc import capture


def test_a_failed_download_is_one_line_and_exit_1(monkeypatch, capsys):
    cause = urllib.error.HTTPError("https://x/pbp-2025.csv.gz", 502, "Bad Gateway", {}, None)

    def run(a):
        raise F.FetchError("nflverse pbp 2025", "https://x/pbp-2025.csv.gz", cause)
    monkeypatch.setattr(CLI, "run", run)
    assert CLI.main(["leg", "Ashton Jeanty", "rush_yds", "over"]) == 1
    out = capsys.readouterr()
    lines = [x for x in (out.out + out.err).splitlines() if x.strip()]
    assert len(lines) == 1 and lines[0].startswith("Download failed: nflverse pbp 2025: download failed (HTTPError")
    assert "Traceback" not in out.out + out.err


def test_capture_counts_sides_so_the_numbers_add_up():
    r = {"lines": 368, "sides": 736, "added": 736, "replaced": 0, "captured_at_utc": "2026-10-10T22:29:56+00:00",
         "paths": ["props/calc/lines/2026/line_archive_2026.jsonl"]}
    line = capture.summary_line(r)
    assert line.startswith("Saved 368 lines (736 sides: 736 new, 0 updated) captured at 2026-10-10T22:29:56+00:00")
    assert capture.summary_line({**r, "added": 700, "replaced": 36}).startswith(
        "Saved 368 lines (736 sides: 700 new, 36 updated)")
    assert capture.summary_line({**r, "paths": []}).endswith("to nowhere (none matched).")
