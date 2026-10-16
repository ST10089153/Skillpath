"""Apply the researcher's chosen visual template to the Part 3 report (v4 -> v5).

    python scripts/refine_exemplar.py && python scripts/finalise_exemplar.py && python scripts/style_exemplar.py

Modelled on Canva's "General Academic Research Doc" (green/blue/yellow, boldly simple): a green cover banner with an
image, large green headings with a green rule under each main section, coloured table header rows, large coloured
statistic callouts, and grey information callouts. The IIE format rules stay in force for running text (Arial 12 pt,
1.5 line spacing, justified, 2 cm margins), so the template's visual system is applied without changing body type.
"""

import os
import sys

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from refine_exemplar import body_word_count, set_text  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "exemplar", "REIT8419_Part3_SkillPath_EXEMPLAR_v4.docx")
OUT = os.path.join(ROOT, "docs", "exemplar", "REIT8419_Part3_SkillPath_EXEMPLAR_v5.docx")
COVER_IMG = os.path.join(ROOT, "docs", "exemplar", "figures", "cover_home.png")

GREEN, BLUE, YELLOW, RED = "286D58", "255C9A", "F2BC50", "E7494A"
INK, MID, GREY, RULE = "0E0F15", "525252", "EFEFEF", "D0D5D3"
YELLOW_TEXT = "B07D12"   # the template's yellow is too light for text on white; a deeper tone of it (4.5:1)


def rgb(h):
    return RGBColor.from_string(h)


def shade(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    for old in tcPr.findall(qn("w:shd")):
        tcPr.remove(old)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def borders(table, color=RULE, size=4, none=False):
    tblPr = table._tbl.tblPr
    for old in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(old)
    b = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{side}")
        e.set(qn("w:val"), "nil" if none else "single")
        if not none:
            e.set(qn("w:sz"), str(size))
            e.set(qn("w:color"), color)
        b.append(e)
    tblPr.append(b)


def para_rule(p, color=GREEN, size=8, where="bottom", space=4):
    pPr = p._p.get_or_add_pPr()
    bdr = pPr.find(qn("w:pBdr"))
    if bdr is None:
        bdr = OxmlElement("w:pBdr")
        pPr.append(bdr)
    e = OxmlElement(f"w:{where}")
    e.set(qn("w:val"), "single")
    e.set(qn("w:sz"), str(size))
    e.set(qn("w:space"), str(space))
    e.set(qn("w:color"), color)
    bdr.append(e)


def run(p, text, size=12, color=INK, bold=False, italic=False, font="Arial"):
    r = p.add_run(text)
    r.font.name, r.font.size, r.font.bold, r.font.italic = font, Pt(size), bold, italic
    r.font.color.rgb = rgb(color)
    rpr = r._r.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(a), font)
    return r


def cell_para(cell, first=True, align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=0, spacing=1.0):
    p = cell.paragraphs[0] if first else cell.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.space_before, pf.space_after, pf.line_spacing = Pt(before), Pt(after), spacing
    return p


def table_before(d, anchor, rows, cols, widths):
    t = d.add_table(rows=rows, cols=cols)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for row in t.rows:
        for c, w in zip(row.cells, widths):
            c.width = Cm(w)
    anchor._p.addprevious(t._tbl)
    return t


def callout(d, anchor, label, text):
    """Grey information box with an 'i' marker, as in the template."""
    t = table_before(d, anchor, 1, 2, [1.4, 15.6])
    borders(t, none=True)
    for c in t.rows[0].cells:
        shade(c, GREY)
    p = cell_para(t.rows[0].cells[0], align=WD_ALIGN_PARAGRAPH.CENTER, before=6)
    run(p, "ⓘ", size=20, color=MID, font="Segoe UI Symbol")
    p = cell_para(t.rows[0].cells[1], before=6, after=6)
    run(p, label + " ", size=10.5, color=INK, bold=True)
    run(p, text, size=10.5, color=INK)
    spacer = anchor.insert_paragraph_before("")
    spacer.paragraph_format.space_after = Pt(0)
    return t


