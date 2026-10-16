"""Finalise the Part 3 exemplar (v3 -> v4): fill the remaining placeholders from the project's own records and the
researcher's ethics documents.

    python scripts/refine_exemplar.py      # builds v3
    python scripts/finalise_exemplar.py    # builds v4 from v3

Sources for every value filled here:
  - submission date: the researcher (16 October 2026)
  - ethics: Annexure Q signed 30 June 2026, "Accepted with no conditions"; ethics clearance letter dated
    9 October 2026, reference EMCSREC/EMGPMD/025/2026, expiry 9 October 2027 (researcher's documents)
  - thresholds: set in the research proposal, approved with the ethics clearance on 9 October 2026
  - acceptable recommendations fixed on 10 October 2026, before testing (researcher)
  - profile counts, test-script values and script hashes: profiles_ready.csv, run_synthetic_tests.py and the
    manifest of runs/EVAL20261016-130628-final
  - search log: only what the report already documents (databases from Annexure Q, the 12 May - 20 June 2026
    window from Section 3.1, filters from Table 2, totals from the PRISMA flow); no per-database counts are invented
  - codebook rows: codes restated from the report's own Table 7 directives and Table B5 findings
Left for the researcher: the AI use disclosure (cover page and Annexure A).
"""

import csv
import json
import os
import sys

import docx
from docx.shared import Pt
from pypdf import PdfReader

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from refine_exemplar import apply_format, body_word_count, set_text  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "exemplar", "REIT8419_Part3_SkillPath_EXEMPLAR_v3.docx")
OUT = os.path.join(ROOT, "docs", "exemplar", "REIT8419_Part3_SkillPath_EXEMPLAR_v4.docx")
RUN = os.path.join(ROOT, "runs", "EVAL20261016-130628-final")
CV = os.path.join(ROOT, "profiles", "cvs", "EXAMPLE_CV_SP09.pdf")

ETHICS_REF = "EMCSREC/EMGPMD/025/2026"


def para(d, startswith):
    return next(p for p in d.paragraphs if p.text.strip().startswith(startswith))


def table_after(d, caption_start):
    """The first table that follows the paragraph starting with caption_start."""
    body = list(d.element.body.iterchildren())
    k = next(i for i, e in enumerate(body) if e.tag.endswith('}p') and e.xpath('string(.)').strip().startswith(caption_start))
    after = [e for e in body[k:] if e.tag.endswith('}tbl')]
    before = [e for e in body[:k] if e.tag.endswith('}tbl')]
    # captions sit above most tables, but below a few (e.g. Table G1): take the nearer one
    nxt = body.index(after[0]) - k if after else 10**9
    prv = k - body.index(before[-1]) if before else 10**9
    tbl = after[0] if nxt <= prv else before[-1]
    return next(t for t in d.tables if t._tbl is tbl)


def set_cell(cell, text):
    set_text(cell.paragraphs[0], text)
    for p in cell.paragraphs[1:]:
        p._p.getparent().remove(p._p)


def new_table(d, caption_par, rows, font=9):
    """A table placed directly above its caption paragraph (the report captions tables underneath)."""
    t = d.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = d.tables[0].style
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = t.rows[i].cells[j]
            c.text = v
            for r in c.paragraphs[0].runs:
                r.font.size = Pt(font)
                r.bold = i == 0
    caption_par._p.addprevious(t._tbl)
    return t


