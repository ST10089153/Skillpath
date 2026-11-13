"""CV skill extraction with a locally hosted sentence-embedding model (skill profiling layer).

The CV text is split into short segments; each segment and each vocabulary skill (ESCO label and
label + official description) is embedded with all-MiniLM-L6-v2 (run offline through fastembed /
ONNX, cached in ./models). A skill is detected when its best-matching CV segment reaches
CV_MATCH_THRESHOLD cosine similarity, or when its label appears verbatim in the CV.

Kept separate from skillpath.engine: the engine stays pure and deterministic over a skill list.
Extraction only PROPOSES skills; the user confirms them before they enter the profile (DD6, DD8).
No CV text or file is stored.
"""

from __future__ import annotations

import io
import json
import os
import re
import zipfile
from dataclasses import dataclass

import numpy as np

from . import config as C
from .engine import SkillMap, normalise

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PER_SEGMENT = 3               # max skills one CV phrase can support
SHORT_PHRASE_THRESHOLD = 0.75 # stricter similarity for one- or two-word phrases
MIN_EXACT_ALIAS_LEN = 4       # ESCO aliases shorter than this (e.g. "R", "C#") are matched semantically only


# ---------------------------------------------------------------------------
# Text extraction (PDF, DOCX, TXT)
# ---------------------------------------------------------------------------
def extract_text(data: bytes, filename: str) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages)
    if name.endswith(".docx"):
        xml = zipfile.ZipFile(io.BytesIO(data)).read("word/document.xml").decode("utf-8", "ignore")
        xml = re.sub(r"</w:p>|<w:br/>|<w:tab/>", "\n", xml)
        text = re.sub(r"<[^>]+>", "", xml)
        return (text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                    .replace("&quot;", '"').replace("&apos;", "'"))
    if name.endswith(".txt"):
        return data.decode("utf-8", "ignore")
    raise ValueError("Upload a PDF, Word (.docx) or text file")


# Common CV section headings (cf. the section taxonomy of ATS parsing corpora: contact, summary, skills,
# experience, projects, education, certifications, awards). Headings name sections; they are not skills.
HEADING_WORDS = {
    "about", "achievements", "activities", "additional", "and", "awards", "career", "certifications",
    "competencies", "contact", "core", "courses", "curriculum", "cv", "details", "education", "employment",
    "experience", "history", "information", "interests", "key", "languages", "me", "objective", "of",
    "other", "personal", "profile", "professional", "projects", "publications", "qualifications",
    "references", "relevant", "resume", "skills", "summary", "technical", "training", "vitae", "volunteer",
    "work", "&", "/",
}


def is_heading(segment: str) -> bool:
    """Section headings ("EXPERIENCE AND PROJECTS", "Skills:") and all-caps banners are not evidence of skills."""
    words = re.findall(r"[A-Za-z&/]+", segment)
    if not words:
        return True
    if all(w.lower() in HEADING_WORDS for w in words):
        return True
    letters = [c for c in segment if c.isalpha()]
    return len(words) >= 2 and len(letters) >= 6 and all(c.isupper() for c in letters)


def segments(text: str) -> list[str]:
    """Split CV text into short phrases (lines, bullets, sentences, list items)."""
    out = []
    for line in re.split(r"[\r\n]+|[•▪●◦·]|\s-\s|(?<=[.;!?])\s+", text):
        line = " ".join(line.split()).strip(" -*:|,")
        if not line:
            continue
        parts = [line] if len(line.split()) <= 25 else []
        if "," in line or len(line.split()) > 25:  # lists such as "Skills: Excel, Pastel, teamwork"
            parts += re.split(r",\s*|\s+and\s+", line.split(":", 1)[-1])
        for p in parts:
            p = p.strip(" -*:|,")
            if 2 <= len(p) and len(p.split()) <= 30 and re.search(r"[A-Za-z]{2}", p) and not is_heading(p):
                out.append(p)
    seen, uniq = set(), []
    for s in out:
        if s.lower() not in seen:
            seen.add(s.lower())
            uniq.append(s)
    return uniq


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------
@dataclass
class DetectedSkill:
    skill: str
    score: float
    evidence: str
    method: str  # "exact" or "semantic"


