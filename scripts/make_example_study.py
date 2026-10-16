"""Generate a complete WORKED EXAMPLE of the Phase 3 study inputs for teaching.

    python scripts/make_example_study.py   -> samples/example_study/

EXAMPLE - NOT STUDY DATA. Written by the AI assistant at the request of the user (a teacher) as an exemplar
for students. Every profile row and every CV is watermarked. It is kept apart from the researcher's own
profiles.csv and profile builder, and run_evaluation.py never uses it unless pointed at it explicitly.

Contents
  profiles_EXAMPLE.csv           28 profiles (24 core = 3 levels x 4 disciplines x 2 goals, + 4 edge cases),
                                 skills named exactly as in SkillPath's vocabulary, acceptable sets left empty
  cvs/EXAMPLE_CV_SPxx.pdf|docx   one fictional CV per profile (SA graduate format: Wits CCDU / UNISA DCCD)
  cvs/expected_skills.csv        the skills each CV was written to show (for scripts/cv_accuracy.py)
"""

import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cv_writers import write_docx, write_pdf  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "samples", "example_study")
MARK = "EXAMPLE - NOT STUDY DATA"

# One realistic CV bullet per skill (fictional organisations); wording mirrors SA graduate CVs and job adverts.
BULLET = {
    "Bookkeeping & journal entries": "Captured invoices and journal entries in Sage Pastel and reconciled monthly bank statements",
    "Microsoft Office & spreadsheets": "Built Excel spreadsheets with VLOOKUP and pivot tables to track monthly figures",
    "Market research": "Designed a customer survey, collected 300 responses and summarised the market research findings",
    "Tax & VAT": "Prepared VAT returns and assisted with individual income tax returns on SARS eFiling",
    "Payroll": "Processed monthly payroll for 45 staff, including PAYE and UIF deductions",
    "Data analysis & statistics": "Analysed data with descriptive statistics and simple regression to explain trends",
    "Financial analysis & risk": "Calculated financial ratios and wrote a short risk analysis of a company's annual results",
    "Data visualisation & dashboards": "Built Power BI dashboards that management used in weekly meetings",
    "Business analysis & process improvement": "Mapped an order-handling process and recommended improvements that cut turnaround time",
    "Financial statements & reporting": "Prepared draft financial statements and month-end financial reporting packs",
    "Customer relationship management": "Logged client queries and follow-ups in a CRM (HubSpot) and resolved customer service issues",
    "Presentation & public speaking": "Gave presentations on project results to staff and external stakeholders",
    "Digital & social media marketing": "Ran Facebook and Instagram social media campaigns and reported results from Google Analytics",
    "Marketing campaigns": "Planned and coordinated a marketing campaign with a set budget, audience and channels",
    "Content management systems": "Updated and published web pages in WordPress",
    "Proofreading & editing": "Proofread and edited reports and newsletters for grammar, clarity and house style",
    "Online research & information sourcing": "Carried out internet research and compiled briefs from credible, cited sources",
    "Recruitment & interviewing": "Screened CVs, scheduled interviews and sat on interview panels for recruitment",
    "Labour law & HR compliance": "Kept leave and disciplinary records in line with the Labour Relations Act and BCEA",
    "Training & mentoring others": "Tutored and mentored first-year students in weekly small groups",
    "Public relations & media": "Drafted press releases and kept a media contact list up to date for public relations",
    "Stakeholder management & negotiation": "Liaised with stakeholders and negotiated delivery dates with suppliers and partners",
    "Translation & localisation": "Translated documents between English and isiZulu using SDL Trados",
    "Additional languages": "Fluent in English, isiZulu and Afrikaans; bilingual client communication",
    "Technical documentation": "Wrote user guides and technical documentation for a software tool",
    "Laboratory techniques & safety": "Worked in a laboratory following good laboratory practice and safety procedures with PPE",
    "Sample preparation & testing": "Prepared and diluted samples to a written method and recorded test results",
    "Field research & data collection": "Carried out fieldwork surveys and recorded field data on standard data sheets",
    "Water quality testing": "Tested river water samples for pH, conductivity and E. coli as part of water quality monitoring",
    "Microbiology & molecular biology": "Grew bacterial cultures and ran PCR in a microbiology laboratory",
    "Scientific research & writing": "Wrote a research proposal and a scientific report following the scientific method",
    "Agricultural & livestock advisory": "Advised small-scale farmers on soil, water and livestock practices",
    "Project management": "Planned and tracked a project schedule, risks and budget using agile project management",
    "IT support & troubleshooting": "Resolved help desk tickets for laptops, printers and user accounts as IT support",
    "Networks & IT infrastructure": "Set up network switches and Wi-Fi access points; studying towards CCNA networking",
    "HTML & CSS (front-end)": "Built responsive web pages with HTML and CSS",
    "Python programming": "Wrote Python scripts with pandas to clean and process data files",
    "SQL & databases": "Wrote SQL queries against a MySQL database for monthly reports",
    "Version control & DevOps tools": "Managed code in Git and GitHub using branches and pull requests",
    "Software testing & debugging": "Wrote unit tests and fixed bugs found in software testing",
    "Machine learning & AI": "Trained a machine learning classification model with scikit-learn and reported its accuracy",
    "JavaScript & TypeScript": "Developed interactive front-end features in JavaScript and React",
    "UX & UI design": "Designed wireframes and UI prototypes in Figma and tested them with users",
    "Cybersecurity fundamentals": "Completed an introductory cybersecurity course and ran a basic vulnerability checklist",
    "Chemical analysis & chromatography": "Ran HPLC chromatography and titrations to analyse chemical samples",
}