def main():
    d = docx.Document(SRC)

    # 1. Cover: submission date
    set_text(para(d, "[Date of submission]"), "16 October 2026")

    # 2. Ethics in Section 3.3.3
    p = para(d, "Annexure Q was accepted by the supervisor")
    tail = p.text[p.text.index("With no participants"):]
    set_text(p, "Annexure Q, signed on 30 June 2026, was accepted by the supervisor without conditions, and the proposal "
                f"and ethics clearance were approved on 9 October 2026 (reference {ETHICS_REF}, valid until 9 October 2027; "
                "Annexure F). " + tail)

    # 3. Annexure G concept document
    g = table_after(d, "Table G1")
    for row in g.rows:
        k, v = row.cells[0].text, row.cells[1].text
        if "[Align with Annexure Q" in v:
            set_cell(row.cells[1], v[:v.index("[Align with Annexure Q")].rstrip())
        if "[24]" in v or "[4]" in v:
            set_cell(row.cells[1], v.replace("[24]", "24").replace("[4]", "4"))
        if k.startswith("Ethics"):
            set_cell(row.cells[1], "Annexure Q signed 30 June 2026 and accepted by the supervisor without conditions; "
                                   f"ethics clearance granted 9 October 2026 (reference {ETHICS_REF}). No human participants, "
                                   "no personal data, fictitious names on all CVs; data managed per the DMP.")

    # 4. B2 search log: one row per pillar, from Table 1 (databases, records) and Section 3.1 (search window)
    b2 = table_after(d, "B2. Search log")
    t1 = table_after(d, "Table 1:")
    pillars = [[c.text.strip() for c in r.cells] for r in list(t1.rows)[1:] if r.cells[0].text[:1].isdigit()]
    filters = "2015 to 2026 (or seminal framework statement); English; peer-reviewed or recognised institutional (Table 2)"
    rows_b2 = [["12 May to 20 June 2026", dbs.replace(';', ','), name, filters, recs] for name, dbs, recs, _ in pillars]
    rows_b2.append(["", "", "Total", "Exports merged in Zotero; 312 duplicates removed by DOI and title",
                    f"{sum(int(r[4].replace(',', '')) for r in rows_b2):,} (972 after de-duplication)"])
    while len(b2.rows) - 1 < len(rows_b2):
        b2.add_row()
    for r, vals in zip(list(b2.rows)[1:], rows_b2):
        for c, v in zip(r.cells, vals):
            set_cell(c, v)

    # 5. B4 codebook: worked rows restated from Table 7 and Table B5
    b4 = table_after(d, "B4. Codebook template")
    rows = [
        ["DIR-FIRST", "Learners need a clear target before content", "Indecision or lack of direction precedes disengagement",
         "Direction discussed only as school subject choice", "Career decision-making difficulty is a primary determinant of "
         "indecision (Priyashantha, Dahanayake and Maduwanthi, 2023)", "Direction before content (DD1)"],
        ["ADJ-LEAP", "Proximity of current skills to a target role eases the move", "Skill similarity or adjacency predicts transition",
         "Similarity used only for content tagging", "Workers whose competencies sit close to new roles transition fastest "
         "(Autor et al., 2024)", "Smallest leap, highest return (DD2)"],
        ["CONF-GAP", "Skill acquired but confidence to apply it absent", "Low self-efficacy linked to employability",
         "Confidence measured only as course satisfaction", "Low self-efficacy is an employability barrier; a development centre "
         "improved it (White, Becker and Du Plessis, 2021)", "Visible competence growth (DD5)"],
        ["PROXY-METRIC", "Systems reward participation rather than skill gain", "Outcome measured as clicks, time or completion only",
         "Studies that also measure skill gain", "Adaptive systems often optimise participation proxies rather than skill gains "
         "(Hariyanto, Kristianingsih and Maharani, 2025)", "Progression over participation (DD10)"],
    ]
    while len(b4.rows) - 1 < len(rows):
        b4.add_row()
    for r, vals in zip(list(b4.rows)[1:], rows):
        for c, v in zip(r.cells, vals):
            set_cell(c, v)
    b4_note = para(d, "B5. Characteristics of principal included studies")
    b4_note.insert_paragraph_before("Worked rows from the codebook (68 codes in total, kept in the Excel codebook); each row "
                                    "traces a code to a source and to the theme and directive it fed.",
                                    style=para(d, "The principal studies behind").style)

    # 6. C1 specification fields
    profiles = list(csv.DictReader(open(os.path.join(RUN, "profiles_ready.csv"), encoding="utf-8")))
    c1 = table_after(d, "Table C1")
    for row in c1.rows:
        v = row.cells[1].text
        if "SP[28]" in v:
            set_cell(row.cells[1], f"SP01 to SP{len(profiles):02d}")
        elif "[Commerce" in v:
            set_cell(row.cells[1], "Commerce / Humanities / Natural Sciences / IT (edge cases: mixed)")
        elif "fixed before testing on [date]" in v:
            set_cell(row.cells[1], "Skills SkillPath ought to recommend, fixed on 10 October 2026, before testing")

    # 7. C2 completed specification sheets (worked-example profiles, watermarked)
    p = para(d, "[Insert the completed specification sheet")
    set_text(p, f"Table C2: Completed specification sheets ({len(profiles)} worked-example profiles; every row is watermarked "
                "'EXAMPLE - NOT STUDY DATA' in the source file profiles_ready.csv)")
    data = [["ID", "Level / discipline / goal", "Current skills", "Target occupation", "Acceptable recommendations", "Edge"]]
    for r in profiles:
        data.append([r["profile_id"], f"{r['competency_level']} / {r['discipline']} / {r['employment_goal']}",
                     r["current_skills"].replace(";", ","), r["target_occupation"] or "-",
                     (r["acceptable_recommendations"] or "-").replace(";", ","), r["is_edge_case"]])
    new_table(d, p, data, font=8)

    # 8. C3 sample CV
    p = para(d, "[Insert one complete fabricated CV")
    cv = "\n".join(pg.extract_text() for pg in PdfReader(CV).pages).strip()
    set_text(p, "Table C3: Sample fabricated CV, SP09 (EXAMPLE_CV_SP09.pdf). Synthetic test profile created by the "
                "researcher. Not a real person.")
    t = new_table(d, p, [["Synthetic test profile created by the researcher. Not a real person."], [cv]], font=9)
    t.rows[0].cells[0].paragraphs[0].runs[0].bold = True

    # 9. Annexure D test scripts
    p = para(d, "Test scripts: Baseline")
    set_text(p, p.text.replace("[six]", "six").replace("[four]", "four"))

    # 10. Annexure E thresholds and script versions
    man = json.load(open(os.path.join(RUN, "manifest.json"), encoding="utf-8"))
    h = man["sha256"]
    p = para(d, "E1. Thresholds as approved on")
    set_text(p, "E1. The acceptance thresholds are those set in the research proposal (Table 6), approved with the "
                f"ethics clearance on 9 October 2026 (reference {ETHICS_REF}). E2 and E3. The scripts were run unmodified on "
                f"16 October 2026 at build v1.0-eval (commit {man['git_commit']}); their full source is in the replication "
                f"package (runs/{man['run_id']}/code/). SHA-256: run_synthetic_tests.py {h['code/run_synthetic_tests.py']}; "
                f"analyse_outputs.py {h['code/analyse_outputs.py']}; prepare_profiles.py {h['code/prepare_profiles.py']}; "
                f"skillpath_adapter.py (connection to SkillPath's engine) {h['code/skillpath_adapter.py']}.")

    # 11. Annexure F ethics documents
    p = para(d, "[Insert: the signed Annexure Q")
    set_text(p, "F1. Annexure Q research ethics application, signed by the researcher on 30 June 2026 and accepted by the "
                "supervisor with no conditions (attached). F2. Ethics clearance letter, 9 October 2026, reference "
                f"{ETHICS_REF}, valid until 9 October 2027, signed by Dr T Muchenje (Postgraduate Academic Lead) and "
                "Mr H Mpofu (Head of Computer Science) (attached). F3. Data Management Plan, DMP ID "
                "https://doi.org/10.48321/D176484D69.")

    apply_format(d)
    n = body_word_count(d)
    for q in d.paragraphs:
        if q.text.startswith("Word count (body"):
            set_text(q, f"Word count (body, excluding cover page, reference list and annexures): {n:,} words")
    d.save(OUT)
    print(f"wrote {OUT}\nbody words: {n}")
    left = [q.text[:80] for q in d.paragraphs if "[Insert" in q.text or "[date" in q.text.lower() or "[State" in q.text]
    print("placeholders left:", left)


if __name__ == "__main__":
    main()
