"""Verify the report's reference list against external records.

    python scripts/verify_references.py docs/exemplar/REIT8419_Part3_SkillPath_EXEMPLAR_v4.docx

DOIs are looked up in Crossref (title words and year compared with the entry); other URLs are fetched; books
without a URL are looked up in Open Library by title and author.
"""

import json
import re
import sys
import urllib.parse
import urllib.request

import docx

UA = {"User-Agent": "SkillPath-reference-check/1.0 (research report verification)"}


def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def words(s):
    return {w for w in re.findall(r"[a-z]{4,}", s.lower())}


def main(path):
    d = docx.Document(path)
    paras = list(d.paragraphs)
    r0 = [i for i, p in enumerate(paras) if p.text.strip() == "Reference List"][-1]
    r1 = next(i for i in range(r0 + 1, len(paras)) if paras[i].text.startswith("Annexure A"))
    refs = [p.text.strip() for p in paras[r0 + 1:r1] if p.text.strip()]
    ok = 0
    for ref in refs:
        lead = ref.split(",")[0]
        year = re.search(r"\b(19|20)\d{2}\b", ref).group(0)
        title = re.split(r"\b(?:19|20)\d{2}\.\s", ref, maxsplit=1)[-1].split(". ")[0]
        doi = re.search(r"doi\.org/(10\.[^\s\]]+?)\.?(?:\s|\[|$)", ref)
        url = re.search(r"Available at:\s*(\S+?)\.?\s*\[", ref)
        try:
            if doi:
                _, body = get("https://api.crossref.org/works/" + urllib.parse.quote(doi.group(1)))
                m = json.loads(body)["message"]
                ct = (m.get("title") or [""])[0]
                cy = str((m.get("issued", {}).get("date-parts") or [[None]])[0][0])
                overlap = len(words(ct) & words(title)) / max(1, len(words(title)))
                status = "OK" if overlap >= 0.6 and cy == year else "CHECK"
                note = f"Crossref: '{ct[:60]}' ({cy}); title overlap {overlap:.0%}"
            elif url:
                code, _ = get(url.group(1))
                status = "OK" if code == 200 else "CHECK"
                note = f"URL {code}: {url.group(1)[:70]}"
            else:
                q = urllib.parse.urlencode({"title": title, "author": lead, "limit": 3})
                _, body = get("https://openlibrary.org/search.json?" + q)
                docs = json.loads(body).get("docs", [])
                hit = next((x for x in docs if words(x.get("title", "")) & words(title)), None)
                status = "OK" if hit else "CHECK"
                note = (f"Open Library: '{hit['title'][:60]}' by {', '.join(hit.get('author_name', [])[:2])}, first published "
                        f"{hit.get('first_publish_year')}" if hit else "no Open Library match")
        except Exception as e:  # network or lookup failure: report, do not hide
            status, note = "CHECK", f"lookup failed: {type(e).__name__}: {e}"
        ok += status == "OK"
        print(f"[{status}] {lead} ({year}) - {note}")
    print(f"\n{ok}/{len(refs)} verified")


if __name__ == "__main__":
    main(sys.argv[1])
