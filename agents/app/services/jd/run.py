import json
import re
import uuid
from io import BytesIO

from docx import Document

from app.config import JD_RUNS_DIR

_EMAIL_IN_LINE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
from app.services.llm.client import rewrite_resume_bullets_llm
from app.services.resume.parser import load_resume

SECTION_HEADERS = [
    "WORK EXPERIENCE", "EDUCATION", "PROJECTS", "SKILLS", "SUMMARY", "EXPERIENCE",
]

CANONICAL_SECTIONS = {
    "work experience": "Work Experience",
    "experience": "Work Experience",
    "professional experience": "Work Experience",
    "employment": "Work Experience",
    "employment history": "Work Experience",
    "relevant experience": "Work Experience",
    "internship": "Work Experience",
    "internships": "Work Experience",
    "education": "Education",
    "academic background": "Education",
    "projects": "Projects",
    "personal projects": "Projects",
    "skills": "Skills",
    "technical skills": "Skills",
    "core competencies": "Skills",
    "summary": "Summary",
    "professional summary": "Summary",
    "objective": "Summary",
    "profile": "Summary",
    "certifications": "Certifications",
    "achievements": "Achievements",
    "awards": "Achievements",
}

# Map regex on header text → display section name
_SECTION_HEADER_RULES: list[tuple[str, str]] = [
    (r"work|professional|employment|internship|career", "Work Experience"),
    (r"education|academic|university|degree", "Education"),
    (r"project", "Projects"),
    (r"skill|competenc|technolog|tools|expertise", "Skills"),
    (r"summary|objective|profile|about me", "Summary"),
    (r"certif", "Certifications"),
    (r"achieve|award|honor", "Achievements"),
]


def normalize_line_breaks(text: str) -> str:
    result = text.replace("\r\n", "\n").strip()
    if "\n\n" not in result:
        for h in SECTION_HEADERS:
            result = re.sub(rf"\s+({h}:?)", r"\n\n\1\n", result, flags=re.I)
    result = re.sub(r"([.!?])\s+(-\s+)", r"\1\n\2", result)
    return re.sub(r"\n{3,}", "\n\n", result)


ALLOW_SHORT_KEYWORDS = frozenset(
    {"sql", "api", "ml", "ai", "etl", "aws", "gcp", "nlp", "llm", "bi", "ux", "pm"}
)

JD_KEYWORD_STOP = frozenset(
    {
        "the", "and", "for", "with", "you", "will", "our", "are", "this", "that",
        "role", "about", "what", "your", "have", "from", "into", "been", "were",
        "who", "has", "had", "not", "need", "just", "some", "any", "all", "can",
        "may", "also", "able", "own", "work", "build", "using", "use", "used",
        "help", "make", "like", "well", "good", "best", "new", "one", "two",
        "job", "team", "company", "years", "year", "day", "days", "time", "times",
        "minutes", "hour", "hours", "people", "person", "world", "life", "way",
        "noon", "forward", "encountered", "young", "aggressive", "talented",
        "fastest", "smartest", "hardest-working", "hardest", "working", "major",
        "missions", "driving", "across",
    }
)

# Missing JD keyword is weave-safe if resume already implies it via related terms.
KEYWORD_SUPPORT_ROOTS: dict[str, tuple[str, ...]] = {
    "experimentation": ("experiment", "testing", "test", "a/b", "ab ", "variant"),
    "lifecycle": ("lifecycle", "campaign", "funnel", "retention", "cohort"),
    "incrementality": ("increment", "lift", "causal", "experiment", "testing"),
    "commercial": ("commercial", "revenue", "pricing", "sales", "business"),
    "promotional": ("promotion", "promo", "campaign", "marketing"),
    "customer": ("customer", "client", "user", "stakeholder"),
    "scientist": ("scientist", "science", "research", "model", "analytics"),
    "models": ("model", "ml", "machine", "prediction", "forecast"),
    "growth": ("growth", "acquisition", "retention", "conversion"),
    "analytics": ("analytics", "analysis", "insights", "metric", "dashboard"),
    "product": ("product", "roadmap", "feature", "requirements"),
    "systems": ("system", "platform", "pipeline", "architecture"),
}