def cover(d):
    paras = d.paragraphs
    toc = next(p for p in paras if p.text.strip() == "Table of Contents")
    old = paras[:paras.index(toc)]
    get = lambda start: next(p.text.strip() for p in old if p.text.strip().startswith(start))  # noqa: E731
    title = old[1].text.strip().rstrip(":")
    subtitle = old[2].text.strip()
    exemplar = get("Exemplar:")
    name, number = old[6].text.strip(), old[7].text.strip()
    supervisor, qual = get("Supervisor:"), get("Bachelor")
    words, date = get("Word count"), old[11].text.strip()
    ai = get("AI use disclosure")

    # cover image: the top of the app's home screen (the route strip), cropped to a portrait block
    src = Image.open(os.path.join(ROOT, "docs", "exemplar", "figures", "fig_home.png"))
    src.crop((0, 0, src.width, int(src.width * 1.32))).save(COVER_IMG)

    # 1. green banner with the module and part, image on the right
    t = table_before(d, toc, 1, 2, [11.2, 5.8])
    borders(t, none=True)
    left, right = t.rows[0].cells
    shade(left, GREEN)
    shade(right, GREEN)
    p = cell_para(left, before=14, after=10)
    run(p, "THE INDEPENDENT INSTITUTE OF EDUCATION", size=9, color="FFFFFF", bold=True)
    para_rule(p, "FFFFFF", 6, "bottom", 8)
    p = cell_para(left, first=False, before=18)
    run(p, "REIT8419 Research for ICT", size=13, color="FFFFFF")
    p = cell_para(left, first=False, before=4, spacing=0.95)
    run(p, "Part 3", size=40, color="FFFFFF")
    p = cell_para(left, first=False, before=0, after=26, spacing=1.0)
    run(p, "Data Collection, Analysis and Findings", size=18, color="FFFFFF")
    para_rule(p, "FFFFFF", 6, "bottom", 10)
    p = cell_para(right, align=WD_ALIGN_PARAGRAPH.RIGHT)
    p.add_run().add_picture(COVER_IMG, width=Cm(5.6))
    for c in (left, right):
        tcPr = c._tc.get_or_add_tcPr()
        mar = OxmlElement("w:tcMar")
        for side, v in (("left", "340" if c is left else "0"), ("right", "0"), ("top", "0"), ("bottom", "0")):
            e = OxmlElement(f"w:{side}")
            e.set(qn("w:w"), v)
            e.set(qn("w:type"), "dxa")
            mar.append(e)
        tcPr.append(mar)

    sp = toc.insert_paragraph_before("")
    sp.paragraph_format.space_after = Pt(6)

    # 2. title on the left, author block on the right
    t = table_before(d, toc, 1, 2, [11.6, 5.4])
    borders(t, none=True)
    p = cell_para(t.rows[0].cells[0], before=6, spacing=1.05)
    run(p, title, size=22, color=GREEN)
    p = cell_para(t.rows[0].cells[0], first=False, before=8, spacing=1.15)
    run(p, subtitle, size=12.5, color=MID)
    a = t.rows[0].cells[1]
    sup = supervisor.split(":", 1)
    lines = [(name, True), (number, False), (sup[0] + ":", False), (sup[1].strip(), False)]
    for i, (txt, bold) in enumerate(lines):
        p = cell_para(a, first=i == 0, align=WD_ALIGN_PARAGRAPH.RIGHT, before=8 if i == 0 else 2)
        run(p, txt, size=11, color=INK, bold=bold)

    p = toc.insert_paragraph_before("")
    para_rule(p, GREEN, 8, "bottom", 1)
    p.paragraph_format.space_after = Pt(10)

    # 3. details
    for txt in (qual, words, f"Date of submission: {date}"):
        p = toc.insert_paragraph_before("")
        p.paragraph_format.space_after, p.paragraph_format.line_spacing = Pt(2), 1.15
        run(p, txt, size=11, color=MID)
    toc.insert_paragraph_before("").paragraph_format.space_after = Pt(6)

    # 4. notes as grey callouts
    callout(d, toc, "Exemplar.", exemplar[len("Exemplar:"):].strip())
    callout(d, toc, "AI use disclosure.", ai[len("AI use disclosure:"):].strip())

    for p in old:
        p._p.getparent().remove(p._p)


