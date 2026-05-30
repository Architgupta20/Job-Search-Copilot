from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.interview_prep.run import run_interview_prep
from app.services.resume.parser import load_resume

router = APIRouter(prefix="/api/interview-prep", tags=["interview-prep"])


class InterviewPrepBody(BaseModel):
    resumeId: str
    companyName: str
    roleTitle: str
    jdText: str | None = None
    confirmed: bool = False


@router.post("/run")
async def interview_prep_run(body: InterviewPrepBody):
    if not body.confirmed:
        raise HTTPException(400, "Please confirm your resume information is accurate.")
    if not body.companyName.strip() or not body.roleTitle.strip():
        raise HTTPException(400, "companyName and roleTitle are required.")
    if not load_resume(body.resumeId):
        raise HTTPException(404, "Resume not found. Upload again from home.")
    try:
        return await run_interview_prep(
            body.resumeId,
            body.companyName.strip(),
            body.roleTitle.strip(),
            jd_text=(body.jdText or "").strip() or None,
        )
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    except Exception as e:
        raise HTTPException(500, str(e)) from e