def _is_quality_jd_keyword(word: str) -> bool:
    w = word.lower().strip()
    if not w:
        return False
    if w in ALLOW_SHORT_KEYWORDS:
        return True
    if len(w) < 4:
        return False
    if w in JD_KEYWORD_STOP:
        return False
    if w.isdigit():
        return False
    return True


def extract_jd_keywords(jd_text: str) -> list[str]:
    words = re.findall(r"[a-z0-9+.#-]{3,}", jd_text.lower())
    freq: dict[str, int] = {}
    for w in words:
        if _is_quality_jd_keyword(w):
            freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:30]]


def _resume_can_support_keyword(kw: str, resume_blob: str) -> bool:
    low = resume_blob.lower()
    if kw in low:
        return True
    for root in KEYWORD_SUPPORT_ROOTS.get(kw, ()):
        if root in low:
            return True
    return False


def _related_to_bullet(kw: str, bullet: str) -> bool:
    b = _tokens(bullet)
    k = _tokens(kw)
    if k & b:
        return True
    for bt in b:
        for kt in k:
            if len(kt) >= 4 and (bt.startswith(kt[:4]) or kt.startswith(bt[:4])):
                return True
    return False


def _build_weave_keywords(
    bullet: str,
    *,
    jd_keywords: list[str],
    resume_blob: str,
    max_keywords: int = 12,
) -> tuple[list[str], list[str]]:
    """
    Returns (keywords_to_weave, missing_keywords_targeted).
    Includes already-matched bullet keywords + missing JD keywords the resume can support.
    """
    text_low = bullet.lower()
    matched = [kw for kw in jd_keywords if kw in text_low]
    weave: list[str] = list(matched)
    missing_targets: list[str] = []

    for kw in jd_keywords:
        if kw in weave:
            continue
        if kw in text_low:
            continue
        if not _resume_can_support_keyword(kw, resume_blob):
            continue
        if not (_related_to_bullet(kw, bullet) or kw in resume_blob):
            continue
        weave.append(kw)
        missing_targets.append(kw)
        if len(weave) >= max_keywords:
            break

    return weave[:max_keywords], missing_targets[:8]


