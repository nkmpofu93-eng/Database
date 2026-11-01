#!/usr/bin/env python3
"""Render a CV or cover letter written in simple Markdown to a PDF that
matches the Barclays CV layout (Calibri, navy underlined headings).

Usage: python3 tools/build-pdf.py input.md [output.pdf]

Input format:
  # Full Name                      name, centred
  contact line                     centred lines until the first blank line
  _italic line_                    or heading; underscores make a line italic
  ## SECTION                       navy heading with a rule under it
  ### Left text || Right text      bold left, italic right (job or degree)
  Left text || Right text          plain left, bold right (e.g. university || grade)
  - bullet text                    bullet point
  any other text                   paragraph (justified)
  **bold** and _italic_ work inline. Use "---" alone on a line for a page break.
"""
import os
import re
import sys

from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (HRFlowable, ListFlowable, ListItem, PageBreak,
                                Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

NAVY = Color(0.122, 0.22, 0.392)
GREY = Color(0.333, 0.333, 0.333)
TEXT = Color(0.133, 0.133, 0.133)

FONT_DIRS = ["/usr/share/fonts/truetype/crosextra", "/usr/share/fonts/truetype/msttcorefonts",
             "/Library/Fonts", "/System/Library/Fonts/Supplemental", "C:/Windows/Fonts",
             os.path.expanduser("~/Library/Fonts")]
FONT_FILES = {
    "Calibri": ("calibri.ttf", "calibrib.ttf", "calibrii.ttf", "calibriz.ttf"),
    "Carlito": ("Carlito-Regular.ttf", "Carlito-Bold.ttf", "Carlito-Italic.ttf", "Carlito-BoldItalic.ttf"),
}


def register_fonts():
    """Use Calibri, else Carlito (same metrics), else Helvetica."""
    for family, files in FONT_FILES.items():
        for d in FONT_DIRS:
            paths = [os.path.join(d, f) for f in files]
            if all(os.path.exists(p) for p in paths):
                names = [family, family + "-Bold", family + "-Italic", family + "-BoldItalic"]
                for n, p in zip(names, paths):
                    pdfmetrics.registerFont(TTFont(n, p))
                pdfmetrics.registerFontFamily(family, normal=names[0], bold=names[1],
                                              italic=names[2], boldItalic=names[3])
                return names
    return ["Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique"]


REG, BOLD, ITAL, _ = register_fonts()


def style(name, **kw):
    base = dict(fontName=REG, fontSize=10, leading=12.5, textColor=TEXT)
    base.update(kw)
    return ParagraphStyle(name, **base)


S = {
    "name": style("name", fontName=BOLD, fontSize=20, leading=24, textColor=NAVY, alignment=TA_CENTER),
    "contact": style("contact", fontSize=9.5, leading=12, textColor=GREY, alignment=TA_CENTER),
    "heading": style("heading", fontName=BOLD, fontSize=12, leading=14, textColor=NAVY, spaceBefore=8),
    "body": style("body", alignment=TA_JUSTIFY, spaceAfter=6),
    "bullet": style("bullet", leading=12.5),
    "left": style("left", fontSize=10.5, leading=13),
    "right": style("right", fontSize=9.5, leading=13, alignment=2),
}


def inline(text):
    """Escape XML and convert **bold** and _italic_ to reportlab markup."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w/])_(.+?)_(?![\w/])", r"<i>\1</i>", text)
    return text


def row(left, right, left_style, right_style):
    t = Table([[Paragraph(left, left_style), Paragraph(right, right_style)]],
              colWidths=["80%", "20%"])
    t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                           ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                           ("VALIGN", (0, 0), (-1, -1), "BOTTOM")]))
    return t


def build(md_path, pdf_path):
    with open(md_path, encoding="utf-8") as f:
        lines = [l.rstrip() for l in f]

    story, bullets, in_header, header_done = [], [], True, False

    def flush_bullets():
        if bullets:
            story.append(ListFlowable(
                [ListItem(Paragraph(b, S["bullet"]), leftIndent=11, value="\u25aa") for b in bullets],
                bulletType="bullet", start="\u25aa", leftIndent=11, bulletFontSize=7,
                bulletColor=NAVY, spaceAfter=3))
            bullets.clear()

    for line in lines:
        s = line.strip()
        if not s:
            flush_bullets()
            if story and in_header:
                in_header, header_done = False, True
            continue
        if s.startswith("- "):
            bullets.append(inline(s[2:]))
            continue
        flush_bullets()
        if header_done:
            # A letter has no section heading under the contact lines, so draw a rule there.
            if not s.startswith("## "):
                story.append(HRFlowable(width="100%", thickness=1.2, color=NAVY, spaceBefore=4, spaceAfter=10))
            header_done = False
        if s == "---":
            story.append(PageBreak())
        elif s.startswith("# "):
            story.append(Paragraph(inline(s[2:]), S["name"]))
            story.append(Spacer(1, 2))
        elif s.startswith("## "):
            in_header, header_done = False, False
            story.append(Paragraph(inline(s[3:]).upper(), S["heading"]))
            story.append(HRFlowable(width="100%", thickness=1.2, color=NAVY, spaceBefore=1, spaceAfter=5))
        elif s.startswith("### "):
            left, _, right = s[4:].partition("||")
            story.append(Spacer(1, 3))
            story.append(row(f"<b>{inline(left.strip())}</b>", f"<i>{inline(right.strip())}</i>",
                             S["left"], S["right"]))
            story.append(Spacer(1, 1))
        elif "||" in s:
            left, _, right = s.partition("||")
            story.append(row(inline(left.strip()), f"<b>{inline(right.strip())}</b>",
                             S["left"], style("r2", fontSize=10, leading=13, alignment=2)))
        elif in_header:
            story.append(Paragraph(inline(s), S["contact"]))
        else:
            story.append(Paragraph(inline(s), S["body"]))
    flush_bullets()

    doc = SimpleDocTemplate(pdf_path, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm,
                            title=os.path.splitext(os.path.basename(pdf_path))[0],
                            author="Nkosilathi S.H. Mpofu")
    doc.build(story)


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) == 3 else os.path.splitext(src)[0] + ".pdf"
    build(src, out)
    print(out)
