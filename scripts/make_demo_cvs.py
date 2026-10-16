"""Generate DEMO CVs for trying the app's CV upload and for testing the CV reader.

    python scripts/make_demo_cvs.py      -> samples/demo_cvs/ (PDF, DOCX, TXT) + expected_skills.csv

DEMO ONLY - NOT STUDY DATA. Every person, employer and reference below is fictional. The layout follows the
South African graduate CV structure recommended by university career services (Wits CCDU "Build a great
CV"; UNISA Directorate: Counselling and Career Development, "CV Writing", 2020): personal summary,
education (with NQF level), experience or projects, skills, references on request. The study's own
synthetic CVs are built by the researcher.

expected_skills.csv lists the SkillPath skills each demo CV was written to show. Because the same author
wrote the CVs and the labels, accuracy measured on this set is a development check, not study evidence.
"""

import csv
import os
import textwrap
import zipfile
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "samples", "demo_cvs")
BANNER = "DEMO CV - FICTIONAL PERSON - NOT STUDY DATA"

CVS = [
    {"id": "DEMO-01", "format": "pdf", "name": "Lerato Demo-Mokoena", "level": "limited",
     "expected": ["Bookkeeping & journal entries", "Microsoft Office & spreadsheets"],
     "summary": "Recent BCom Accounting graduate looking for a trainee accountant or bookkeeping role. Accurate, "
                "reliable and keen to complete my articles.",
     "education": ["BCom Accounting (NQF 7), University of Johannesburg, 2025",
                   "National Senior Certificate, 2021 - Accounting 78%, Mathematics 72%"],
     "experience": ["Vacation work: Accounts clerk, Ubuntu Numbers Bookkeeping (fictional), Dec 2024 - Jan 2025",
                    "- Captured supplier invoices and receipts in Sage Pastel Partner",
                    "- Reconciled monthly bank statements for three small-business clients",
                    "- Prepared client expense schedules in Microsoft Excel using SUM and VLOOKUP"],
     "skills": "Sage Pastel, Microsoft Excel, Microsoft Word, attention to detail"},
    {"id": "DEMO-02", "format": "docx", "name": "Sipho Demo-Nkosi", "level": "moderate",
     "expected": ["Digital & social media marketing", "Marketing campaigns", "Market research",
                  "Presentation & public speaking", "Microsoft Office & spreadsheets"],
     "summary": "Marketing graduate with 18 months' experience running digital campaigns for a retail brand.",
     "education": ["BCom Marketing Management (NQF 7), University of Pretoria, 2023"],
     "experience": ["Marketing assistant, Mzansi Home Goods (fictional), Jan 2024 - present",
                    "- Planned and ran Facebook and Instagram campaigns with a monthly budget of R15 000",
                    "- Built email marketing newsletters in Mailchimp and tracked open rates",
                    "- Reported website traffic and conversions from Google Analytics every week",
                    "- Designed and analysed a customer survey of 400 shoppers to guide a product launch",
                    "- Presented campaign results to the management team each quarter"],
     "skills": "Social media marketing, Google Analytics, Mailchimp, Canva, Excel, PowerPoint"},
    {"id": "DEMO-03", "format": "txt", "name": "Ayanda Demo-Dlamini", "level": "foundational",
     "expected": ["Translation & localisation", "Proofreading & editing", "Additional languages",
                  "Training & mentoring others"],
     "summary": "Languages graduate fluent in isiZulu, English and French, seeking a junior translator post.",
     "education": ["BA Languages and Literature (NQF 7), University of KwaZulu-Natal, 2024"],
     "experience": ["Freelance translator (part-time), 2024 - present",
                    "- Translated community health pamphlets from English into isiZulu for an NGO (fictional client)",
                    "- Used SDL Trados to keep terminology consistent across documents",
                    "- Proofread and edited student theses for grammar, spelling and style",
                    "Language tutor, university writing centre, 2023",
                    "- Tutored first-year students in academic writing in weekly small groups"],
     "skills": "Translation (English, isiZulu, French), proofreading, Trados, tutoring"},
    {"id": "DEMO-04", "format": "pdf", "name": "Naledi Demo-Khumalo", "level": "moderate",
     "expected": ["Recruitment & interviewing", "Labour law & HR compliance", "Payroll",
                  "Microsoft Office & spreadsheets"],
     "summary": "Human resources graduate with two years of generalist HR support experience.",
     "education": ["BA Industrial Psychology (NQF 7), Stellenbosch University, 2022",
                   "Short course: Labour Relations Act and Basic Conditions of Employment Act, 2023"],
     "experience": ["HR administrator, Kopano Logistics (Pty) Ltd (fictional), 2023 - present",
                    "- Screened CVs and scheduled interviews for 30+ vacancies a year",
                    "- Sat on interview panels and wrote candidate interview notes",
                    "- Captured monthly payroll changes, PAYE and UIF deductions in VIP Payroll",
                    "- Kept leave and disciplinary records in line with the BCEA",
                    "- Built Excel headcount and leave reports for managers"],
     "skills": "Recruitment, interviewing, payroll (VIP), labour law, Microsoft Excel"},
    {"id": "DEMO-05", "format": "docx", "name": "Pieter Demo-van Wyk", "level": "limited",
     "expected": ["Laboratory techniques & safety", "Chemical analysis & chromatography",
                  "Sample preparation & testing"],
     "summary": "BSc Chemistry graduate looking for a first laboratory analyst position.",
     "education": ["BSc Chemistry (NQF 7), North-West University, 2025"],
     "experience": ["Final-year research project, 2025",
                    "- Prepared and diluted samples to a written method for HPLC analysis",
                    "- Ran acid-base titrations and recorded results in a lab notebook",
                    "- Followed laboratory safety rules and wore PPE when handling chemicals"],
     "skills": "HPLC, titration, laboratory safety, sample preparation"},
    {"id": "DEMO-06", "format": "pdf", "name": "Zinhle Demo-Mthembu", "level": "foundational",
     "expected": ["Field research & data collection", "Water quality testing",
                  "Environmental compliance & impact assessment", "Data analysis & statistics",
                  "R, SAS or MATLAB"],
     "summary": "Environmental Science graduate with field and data experience from an internship.",
     "education": ["BSc Environmental Science (NQF 7), Rhodes University, 2024"],
     "experience": ["Environmental intern, Green Karoo Consulting (fictional), 2025",
                    "- Carried out field surveys of wetland vegetation and recorded data sheets",
                    "- Collected river water samples and tested pH, conductivity and E. coli for water quality",
                    "- Helped compile an environmental impact assessment (EIA) report under NEMA",
                    "- Analysed survey data with descriptive statistics in R and RStudio"],
     "skills": "Fieldwork, water quality testing, EIA, statistics, R"},
    {"id": "DEMO-07", "format": "txt", "name": "Kabelo Demo-Molefe", "level": "foundational",
     "expected": ["IT support & troubleshooting", "Systems administration", "Networks & IT infrastructure"],
     "summary": "Diploma in IT graduate with help desk experience, studying towards CCNA.",
     "education": ["Diploma in Information Technology (NQF 6), Tshwane University of Technology, 2024"],
     "experience": ["IT help desk technician (contract), Bright Schools Trust (fictional), 2025",
                    "- Resolved 40+ support tickets a week for staff laptops and printers",
                    "- Created user accounts and reset passwords in Active Directory on Windows Server",
                    "- Set up and tested network switches and Wi-Fi access points in two classrooms"],
     "skills": "Help desk support, Windows Server, Active Directory, networking, CCNA (in progress)"},
    {"id": "DEMO-08", "format": "pdf", "name": "Thando Demo-Ndlovu", "level": "moderate",
     "expected": ["Python programming", "SQL & databases", "Data visualisation & dashboards",
                  "Version control & DevOps tools", "Software testing & debugging", "Data analysis & statistics"],
     "summary": "Computer Science graduate with a year of junior data and development work.",
     "education": ["BSc Computer Science and Statistics (NQF 7), University of Cape Town, 2023"],
     "experience": ["Junior data developer, Fynbos Analytics (fictional), 2024 - present",
                    "- Wrote Python (pandas) scripts to clean and analyse sales data",
                    "- Wrote SQL queries against a PostgreSQL database for monthly reports",
                    "- Built Power BI dashboards used by the sales team",
                    "- Managed code in Git and GitHub with pull requests and code reviews",
                    "- Wrote unit tests and fixed bugs before each release"],
     "skills": "Python, pandas, SQL, PostgreSQL, Power BI, Git, unit testing, statistics"},
]


