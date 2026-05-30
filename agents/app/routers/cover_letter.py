from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.cover_letter.run import run_cover_letter
from app.services.resume.parser import load_resume

router = APIRouter(prefix="/api/cover-letter", tags=["cover-letter"])


class CoverLetterBody(BaseModel):
    resumeId: str
    companyName: str
    roleTitle: str
    jdText: str | None = None
    companyDomain: str | None = None
    confirmed: bool = False


@router.post("/run")
async def cover_letter_run(body: CoverLetterBody):
    if not body.confirmed:
        raise HTTPException(400, "Please confirm your resume information is accurate.")
    if not body.companyName.strip() or not body.roleTitle.strip():
        raise HTTPException(400, "companyName and roleTitle are required.")
    if not load_resume(body.resumeId):
        raise HTTPException(404, "Resume not found. Upload again from home.")
    try:
        return await run_cover_letter(
            body.resumeId,
            body.companyName.strip(),
            body.roleTitle.strip(),
            jd_text=(body.jdText or "").strip() or None,
            company_domain=(body.companyDomain or "").strip() or None,
        )
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    except Exception as e:
        raise HTTPException(500, str(e)) from e
