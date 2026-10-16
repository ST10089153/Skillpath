"""Export the Part 3 report to PDF with the signed ethics documents inserted as Annexure F attachments.

    python scripts/export_final_pdf.py <report.docx> <annexure_q.docx> <clearance_letter.pdf> <out.pdf>

Word (via COM, Windows) converts the .docx files to PDF; pypdf then inserts the Annexure Q application and the
ethics clearance letter after Annexure F, before Annexure G. The output contains signatures, so keep it out of the
repository.
"""

import os
import subprocess
import sys
import tempfile

from pypdf import PdfReader, PdfWriter


def to_pdf(docx_path, pdf_path):
    ps = ("$w = New-Object -ComObject Word.Application; $w.Visible = $false; "
          f"$d = $w.Documents.Open('{os.path.abspath(docx_path)}', $false, $true); "
          f"$d.ExportAsFixedFormat('{os.path.abspath(pdf_path)}', 17); $d.Close($false); $w.Quit()")
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], check=True)


def main(report, annex_q, letter, out):
    tmp = tempfile.mkdtemp()
    report_pdf, q_pdf = os.path.join(tmp, "report.pdf"), os.path.join(tmp, "annexure_q.pdf")
    to_pdf(report, report_pdf)
    to_pdf(annex_q, q_pdf)

    rep = PdfReader(report_pdf)
    texts = [(p.extract_text() or "") for p in rep.pages]
    g = max(i for i, t in enumerate(texts) if "Annexure G: Updated Concept Document" in t)  # last hit (not the TOC)

    w = PdfWriter()
    for p in rep.pages[:g]:
        w.add_page(p)
    f1 = len(w.pages)
    for p in PdfReader(q_pdf).pages:
        w.add_page(p)
    f2 = len(w.pages)
    for p in PdfReader(letter).pages:
        w.add_page(p)
    gpage = len(w.pages)
    for p in rep.pages[g:]:
        w.add_page(p)
    w.add_outline_item("Annexure F1: Annexure Q ethics application", f1)
    w.add_outline_item("Annexure F2: Ethics clearance letter", f2)
    w.add_outline_item("Annexure G: Updated concept document", gpage)
    with open(out, "wb") as fh:
        w.write(fh)
    print(f"wrote {out}: {len(w.pages)} pages (report {len(rep.pages)}; F1 from page {f1 + 1}; F2 page {f2 + 1}; "
          f"Annexure G from page {gpage + 1})")


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
