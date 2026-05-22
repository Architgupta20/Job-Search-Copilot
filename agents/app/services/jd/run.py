import json
import re
import uuid
import zipfile
from io import BytesIO
from pathlib import Path

from docx import Document
from docx.shared import Pt

from app.config import JD_RUNS_DIR
from app.services.llm.client import tailor_resume_llm
from app.services.resume.parser import load_resume

SECTION_HEADERS = [
    "WORK EXPERIENCE", "EDUCATION", "PROJECTS", "SKILLS", "SUMMARY", "EXPERIENCE",
]


def normalize_line_breaks(text: str) -> str:
    result = text.replace("\r\n", "\n").strip()
    if "\n\n" not in result:
        for h in SECTION_HEADERS:
            result = re.sub(rf"\s+({h}:?)", r"\n\n\1\n", result, flags=re.I)
    result = re.sub(r"([.!?])\s+(-\s+)", r"\1\n\2", result)
    return re.sub(r"\n{3,}", "\n\n", result)


def extract_jd_keywords(jd_text: str) -> list[str]:
    words = re.findall(r"[a-z0-9+.#-]{3,}", jd_text.lower())
    stop = {"the", "and", "for", "with", "you", "will", "our", "are", "this", "that"}
    freq: dict[str, int] = {}
    for w in words:
        if w not in stop:
            freq[w] = freq.get(w, 0) + 1
    top = sorted(freq, key=freq.get, reverse=True)[:25]
    return top[:40]


def ats_score(jd_keywords: list[str], claims: list[str], used: list[str]) -> int:
    if not jd_keywords:
        return 0
    blob = " ".join(claims).lower()
    supported = sum(
        1
        for kw in jd_keywords
        if kw in blob or any(kw in u.lower() for u in used)
    )
    return round(supported / len(jd_keywords) * 100)


async def run_jd_tailor(resume_id: str, jd_text: str) -> dict:
    resume = load_resume(resume_id)
    if not resume:
        raise ValueError("Resume not found.")

    facts = resume["parsedFacts"]
    tailored = await tailor_resume_llm({
        "jobDescription": jd_text[:8000],
        "jdKeywords": extract_jd_keywords(jd_text),
        "allowedClaims": facts["allowedClaims"][:120],
        "originalResume": facts["rawText"][:12000],
    })

    text = normalize_line_breaks(tailored.get("tailoredText", "").strip())
    if not text:
        raise ValueError("Tailoring produced no content.")

    warnings = []
    skipped = tailored.get("keywordsSkipped") or []
    if skipped:
        warnings.append(
            f"{len(skipped)} JD keyword(s) not added (not in your resume)."
        )

    run_id = str(uuid.uuid4())
    result = {
        "runId": run_id,
        "resumeId": resume_id,
        "jdTitle": tailored.get("jdTitle"),
        "tailoredText": text,
        "keywordsUsed": tailored.get("keywordsUsed") or [],
        "keywordsSkipped": skipped,
        "atsScorePercent": ats_score(
            extract_jd_keywords(jd_text),
            facts["allowedClaims"],
            tailored.get("keywordsUsed") or [],
        ),
        "changeSummary": tailored.get("changeSummary") or [],
        "warnings": warnings,
    }
    JD_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    (JD_RUNS_DIR / f"{run_id}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def build_docx_bytes(tailored_text: str, original_path: str | None, is_docx: bool) -> bytes:
    if is_docx and original_path and Path(original_path).exists():
        try:
            return _merge_docx_template(original_path, tailored_text)
        except Exception:
            pass
    doc = Document()
    for line in tailored_text.splitlines():
        p = doc.add_paragraph(line.strip() or "")
        if line.strip().isupper() and len(line.strip()) < 50:
            for run in p.runs:
                run.bold = True
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _merge_docx_template(original_path: str, tailored_text: str) -> bytes:
    lines = tailored_text.splitlines()
    with zipfile.ZipFile(original_path, "r") as zin:
        files = {name: zin.read(name) for name in zin.namelist()}
    xml = files["word/document.xml"].decode("utf-8")
    paras = re.findall(r"<w:p\b[^>]*>[\s\S]*?</w:p>", xml)
    sect = re.search(r"<w:sectPr[\s\S]*?</w:sectPr>", xml)
    sect_pr = sect.group(0) if sect else ""
    new_paras = []
    for i, p_xml in enumerate(paras):
        line = lines[i] if i < len(lines) else ""
        safe = (
            line.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
        ppr = re.search(r"<w:pPr[\s\S]*?</w:pPr>|<w:pPr[^/]*/>", p_xml)
        rpr = re.search(r"<w:rPr[\s\S]*?</w:rPr>|<w:rPr[^/]*/>", p_xml)
        ppr_s = ppr.group(0) if ppr else ""
        rpr_s = rpr.group(0) if rpr else ""
        new_paras.append(
            f"<w:p>{ppr_s}<w:r>{rpr_s}<w:t xml:space=\"preserve\">{safe}</w:t></w:r></w:p>"
        )
    for j in range(len(paras), len(lines)):
        safe = lines[j].replace("&", "&amp;").replace("<", "&lt;")
        new_paras.append(f'<w:p><w:r><w:t xml:space="preserve">{safe}</w:t></w:r></w:p>')
    body = "".join(new_paras) + sect_pr
    new_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}</w:body></w:document>"
    )
    files["word/document.xml"] = new_xml.encode("utf-8")
    out = BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in files.items():
            zout.writestr(name, data)
    return out.getvalue()


def load_jd_run(run_id: str) -> dict | None:
    p = JD_RUNS_DIR / f"{run_id}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))