def headings(d):
    sizes = {"1": 22, "2": 16, "3": 13}
    for p in d.paragraphs:
        if p.style is None or not p.style.name.lower().startswith("heading"):
            continue
        level = p.style.name.split()[-1]
        size = sizes.get(level, 13)
        for r in p.runs:
            r.font.size, r.font.bold = Pt(size), False
            r.font.color.rgb = rgb(GREEN)
        pf = p.paragraph_format
        pf.space_before = Pt({"1": 20, "2": 14, "3": 10}.get(level, 10))
        pf.space_after = Pt(8 if level == "1" else 4)
        pf.line_spacing = 1.15
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        if level == "1":
            para_rule(p, GREEN, 8, "bottom", 6)


def tables(d, skip):
    for t in d.tables:
        if t._tbl in skip:
            continue
        borders(t)
        head = t.rows[0]
        for c in head.cells:
            shade(c, GREEN)
            for p in c.paragraphs:
                for r in p.runs:
                    r.font.bold = True
                    r.font.color.rgb = rgb("FFFFFF")
        met = [i for i, c in enumerate(head.cells) if c.text.strip().lower().startswith("met")]
        for row in list(t.rows)[1:]:
            for i in met:
                for p in row.cells[i].paragraphs:
                    for r in p.runs:
                        if r.text.strip() == "Yes":
                            r.font.bold, r.font.color.rgb = True, rgb(GREEN)


def stat_strip(d):
    """Large coloured statistics under the evaluation summary, taken from Table 10 and Table 11."""
    t10 = next(t for t in d.tables if t.rows[0].cells[0].text.strip() == "Criterion" and len(t.columns) == 5
               and "Met" in t.rows[0].cells[4].text)
    met = sum(1 for r in list(t10.rows)[1:] if r.cells[4].text.strip() == "Yes")
    total = len(t10.rows) - 1
    t11 = next(t for t in d.tables if len(t.columns) > 3
               and any(r.cells[1].text.strip().lower() in ("in-field", "within field") for r in t.rows))
    goal = {r.cells[1].text.strip().lower(): (r.cells[2].text.strip(), r.cells[3].text.strip()) for r in t11.rows}
    infield = goal.get("in-field") or goal.get("within field")
    pivot = goal.get("pivot")
    anchor = next(p for p in d.paragraphs if p.text.startswith("Table 10 and Figure 6 present"))
    nxt = anchor._p.getnext()
    holder = d.add_paragraph()
    nxt.addprevious(holder._p)
    stats = [(f"{met}/{total}", BLUE, "thresholds met in controlled synthetic testing"),
             (infield[1], YELLOW_TEXT, f"of in-field profiles got an expected skill ({infield[0]})"),
             (pivot[1], RED, f"of career-pivot profiles got an expected skill ({pivot[0]})")]
    t = table_before(d, holder, 2, 3, [5.6, 5.6, 5.6])
    borders(t, none=True)
    for row in t.rows:  # gutter between the three columns
        for c in row.cells[:-1]:
            mar = OxmlElement("w:tcMar")
            e = OxmlElement("w:right")
            e.set(qn("w:w"), "340")
            e.set(qn("w:type"), "dxa")
            mar.append(e)
            c._tc.get_or_add_tcPr().append(mar)
    for j, (num, col, cap) in enumerate(stats):
        p = cell_para(t.rows[0].cells[j], before=4, after=4)
        run(p, num, size=30, color=col)
        para_rule(p, "BDBDBD", 8, "bottom", 6)
        p = cell_para(t.rows[1].cells[j], before=4, after=8, spacing=1.1)
        run(p, cap, size=10.5, color=INK)
    holder._p.getparent().remove(holder._p)
    return t


def footer(d):
    for s in d.sections:
        for p in s.footer.paragraphs:
            for r in p.runs:
                r.font.size, r.font.color.rgb = Pt(9), rgb(GREEN)


def main():
    d = docx.Document(SRC)
    headings(d)
    strip = stat_strip(d)
    before = {t._tbl for t in d.tables}
    cover(d)
    new = {t._tbl for t in d.tables} - before
    tables(d, skip=new | {strip._tbl})
    footer(d)
    n = body_word_count(d)
    for p in d.paragraphs + [p for t in d.tables for r in t.rows for c in r.cells for p in c.paragraphs]:
        if p.text.startswith("Word count (body"):
            for r in p.runs[1:]:
                r.text = ""
            p.runs[0].text = f"Word count (body, excluding cover page, reference list and annexures): {n:,} words"
    d.save(OUT)
    print(f"wrote {OUT}\nbody words: {n}")


if __name__ == "__main__":
    main()