# (id, level, discipline, goal, qualification, target, skills, cv format)
CORE = [
    ("SP01", "limited", "Commerce", "in-field", "BCom Accounting", "Financial Accountant",
     ["Bookkeeping & journal entries", "Microsoft Office & spreadsheets"], "pdf"),
    ("SP02", "limited", "Commerce", "pivot", "BCom Marketing", "Communication Coordinator",
     ["Microsoft Office & spreadsheets", "Market research"], "docx"),
    ("SP03", "limited", "Humanities", "in-field", "BA English", "Translator",
     ["Proofreading & editing", "Online research & information sourcing"], "pdf"),
    ("SP04", "limited", "Humanities", "pivot", "BA Psychology", "Management Consultant",
     ["Recruitment & interviewing", "Microsoft Office & spreadsheets"], "pdf"),
    ("SP05", "limited", "Natural Sciences", "in-field", "BSc Chemistry", "Chemistry Technician",
     ["Laboratory techniques & safety", "Sample preparation & testing"], "docx"),
    ("SP06", "limited", "Natural Sciences", "pivot", "BSc Biological Sciences", "Data Scientist",
     ["Data analysis & statistics", "Microsoft Office & spreadsheets"], "pdf"),
    ("SP07", "limited", "IT", "in-field", "Diploma in Information Technology", "Systems Administrator",
     ["IT support & troubleshooting", "Networks & IT infrastructure"], "pdf"),
    ("SP08", "limited", "IT", "pivot", "Diploma in Information Technology", "Technical Writer",
     ["HTML & CSS (front-end)", "Content management systems"], "docx"),
    ("SP09", "foundational", "Commerce", "in-field", "BCom Accounting", "Tax Professional",
     ["Bookkeeping & journal entries", "Microsoft Office & spreadsheets", "Tax & VAT", "Payroll"], "pdf"),
    ("SP10", "foundational", "Commerce", "pivot", "BCom Economics", "Data Scientist",
     ["Data analysis & statistics", "Microsoft Office & spreadsheets", "Financial analysis & risk",
      "Data visualisation & dashboards"], "pdf"),
    ("SP11", "foundational", "Humanities", "in-field", "BA Industrial Psychology", "Human Resource Advisor",
     ["Recruitment & interviewing", "Labour law & HR compliance", "Microsoft Office & spreadsheets",
      "Training & mentoring others"], "docx"),
    ("SP12", "foundational", "Humanities", "pivot", "BA Media Studies", "Marketing Practitioner",
     ["Proofreading & editing", "Public relations & media", "Digital & social media marketing",
      "Online research & information sourcing"], "pdf"),
    ("SP13", "foundational", "Natural Sciences", "in-field", "BSc Environmental Science", "Environmental Scientist",
     ["Field research & data collection", "Water quality testing", "Data analysis & statistics",
      "Microsoft Office & spreadsheets"], "pdf"),
    ("SP14", "foundational", "Natural Sciences", "pivot", "BSc Geography", "Marketing Practitioner",
     ["Field research & data collection", "Data analysis & statistics", "Data visualisation & dashboards",
      "Online research & information sourcing"], "docx"),
    ("SP15", "foundational", "IT", "in-field", "BSc Computer Science", "Software Developer",
     ["Python programming", "SQL & databases", "Version control & DevOps tools", "Software testing & debugging"], "pdf"),
    ("SP16", "foundational", "IT", "pivot", "BSc Information Technology", "Management Consultant",
     ["SQL & databases", "Data visualisation & dashboards", "Business analysis & process improvement",
      "Microsoft Office & spreadsheets"], "pdf"),
    ("SP17", "moderate", "Commerce", "in-field", "BCom Information Systems", "Management Consultant",
     ["Business analysis & process improvement", "Data analysis & statistics", "Financial statements & reporting",
      "Customer relationship management", "Presentation & public speaking", "Microsoft Office & spreadsheets"], "docx"),
    ("SP18", "moderate", "Commerce", "pivot", "BCom Marketing Management", "Technical Writer",
     ["Digital & social media marketing", "Marketing campaigns", "Market research", "Content management systems",
      "Data visualisation & dashboards", "Microsoft Office & spreadsheets"], "pdf"),
    ("SP19", "moderate", "Humanities", "in-field", "BA Journalism", "Communication Coordinator",
     ["Public relations & media", "Digital & social media marketing", "Presentation & public speaking",
      "Market research", "Proofreading & editing", "Stakeholder management & negotiation"], "pdf"),
    ("SP20", "moderate", "Humanities", "pivot", "BA Linguistics", "Web Developer",
     ["Translation & localisation", "Additional languages", "Proofreading & editing",
      "Online research & information sourcing", "Technical documentation", "Content management systems"], "docx"),
    ("SP21", "moderate", "Natural Sciences", "in-field", "BSc Microbiology", "Water Quality Analyst",
     ["Laboratory techniques & safety", "Microbiology & molecular biology", "Sample preparation & testing",
      "Water quality testing", "Scientific research & writing", "Data analysis & statistics"], "pdf"),
    ("SP22", "moderate", "Natural Sciences", "pivot", "BSc Agriculture", "Policy Analyst",
     ["Agricultural & livestock advisory", "Field research & data collection", "Scientific research & writing",
      "Project management", "Data analysis & statistics", "Presentation & public speaking"], "pdf"),
    ("SP23", "moderate", "IT", "in-field", "BSc Computer Science", "Data Scientist",
     ["Python programming", "SQL & databases", "Data analysis & statistics", "Machine learning & AI",
      "Version control & DevOps tools", "JavaScript & TypeScript"], "docx"),
    ("SP24", "moderate", "IT", "pivot", "Diploma in Software Development", "Marketing Practitioner",
     ["JavaScript & TypeScript", "HTML & CSS (front-end)", "UX & UI design", "Content management systems",
      "Digital & social media marketing", "Version control & DevOps tools"], "pdf"),
]
EDGE = [
    ("SP25", "BA General", [], "Empty skills profile: tests fallback message"),
    ("SP26", "BSc General", ["Payroll", "Python programming", "Water quality testing", "Translation & localisation",
                            "Agricultural & livestock advisory", "Cybersecurity fundamentals", "Public relations & media",
                            "Tax & VAT", "Chemical analysis & chromatography", "UX & UI design"],
     "Very broad profile (many unrelated skills): tests ranking stability"),
    ("SP27", "Diploma in Engineering", ["welding", "forklift operation", "autocad drafting"],
     "Skills not in SkillPath vocabulary: tests unmatched-input handling"),
    ("SP28", "BCom Honours", "ALL", "Profile already holding all skills of nearest occupations: tests 'nothing to add' response"),
]
NAMES = ["Lerato", "Sipho", "Ayanda", "Naledi", "Pieter", "Zinhle", "Kabelo", "Thando", "Aisha", "Johan", "Nomsa",
         "Tumelo", "Megan", "Bongani", "Priya", "Lwazi", "Refilwe", "Ruan", "Khanyisile", "Musa", "Karabo", "Lindiwe",
         "Themba", "Chantel", "Sello", "Busisiwe", "Tiaan", "Palesa"]
