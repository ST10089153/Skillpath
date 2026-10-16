"""CV skill extraction (skill profiling layer). Unit tests use a deterministic bag-of-words embedder;
one test runs the real local model when it has been downloaded to ./models."""

import io
import os
import re
import zipfile

import numpy as np
import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from skillpath.cv import CVSkillExtractor, extract_text, segments

from conftest import FIXTURES, ROOT, SKILL_MAP_CSV


def bow_embed(texts):
    """Deterministic stand-in for the model: bag of word tokens hashed into 64 dims."""
    out = np.zeros((len(texts), 64), dtype=np.float32)
    for i, t in enumerate(texts):
        for tok in re.findall(r"[a-z0-9_]+", t.lower()):
            out[i, sum(map(ord, tok)) % 64] += 1
    return out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-12)


@pytest.fixture
def cv_text():
    return open(os.path.join(FIXTURES, "cv_fake.txt"), encoding="utf-8").read()


@pytest.fixture
def extractor(skill_map):
    return CVSkillExtractor(skill_map, {}, embed=bow_embed, threshold=0.55)


def test_segments_split_lines_bullets_and_lists(cv_text):
    segs = segments(cv_text)
    assert "Did skill_a work every day at occ_alpha style job" in segs
    assert "skill_e" in segs and "cooking" in segs  # comma list split into items


def test_exact_label_detected_with_evidence(extractor, cv_text):
    found = {d.skill: d for d in extractor.extract(cv_text)}
    assert found["skill_a"].method == "exact" and found["skill_a"].score == 1.0
    assert "skill_a" in found["skill_a"].evidence
    assert {"skill_x", "skill_y", "skill_e"} <= set(found)


def test_unrelated_cv_detects_nothing(extractor):
    assert extractor.extract("Enjoys hiking and reading novels.") == []


def test_extraction_is_deterministic(extractor, cv_text):
    assert extractor.extract(cv_text) == extractor.extract(cv_text)


def test_results_sorted_and_capped(skill_map, cv_text):
    x = CVSkillExtractor(skill_map, {}, embed=bow_embed, max_skills=2)
    found = x.extract(cv_text)
    assert len(found) == 2 and [d.score for d in found] == sorted([d.score for d in found], reverse=True)


def test_docx_and_txt_text_extraction():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", "<w:document><w:body><w:p><w:r><w:t>skill_a &amp; more</w:t></w:r></w:p>"
                                        "<w:p><w:r><w:t>line two</w:t></w:r></w:p></w:body></w:document>")
    text = extract_text(buf.getvalue(), "cv.docx")
    assert "skill_a & more" in text and "line two" in text
    assert extract_text(b"hello", "cv.txt") == "hello"
    with pytest.raises(ValueError):
        extract_text(b"x", "cv.png")


def test_cv_endpoint(tmp_path, cv_text):
    c = TestClient(create_app(db_path=str(tmp_path / "c.db"), skill_map_path=SKILL_MAP_CSV,
                              admin_token="t", cv_embed=bow_embed))
    r = c.post("/cv/extract", files={"file": ("cv.txt", cv_text.encode(), "text/plain")})
    assert r.status_code == 200
    skills = [s["skill"] for s in r.json()["skills"]]
    assert "skill_a" in skills and all(s["evidence"] for s in r.json()["skills"])
    assert c.post("/cv/extract", files={"file": ("cv.png", b"x", "image/png")}).status_code == 400
    assert not list(tmp_path.glob("*.txt"))  # nothing stored


def test_recommendation_lists_missing_skills(engine):
    from conftest import profile
    res = engine.recommend(profile("skill_a; skill_b"), "B")
    alpha = next(o for o in res["nearest_occupations"] if o["occupation"] == "occ_alpha")
    assert alpha["skills_missing"] == ["skill_c"]


@pytest.mark.skipif(not os.path.isdir(os.path.join(ROOT, "models")), reason="local model not downloaded")
def test_real_local_model_matches_by_meaning(skill_map):
    from skillpath.engine import SkillMap
    sm = SkillMap([{"occupation": "o", "essential_skills": "use office systems; translate texts; statistics"}])
    found = [d.skill for d in CVSkillExtractor(sm, {}, threshold=0.4).extract(
        "Converted documents from French into English for a publishing house")]
    assert found and found[0] == "translate texts"


def test_section_headings_and_banners_are_not_evidence():
    from skillpath.cv import is_heading
    for h in ["EXPERIENCE AND PROJECTS", "Skills:", "Personal Summary", "REFERENCES", "DEMO CV - NOT STUDY DATA"]:
        assert is_heading(h), h
    for s in ["Wrote SQL queries for reports", "Python", "CCNA", "Reconciled bank statements"]:
        assert not is_heading(s), s
    assert "EXPERIENCE AND PROJECTS" not in segments("EXPERIENCE AND PROJECTS\nBuilt dashboards in Power BI")


def test_demo_cvs_are_readable_in_every_format():
    folder = os.path.join(ROOT, "samples", "demo_cvs")
    if not os.path.isdir(folder):
        pytest.skip("demo CVs not generated")
    for fn in os.listdir(folder):
        if fn.endswith((".pdf", ".docx", ".txt")) and fn.startswith("DEMO"):
            text = extract_text(open(os.path.join(folder, fn), "rb").read(), fn)
            assert "NOT STUDY DATA" in text and "EDUCATION" in text, fn
