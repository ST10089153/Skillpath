"""SQ4 and the updated concept document (Annexure G), applied by finalise_exemplar.py.

Sources, all the researcher's own documents:
  - the Part 1 concept document (REIT8419_ConceptDoc_1.2.docx; submitted and marked 31 March 2026) and the
    supervisor's comments on it
  - the approved research proposal (REIT8419_Prop_ST10089153), for the title, RQ1, SQ1, SQ2 and objectives
  - this report, for the revised SQ3, the evaluation design, findings and ethics
The supervisor asked for one research question per objective, so SQ4 is added for objective 4 (researcher's
decision, 16 October 2026). Only works in the report's reference list are cited here.
"""

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

SQ4 = ("SQ4 (added): What do SkillPath's own operational records show about how its design supports engagement and "
       "recommendation relevance, with income visible and hidden?")


def _para(d, start):
    return next(p for p in d.paragraphs if p.text.strip().startswith(start))


def _set(p, text):
    if p.runs:
        p.runs[0].text = text
        for r in p.runs[1:]:
            r.text = ""
    else:
        p.add_run(text)


def add_sq4(d):
    # make room for SQ4 within the word limit: a shorter roadmap sentence with the same content
    p = _para(d, "This document reports what was actually done")
    old = "Section 2 defines the populations and sampling, Sections 3 and 4 describe data collection and analysis, "           "Section 5 presents the findings, Section 6 interprets them and Section 7 answers the research questions."
    assert old in p.text
    _set(p, p.text.replace(old, "Sections 2 to 4 cover sampling, data collection and analysis; Sections 5 to 7 present, "
                                 "interpret and apply the findings."))
    # Section 1: introduce SQ4 after the revised SQ3
    p = _para(d, "SQ1 asked which frameworks")
    _set(p, "SQ1 asked which frameworks and findings were most relevant for design, and SQ2 how SkillPath could apply "
            "the derived principles. SQ3 was revised to match the approved evaluation design, since engagement needs "
            "real users, and SQ4 was added so that each objective has its own question:")
    sq3 = _para(d, "SQ3 (revised):")
    import copy
    el = copy.deepcopy(sq3._p)                  # same indent, spacing and italics as the SQ3 block
    sq3._p.addnext(el)
    new = next(p for p in d.paragraphs if p._p is el)
    _set(new, SQ4)

    # Table 4: a row for SQ4, before RQ1
    t4 = next(t for t in d.tables if t.rows[0].cells[0].text.strip() == "Question")
    rq1 = next(r for r in t4.rows if r.cells[0].text.strip() == "RQ1")
    sq3row = next(r for r in t4.rows if r.cells[0].text.strip() == "SQ3")
    row = copy.deepcopy(sq3row._tr)
    rq1._tr.addprevious(row)
    cells = [c for c in t4.rows if c._tr is row][0].cells
    for c, v in zip(cells, ["SQ4", "SkillPath's event log for 392 simulated users; paired outputs of both versions",
                            "Persona simulation scripts and SkillPath's event export (Section 3.3.4)",
                            "Phase 3: 16 October 2026"]):
        _set(c.paragraphs[0], v)

    # Table 14: pair each objective with its question
    t14 = next(t for t in d.tables if t.rows[0].cells[0].text.strip() == "Objective")
    for r in list(t14.rows)[1:]:
        k = r.cells[0].text.strip()[:1]
        if k in "1234" and "(SQ" not in r.cells[0].text:
            _set(r.cells[0].paragraphs[0], r.cells[0].text.strip() + f" (SQ{k})")

    # Section 7.2: answer SQ4
    sq3a = _para(d, "SQ3 was answered by")
    ans = sq3a.insert_paragraph_before(
        "SQ4 was answered by Tables 12 and 13a. Showing or hiding income changed no recommendation, and for simulated "
        "users SkillPath met every operational threshold and exposed a nudge fault that was then fixed. Because "
        "behaviour was scripted, this shows that the design supports and records engagement, not that graduates "
        "engage, which needs real users (Section 6.7).", style=sq3a.style)
    sq3a._p.addnext(ans._p)
    ans.paragraph_format.alignment = sq3a.paragraph_format.alignment


