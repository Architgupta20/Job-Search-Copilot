from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import MAX_UPLOAD_BYTES
from app.services.resume.parser import (
    build_parsed_facts,
    extract_text,
    load_resume,
    save_resume,
)

router = APIRouter(prefix="/api/resume", tags=["resume"])


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "No file provided.")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(400, "File must be 10 MB or smaller.")

    lower = file.filename.lower()
    if not (lower.endswith(".docx") or lower.endswith(".pdf")):
        raise HTTPException(400, "Only PDF and DOCX files are supported.")

    mime = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if lower.endswith(".docx")
        else "application/pdf"
    )

    try:
        raw = extract_text(data, file.filename)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    if not raw or len(raw) < 50:
        raise HTTPException(
            422,
            "Could not extract enough text. Try DOCX format.",
        )

    facts = build_parsed_facts(raw)
    record = save_resume(data, file.filename, mime, facts)
    return {
        "id": record["id"],
        "fileName": record["fileName"],
        "uploadedAt": record["uploadedAt"],
        "contact": facts["contact"],
        "claimCount": len(facts["allowedClaims"]),
    }


@router.get("/{resume_id}")
async def get_resume(resume_id: str):
    record = load_resume(resume_id)
    if not record:
        raise HTTPException(404, "Resume not found.")
    return record