def compute_ats_breakdown(
    jd_keywords: list[str],
    claims: list[str],
    used: list[str],
) -> dict:
    blob = " ".join(claims).lower()
    used_blob = " ".join(used).lower()
    blob_tokens = set(re.findall(r"[a-z0-9+#.-]{3,}", f"{blob} {used_blob}"))
    matched: list[str] = []
    missing: list[str] = []
    for kw in jd_keywords:
        roots = KEYWORD_SUPPORT_ROOTS.get(kw, ())
        supported_by_root = any(root in blob or root in used_blob for root in roots)
        # Lightweight stem-family fallback: experiment ~= experimentation, model ~= models, etc.
        stem = kw[:5] if len(kw) >= 5 else kw
        supported_by_stem = any(
            tok.startswith(stem) or stem.startswith(tok[:5] if len(tok) >= 5 else tok)
            for tok in blob_tokens
        )
        if (
            kw in blob
            or kw in used_blob
            or any(kw in u.lower() for u in used)
            or supported_by_root
            or supported_by_stem
        ):
            matched.append(kw)
        else:
            missing.append(kw)
    total = len(jd_keywords) or 1
    score = round(len(matched) / total * 100)
    return {
        "scorePercent": score,
        "totalKeywords": len(jd_keywords),
        "matchedKeywords": matched,
        "missingKeywords": missing,
        "supportedCount": len(matched),
    }


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def _tokens(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9+#.-]{3,}", (s or "").lower()))


def _header_to_section_name(header: str) -> str:
    key = _norm(header).lower().rstrip(":")
    if key in CANONICAL_SECTIONS:
        return CANONICAL_SECTIONS[key]
    for pattern, name in _SECTION_HEADER_RULES:
        if re.search(pattern, key):
            return name
    cleaned = _norm(header).rstrip(":")
    if cleaned and len(cleaned) <= 80:
        if cleaned.isupper():
            return cleaned.title()
        return cleaned
    return "Other"


def _is_section_header(line: str) -> bool:
    t = _norm(line)
    if not t or len(t) > 90:
        return False
    low = t.lower().rstrip(":")
    if low in CANONICAL_SECTIONS:
        return True
    for pattern, _ in _SECTION_HEADER_RULES:
        if re.search(pattern, low):
            return True
    # Typical resume headings: short ALL CAPS line
    alpha = re.sub(r"[^A-Za-z]", "", t)
    words = t.split()
    if (
        len(words) <= 8
        and len(alpha) >= 3
        and alpha.isupper()
        and not _EMAIL_IN_LINE.search(t)
    ):
        return True
    return False


def _extract_resume_sections(raw_text: str) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    current_name = "Header / Contact"
    current_lines: list[str] = []

    for raw in raw_text.splitlines():
        line = _norm(raw)
        if not line:
            continue
        if _is_section_header(line):
            if current_lines:
                sections.append((current_name, current_lines))
            current_name = _header_to_section_name(line)
            current_lines = []
            continue
        current_lines.append(line)

    if current_lines:
        sections.append((current_name, current_lines))
    return sections


JD_PHRASE_PATTERNS = (
    r"\ba plus\b",
    r"\brequired\b",
    r"\bpreferred\b",
    r"\bmust have\b",
    r"\bwe are looking\b",
    r"\byou will\b",
    r"\bcandidates?\b",
    r"\bqualifications?\b",
    r"\ball about you\b",
    r"\bskills required\b",
    r"\bresponsibilities\b",
    r"\bwhat you.ll\b",
)


def _section_for_line(line: str, sections: list[tuple[str, list[str]]]) -> str:
    line_low = _norm(line).lower()
    if not line_low:
        return "General"
    for section_name, lines in sections:
        for entry in lines:
            entry_low = _norm(entry).lower()
            if line_low in entry_low or entry_low in line_low:
                return section_name
    return "General"


def _is_valid_resume_bullet(line: str) -> bool:
    if len(line) < 25:
        return False
    if line.isupper() and len(line) < 90:
        return False
    if re.match(r"^[\w\s/&+-]+:$", line):
        return False
    return True


def _line_in_resume(line: str, resume_text: str) -> bool:
    line_l = _norm(line).lower()
    resume_l = resume_text.lower()
    if line_l in resume_l:
        return True
    line_tokens = _tokens(line)
    if not line_tokens:
        return False
    for raw in resume_text.splitlines():
        chunk = _norm(raw)
        if len(chunk) < 20:
            continue
        overlap = len(line_tokens & _tokens(chunk))
        if overlap / max(len(line_tokens), 1) >= 0.88:
            return True
    return False


def _looks_like_jd_requirement(line: str, jd_text: str, resume_text: str) -> bool:
    line_l = _norm(line).lower()
    if not _line_in_resume(line, resume_text):
        return True
    jd_l = jd_text.lower()
    if len(line_l) > 35 and line_l in jd_l:
        # Long sentence copied from posting — only allow if clearly present in resume upload.
        if line_l not in resume_text.lower():
            return True
    for pat in JD_PHRASE_PATTERNS:
        if re.search(pat, line_l):
            return True
    return False


def _extract_resume_bullets(
    raw_text: str, allowed_claims: list[str]
) -> list[tuple[str, str]]:
    """Return (section, bullet_text) only from the uploaded resume."""
    sections = _extract_resume_sections(raw_text)
    seen: set[str] = set()
    out: list[tuple[str, str]] = []

    def add(section: str, text: str) -> None:
        t = _norm(text)
        key = t.lower()
        if not _is_valid_resume_bullet(t) or key in seen:
            return
        seen.add(key)
        out.append((section, t))

    for section_name, lines in sections:
        for line in lines:
            add(section_name, line)

    for claim in allowed_claims:
        t = _norm(claim)
        if not t:
            continue
        section = _section_for_line(t, sections)
        add(section, t)

    return out


def _jd_keywords_in_bullet(bullet: str, jd_keywords: list[str]) -> list[str]:
    blob = bullet.lower()
    return [kw for kw in jd_keywords if kw in blob]


def _guess_jd_title(jd_text: str) -> str | None:
    for line in jd_text.splitlines()[:8]:
        t = _norm(line)
        if 8 < len(t) < 90 and re.search(
            r"engineer|analyst|manager|scientist|developer|designer|lead|architect",
            t,
            re.I,
        ):
            return t
    first = _norm(jd_text.splitlines()[0]) if jd_text.splitlines() else ""
    return first[:90] if first else None


def _simple_rewrite(bullet: str, keywords: list[str]) -> str:
    """Fallback when LLM rewrite missing — keep original facts and wording style."""
    text = _norm(bullet).strip("- ").rstrip(".")
    if not keywords:
        return text
    head = [w for w in text.split() if len(w) > 0]
    missing = [kw for kw in keywords if kw.lower() not in text.lower()]
    if missing:
        # Weave available JD keywords without adding new factual claims.
        head = missing[:2] + head
    return " ".join(head)


def _word_tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9+#./%-]+", text)


def _enforce_bullet_word_window(
    suggested: str,
    *,
    original: str,
    keywords: list[str],
    missing_priority: list[str] | None = None,
    min_words: int = 19,
    max_words: int = 20,
) -> str:
    """
    Force rewritten bullet to 19–20 words using only resume-safe wording.
    - Removes obvious append style tails.
    - Keeps/uses words from original bullet as padding source.
    """
    cand = _norm(suggested).strip("- ").rstrip(".")
    orig = _norm(original).strip("- ").rstrip(".")
    if not cand:
        cand = orig

    # Remove common append-pattern tail produced by weak rewrites.
    cand = re.sub(r"\s+[—-]\s*emphasizing\s+.+$", "", cand, flags=re.I)
    cand = re.sub(r"\s+[—-]\s*highlighting\s+.+$", "", cand, flags=re.I)

    # If model mostly echoed original + suffix, prefer original then weave keywords.
    if cand.lower().startswith(orig.lower()) and len(cand) > len(orig) + 12:
        cand = orig

    words = _word_tokens(cand)
    orig_words = _word_tokens(orig)

    # If too short, add missing JD keywords first (ATS boost), then other weave words.
    if len(words) < min_words:
        priority = list(missing_priority or [])
        for kw in priority + [k for k in keywords if k not in priority]:
            kw_tokens = _word_tokens(kw)
            for t in kw_tokens:
                if len(words) >= min_words:
                    break
                if t.lower() not in {w.lower() for w in words}:
                    words.append(t)
            if len(words) >= min_words:
                break

    if len(words) < min_words:
        for t in orig_words:
            if len(words) >= min_words:
                break
            words.append(t)

    # Trim to max words.
    if len(words) > max_words:
        words = words[:max_words]

    # Final safety: if still short due to empty original, repeat last token.
    while len(words) < min_words and words:
        words.append(words[-1])

    out = " ".join(words).strip()
    return out


def _apply_edits_to_resume(raw_text: str, edits: list[dict]) -> str:
    updated = raw_text
    for e in edits:
        orig = e.get("original") or ""
        sugg = e.get("suggested") or ""
        if orig and sugg and orig in updated:
            updated = updated.replace(orig, sugg, 1)
    return normalize_line_breaks(updated)


async def _build_edits_from_resume(
    *,
    raw_text: str,
    allowed_claims: list[str],
    jd_text: str,
    jd_keywords: list[str],
    max_edits: int = 8,
) -> list[dict]:
    bullets = _extract_resume_bullets(raw_text, allowed_claims)
    resume_blob = " ".join(allowed_claims).lower()
    selected: list[tuple[int, str, str, list[str], list[str], list[str]]] = []

    for section, text in bullets:
        if _looks_like_jd_requirement(text, jd_text, raw_text):
            continue
        hits = _jd_keywords_in_bullet(text, jd_keywords)
        weave, missing_targets = _build_weave_keywords(
            text,
            jd_keywords=jd_keywords,
            resume_blob=resume_blob,
        )
        if not weave:
            continue
        score = (len(missing_targets) * 4) + len(weave) + len(hits)
        selected.append((score, section, text, weave, missing_targets, hits))

    selected.sort(key=lambda x: x[0], reverse=True)
    selected = selected[:max_edits]

    if not selected:
        return []

    llm_payload = [
        {
            "id": i + 1,
            "section": section,
            "original": text,
            "keywordsToWeave": weave,
            "missingKeywordsPriority": missing_targets,
            "alreadyInBullet": hits,
        }
        for i, (_, section, text, weave, missing_targets, hits) in enumerate(selected)
    ]
    rewrites = await rewrite_resume_bullets_llm(llm_payload)

    edits: list[dict] = []
    for i, (_, section, text, weave, missing_targets, hits) in enumerate(selected):
        rid = i + 1
        suggested_raw = rewrites.get(rid) or _simple_rewrite(text, weave)
        suggested = _enforce_bullet_word_window(
            suggested_raw,
            original=text,
            keywords=weave,
            missing_priority=missing_targets,
        )
        added_in_rewrite = [
            kw for kw in weave if kw in suggested.lower() and kw not in text.lower()
        ]
        edits.append(
            {
                "section": section,
                "sectionHint": (
                    f"In your resume file, open the \"{section}\" section and replace this bullet."
                ),
                "original": text,
                "suggested": suggested,
                "matchedKeywords": hits[:8],
                "targetMissingKeywords": missing_targets,
                "addedKeywords": added_in_rewrite,
                "reason": (
                    f"Picked from \"{section}\". "
                    f"Targets missing JD keywords: {', '.join(missing_targets[:6]) or '—'}. "
                    "Full rewrite only (19–20 words), no invented experience."
                ),
            }
        )
    return edits


async def run_jd_tailor(resume_id: str, jd_text: str) -> dict:
    resume = load_resume(resume_id)
    if not resume:
        raise ValueError("Resume not found.")

    facts = resume["parsedFacts"]
    raw_text = facts["rawText"]
    claims = facts["allowedClaims"]
    jd_keywords = extract_jd_keywords(jd_text)

    suggested_edits = await _build_edits_from_resume(
        raw_text=raw_text,
        allowed_claims=claims,
        jd_text=jd_text,
        jd_keywords=jd_keywords,
    )

    if suggested_edits:
        text = _apply_edits_to_resume(raw_text, suggested_edits)
    else:
        text = normalize_line_breaks(raw_text)

    resume_blob = " ".join(claims).lower()
    keywords_used: list[str] = []
    for kw in jd_keywords:
        if kw in resume_blob or any(
            kw in (e.get("suggested") or "").lower() for e in suggested_edits
        ):
            if kw not in keywords_used:
                keywords_used.append(kw)

    skipped = [kw for kw in jd_keywords if kw not in keywords_used]
    ats = compute_ats_breakdown(jd_keywords, claims, keywords_used)

    warnings = [
        "Rewrites try to add missing JD keywords only when your resume already supports them (same domain/skills elsewhere).",
        "We do not invent employers, tools, or metrics. Copy each green rewrite into the section shown.",
    ]
    if not suggested_edits:
        warnings.append(
            "No resume bullets matched this JD yet. Try a role closer to your experience, or upload a resume with clearer bullet points."
        )
    if skipped:
        warnings.append(
            f"{len(skipped)} JD keyword(s) are not in your resume and were not invented."
        )

    change_summary = [
        (
            f"{e['section']} (#{i + 1}): added "
            f"{', '.join((e.get('addedKeywords') or [])[:4]) or 'JD-aligned wording'}"
        )
        for i, e in enumerate(suggested_edits)
    ]

    run_id = str(uuid.uuid4())
    result = {
        "runId": run_id,
        "resumeId": resume_id,
        "jdTitle": _guess_jd_title(jd_text),
        "tailoredText": text,
        "suggestedEdits": suggested_edits,
        "keywordsUsed": keywords_used,
        "keywordsSkipped": skipped,
        "atsScorePercent": ats["scorePercent"],
        "atsBreakdown": ats,
        "changeSummary": change_summary,
        "warnings": warnings,
    }
    JD_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    (JD_RUNS_DIR / f"{run_id}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def build_docx_bytes(tailored_text: str, _original_path: str | None = None, _is_docx: bool = False) -> bytes:
    """Plain DOCX export only — never merge into user's uploaded template."""
    doc = Document()
    for line in tailored_text.splitlines():
        p = doc.add_paragraph(line.strip() or "")
        if line.strip().isupper() and len(line.strip()) < 50:
            for run in p.runs:
                run.bold = True
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def load_jd_run(run_id: str) -> dict | None:
    p = JD_RUNS_DIR / f"{run_id}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))