YEARS = {"limited": "2025", "foundational": "2024", "moderate": "2023", "edge": "2024"}
FRAME = {"limited": ("Final-year project and vacation work (fictional host), 2025", "Recent graduate looking for an entry-level role."),
         "foundational": ("Part-time assistant, Ubuntu Services (fictional), 2024 - 2025", "Graduate with part-time work experience and practical projects."),
         "moderate": ("Junior officer, Kopano Group (fictional), 2023 - present", "Graduate with two years' work experience, looking to grow into the next role."),
         "edge": ("Various short-term roles (fictional), 2024 - 2025", "Graduate looking for work.")}


def cv_lines(pid, i, level, qual, skills, target):
    role, summary = FRAME[level]
    lines = [f"{MARK} - Synthetic test profile {pid}. Fictional person.", "",
             f"{NAMES[i].upper()} EXAMPLE-{pid}", "Gauteng | example@example.com | 000 000 0000 (fictional)", "",
             "PERSONAL SUMMARY", f"{qual} graduate. {summary}",
             "", "EDUCATION", f"{qual} (NQF 7), fictional university, {YEARS[level]}", "National Senior Certificate", ""]
    known = [s for s in skills if s in BULLET]
    if known or skills:
        lines += ["EXPERIENCE AND PROJECTS", role] + [f"- {BULLET[s]}" for s in known]
        lines += [f"- Used {s} on site" for s in skills if s not in BULLET and len(skills) < 20]
        lines += [""]
    lines += ["SKILLS", ", ".join(skills) if skills else "(none listed)", "", "REFERENCES", "Available on request.",
              "", MARK]
    return lines