def cv_lines(cv: dict) -> list[str]:
    lines = [BANNER, "", cv["name"].upper(), "Johannesburg, Gauteng | demo@example.com | 000 000 0000 (fictional)", "",
             "PERSONAL SUMMARY", cv["summary"], "", "EDUCATION", *cv["education"], "", "EXPERIENCE AND PROJECTS",
             *cv["experience"], "", "SKILLS", cv["skills"], "", "REFERENCES", "Available on request.", "", BANNER]
    return lines


def write_txt(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_docx(path, lines):
    paras = "".join(f"<w:p><w:r><w:t xml:space=\"preserve\">{escape(l)}</w:t></w:r></w:p>" for l in lines)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr("word/document.xml",
                   '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                   f"<w:body>{paras}</w:body></w:document>")


def write_pdf(path, lines):
    """Minimal text PDF (Helvetica, A4), wrapped at 95 characters, multiple pages if needed."""
    wrapped = []
    for l in lines:
        wrapped += textwrap.wrap(l, 95) or [""]
    pages = [wrapped[i:i + 50] for i in range(0, len(wrapped), 50)]
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", None,
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"]
    kids = []
    for page in pages:
        ops = ["BT", "/F1 10 Tf", "13 TL", "56 790 Td"]
        for l in page:
            t = l.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            ops.append(f"({t}) Tj T*")
        ops.append("ET")
        stream = "\n".join(ops).encode("cp1252", "replace")
        objs.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
        content_no = len(objs)
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                    f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_no} 0 R >>")
        kids.append(len(objs))
    objs[1] = f"<< /Type /Pages /Kids [{' '.join(f'{k} 0 R' for k in kids)}] /Count {len(kids)} >>"
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        body = o if isinstance(o, bytes) else o.encode()
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{off:010d} 00000 n \n".encode() for off in offsets)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    with open(path, "wb") as f:
        f.write(out)


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for cv in CVS:
        fn = f"{cv['id']}.{cv['format']}"
        {"pdf": write_pdf, "docx": write_docx, "txt": write_txt}[cv["format"]](os.path.join(OUT, fn), cv_lines(cv))
        rows.append({"cv_file": fn, "competency_level": cv["level"], "expected_skills": "; ".join(cv["expected"])})
    with open(os.path.join(OUT, "expected_skills.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["cv_file", "competency_level", "expected_skills"])
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(OUT, "README.txt"), "w", encoding="utf-8") as f:
        f.write(f"{BANNER}\n\nGenerated by scripts/make_demo_cvs.py for trying the app's CV upload and for "
                "development checks of the CV reader (scripts/cv_accuracy.py).\nAll people, employers and "
                "contact details are fictional. Do not use these as the study's synthetic CVs.\n")
    print(f"Wrote {len(rows)} demo CVs to {OUT}")


if __name__ == "__main__":
    main()
