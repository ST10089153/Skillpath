"""Cross-check in-text citations against the reference list of the Part 3 report (Harvard style).

    python scripts/check_citations.py docs/exemplar/REIT8419_Part3_SkillPath_EXEMPLAR_v4.docx

Reports: citations with no reference entry, reference entries never cited, and author/year mismatches.
Text outside the reference list is scanned, including tables, captions and annexures.
"""

import re
import sys

import docx

# Names cited in the text that appear in the reference list under a different lead name.
ALIASES = {"stats sa": "statistics south africa", "dhet": "dhet", "wef": "world economic forum",
           "esco": "european commission"}


def all_text(d):
    """(text outside the reference list, reference entries)."""
    paras = list(d.paragraphs)
    r0 = [i for i, p in enumerate(paras) if p.text.strip() == "Reference List"][-1]
    r1 = next(i for i in range(r0 + 1, len(paras)) if paras[i].text.startswith("Annexure A"))
    refs = [p.text.strip() for p in paras[r0 + 1:r1] if p.text.strip()]
    body = [p.text for p in paras[:r0]] + [p.text for p in paras[r1:]]
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                body.append(c.text)
    start = next(i for i, x in enumerate(body) if x.startswith("1. Introduction to Part 3") and i > 20)
    return "\n".join(body[start:]), refs


def ref_key(entry):
    lead = re.split(r",|\(|\s\d{4}", entry)[0].strip().lower()
    year = re.search(r"\b(19|20)\d{2}\b", entry).group(0)
    return lead, year


CITE = re.compile(
    r"(?P<names>(?:(?:(?:Du|De|Van|Von|Le|La)\s)?[A-Z][A-Za-z\-]+(?:(?:\s(?:and|&)\s|,\s)(?:(?:Du|De|Van|Von|Le|La)\s)?[A-Z][A-Za-z\-]+)*(?:\set al\.)?"
    r"|DHET|Stats SA|World Economic Forum|European Commission|Statistics South Africa|PwC))(?:'s)?"
    r"\s?(?:\(|,\s)(?P<year>(?:19|20)\d{2})\)?")


def cites(text):
    found = set()
    for m in CITE.finditer(text):
        names, year = m.group("names"), m.group("year")
        lead = re.split(r"\s(?:and|&)\s|,|\set al\.", names)[0].strip().lower()
        if lead in {"census", "table", "figure", "phase", "section", "annexure", "week", "weeks", "until", "on", "in",
                    "from", "may", "june", "july", "october", "march", "april", "between", "to", "and", "q", "ofo",
                    "commit", "build", "version", "ms", "the", "of", "by", "jobs", "future", "report", "list"}:
            continue
        found.add((ALIASES.get(lead, lead), year, names))
    return found


def main(path):
    d = docx.Document(path)
    text, refs = all_text(d)
    keys = {}
    for r in refs:
        k = ref_key(r)
        keys[(ALIASES.get(k[0], k[0]), k[1])] = r
    found = cites(text)
    cited = {(lead, year) for lead, year, _ in found}
    ref_leads = {k[0] for k in keys}

    print(f"reference entries: {len(refs)}; distinct in-text citations: {len(cited)}")
    missing = sorted(c for c in found if (c[0], c[1]) not in keys and c[0] in ref_leads | {c[0]})
    print("\nCITED BUT NOT IN REFERENCE LIST (or year differs):")
    shown = False
    for lead, year, names in sorted(found):
        if (lead, year) not in keys:
            alt = [k for k in keys if k[0] == lead]
            print(f"  {names} ({year})" + (f"  <- reference list has {alt[0][1]}" if alt else ""))
            shown = True
    if not shown:
        print("  none")
    print("\nIN REFERENCE LIST BUT NEVER CITED:")
    never = [keys[k] for k in keys if k not in cited]
    print("\n".join("  " + n[:110] for n in never) if never else "  none")
    _ = missing


if __name__ == "__main__":
    main(sys.argv[1])
