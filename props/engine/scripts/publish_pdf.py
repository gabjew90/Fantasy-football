"""The external version as a PDF (DECISIONS #218): publish_render.render_external's Markdown,
typeset with reportlab.

The Markdown is the narrow subset the renders write -- headings (#, ##, ###), paragraphs, **bold**
and *italic*, pipe tables (a '---:' column is right-aligned), '- ' bullets and '> ' quotes -- so
the PDF holds exactly the words and numbers the checked Markdown holds; this module only lays
them out. Fonts: the Bitstream Vera family reportlab bundles, embedded, so the page is the same
on any machine. Vera has no arrow, so '->' is written out (DECISIONS #218).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

INK, ACCENT, MUTED, RULE, FILL, BAND = "#1F2933", "#2F5D8A", "#5F6B78", "#C9D3DD", "#EAF0F6", "#F6F8FA"


def available() -> bool:
    try:
        import reportlab  # noqa: F401
        return True
    except ImportError:
        return False


def _fonts():
    import reportlab
    from reportlab.lib.fonts import addMapping
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    d = os.path.join(os.path.dirname(reportlab.__file__), "fonts")
    for name, f in (("Vera", "Vera.ttf"), ("Vera-Bold", "VeraBd.ttf"), ("Vera-Italic", "VeraIt.ttf"),
                    ("Vera-BoldItalic", "VeraBI.ttf")):
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, os.path.join(d, f)))
    # each face as its own family too, so <b> / <i> inside a bold or italic style resolve
    for fam, (r, b, i, bi) in {"Vera": ("Vera", "Vera-Bold", "Vera-Italic", "Vera-BoldItalic"),
                               "Vera-Bold": ("Vera-Bold", "Vera-Bold", "Vera-BoldItalic", "Vera-BoldItalic"),
                               "Vera-Italic": ("Vera-Italic", "Vera-BoldItalic", "Vera-Italic", "Vera-BoldItalic"),
                               "Vera-BoldItalic": ("Vera-BoldItalic",) * 4}.items():
        addMapping(fam, 0, 0, r)
        addMapping(fam, 1, 0, b)
        addMapping(fam, 0, 1, i)
        addMapping(fam, 1, 1, bi)


def plain(text: str) -> str:
    """'10.7 targets -> 8.0 catches' -> '10.7 targets (8.0 catches)'; any other ' -> ' -> ': '."""
    text = re.sub(r"(\d[\d.]* targets) -> (\d[\d.]* catches)", r"\1 (\2)", text)
    return text.replace(" -> ", ": ")


def inline(text: str) -> str:
    """Markdown inline marks to reportlab's mini-markup, the text escaped first."""
    t = plain(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", t)
    t = re.sub(r"`([^`]+)`", r"\1", t)
    return t


def _styles():
    from reportlab.lib.colors import HexColor
    from reportlab.lib.styles import ParagraphStyle
    c = HexColor
    base = ParagraphStyle("body", fontName="Vera", fontSize=9.2, leading=13, textColor=c(INK), spaceAfter=5)
    return {
        "body": base,
        "title": ParagraphStyle("title", parent=base, fontName="Vera-Bold", fontSize=20, leading=24, textColor=c(INK),
                                spaceAfter=4),
        "h2": ParagraphStyle("h2", parent=base, fontName="Vera-Bold", fontSize=12.5, leading=16, textColor=c(ACCENT),
                             spaceBefore=12, spaceAfter=5),
        "h3": ParagraphStyle("h3", parent=base, fontName="Vera-Bold", fontSize=10.5, leading=14, textColor=c(INK),
                             spaceBefore=9, spaceAfter=4),
        "note": ParagraphStyle("note", parent=base, fontSize=7.6, leading=10, textColor=c(MUTED), spaceAfter=4),
        "meta": ParagraphStyle("meta", parent=base, fontSize=8, leading=11, textColor=c(MUTED), spaceAfter=2),
        "cell": ParagraphStyle("cell", parent=base, fontSize=7.8, leading=10, spaceAfter=0),
        "cellr": ParagraphStyle("cellr", parent=base, fontSize=7.8, leading=10, spaceAfter=0, alignment=2),
        "head": ParagraphStyle("head", parent=base, fontName="Vera-Bold", fontSize=7.8, leading=10, spaceAfter=0),
        "headr": ParagraphStyle("headr", parent=base, fontName="Vera-Bold", fontSize=7.8, leading=10, spaceAfter=0,
                                alignment=2),
        "quote": ParagraphStyle("quote", parent=base, leftIndent=8, borderPadding=(5, 6, 5, 6), backColor=c(BAND),
                                spaceBefore=3, spaceAfter=7),
        "bullet": ParagraphStyle("bullet", parent=base, leftIndent=12, bulletIndent=2, spaceAfter=3, bulletFontName="Vera"),
    }


def _table(rows, aligns, S, width):
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import Paragraph, Table, TableStyle
    ncol = max(len(r) for r in rows)
    rows = [r + [""] * (ncol - len(r)) for r in rows]
    data = []
    for i, r in enumerate(rows):
        out = []
        for j, cell in enumerate(r):
            right = j < len(aligns) and aligns[j] == "right"
            style = (S["headr"] if right else S["head"]) if i == 0 else (S["cellr"] if right else S["cell"])
            out.append(Paragraph(inline(cell), style))
        data.append(out)
    first = 0.34 if ncol > 2 else 0.5
    widths = [width * first] + [width * (1 - first) / (ncol - 1)] * (ncol - 1) if ncol > 1 else [width]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    st = [("BACKGROUND", (0, 0), (-1, 0), HexColor(FILL)), ("LINEBELOW", (0, 0), (-1, 0), 0.8, HexColor(ACCENT)),
          ("LINEBELOW", (0, 1), (-1, -1), 0.25, HexColor(RULE)), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
          ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    for i in range(2, len(data), 2):
        st.append(("BACKGROUND", (0, i), (-1, i), HexColor(BAND)))
    t.setStyle(TableStyle(st))
    return t


def _cells(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def flowables(md: str, width: float) -> list:
    """The Markdown subset as reportlab flowables."""
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, Spacer
    _fonts()
    S = _styles()
    out, lines, i = [], md.splitlines(), 0
    para = []

    def flush():
        if para:
            text = " ".join(x.strip() for x in para)
            style = S["note"] if text.startswith("*") and text.endswith("*") and not text.startswith("**") else S["body"]
            out.append(Paragraph(inline(text), style))
            para.clear()
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s:
            flush()
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\|?\s*:?-{3,}", lines[i + 1].strip()):
            flush()
            head = _cells(s)
            aligns = ["right" if c.strip().endswith(":") else "left" for c in _cells(lines[i + 1])]
            rows = [head]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(_cells(lines[i]))
                i += 1
            out += [_table(rows, aligns, S, width), Spacer(1, 5)]
            continue
        if s.startswith("# "):
            flush()
            out.append(Paragraph(inline(s[2:]), S["title"]))
        elif s.startswith("## "):
            flush()
            out += [Paragraph(inline(s[3:]), S["h2"]), HRFlowable(width="100%", thickness=0.6, color=HexColor(RULE),
                                                                   spaceBefore=0, spaceAfter=5)]
        elif s.startswith("### "):
            flush()
            out.append(KeepTogether([Paragraph(inline(s[4:]), S["h3"])]))
        elif s.startswith("> "):
            flush()
            q = [s[2:].rstrip()]
            while i + 1 < len(lines) and lines[i + 1].strip().startswith("> "):
                i += 1
                q.append(lines[i].strip()[2:].rstrip())
            out.append(Paragraph("<br/>".join(inline(x.rstrip()) for x in q), S["quote"]))
        elif s.startswith("- "):
            flush()
            out.append(Paragraph(inline(s[2:]), S["bullet"], bulletText="•"))
        elif s.startswith("Thursday") or s.startswith("Sources updated") or re.match(r"^[A-Z][a-z]+day, ", s):
            flush()
            out.append(Paragraph(inline(s), S["meta"]))
        else:
            para.append(s)
        i += 1
    flush()
    return out


def build(md: str, path, title: str, footer: str = "Research, not betting advice") -> Path:
    """Write the PDF; returns its path."""
    _fonts()
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate
    path = Path(path)
    margin = 0.7 * inch
    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=margin, rightMargin=margin, topMargin=margin,
                            bottomMargin=margin, title=title, author="NFL props research", subject=title)

    def on_page(canvas, d):
        canvas.saveState()
        canvas.setFont("Vera", 7.5)
        canvas.setFillColor(HexColor(MUTED))
        canvas.drawString(margin, 0.45 * inch, f"{title} · {footer}")
        canvas.drawRightString(letter[0] - margin, 0.45 * inch, f"Page {d.page}")
        canvas.restoreState()
    from functools import partial
    from reportlab.pdfgen.canvas import Canvas
    # the canvas starts in Vera (reportlab still lists Helvetica as its unused /F1 default resource)
    doc.build(flowables(md, letter[0] - 2 * margin), onFirstPage=on_page, onLaterPages=on_page,
              canvasmaker=partial(Canvas, initialFontName="Vera", initialFontSize=9))
    return path
