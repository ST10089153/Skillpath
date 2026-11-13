"""Replace the app screenshots (Figures 8-11) in the research report with fresh captures of the current app.

    python scripts/capture_screens.py                              (research build, not the demo)
    python scripts/refresh_report_figures.py IN.docx OUT.docx

Only the four image files change: the output is a byte-for-byte copy of the input apart from those images, so
captions, picture sizes, page layout and all other content stay exactly as they are. Each figure is found by its
caption, and the script stops rather than replace a picture it cannot match.
"""

import io
import os
import sys
import zipfile

from docx import Document
from docx.oxml.ns import qn
from PIL import Image

from refine_exemplar import SHOTS, app_panel

# caption prefix -> the two panels (screenshot from capture_screens.py, annotation under it)
FIGURES = {
    "Figure 8:": [("fig1_welcome.png", "Consent and age check; no name, email or phone"),
                  ("fig2_profile_cv.png", "Local AI proposes skills from the CV; user confirms")],
    "Figure 9:": [("fig3a_recommendation.png", "One recommended skill with its demand evidence"),
                  ("fig3b_transparency.png", "Transparency: nearest occupations and missing skills")],
    "Figure 10:": [("fig4_pathway.png", "Six 5-10 minute steps; difficulty shown as dots"),
                   ("fig_home.png", "Home: pathway progress and one-tap navigation")],
    "Figure 11:": [("fig5_progress.png", "Milestone every three completed steps"),
                   ("fig_settings.png", "View and delete my data (POPIA)")],
}


def picture_above(pars, caption_index):
    """The picture elements in the nearest paragraph above a caption (none for a table-of-figures entry)."""
    for k in range(caption_index - 1, max(caption_index - 3, -1), -1):
        blips = pars[k]._p.findall(".//" + qn("a:blip"))
        if blips:
            return blips
    return []


def main(src, dst):
    if os.path.abspath(src) == os.path.abspath(dst):
        raise SystemExit("write to a new file; the input report is left untouched")
    doc = Document(src)
    pars = doc.paragraphs
    replace = {}  # zip entry name -> new PNG bytes
    for prefix, panels in FIGURES.items():
        caps = [k for k, p in enumerate(pars) if p.text.startswith(prefix) and picture_above(pars, k)]
        if len(caps) != 1:
            raise SystemExit(f"expected one captioned picture for '{prefix}', found {len(caps)}")
        blips = picture_above(pars, caps[0])
        if len(blips) != 1:
            raise SystemExit(f"expected one picture above '{prefix}', found {len(blips)}")
        part = doc.part.related_parts[blips[0].get(qn("r:embed"))]
        png = os.path.join(SHOTS, f"report_{prefix[:-1].replace(' ', '_').lower()}.png")
        app_panel(panels, png)
        old, new = Image.open(io.BytesIO(part.blob)).size, Image.open(png).size
        if old != new:  # same pixel size keeps the picture's shape on the page
            raise SystemExit(f"{prefix} new picture is {new}, the report's is {old}")
        with open(png, "rb") as f:
            replace[part.partname.lstrip("/")] = f.read()
        print(f"{prefix:11} {part.partname} <- {os.path.basename(png)}")
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w") as zout:
        for item in zin.infolist():
            zout.writestr(item, replace.pop(item.filename, None) or zin.read(item.filename))
    if replace:
        raise SystemExit(f"not found in the package: {sorted(replace)}")
    print("saved", dst)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