def main():
    desc = json.load(open(os.path.join(ROOT, "data", "skill_descriptions.json"), encoding="utf-8"))
    vocab = {d["label"] for d in desc.values()}
    all_skills = sorted(vocab, key=str.lower)
    os.makedirs(os.path.join(OUT, "cvs"), exist_ok=True)
    profiles, expected = [], []
    for i, (pid, level, disc, goal, qual, target, skills, fmt) in enumerate(CORE):
        bad = [s for s in skills + [None] if s and s not in vocab]
        assert not bad, (pid, bad)
        cv = f"EXAMPLE_CV_{pid}.{fmt}"
        profiles.append({"profile_id": pid, "competency_level": level, "discipline": disc, "employment_goal": goal,
                         "qualification": qual, "current_skills": "; ".join(skills), "target_occupation": target,
                         "designed_to_test": f"{MARK}: adjacency and pathway calibration for a {level}-competency "
                                             f"{disc} graduate seeking a {goal} move to {target}",
                         "acceptable_recommendations": "", "is_edge_case": "N", "cv_file": cv})
        {"pdf": write_pdf, "docx": write_docx}[fmt](os.path.join(OUT, "cvs", cv), cv_lines(pid, i, level, qual, skills, target))
        expected.append({"cv_file": cv, "competency_level": level, "expected_skills": "; ".join(skills)})
    for j, (pid, qual, skills, test) in enumerate(EDGE, start=len(CORE)):
        skills = all_skills if skills == "ALL" else skills
        cv = f"EXAMPLE_CV_{pid}.pdf"
        profiles.append({"profile_id": pid, "competency_level": "edge", "discipline": "mixed", "employment_goal": "n/a",
                         "qualification": qual, "current_skills": "; ".join(skills), "target_occupation": "",
                         "designed_to_test": f"{MARK}: {test}", "acceptable_recommendations": "", "is_edge_case": "Y",
                         "cv_file": cv})
        write_pdf(os.path.join(OUT, "cvs", cv), cv_lines(pid, j, "edge", qual, skills, ""))
        in_vocab = [s for s in skills if s in vocab]
        # SP28 lists every skill; the CV reader proposes at most CV_MAX_SKILLS (25), so it is left out of the
        # CV accuracy check by design. SP25/SP27 have no in-vocabulary skills to find.
        if in_vocab and len(in_vocab) <= 25:
            expected.append({"cv_file": cv, "competency_level": "edge", "expected_skills": "; ".join(in_vocab)})
    fields = ["profile_id", "competency_level", "discipline", "employment_goal", "qualification", "current_skills",
              "target_occupation", "designed_to_test", "acceptable_recommendations", "is_edge_case", "cv_file"]
    with open(os.path.join(OUT, "profiles_EXAMPLE.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(profiles)
    with open(os.path.join(OUT, "cvs", "expected_skills.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["cv_file", "competency_level", "expected_skills"])
        w.writeheader()
        w.writerows(expected)
    with open(os.path.join(OUT, "README.txt"), "w", encoding="utf-8") as f:
        f.write(f"""{MARK}

Worked example of the Phase 3 study inputs, created with AI assistance as a teaching exemplar.
It is NOT a student's research data and must not be submitted or reported as findings.

profiles_EXAMPLE.csv  28 profiles (24-cell design matrix + 4 edge cases) using SkillPath's skill names
cvs/                  one fictional CV per profile and expected_skills.csv

Try it (from the repository folder):
  .venv\\Scripts\\python scripts\\cv_accuracy.py samples\\example_study\\cvs
  .venv\\Scripts\\python run_evaluation.py samples\\example_study\\profiles_EXAMPLE.csv --label EXAMPLE --out-dir samples\\example_study\\runs --allow-dirty

How a student builds their own: profiles\\profile_builder.xlsx (see its Guide sheet) and
profiles\\cv_template\\CV_TEMPLATE.docx, then scripts\\profiles_from_builder.py.
""")
    print(f"Wrote {len(profiles)} example profiles and {len(profiles)} CVs to {OUT}")


if __name__ == "__main__":
    main()
