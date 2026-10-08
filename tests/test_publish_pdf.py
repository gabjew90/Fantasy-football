"""props/engine/scripts/publish_pdf.py: the external version as a PDF (DECISIONS #218). In the root
suite, whose CI installs requirements.txt (reportlab); props/tests runs before every capture and
must not depend on it."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "props" / "tests"))
sys.path.insert(0, str(ROOT / "props" / "engine" / "scripts"))
pytest.importorskip("reportlab")
import publish_pdf as PDF  # noqa: E402
import publish_render as PR  # noqa: E402
import test_publish as T  # noqa: E402


def _pdf_text(path) -> str:
    return Path(path).read_bytes().decode("latin-1")


def test_inline_marks_escape_and_the_arrow_is_written_out():
    assert PDF.inline("**a** & *b* < c") == "<b>a</b> &amp; <i>b</i> &lt; c"
    assert PDF.plain("10.7 targets -> 8.0 catches") == "10.7 targets (8.0 catches)"
    assert PDF.plain("9 targets at 79% -> 67%", cell=True) == "9 targets at 79%: 67%"
    assert PDF.inline("Win probability*") == "Win probability*"          # a lone star is not italic


def test_tables_headings_bullets_and_quotes_become_flowables():
    from reportlab.platypus import Paragraph, Table
    md = "# T\n\n## S\n\n| a | b |\n|---|---:|\n| x | 1 |\n\n- one\n\n> **q:** z\n\nplain text\n"
    fl = PDF.flowables(md, 500)
    assert any(isinstance(f, Table) for f in fl)
    assert sum(isinstance(f, Paragraph) for f in fl) >= 5


def test_the_external_pdf_builds_with_the_embedded_fonts_and_its_title(tmp_path):
    reads = T.good()
    md = PR.scrub(PR.render_external(T.RUN, reads))
    p = PDF.build(md, tmp_path / "x.pdf", title="TB at DAL, week 5")
    raw = _pdf_text(p)
    assert raw.startswith("%PDF")
    assert len(re.findall(r"/Type /Page[^s]", raw)) >= 1
    fonts = set(re.findall(r"/BaseFont /([A-Za-z+\-]+)", raw))
    # the text is set in the embedded Vera faces (reportlab always lists Helvetica as its unused /F1 default)
    assert {"BitstreamVeraSans-Roman", "BitstreamVeraSans-Bold"} <= {f.split("+")[-1] for f in fonts}, fonts
    assert "/Title (TB at DAL, week 5)" in raw


def test_publish_writes_the_pdf_and_says_so_when_reportlab_is_missing(tmp_path, monkeypatch, capsys):
    import publish as P
    run_p, reads_p = T._files(tmp_path)
    out = tmp_path / "o"
    assert P.main(["--run", str(run_p), "--reads", str(reads_p), "--out", str(out), "--no-ci"]) == 0
    assert (out / "2026_wk05_TB_DAL.pdf").exists()
    monkeypatch.setattr(PDF, "available", lambda: False)
    out2 = tmp_path / "o2"
    assert P.main(["--run", str(run_p), "--reads", str(reads_p), "--out", str(out2), "--no-ci"]) == 0
    assert not (out2 / "2026_wk05_TB_DAL.pdf").exists()
    assert "PDF skipped" in capsys.readouterr().err


# ---- the code review (2026-10-08) ----
def test_every_markdown_table_and_header_line_reaches_the_pdf_as_itself():
    from reportlab.platypus import Paragraph, Table
    md = PR.render_external(T.RUN, T.good())
    lines = md.splitlines()
    n_md = sum(1 for a, b in zip(lines, lines[1:]) if a.startswith("|") and re.match(r"^\|?\s*:?-{3,}", b.strip()))
    fl = PDF.flowables(md, 500)
    assert sum(isinstance(f, Table) for f in fl) == n_md > 5
    paras = [f for f in fl if isinstance(f, Paragraph)]
    assert not any(p.text.lstrip().startswith("|") for p in paras)          # no table set as a paragraph
    meta = [p for p in paras if p.style.name == "meta"]
    assert meta and all(not p.text.startswith("%%") for p in paras)


def test_only_the_renderers_arrows_are_written_out():
    assert PDF.plain("his share went 26% -> 49%") == "his share went 26% -> 49%"
    assert PDF.plain("9 targets at 79% -> 67%", cell=True) == "9 targets at 79%: 67%"
    assert PDF.plain("10.7 targets -> 8.0 catches") == "10.7 targets (8.0 catches)"


def test_headings_keep_with_what_follows():
    S = PDF._styles()
    assert S["h2"].keepWithNext and S["h3"].keepWithNext