def _shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def rebuild_annexure_g(d, ethics_ref):
    old = next(t for t in d.tables if t.rows[0].cells[0].text.strip() == "Element"
               and any(r.cells[0].text.strip() == "Key findings" for r in t.rows))
    keep = {r.cells[0].text.strip(): r.cells[1].text.strip() for r in old.rows}
    cap = _para(d, "Table G1:")
    style = old.style

    rq = next(p.text.strip() for p in d.paragraphs if p.text.strip().startswith("RQ1:"))
    sq3 = next(p.text.strip() for p in d.paragraphs if p.text.strip().startswith("SQ3 (revised):"))
    U = " (UPDATED)"
    sections = [
        ("Project details", [
            ("Name", "Charne Janse van Rensburg"),
            ("Student number", "ST10089153"),
            ("Supervisor", "Dr. Rodney Mushininga"),
            ("Date" + U, "16/10/2026 (Part 1 concept document: 31/03/2026)"),
        ]),
        ("Proposed title", [
            ("Title" + U, "Developing a Personalised AI Learning Recommender for Unemployed Graduates: A Design Science "
                          "Approach to Direction Clarity and Employability Confidence. Part 1 title: AI-Driven "
                          "Personalised Skill Gap Recommender for Graduate Employability."),
        ]),
        ("Research details", [
            ("Problem statement" + U,
             "Unemployed graduates in digitally disrupted labour markets face three linked problems that no consumer "
             "platform addresses together: they do not know which skill to develop first, given their profile and "
             "goals (Priyashantha, Dahanayake and Maduwanthi, 2023); finishing a course does not by itself give them "
             "the confidence to use the skill (White, Becker and Du Plessis, 2021); and learning platforms built for "
             "employers do not reach them. In South Africa, youth unemployment stood at 46.1% in early 2025 "
             "(Statistics South Africa, 2025), and skill inequalities between faculties shape who is recruited "
             "(Chigbu and Nekhwevha, 2022)."),
            ("Purpose statement" + U,
             "The purpose of this study is to identify the design requirements for an AI-powered mobile recommender "
             "that gives unemployed graduates a clear next skill and visible progress towards it. It does so by "
             "designing, developing and evaluating SkillPath as a Design Science Research artefact (Hevner et al., "
             "2004), evaluated through controlled synthetic testing against utility, quality and efficacy."),
            ("Research questions" + U,
             f"{rq}\nSQ1: Which theoretical frameworks and empirical findings from adaptive learning, AI literacy, "
             "behavioural design, career development and labour market research are most relevant for designing a "
             "skill recommender for informal learners outside formal education structures?\nSQ2: How can SkillPath be "
             "developed to apply derived design principles through personalised skill profiling, adaptive "
             "micro-learning, skill adjacency prioritisation and progression-based engagement architecture?\n"
             f"{sq3}\n{SQ4}"),
            ("Objectives" + U,
             "This qualitative study set four objectives, each answered by one sub-question:\n"
             "1. (SQ1) Conduct a systematic literature review that derives design directives from five pillars: "
             "adaptive learning, AI literacy, behavioural design, career development, and labour market demand.\n"
             "2. (SQ2) Develop SkillPath by applying these directives, focusing on direction clarity, skill adjacency, "
             "adaptive micro-learning and progression-based confidence building.\n"
             "3. (SQ3) Evaluate SkillPath against the Design Science Research criteria of utility, quality and "
             "efficacy (Hevner et al., 2004) through controlled synthetic testing.\n"
             "4. (SQ4) Analyse SkillPath's operational records, including a paired income-visible and income-neutral "
             "comparison, for engagement support and recommendation relevance."),
            ("Research rationale" + U,
             "Academically, no evaluated artefact combines direction-first recommendation, skill adjacency, adaptive "
             "micro-learning and confidence-building progression for graduates learning outside formal structures, "
             "where adaptive learning is known to weaken (Du Plooy, Casteleijn and Franzsen, 2024). Practically, a "
             "free mobile tool can reach graduates whom employer-funded learning platforms do not."),
        ]),
        ("Literature overview", [
            ("Key theories" + U,
             "Zone of Proximal Development (Vygotsky, 1978): difficulty is set to the gap between current and next "
             "achievable ability, which shapes the adaptive micro-learning layer.\nSelf-Determination Theory (Deci and "
             "Ryan, 2000): autonomy, competence and relatedness justify learner control, visible progress and income "
             "shown as information rather than as an incentive.\nFogg Behaviour Model (Fogg, 2003): motivation, ability "
             "and a trigger must coincide, which governs when nudges are sent.\nDesign Science Research (Hevner et al., "
             "2004): the build-and-evaluate strategy and its criteria of utility, quality and efficacy."),
            ("Seminal authors and sources" + U,
             "Hevner et al. (2004); Vygotsky (1978); Deci and Ryan (2000); Fogg (2003); added since Part 1: Bandura "
             "(1997) on self-efficacy and Braun and Clarke (2006) for the thematic analysis."),
            ("Literature review themes" + U,
             "Five pillars (four in Part 1): (1) adaptive and personalised learning; (2) AI literacy as an "
             "employability competency; (3) behavioural design and persuasive technology; (4) career development and "
             "direction clarity, added because indecision and low self-efficacy proved central; (5) labour market "
             "demand and skill adjacency."),
            ("Sources" + U,
             "The final corpus holds 46 sources (Figure 1); Annexure B5 lists the principal studies, and every source "
             "cited in this report is in the Reference List."),
            ("Key concepts" + U,
             "Direction clarity; self-efficacy (Bandura, 1997); skill gap analysis; skill adjacency; personalised "
             "adaptive learning; micro-learning; Zone of Proximal Development; Self-Determination Theory; persuasive "
             "technology; AI literacy; income visibility (replacing 'income-outcome mapping'); Design Science Research "
             "artefact; controlled synthetic testing as artificial evaluation (Venable, Pries-Heje and Baskerville, "
             "2016)."),
        ]),
        ("Research approach", [
            ("Approach and design" + U,
             "Interpretivist philosophy (as ticked on Annexure Q); qualitative approach; Design Science Research "
             "strategy in three phases (derive directives, build SkillPath, evaluate it); cross-sectional design; "
             "abductive reasoning; artificial evaluation through controlled synthetic testing rather than operational "
             "data from live users."),
        ]),
        ("Research plan", [
            ("Population" + U, keep.get("Population (UPDATED)", "")),
            ("Sampling" + U,
             "Phase 1: purposive, criteria-based selection of sources from 2015 to 2026 (2018 to 2025 in Part 1) plus "
             "seminal works, reported with PRISMA 2020 (Page et al., 2021). Phase 3: no sampling of people; a "
             "purposive full-factorial design of 24 core profiles (competency x discipline x goal) plus 4 edge cases, "
             "each run under both logic versions."),
            ("Data collection" + U,
             "Literature: systematic search of Google Scholar, IEEE Xplore, Scopus and PubMed (12 May to 20 June "
             "2026). Development: design directive traceability matrix and decision log. Evaluation: fabricated CVs "
             "and specification sheets fed into the developed recommender, with every output logged by test script; "
             "operational records from 392 scripted simulated users."),
            ("Data analysis" + U,
             "Thematic analysis (Braun and Clarke, 2006) producing ten design directives; nine utility, quality and "
             "efficacy metrics against thresholds fixed before testing; a paired income-visibility comparison; "
             "qualitative coding of mismatches; operational measures for simulated users."),
        ]),
        ("Ethical considerations and limitations", [
            ("Ethics" + U,
             f"Annexure Q signed 30 June 2026 and accepted without conditions; ethics clearance granted 9 October 2026 "
             f"(reference {ethics_ref}). No human participants; all CVs fictitious. SkillPath stores only an anonymous "
             "ID, keeps data locally, uses no trackers and lets users delete their data (POPIA). Recommendations are "
             "disclosed as AI-generated and not career advice; data sources are shown and income is labelled as an "
             "estimate to limit bias."),
            ("Limitations" + U,
             "Controlled synthetic testing shows what SkillPath does, not how graduates respond: self-efficacy, "
             "engagement and trust need real users. The researcher built the artefact, the profiles and the acceptable "
             "sets. Labour-market data are fixed snapshots, the South African context limits generalisability, and a "
             "cross-sectional design cannot show long-term employment outcomes."),
        ]),
        ("Progress at Part 3", [
            ("Key findings", keep.get("Key findings", "")),
            ("Contribution", keep.get("Contribution", "")),
        ]),
        ("Reference list", [
            ("References", "See the Reference List of this report."),
        ]),
    ]

    n_rows = 1 + sum(1 + len(rows) for _, rows in sections)
    t = d.add_table(rows=n_rows, cols=2)
    t.style = style
    i = 0

    def fill(cell, text, bold=False, size=10):
        cell.text = ""
        lines = text.split("\n")
        for k, line in enumerate(lines):
            p = cell.paragraphs[0] if k == 0 else cell.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(3 if k < len(lines) - 1 else 0)
            r = p.add_run(line)
            r.bold, r.font.size = bold, Pt(size)

    fill(t.rows[0].cells[0], "Element", True)
    fill(t.rows[0].cells[1], "Updated content (changes since the Part 1 concept document marked UPDATED)", True)
    i = 1
    for name, rows in sections:
        a, b = t.rows[i].cells
        merged = a.merge(b)
        fill(merged, name, True, 10.5)
        _shade(merged, "D9E7E1")
        i += 1
        for k, v in rows:
            fill(t.rows[i].cells[0], k, True)
            fill(t.rows[i].cells[1], v)
            i += 1
    for row in t.rows:
        for c, w in zip(row.cells, (Cm(4.3), Cm(12.7))):
            c.width = w
    old._tbl.addprevious(t._tbl)
    old._tbl.getparent().remove(old._tbl)
    _set(cap, "Table G1: Updated concept document, following the sections of the IIE concept document template")

    # intro line under the Annexure G heading
    head = [p for p in d.paragraphs if p.text.strip() == "Annexure G: Updated Concept Document"][-1]  # not the TOC line
    intro = head.insert_paragraph_before("")
    head._p.addnext(intro._p)
    intro.add_run("The concept document submitted in Part 1 (31 March 2026), updated to the study as completed. Rows "
                  "marked UPDATED changed since Part 1; Table G2 shows how the supervisor's feedback was addressed.")

    # Table G2: supervisor feedback and response
    feedback = [
        ("Feedback on the Part 1 concept document", "How it was addressed"),
        ("Title: 'put a verb, and make it recommender system'",
         "The title now opens with a verb ('Developing') and names the system a recommender."),
        ("Problem statement: 'is that a comma or semi colon and why'",
         "Rewritten as three problems separated by semicolons, because the list items themselves contain commas."),
        ("Purpose statement: 'start with the purpose not the objective'",
         "The purpose statement now opens with 'The purpose of this study is…'."),
        ("Objectives: 'If there are 4 objectives, there must be 4 research questions directly related to the objectives'",
         "SQ4 was added, and each objective is now paired with one sub-question (Table 14)."),
        ("Data collection: 'are we not collecting our data from the simulations using the developed recommender'",
         "Yes: evaluation data now comes from controlled synthetic testing of the developed recommender and from "
         "scripted simulated users (Sections 3.3 and 5.3 to 5.8)."),
        ("'Take note of the highlighted areas and paraphrase where you can'",
         "Every section was rewritten for this update rather than carried over."),
        ("'remove previous comments when submitting final document'",
         "No comments from the marked Part 1 document are carried into this report."),
    ]
    g2 = d.add_table(rows=len(feedback), cols=2)
    g2.style = style
    for row in g2.rows:
        for c, w in zip(row.cells, (Cm(7.0), Cm(10.0))):
            c.width = w
    for r, (a, b) in zip(g2.rows, feedback):
        fill(r.cells[0], a, r is g2.rows[0])
        fill(r.cells[1], b, r is g2.rows[0])
    g2cap = cap.insert_paragraph_before("Table G2: Supervisor feedback on the concept document and how it was addressed",
                                        style=cap.style)
    cap._p.addnext(g2cap._p)
    g2cap._p.addprevious(g2._tbl)