class FastEmbedder:
    """Local all-MiniLM-L6-v2 via fastembed (ONNX). Downloads once into ./models, then offline."""

    def __init__(self, model_name: str = C.CV_MODEL, cache_dir: str = os.path.join(ROOT, "models")):
        from fastembed import TextEmbedding
        self.model_name = model_name
        # Optional limits for small servers (the hosted demo sets both); unset locally, so research runs are unchanged.
        threads = os.environ.get("SKILLPATH_CV_THREADS")
        batch = os.environ.get("SKILLPATH_CV_BATCH")
        self._embed_kw = {"batch_size": int(batch)} if batch else {}
        self._model = TextEmbedding(model_name, cache_dir=cache_dir, **({"threads": int(threads)} if threads else {}))

    def __call__(self, texts: list[str]) -> np.ndarray:
        v = np.array(list(self._model.embed(texts, **self._embed_kw)), dtype=np.float32)
        return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-12)


class CVSkillExtractor:
    def __init__(self, skill_map: SkillMap, descriptions: dict | None = None, embed=None,
                 threshold: float = C.CV_MATCH_THRESHOLD, max_skills: int = C.CV_MAX_SKILLS):
        self.skills = sorted(skill_map.vocabulary)
        self.threshold = threshold
        self.max_skills = max_skills
        self.embed = embed or FastEmbedder()
        descriptions = descriptions or {}
        # Each skill is represented by several texts: its name, name + definition, and every ESCO skill
        # label that evidences it (aliases). A CV phrase's similarity to a skill is its best match.
        texts, owner = [], []
        self.aliases: dict[str, list[str]] = {}
        for j, s in enumerate(self.skills):
            d = descriptions.get(s, {})
            al = [normalise(a) for a in d.get("esco_aliases", [])]
            kw = [normalise(k) for k in d.get("keywords", [])]
            self.aliases[s] = [a for a in al if len(a) >= MIN_EXACT_ALIAS_LEN] + kw
            for t in [s, f"{s}. {d.get('description', '')}".strip(" ."), *al]:
                texts.append(t)
                owner.append(j)
        self._owner = np.array(owner)
        self._exact_name = {}
        for j, sk in enumerate(self.skills):
            for term in [sk, *self.aliases[sk]]:
                self._exact_name.setdefault(term, j)
        self._text_vecs = self.embed(texts)

    @classmethod
    def from_files(cls, skill_map: SkillMap, descriptions_path: str | None = None, **kw):
        path = descriptions_path or os.path.join(ROOT, "data", "skill_descriptions.json")
        desc = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
        return cls(skill_map, desc, **kw)

    def extract(self, text: str) -> list[DetectedSkill]:
        segs = segments(text)
        found: dict[str, DetectedSkill] = {}
        low = " " + normalise(text) + " "
        for s in self.skills:  # verbatim mention of the skill name or one of its ESCO labels
            for term in [s, *self.aliases.get(s, [])]:
                if re.search(r"(?<![a-z0-9+#.])" + re.escape(term) + r"(?![a-z0-9+#])", low):
                    ev = next((g for g in segs if term in normalise(g)), term)
                    found[s] = DetectedSkill(s, 1.0, ev, "exact")
                    break
        if segs:
            seg_vecs = self.embed(segs)
            per_text = seg_vecs @ self._text_vecs.T  # (segments, texts)
            sim = np.full((len(segs), len(self.skills)), -1.0, dtype=np.float32)
            for j in range(len(self.skills)):  # best text per skill
                sim[:, j] = per_text[:, self._owner == j].max(axis=1)
            # Each CV phrase may support at most PER_SEGMENT skills (its closest ones), so one vague
            # phrase cannot propose a long list; one- or two-word phrases need a stronger match.
            keep = np.zeros_like(sim, dtype=bool)
            top = np.argsort(-sim, axis=1, kind="stable")[:, :PER_SEGMENT]
            np.put_along_axis(keep, top, True, axis=1)
            short = np.array([len(g.split()) <= 2 for g in segs])
            keep[short] = False  # a one- or two-word phrase supports only its single closest skill
            keep[short, top[short, 0]] = True
            # A phrase that exactly names a skill (or one of its aliases) is evidence for that skill only,
            # not for neighbouring skills that merely sound similar.
            for i, g in enumerate(segs):
                owner = self._exact_name.get(normalise(g).strip(" .:"))
                if owner is not None:
                    keep[i] = False
                    keep[i, owner] = True
            need = np.where(short, max(self.threshold, SHORT_PHRASE_THRESHOLD), self.threshold)[:, None]
            sim = np.where(keep & (sim >= need), sim, -1.0)
            best_seg = sim.argmax(axis=0)
            best = sim.max(axis=0)
            for j, s in enumerate(self.skills):
                score = round(float(best[j]), 3)
                if s not in found and score >= self.threshold:
                    found[s] = DetectedSkill(s, score, segs[int(best_seg[j])], "semantic")
        ranked = sorted(found.values(), key=lambda d: (-d.score, d.skill))
        return ranked[: self.max_skills]
